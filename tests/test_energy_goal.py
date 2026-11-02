"""Energy goals across midnight, deadlines and DST, independent of equipment."""
from datetime import datetime, timezone, timedelta
import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

package=ModuleType('ems_goal_test');package.__path__=[str(Path(__file__).resolve().parents[1]/'custom_components/ehome_ems')]
with patch.dict(sys.modules,{'ems_goal_test':package}):goal=importlib.import_module('ems_goal_test.energy_goal')


def settings(**changes):
    return {'mode':'observe','goal_kwh':3.,'deadline':'07:00','window_start':'01:00','window_end':'07:00',
        'nominal_power_w':1800.,'margin_minutes':5.,'energy_entity':'sensor.demo_water_total',
        'counter_confirmed':True,'router_usage':'r','max_age_seconds':300.,**changes}


def at(value):return datetime.fromisoformat(value).astimezone(timezone.utc)


class GoalPlanTests(TestCase):
    def test_missing_two_kwh_requires_67_minutes_and_starts_only_when_due(self):
        config=settings()
        early=goal.evaluate(config,at('2026-11-03T03:00:00+01:00'),'Europe/Paris',1)
        self.assertEqual(early['missing_kwh'],2);self.assertEqual(early['needed_minutes'],67)
        self.assertFalse(early['should_heat']);self.assertEqual(early['reason'],'solar_priority')
        due=goal.evaluate(config,at('2026-11-03T05:49:00+01:00'),'Europe/Paris',1)
        self.assertTrue(due['should_heat']);self.assertEqual(due['reason'],'complement_due')
        full=goal.evaluate(config,at('2026-11-03T06:30:00+01:00'),'Europe/Paris',3,running=True)
        self.assertFalse(full['should_heat']);self.assertEqual(full['reason'],'target_reached')

    def test_midnight_keeps_previous_solar_and_deadline_opens_a_new_cycle(self):
        config=settings()
        first=goal.cycle(config,at('2026-11-02T22:00:00+01:00'),'Europe/Paris')
        second=goal.cycle(config,at('2026-11-03T02:00:00+01:00'),'Europe/Paris')
        self.assertEqual(first,second)
        third=goal.cycle(config,at('2026-11-03T07:00:00+01:00'),'Europe/Paris')
        self.assertEqual(third[0],first[1]);self.assertNotEqual(first,third)

    def test_insufficient_window_is_reported_and_heats_only_when_permitted(self):
        config=settings(window_start='06:00',window_end='07:00')
        before=goal.evaluate(config,at('2026-11-03T05:30:00+01:00'),'Europe/Paris',1)
        self.assertFalse(before['reachable']);self.assertFalse(before['should_heat'])
        allowed=goal.evaluate(config,at('2026-11-03T06:00:00+01:00'),'Europe/Paris',1)
        self.assertFalse(allowed['reachable']);self.assertTrue(allowed['should_heat'])

    def test_cross_midnight_window_and_solar_during_top_up(self):
        config=settings(window_start='23:00',window_end='02:00')
        late=goal.evaluate(config,at('2026-11-03T01:00:00+01:00'),'Europe/Paris',1)
        self.assertTrue(late['should_heat']);self.assertEqual(late['allowed_minutes'],60)
        after=goal.evaluate(config,at('2026-11-03T02:30:00+01:00'),'Europe/Paris',1,running=True)
        self.assertFalse(after['should_heat'])
        reached=goal.evaluate(config,at('2026-11-03T01:30:00+01:00'),'Europe/Paris',3.1,running=True)
        self.assertEqual(reached['missing_kwh'],0);self.assertFalse(reached['should_heat'])

    def test_dst_cycles_are_23_and_25_hours_and_nonexistent_clock_is_shifted(self):
        for stamp,hours in [('2026-03-29T06:00:00+02:00',23),('2026-10-25T06:00:00+01:00',25)]:
            start,end=goal.cycle(settings(),at(stamp),'Europe/Paris')
            self.assertEqual((end-start).total_seconds()/3600,hours)
        start,end=goal.cycle(settings(deadline='02:30'),at('2026-03-29T01:00:00+01:00'),'Europe/Paris')
        self.assertEqual(end,at('2026-03-29T03:30:00+02:00'))

    def test_missing_baseline_invalid_values_resets_and_unit_conversion(self):
        self.assertEqual(goal.counter_kwh('2000','Wh'),2)
        for value,unit in [('unavailable','kWh'),('nan','kWh'),('-2','kWh'),('20','W')]:self.assertIsNone(goal.counter_kwh(value,unit))
        self.assertEqual(goal.progress(None,None,100),(None,'energy_unavailable'))
        self.assertEqual(goal.progress(100,101,1),(None,'counter_reset'))
        self.assertEqual(goal.progress(100,100.5,101),(1,'valid'))
        self.assertFalse(goal.evaluate(settings(),at('2026-11-03T06:00:00+01:00'),'Europe/Paris',None)['should_heat'])

    def test_goal_save_is_scoped_revision_checked_and_preserves_existing_mappings(self):
        mapping={'home_power':'sensor.demo_home','usages':{'h':{'name':'Water heater','kind':'water_heater','energy':'sensor.demo_day'}}}
        entry=SimpleNamespace(options=mapping,data={},modified_at=at('2026-11-02T00:00:00Z'))
        states={'sensor.demo_water_total':SimpleNamespace(attributes={'unit_of_measurement':'kWh','state_class':'total_increasing'})}
        writes=[]
        hass=SimpleNamespace(states=states,config_entries=SimpleNamespace(async_update_entry=lambda entry,**kw:writes.append(kw)))
        with self.assertRaisesRegex(ValueError,'conflict'):goal.save_goal(hass,entry,'h',settings(),'old')
        self.assertEqual(writes,[])
        goal.save_goal(hass,entry,'h',settings(),entry.modified_at.isoformat())
        self.assertEqual(writes[0]['options']['home_power'],'sensor.demo_home')
        self.assertEqual(writes[0]['options']['usages'],mapping['usages'])
        self.assertNotIn('energy_goals',mapping)
        self.assertEqual(writes[0]['options']['energy_goals']['h']['mode'],'observe')

    def test_validation_requires_explicit_counter_and_native_http_for_auto(self):
        states={'sensor.demo_water_total':SimpleNamespace(attributes={'unit_of_measurement':'kWh','state_class':'total_increasing'})}
        mapping={'usages':{'h':{'kind':'water_heater'},'r':{'kind':'solar_router','router_type':'f1atb','router_connection':'http','router_http_enabled':True}}}
        self.assertEqual(goal.validate_goal(mapping,'h',settings(mode='auto'),states)['goal_kwh'],3)
        for changes in [{'counter_confirmed':False},{'goal_kwh':float('nan')},{'deadline':'25:00'},{'nominal_power_w':True}]:
            with self.assertRaises(ValueError):goal.validate_goal(mapping,'h',settings(**changes),states)
        mapping['usages']['r']['router_connection']='mqtt'
        with self.assertRaisesRegex(ValueError,'native_f1atb'):goal.validate_goal(mapping,'h',settings(mode='auto'),states)
        self.assertEqual(goal.validate_goal(mapping,'h',settings(),states)['mode'],'observe')
