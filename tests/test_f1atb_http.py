"""Native HTTP interoperability against a local simulated ESP32 server."""
import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import importlib
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, AsyncMock

import aiohttp
from aiohttp import web

package = ModuleType('ems_http_test')
package.__path__ = [str(Path(__file__).resolve().parents[1] / 'custom_components/ehome_ems')]
with patch.dict(sys.modules, {'ems_http_test': package}):
    api = importlib.import_module('ems_http_test.f1atb_http')

GS, RS = chr(29), chr(30)


def config_fixture():
    return {'ssid': 'never_expose', 'secret': 'never_expose', 'unknown_field': {'keep': True}, 'Actions': [
        {'Titre': 'Triac', 'Actif': 2, 'ForceOuvre': 80,
         'Periodes': [{'Type': 4, 'Hfin': 1200, 'Vmax': 70, 'Vmin': -30, 'Tsup': 650},
                      {'Type': 1, 'Hfin': 2400, 'Vmax': 0}]},
        {'Titre': 'SSR', 'Actif': 1, 'ForceOuvre': 100,
         'Periodes': [{'Type': 3, 'Vmax': 1000, 'Vmin': -500}]}]}


def live_fixture():
    return GS.join([RS.join(['Deb','date','UxIx2','','','20|-127|nan|25']),
                    RS.join(map(str,[100,0,110,0,5,0,2000,0])),
                    RS.join(map(str,[800,0,900,0,500,0,12345,0]))])


def runtime_module():
    coordinator = ModuleType('homeassistant.helpers.update_coordinator')
    coordinator.DataUpdateCoordinator = object
    coordinator.UpdateFailed = RuntimeError
    session = ModuleType('homeassistant.helpers.aiohttp_client')
    session.async_get_clientsession = lambda h: h.session
    with patch.dict(sys.modules, {'ems_http_test':package, 'ems_http_test.f1atb_http':api,
        'homeassistant':ModuleType('homeassistant'), 'homeassistant.helpers':ModuleType('homeassistant.helpers'),
        'homeassistant.helpers.aiohttp_client':session, 'homeassistant.helpers.update_coordinator':coordinator}):
        return importlib.import_module('ems_http_test.f1atb_runtime')


runtime = runtime_module()


class HttpRouterTests(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.config, self.calls, self.forces, self.ignore_write = config_fixture(), [], {}, False
        self.fail_live=False
        async def handle(request):
            self.calls.append((request.method,request.path,dict(request.query)))
            if request.path == '/ParaFixe':return web.json_response(self.config)
            if request.path == '/ajax_data' and self.fail_live:return web.Response(status=503)
            if request.path == '/ajax_data':return web.Response(text=live_fixture())
            if request.path == '/ajax_etatActions':return web.Response(text=GS.join(['','','','2',RS.join(['0','Triac','50',str(self.forces.get(0,0))]),RS.join(['1','SSR','Off',str(self.forces.get(1,0))])]))
            if request.path == '/ForceAction':
                self.forces[int(request.query['NumAction'])] = int(request.query['Force'])
                return web.Response(text='Force')
            if request.path == '/ParaNew':
                self.assertEqual(request.headers['Content-Type'],'text/plain')
                received = json.loads(await request.text())
                if not self.ignore_write:self.config=received
                return web.json_response({'new_config':'ok'})
            return web.Response(status=404)
        app=web.Application();app.router.add_route('*','/{path:.*}',handle)
        self.runner=web.AppRunner(app);await self.runner.setup()
        site=web.TCPSite(self.runner,'127.0.0.1',0);await site.start()
        self.host=f'http://127.0.0.1:{site._server.sockets[0].getsockname()[1]}'
        self.session=aiohttp.ClientSession();self.client=api.F1atbClient(self.session,self.host)
        self.usage={'kind':'solar_router','router_type':'f1atb','router_connection':'http','router_http_enabled':True,'router_action':0,'router_url':self.host}
        self.entry=SimpleNamespace(entry_id='entry',modified_at=datetime.now(timezone.utc),options={'usages':{'r':self.usage}})
        self.coordinator=SimpleNamespace(client=self.client,lock=asyncio.Lock(),async_refresh=AsyncMock())
        self.hass=SimpleNamespace(data={'ehome_ems':{'router_http':{'entry':{'r':self.coordinator}}}})

    async def asyncTearDown(self):
        await self.session.close();await self.runner.cleanup()

    async def command(self, action, values, revision=None):
        return await runtime.async_http_command(self.hass,self.entry,'r',revision or self.entry.modified_at.isoformat(),action,values)

    async def test_read_only_discovery_redacts_credentials_preserves_missing_measurements(self):
        data=await self.client.read()
        self.assertNotIn('never_expose',json.dumps(data))
        self.assertEqual(data['probe_energy_total_kwh'],12.345)
        self.assertEqual(data['live_actions'][1]['opening'],0)
        self.assertEqual(data['temperatures'],[20,None,None,25])
        self.assertEqual(data['actions'][1]['name'],'SSR')
        self.assertEqual(api.base_url('HTTP://Router.Example.Local:80/'),'http://router.example.local')
        self.assertTrue(all(method=='GET' and path!='/ForceAction' for method,path,_ in self.calls))
        missing=api.parse_live(live_fixture().split(GS)[0]+GS+live_fixture().split(GS)[1]+GS+'Fake',GS.join(['','','','0']))
        self.assertIsNone(missing['probe_power']);self.assertIsNone(missing['probe_energy_total_kwh'])
        for value in ['<html>login</html>', 'Deb'+GS+'0'+GS+'Fake']:
            with self.assertRaises(api.RouterError):api.parse_live(value,'')

    async def test_persistent_patch_preserves_schedules_secrets_other_actions_and_checks_readback(self):
        original=deepcopy(self.config)
        result=await self.command('http_parameters',{'config_token':api.config_token(self.config),'forced_opening':60,'period':0,'opening_max':55})
        self.assertTrue(result['confirmed_by_router']);self.assertTrue(result['persistent'])
        original['Actions'][0]['ForceOuvre']=60;original['Actions'][0]['Periodes'][0]['Vmax']=55
        self.assertEqual(self.config,original)
        self.assertEqual(sum(path=='/ParaNew' for _,path,_ in self.calls),1)
        self.ignore_write=True
        result=await self.command('http_parameters',{'config_token':api.config_token(self.config),'forced_opening':40})
        self.assertFalse(result['confirmed_by_router'])

    async def test_conflicts_disabled_commands_and_incompatible_period_never_write(self):
        for action,values,rev in [('http_parameters',{'config_token':'old','forced_opening':60},None),
             ('force_on',{'minutes':30},'old'),('force_on',{'minutes':True},None),
             ('http_parameters',{'config_token':api.config_token(self.config),'period':1,'opening_max':60},None),
             ('http_parameters',{'config_token':api.config_token(self.config),'ssid':'change'},None)]:
            with self.assertRaises(api.RouterError):await self.command(action,values,rev)
        self.usage['router_http_enabled']=False
        with self.assertRaises(api.RouterError):await self.command('release',{})
        self.assertFalse(any(path in ('/ParaNew','/ForceAction') for _,path,_ in self.calls))
        self.usage['router_http_enabled']=True;self.usage['router_action']=1
        with self.assertRaises(api.RouterError):await self.command('http_parameters',{'config_token':api.config_token(self.config),'period':0,'opening_max':50})

    async def test_forcing_signed_duration_explicit_return_auto_and_busy(self):
        for action,values,expected in [('force_on',{'minutes':30},30),('force_off',{'minutes':40},-40),('release',{},0)]:
            result=await self.command(action,values)
            self.assertTrue(result['confirmed_by_router']);self.assertEqual(self.forces[0],expected)
        await self.coordinator.lock.acquire()
        try:
            with self.assertRaisesRegex(api.RouterError,'command_in_progress'):await self.command('release',{})
        finally:self.coordinator.lock.release()
        self.assertEqual(sum(path=='/ForceAction' for _,path,_ in self.calls),3)

    async def test_unconfirmed_write_is_not_retried_and_inactive_action_cannot_force(self):
        self.fail_live=True
        result=await self.command('force_on',{'minutes':30})
        self.assertFalse(result['confirmed_by_router'])
        self.assertEqual(sum(path=='/ForceAction' for _,path,_ in self.calls),1)
        self.config['Actions'][0]['Actif']=0
        with self.assertRaisesRegex(api.RouterError,'router_action_inactive'):await self.command('force_on',{'minutes':30})
        self.assertEqual(sum(path=='/ForceAction' for _,path,_ in self.calls),1)

    async def test_invalid_hosts_and_offline_are_errors_not_zero(self):
        for host in ['file:///tmp/a','http://user:password@host/','http://router/x','http://router/?x=1','http://router/#x','http://router:bad','http://router\n.local']:
            with self.assertRaises(api.RouterError):api.base_url(host)
        await self.runner.cleanup()
        with self.assertRaisesRegex(api.RouterError,'router_unavailable'):await self.client.read()
