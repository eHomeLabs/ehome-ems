"""Opt-in goal scheduling with simulated history, F1ATB, storage and clock."""
import asyncio
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from test_energy_goal import settings, at


class MemoryStore:
    database={}
    def __init__(self,hass,version,key):self.key=key
    async def async_load(self):return deepcopy(self.database.get(self.key))
    async def async_save(self,data):self.database[self.key]=deepcopy(data)


package=ModuleType('ems_goal_runtime_test');package.__path__=[str(Path(__file__).resolve().parents[1]/'custom_components/ehome_ems')]
modules={name:ModuleType(name) for name in ['homeassistant','homeassistant.const','homeassistant.core','homeassistant.helpers','homeassistant.helpers.event','homeassistant.helpers.storage']}
modules['ems_goal_runtime_test']=package
modules['homeassistant.const'].EVENT_HOMEASSISTANT_STOP='stop'
modules['homeassistant.core'].callback=lambda f:f
modules['homeassistant.helpers.storage'].Store=MemoryStore
modules['homeassistant.helpers.event'].async_track_time_interval=lambda *args:lambda:None
with patch.dict(sys.modules,modules):runtime=importlib.import_module('ems_goal_runtime_test.energy_goal_runtime')


class FakeRouter:
    base='http://router.example.local'
    def __init__(self):self.force_minutes=0;self.writes=[];self.opening=100;self.mode=2;self.fail_after_write=False;self.on_read=None
    async def read(self):
        if self.fail_after_write and self.writes:raise runtime.RouterError('router_unavailable')
        if self.on_read:self.on_read()
        return {'actions':[{'index':0,'mode':self.mode,'forced_opening':self.opening}],
                'live_actions':{0:{'force_minutes':self.force_minutes}}}
    async def force(self,index,minutes):self.writes.append((index,minutes));self.force_minutes=minutes


class GoalRuntimeTests(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        MemoryStore.database.clear()
        self.clock=at('2026-11-03T05:55:00+01:00')
        self.energy=SimpleNamespace(state='101',attributes={'unit_of_measurement':'kWh'},last_reported=self.clock)
        self.goal=settings(mode='auto')
        self.mapping={'energy_goals':{'h':self.goal},'usages':{'h':{'kind':'water_heater','name':'Cumulus'},'r':{'kind':'solar_router','router_type':'f1atb','router_connection':'http','router_http_enabled':True,'router_action':0}}}
        self.entry=SimpleNamespace(entry_id='entry',options=self.mapping,data={},modified_at=self.clock)
        self.client=FakeRouter();self.coordinator=SimpleNamespace(client=self.client,lock=asyncio.Lock())
        self.hass=SimpleNamespace(data={'ehome_ems':{'router_http':{'entry':{'r':self.coordinator}}}},
            config=SimpleNamespace(time_zone='Europe/Paris'),states=SimpleNamespace(get=lambda id:self.energy),bus=SimpleNamespace(async_listen_once=lambda *args:lambda:None))
        self.history=AsyncMock(return_value=(100.,100.,'valid'))
        self.rt=self.make_runtime();await self.rt.async_start()

    def make_runtime(self):return runtime.EnergyGoalRuntime(self.hass,self.entry,history_reader=self.history,now=lambda:self.clock)
    def advance(self,seconds=60):self.clock+=timedelta(seconds=seconds);self.energy.last_reported=self.clock

    async def test_due_starts_short_lease_renews_and_releases_at_target(self):
        self.assertEqual(self.client.writes,[(0,2)])
        self.advance();await self.rt.async_tick();self.assertEqual(self.client.writes,[(0,2),(0,2)])
        self.energy.state='103';self.advance(30);await self.rt.async_tick()
        self.assertEqual(self.client.writes[-1],(0,0));self.assertFalse(self.rt.results['h']['running'])
        self.assertEqual(self.rt.results['h']['reason'],'target_reached')

    async def test_observation_never_writes_even_when_complement_due(self):
        await self.rt.async_stop();self.client.writes.clear();self.goal['mode']='observe'
        rt=self.make_runtime();await rt.async_start();await rt.async_tick()
        self.assertEqual(self.client.writes,[]);self.assertTrue(rt.results['h']['should_heat'])

    async def test_stale_or_reset_energy_stops_and_never_becomes_zero(self):
        self.goal["max_age_seconds"]=30
        self.clock+=timedelta(seconds=60);await self.rt.async_tick()
        self.assertEqual(self.rt.results['h']['reason'],'stale_energy');self.assertEqual(self.client.writes[-1],(0,0))
        self.energy.state='1';self.energy.last_reported=self.clock;await self.rt.async_tick()
        self.assertEqual(self.rt.results['h']['reason'],'counter_reset');self.assertIsNone(self.rt.results['h']['consumed_kwh'])
        writes=len(self.client.writes);self.energy.state='104';await self.rt.async_tick();self.assertEqual(len(self.client.writes),writes)

    async def test_missing_baseline_blocks_start_and_survives_reload_without_resetting_energy(self):
        await self.rt.async_stop();self.client.writes.clear();self.history.return_value=(None,None,'baseline_missing')
        rt=self.make_runtime();await rt.async_start();self.assertEqual(self.client.writes,[])
        self.assertIsNone(rt.results['h']['consumed_kwh'])
        self.history.return_value=(100.,101.,'valid');self.advance(61);await rt.async_tick()
        self.assertEqual(rt.results['h']['consumed_kwh'],1);self.assertEqual(self.client.writes,[(0,2)])

    async def test_manual_override_wins_and_is_persisted_across_reload(self):
        await self.rt.async_manual_override('r');self.client.force_minutes=30
        self.advance();await self.rt.async_tick()
        self.assertEqual(self.client.writes,[(0,2)]);self.assertEqual(self.rt.results['h']['reason'],'manual_override')
        await self.rt.async_stop();rt=self.make_runtime();await rt.async_start()
        self.assertEqual(self.client.writes,[(0,2)]);self.assertFalse(rt.results['h']['running'])
        await rt.async_rearm('h');self.client.force_minutes=0;await rt.async_tick()
        self.assertEqual(self.client.writes[-1],(0,2))

    async def test_external_long_override_is_not_cancelled_on_shutdown(self):
        self.client.force_minutes=30;await self.rt.async_stop()
        self.assertEqual(self.client.writes,[(0,2)])

    async def test_unconfirmed_write_suspends_without_retry_after_restart(self):
        await self.rt.async_stop();self.client.writes.clear();self.client.force_minutes=0;self.client.fail_after_write=True
        rt=self.make_runtime();await rt.async_start()
        self.assertEqual(self.client.writes,[(0,2)])
        self.client.fail_after_write=False;self.client.force_minutes=0;self.advance();await rt.async_tick()
        self.assertEqual(self.client.writes,[(0,2)])
        await rt.async_stop();again=self.make_runtime();await again.async_start()
        self.assertEqual(self.client.writes,[(0,2)]);self.assertFalse(again.results['h']['running'])

    async def test_progress_is_rechecked_after_network_read_before_write(self):
        await self.rt.async_stop();self.client.writes.clear();self.client.force_minutes=0
        self.client.on_read=lambda:setattr(self.energy,'state','103')
        rt=self.make_runtime();await rt.async_start();self.assertEqual(self.client.writes,[])
        self.assertEqual(rt.results['h']['reason'],'target_reached')

    async def test_leases_do_not_start_in_final_seconds_of_window(self):
        await self.rt.async_stop();self.client.writes.clear();self.client.force_minutes=0
        self.clock=at('2026-11-03T06:59:30+01:00');self.energy.last_reported=self.clock
        rt=self.make_runtime();await rt.async_start()
        self.assertEqual(self.client.writes,[]);self.assertEqual(rt.results['h']['reason'],'lease_too_short')

    async def test_slow_intent_save_cannot_start_a_lease_after_the_allowed_window(self):
        await self.rt.async_stop();self.client.writes.clear();self.client.force_minutes=0
        rt=self.make_runtime()
        save=rt.store.async_save
        first=[True]
        async def delayed_save(data):
            if first[0]:
                first[0]=False
                self.clock=at('2026-11-03T06:59:50+01:00');self.energy.last_reported=self.clock
            await save(data)
        rt.store.async_save=delayed_save
        await rt.async_start()
        self.assertEqual(self.client.writes,[])
        self.assertEqual(rt.results['h']['reason'],'lease_too_short')
        self.assertNotIn('h',rt.faults)

    async def test_two_entries_cannot_own_the_same_router_action(self):
        other_entry=SimpleNamespace(entry_id='other',options=self.mapping,data={},modified_at=self.clock)
        self.hass.data['ehome_ems']['router_http']['other']={'r':self.coordinator}
        other=runtime.EnergyGoalRuntime(self.hass,other_entry,history_reader=self.history,now=lambda:self.clock)
        await other.async_start()
        self.assertEqual(other.results['h']['reason'],'router_already_managed')
        self.assertEqual(self.client.writes,[(0,2)])
        await other.async_stop()
        self.assertEqual(self.client.writes,[(0,2)])

    async def test_non_full_opening_is_not_modified_or_forced(self):
        await self.rt.async_stop();self.client.writes.clear();self.client.force_minutes=0;self.client.opening=50
        rt=self.make_runtime();await rt.async_start()
        self.assertEqual(self.client.writes,[]);self.assertEqual(self.client.opening,50)
        self.assertEqual(rt.results['h']['reason'],'router_requires_full_opening')

    async def test_new_cycle_does_not_carry_ownership_or_previous_energy(self):
        self.clock=at('2026-11-03T07:00:00+01:00');self.energy.last_reported=self.clock
        self.client.force_minutes=0;self.history.return_value=(101.,101.,'valid')
        await self.rt.async_tick()
        self.assertFalse(self.rt.results['h']['running']);self.assertEqual(self.rt.results['h']['consumed_kwh'],0)
        self.assertEqual(self.client.writes,[(0,2)])
