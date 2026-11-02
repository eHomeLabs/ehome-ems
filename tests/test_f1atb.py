"""F1ATB documented payloads, opt-in boundaries and non-retained publication."""
import importlib
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone
import json
import sys

package=ModuleType('ems_f1atb_test');package.__path__=[str(Path(__file__).resolve().parents[1]/'custom_components/ehome_ems')]
with patch.dict(sys.modules,{'ems_f1atb_test':package}):router=importlib.import_module('ems_f1atb_test.f1atb')


class RouterPayloadTests(TestCase):
    def test_documented_force_minutes_release_and_period_settings(self):
        usage={'router_output':'ssr'}
        self.assertEqual(router.router_payload(usage,'force_on',{'minutes':30}),{'tOnOff':30})
        self.assertEqual(router.router_payload(usage,'force_off',{'minutes':40}),{'tOnOff':-40})
        self.assertEqual(router.router_payload(usage,'release',{}),{'tOnOff':0})
        self.assertEqual(router.router_payload(usage,'parameters',{'period':0,'mode':'Train','opening_max':60,'threshold_on':-50}),{'Periode':0,'Mode':'Train','OuvreMax':60,'SeuilOn':-50})
        for action,values in [('force_on',{'minutes':0}),('force_on',{'minutes':True}),('release',{'retain':True}),('parameters',{'period':8,'opening_max':50}),('parameters',{'period':0,'mode':'Decoupe'}),('parameters',{'period':0,'opening_max':float('nan')}),('parameters',{'period':0})]:
            with self.assertRaises(ValueError):router.router_payload(usage,action,values)
    def test_topic_url_and_opt_in_are_explicit(self):
        self.assertTrue(router.valid_topic('demo_router/SSR Cumulus'))
        for value in ['demo/#','demo/+','/SSR','demo/SSR/extra','demo/\nSSR','$SYS/SSR']:
            self.assertFalse(router.valid_topic(value))
        for url in ['javascript:alert(1)','file:///tmp/a','http://user:password@router/','//router.local']:
            self.assertFalse(router.valid_web_url(url))
        self.assertTrue(router.valid_web_url('http://router.example.local/'))
        self.assertEqual(router.router_error({'router_mqtt_enabled':True}),'router_configuration')


class RouterCommandTests(IsolatedAsyncioTestCase):
    async def test_fixed_target_non_retained_context_and_revision(self):
        usage={'kind':'solar_router','router_type':'f1atb','router_mqtt_enabled':True,'router_protocol_confirmed':True,'router_mqtt_topic':'demo/SSR'}
        entry=SimpleNamespace(options={},data={'usages':{'r':usage}},modified_at=datetime.now(timezone.utc))
        hass=SimpleNamespace(data={},services=SimpleNamespace(has_service=lambda *a:True,async_call=AsyncMock()))
        context=object();revision=entry.modified_at.isoformat()
        result=await router.async_router_command(hass,entry,'r',revision,'force_on',{'minutes':30},context)
        call=hass.services.async_call.call_args
        self.assertEqual(call.args[:2],('mqtt','publish'));self.assertEqual(call.args[2]['topic'],'demo/SSR')
        self.assertFalse(call.args[2]['retain']);self.assertEqual(json.loads(call.args[2]['payload']),{'tOnOff':30});self.assertIs(call.kwargs['context'],context)
        self.assertFalse(result['confirmed_by_router'])
        for identifier,rev in [('r','old'),('missing',revision)]:
            with self.assertRaises(ValueError):await router.async_router_command(hass,entry,identifier,rev,'release',{},context)
        usage['router_mqtt_enabled']=False
        with self.assertRaises(ValueError):await router.async_router_command(hass,entry,'r',revision,'release',{},context)
        self.assertEqual(hass.services.async_call.await_count,1)
