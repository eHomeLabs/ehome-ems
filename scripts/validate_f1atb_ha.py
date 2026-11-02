"""Real HA lifecycle/WS checks against a simulated local F1ATB, never real hardware."""
from copy import deepcopy
import json
from aiohttp import web, ThreadedResolver
from unittest.mock import patch
from homeassistant.helpers import entity_registry as er


async def validate_native_router(hass, entry, command):
    from custom_components.ehome_ems.const import DOMAIN
    from custom_components.ehome_ems.f1atb_http import config_token
    gs, rs = chr(29), chr(30)
    config = {'secret':'simulated-secret', 'Actions':[{'Titre':'Demo SSR', 'Actif':2,
        'ForceOuvre':80,'Periodes':[{'Type':4,'Hfin':2400,'Vmax':70,'Vmin':-20,'Tsup':650}]}]}
    forces, writes, online = {}, [], [True]
    async def handle(request):
        if not online[0]:return web.Response(status=503)
        if request.path == '/ParaFixe':return web.json_response(config)
        if request.path == '/ajax_data':return web.Response(text=gs.join([rs.join(['Deb','','UxIx2','','','20|-127']),rs.join(['100','0','100','0','1','0','1000','0']),rs.join(['300','0','300','0','1','0','2000','0'])]))
        if request.path == '/ajax_etatActions':return web.Response(text=gs.join(['','','','1',rs.join(['0','Demo SSR','50',str(forces.get(0,0))])]))
        writes.append(request.path)
        if request.path == '/ForceAction':forces[0]=int(request.query['Force']);return web.Response(text='Force')
        if request.path == '/ParaNew':
            assert request.headers['Content-Type']=='text/plain'
            data=json.loads(await request.text());config.clear();config.update(data)
            return web.json_response({'new_config':'ok'})
        return web.Response(status=404)
    app=web.Application();app.router.add_route('*','/{path:.*}',handle)
    runner=web.AppRunner(app);await runner.setup()
    site=web.TCPSite(runner,'127.0.0.1',0);await site.start()
    host=f'http://127.0.0.1:{site._server.sockets[0].getsockname()[1]}'
    try:
        from homeassistant.helpers.aiohttp_client import async_get_clientsession
        from custom_components.ehome_ems.f1atb_http import F1atbClient
        # This test host has no multicast adapter. HTTP still uses a real socket
        # and HA-owned ClientSession, with a standard resolver for loopback only.
        resolver=ThreadedResolver();resolver.real_close=resolver.close
        with patch("homeassistant.helpers.aiohttp_client._async_make_resolver",return_value=resolver):
            await F1atbClient(async_get_clientsession(hass), host).read_config()
        discovery=await command({'type':'ehome_ems/router_discover','host':host})
        assert 'secret' not in json.dumps(discovery)
        online[0]=False
        created=await command({'type':'ehome_ems/manage_settings','entry_id':entry.entry_id,'revision':entry.modified_at.isoformat(),
            'section':'usages','action':'save','values':{'name':'Native demo','kind':'solar_router','router_type':'f1atb',
                'router_connection':'http','router_url':host,'router_action':0,'router_http_enabled':True,'included_in_home':True}})
        await hass.async_block_till_done()
        identifier=created['identifier']
        assert not writes
        registry=er.async_get(hass)
        sensor=lambda key: registry.async_get_entity_id('sensor',DOMAIN,f'{entry.entry_id}_router_{identifier}_{key}')
        coordinator=hass.data[DOMAIN]['router_http'][entry.entry_id][identifier]
        assert hass.states.get(sensor('connection')).state=='offline'
        assert hass.states.get(sensor('probe_power')).state=='unavailable'
        online[0]=True
        await coordinator.async_refresh()
        assert hass.states.get(sensor('connection')).state=='online'
        assert float(hass.states.get(sensor('probe_power')).state)==300
        assert float(hass.states.get(sensor('probe_energy_total_kwh')).state)==2
        assert hass.states.get(sensor('temperature_1')).state=='unavailable'
        snapshot=await command({'type':'ehome_ems/dashboard','entry_id':entry.entry_id})
        native=next(u for u in snapshot['flow']['usages'] if u['id']==identifier)
        assert native['router_native']['available']
        assert native['router_entities']['status']==sensor('status')
        assert 'simulated-secret' not in json.dumps(snapshot)
        msg={'type':'ehome_ems/router_command','entry_id':entry.entry_id,'identifier':identifier,'revision':entry.modified_at.isoformat()}
        assert (await command({**msg,'action':'force_on','values':{'minutes':30}}))['confirmed_by_router']
        assert forces[0]==30
        original=deepcopy(config)
        assert (await command({**msg,'action':'http_parameters','values':{'config_token':config_token(config),'forced_opening':60}}))['confirmed_by_router']
        original['Actions'][0]['ForceOuvre']=60
        assert config==original
        await command({**msg,'action':'http_parameters','values':{'config_token':'stale','forced_opening':50}},success=False)
        assert writes==['/ForceAction','/ParaNew']
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.entry_id not in hass.data[DOMAIN]['router_http']
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert float(hass.states.get(sensor('probe_power')).state)==300
        await command({'type':'ehome_ems/manage_settings','entry_id':entry.entry_id,'revision':entry.modified_at.isoformat(),
            'section':'usages','action':'remove','identifier':identifier,'values':{}})
        await hass.async_block_till_done()
        assert entry.entry_id not in hass.data[DOMAIN]['router_http']
        assert writes==['/ForceAction','/ParaNew']
        print('PASS native F1ATB: direct HTTP, secrets redacted, measurements, manual writes, conflict, unload/reload')
    finally:
        await runner.cleanup()
