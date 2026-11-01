"""Manual commands are explicit, scoped and guarded independently of simulation."""
import asyncio
import importlib
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch
import sys

package = ModuleType('ems_control_test')
package.__path__ = [str(Path(__file__).resolve().parents[1]/'custom_components/ehome_ems')]
with patch.dict(sys.modules, {'ems_control_test':package}):
    control = importlib.import_module('ems_control_test.manual_control').async_control


class ManualControlTests(IsolatedAsyncioTestCase):
    def setUp(self):
        self.entry=SimpleNamespace(modified_at=datetime.now(timezone.utc),options={},data={'usages':{'device':{'control_entity':'switch.load','control_enabled':True}}})
        self.states={'switch.load':SimpleNamespace(state='off')}
        self.hass=SimpleNamespace(data={},states=SimpleNamespace(get=self.states.get),services=SimpleNamespace(has_service=lambda d,s:True,async_call=AsyncMock()))
        self.context=object()

    async def send(self, **changes):
        args={'identifier':'device','desired_on':True,'expected_state':'off','revision':self.entry.modified_at.isoformat(),'context':self.context,**changes}
        return await control(self.hass,self.entry,**args)

    async def test_only_configured_entity_and_fixed_service_receive_user_context(self):
        result=await self.send()
        self.assertTrue(result['command_sent'])
        self.hass.services.async_call.assert_awaited_once_with('switch','turn_on',{'entity_id':'switch.load'},blocking=True,context=self.context)
        self.assertFalse(self.hass.data['ehome_ems']['manual_control_busy'])

    async def test_disabled_stale_unknown_and_non_binary_states_never_send(self):
        for changes in [{'revision':'old'},{'identifier':'missing'},{'expected_state':'on'},{'desired_on':1}]:
            with self.assertRaises(ValueError):await self.send(**changes)
        for state in ['unknown','unavailable','charging']:
            self.states['switch.load'].state=state
            with self.assertRaises(ValueError):await self.send()
        self.states['switch.load'].state='off'
        self.entry.data['usages']['device']['control_enabled']=False
        with self.assertRaises(ValueError):await self.send()
        self.hass.services.async_call.assert_not_awaited()

    async def test_non_commandable_domains_and_missing_service_rejected(self):
        self.entry.data['usages']['device']['control_entity']='sensor.power'
        with self.assertRaises(ValueError):await self.send()
        self.entry.data['usages']['device']['control_entity']='switch.load'
        self.hass.services.has_service=lambda d,s:False
        with self.assertRaises(ValueError):await self.send()
        self.hass.services.async_call.assert_not_awaited()

    async def test_no_duplicate_while_pending_and_failure_releases_lock(self):
        started,finish=asyncio.Event(),asyncio.Event()
        async def wait(*args,**kwargs):started.set();await finish.wait();raise RuntimeError('failed')
        self.hass.services.async_call.side_effect=wait
        task=asyncio.create_task(self.send());await started.wait()
        with self.assertRaisesRegex(ValueError,'command_in_progress'):await self.send()
        finish.set()
        with self.assertRaises(RuntimeError):await task
        self.assertFalse(self.hass.data['ehome_ems']['manual_control_busy'])
