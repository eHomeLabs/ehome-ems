"""Alert deduplication, midnight, missing values and explicit destinations."""
import importlib
import sys
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

package=ModuleType('ems_alert_test');package.__path__=[str(Path(__file__).resolve().parents[1]/'custom_components/ehome_ems')]
modules={name:ModuleType(name) for name in ['homeassistant','homeassistant.helpers','homeassistant.helpers.event','homeassistant.helpers.storage']}
modules['ems_alert_test']=package
class MemoryStore:
    data={}
    def __init__(self,hass,version,key):self.key=key
    async def async_load(self):return deepcopy(self.data.get(self.key))
    async def async_save(self,data):self.data[self.key]=deepcopy(data)
modules['homeassistant.helpers.storage'].Store=MemoryStore
modules['homeassistant.helpers.event'].async_track_time_interval=lambda *args:lambda:None
with patch.dict(sys.modules,modules):alerts=importlib.import_module('ems_alert_test.alerts')

def rule(**kw):return dict(id='daily',kind='daily_import',entity='sensor.import',threshold=12.,duration_minutes=0.,enabled=True,notify_service='persistent_notification.create',daily_confirmed=True,**kw)

class AlertTests(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        MemoryStore.data.clear();self.now=datetime(2026,11,3,12,tzinfo=timezone.utc)
        self.state=SimpleNamespace(state='13',attributes={'unit_of_measurement':'kWh'})
        self.entry=SimpleNamespace(entry_id='entry',options={'alerts':[rule()]},data={},modified_at=self.now,async_on_unload=lambda cb:None)
        self.hass=SimpleNamespace(data={},config=SimpleNamespace(time_zone='Europe/Paris'),states=SimpleNamespace(get=lambda _:self.state),services=SimpleNamespace(async_call=AsyncMock(),has_service=lambda d,s:True),config_entries=SimpleNamespace(async_update_entry=lambda *a,**kw:None))
        self.rt=alerts.AlertRuntime(self.hass,self.entry,now=lambda:self.now)
    async def test_daily_once_across_restart_and_after_drop_or_unavailable(self):
        await self.rt.async_start();await self.rt.async_tick()
        self.assertEqual(self.hass.services.async_call.await_count,1)
        self.state.state='unavailable';await self.rt.async_tick()
        self.state.state='13';await self.rt.async_tick()
        await self.rt.async_stop()
        rt=alerts.AlertRuntime(self.hass,self.entry,now=lambda:self.now);await rt.async_start()
        self.assertEqual(self.hass.services.async_call.await_count,1)
        self.now+=timedelta(days=1);await rt.async_tick()
        self.assertEqual(self.hass.services.async_call.await_count,2)
        self.assertIn('plus de 12 kWh',self.rt.journal[0]['message'])
    async def test_disabled_alert_never_sends_and_threshold_is_strict(self):
        self.entry.options['alerts'][0]['enabled']=False
        await self.rt.async_start();self.assertEqual(self.hass.services.async_call.await_count,0)
        self.entry.options['alerts'][0]['enabled']=True;self.state.state='12';await self.rt.async_tick()
        self.assertEqual(self.hass.services.async_call.await_count,0)
    async def test_unavailable_requires_delay_then_rearms_on_recovery(self):
        self.entry.options['alerts'][0].update(kind='entity_unavailable',duration_minutes=5)
        self.state.state='unavailable';await self.rt.async_start()
        self.now+=timedelta(minutes=4);await self.rt.async_tick();self.assertEqual(self.hass.services.async_call.await_count,0)
        self.now+=timedelta(minutes=1);await self.rt.async_tick();await self.rt.async_tick();self.assertEqual(self.hass.services.async_call.await_count,1)
        self.state.state='0';await self.rt.async_tick();self.state.state='unknown';await self.rt.async_tick()
        self.now+=timedelta(minutes=5);await self.rt.async_tick();self.assertEqual(self.hass.services.async_call.await_count,2)
    async def test_failed_delivery_is_logged_and_not_retried(self):
        self.hass.services.async_call.side_effect=RuntimeError('offline')
        await self.rt.async_start();await self.rt.async_tick()
        self.assertEqual(self.hass.services.async_call.await_count,1);self.assertEqual(self.rt.journal[0]['status'],'failed')
    async def test_power_conversion_duration_and_recovery(self):
        self.entry.options['alerts'][0].update(kind='import_power',threshold=1000,duration_minutes=2)
        self.state.attributes['unit_of_measurement']='kW';self.state.state='1.5';await self.rt.async_start()
        self.now+=timedelta(minutes=2);await self.rt.async_tick();self.assertEqual(self.hass.services.async_call.await_count,1)
        self.state.state='0.5';await self.rt.async_tick();self.state.state='1.6';await self.rt.async_tick()
        self.now+=timedelta(minutes=2);await self.rt.async_tick();self.assertEqual(self.hass.services.async_call.await_count,2)
    async def test_validation_rejects_undeclared_energy_arbitrary_services_and_stale_revision(self):
        alerts.validate_rules(self.hass,[rule()])
        for change in [{'daily_confirmed':False},{'threshold':True},{'threshold':float('nan')},{'notify_service':'switch.turn_on'},{'enabled':'true'}]:
            value=rule();value.update(change)
            with self.assertRaises(ValueError):alerts.validate_rules(self.hass,[value])
        with self.assertRaisesRegex(ValueError,'conflict'):alerts.save_alerts(self.hass,self.entry,[rule()],'old')
    async def test_stop_removes_runtime_and_prevents_send(self):
        await self.rt.async_stop();await self.rt.async_tick();self.hass.services.async_call.assert_not_awaited()
