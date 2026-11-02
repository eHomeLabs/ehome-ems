"""HA WS/reload control checks with simulated history and a local fake router."""
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo


async def validate_energy_goals(hass, entry, command, identifier, config, writes, forces):
    from custom_components.ehome_ems.const import DOMAIN
    from custom_components.ehome_ems import energy_goal_runtime
    initial = list(writes)
    hass.states.async_set('sensor.sim_goal_total', '101', {'unit_of_measurement':'kWh','device_class':'energy','state_class':'total_increasing'})
    now = datetime.now(timezone.utc).astimezone(ZoneInfo(hass.config.time_zone))
    values = {'mode':'observe','goal_kwh':3.,'deadline':(now+timedelta(minutes=30)).strftime('%H:%M'),
        'window_start':'00:00','window_end':'00:00','nominal_power_w':1800.,'margin_minutes':5.,
        'energy_entity':'sensor.sim_goal_total','counter_confirmed':True,'router_usage':identifier,'max_age_seconds':300.}
    history = AsyncMock(return_value=(100.,100.,'valid'))
    with patch.object(energy_goal_runtime, 'history_baseline', history):
        async def save(settings, remove=False):
            await command({'type':'ehome_ems/save_energy_goal','entry_id':entry.entry_id,'identifier':identifier,
                'revision':entry.modified_at.isoformat(),'values':settings,'remove':remove})
            await hass.async_block_till_done()
        await save(values)
        rt = hass.data[DOMAIN]['energy_goal_runtime'][entry.entry_id]
        assert rt.results[identifier]['consumed_kwh']==1
        assert rt.results[identifier]['missing_kwh']==2
        assert rt.results[identifier]['needed_minutes']==67
        assert writes==initial  # Observation cannot issue equipment commands.
        response = await command({'type':'ehome_ems/energy_goals','entry_id':entry.entry_id})
        assert response[0]['mode']=='observe'
        snapshot = await command({'type':'ehome_ems/dashboard','entry_id':entry.entry_id})
        assert snapshot['energy_goals'][0]['missing_kwh']==2
        forces[0]=0  # The earlier manual scenario has explicitly returned to Auto.
        await save({**values,'mode':'auto'})
        rt = hass.data[DOMAIN]['energy_goal_runtime'][entry.entry_id]
        # The prior manual test configured only 60% forced opening. Automatic
        # scheduling must refuse to change that persistent setting or force On.
        assert rt.results[identifier]['reason']=='router_requires_full_opening'
        assert writes==initial
        config['Actions'][0]['ForceOuvre']=100
        await rt.async_tick()
        assert forces[0] in (1,2), (rt.results, writes, forces)
        assert rt.results[identifier]['running']
        assert writes==initial+['/ForceAction']
        hass.states.async_set('sensor.sim_goal_total','103',{'unit_of_measurement':'kWh','device_class':'energy','state_class':'total_increasing'})
        await rt.async_tick()
        assert forces[0]==0
        assert not rt.results[identifier]['running']
        assert rt.results[identifier]['reason']=='target_reached'
        assert writes==initial+['/ForceAction','/ForceAction']
        await command({'type':'ehome_ems/rearm_energy_goal','entry_id':entry.entry_id,'identifier':identifier,
            'revision':entry.modified_at.isoformat()})
        await save({},remove=True)
        assert entry.entry_id not in hass.data[DOMAIN]['energy_goal_runtime']
        assert writes==initial+['/ForceAction','/ForceAction']
    await validate_recorder_baseline(hass)
    print('PASS energy goals: HA observation, explicit auto opt-in, full opening requirement, measured target, return Auto, WS and unload')


async def validate_recorder_baseline(hass):
    """Exercise the public Recorder SQL API in the temporary HA database."""
    from homeassistant.components.recorder import get_instance
    from custom_components.ehome_ems.energy_goal_runtime import history_baseline
    recorder=get_instance(hass)
    entity='sensor.sim_cycle_counter_db'
    attrs={'unit_of_measurement':'kWh','device_class':'energy','state_class':'total_increasing'}
    hass.states.async_set(entity,'100',attrs)
    await hass.async_block_till_done()
    await recorder.async_block_till_done()
    start=datetime.now(timezone.utc)
    await asyncio.sleep(.01)  # Ensure a distinct timestamp after the cycle boundary.
    hass.states.async_set(entity,'101',attrs)
    await hass.async_block_till_done()
    await recorder.async_block_till_done()
    async def wait_history(predicate):
        # Recorder is a separate writer thread. Wait for committed data through
        # its public query API rather than reading a partially committed batch.
        async with asyncio.timeout(10):
            while True:
                value=await history_baseline(hass,entity,start,datetime.now(timezone.utc))
                if predicate(value):return value
                await asyncio.sleep(.05)
    assert await wait_history(lambda value:value==(100.,101.,'valid'))==(100.,101.,'valid')
    await asyncio.sleep(.01)
    hass.states.async_set(entity,'1',attrs)
    await hass.async_block_till_done()
    await recorder.async_block_till_done()
    assert (await wait_history(lambda value:value[2]=='counter_reset'))[2]=='counter_reset'
    assert (await history_baseline(hass,'sensor.sim_missing_cycle_counter',start,datetime.now(timezone.utc)))[2]=='baseline_missing'
    print('PASS Recorder energy baseline: real temporary SQL database, boundary state, cumulative progress, reset, missing reference')
