"""Scoped writes preserve IDs and configuration; only the WS admin boundary can invoke them."""
from datetime import datetime, timezone, timedelta
from importlib import import_module
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
from types import ModuleType
from pathlib import Path
import sys
from test_config_flow import flow_module, state



class SettingsTests(TestCase):
    def setUp(self):
        package=ModuleType('ems_settings_test')
        package.__path__=[str(Path(__file__).resolve().parents[1]/'custom_components/ehome_ems')]
        patcher=patch.dict(sys.modules,{'ems_settings_test':package,'ems_settings_test.config_flow':flow_module})
        patcher.start();self.addCleanup(patcher.stop)
        global settings
        settings=import_module('ems_settings_test.settings')
        self.states={'sensor.home':state('400'),'sensor.fridge':state('85'),'sensor.fridge_day':state('.8','kWh'),'sensor.other':state('20')}
        self.entry=SimpleNamespace(modified_at=datetime.now(timezone.utc),data={'home_power':'sensor.home','simulation':{'schema_version':1,'targets':[]}},options={})
        self.writes=[]
        def update(entry, options):
            self.writes.append(options)
            entry.options=options
            entry.modified_at+=timedelta(microseconds=1)
        self.hass=SimpleNamespace(states=SimpleNamespace(get=self.states.get),registry=SimpleNamespace(async_get=lambda _:None),config_entries=SimpleNamespace(async_update_entry=update))

    def save(self,section,values,identifier=None,action='save',revision=None):
        return settings.update_settings(self.hass,self.entry,section,action,values,identifier,revision or self.entry.modified_at.isoformat())

    def test_daily_goal_tolerance_and_manual_control_are_explicit_and_preserved(self):
        self.states['switch.load']=state('off',None)
        result=self.save('appliances',{'name':'Load','power':'sensor.fridge','included_in_home':True,'daily_energy_goal_kwh':3,'negative_power_tolerance_w':5,'control_entity':'switch.load','control_enabled':True})
        item=self.entry.options['usages'][result['identifier']]
        self.assertEqual(item['daily_energy_goal_kwh'],3)
        self.assertEqual(item['control_entity'],'switch.load')
        self.assertTrue(item['control_enabled'])
        for goal in (0,-1,float('nan'),float('inf')):
            with self.assertRaises(settings.SettingsError):self.save('appliances',{'name':'Bad','power':'sensor.other','included_in_home':True,'daily_energy_goal_kwh':goal})
        with self.assertRaises(settings.SettingsError):self.save('appliances',{'name':'Bad','power':'sensor.other','included_in_home':True,'control_enabled':True})
        for tolerance in (-1,21,float('nan'),True):
            with self.assertRaises(settings.SettingsError):self.save('appliances',{'name':'Bad','power':'sensor.other','included_in_home':True,'negative_power_tolerance_w':tolerance})

    def test_photovoltaic_metadata_never_changes_total_or_balance_and_survives_other_edits(self):
        data={"name":"Hybrid","kind":"hybrid_inverter","power":"sensor.fridge","dc_power":"sensor.other","energy":"sensor.fridge_day","energy_period":"total","nominal_power_w":6000}
        result=self.save('photovoltaic',data);identifier=result['identifier']
        self.assertEqual(self.entry.options['home_power'],'sensor.home')
        self.assertNotIn('solar_power',self.entry.options)
        self.save('daily',{'tariff_eur_kwh':.2})
        self.assertEqual(self.entry.options['photovoltaic'][identifier]['power'],'sensor.fridge')
        with self.assertRaises(settings.SettingsError):self.save('photovoltaic',{'name':'Wrong','kind':'dc_inverter','power':'sensor.fridge_day'})
        self.save('photovoltaic',{},identifier,'remove')
        self.assertFalse(self.entry.options['photovoltaic'])
    def test_f1atb_profile_requires_exact_topic_and_confirmation(self):
        data={'name':'Router','kind':'solar_router','power':'sensor.other','included_in_home':True,'router_type':'f1atb','router_mqtt_enabled':True,'router_mqtt_topic':'demo/SSR'}
        with self.assertRaises(settings.SettingsError):self.save('usages',data)
        self.save('usages',{**data,'router_protocol_confirmed':True})
        with self.assertRaises(settings.SettingsError):self.save('usages',{**data,'router_protocol_confirmed':True,'router_mqtt_topic':'demo/#'})

    def test_add_update_and_remove_keeps_other_settings_and_id(self):
        data={'name':'Fridge','power':'sensor.fridge','energy':'sensor.fridge_day','included_in_home':True,'energy_period':'today'}
        result=self.save('appliances',data)
        key=result['identifier']
        self.assertEqual(self.entry.options['home_power'],'sensor.home')
        self.assertEqual(self.entry.options['simulation'],self.entry.data['simulation'])
        self.assertNotIn('usages',self.entry.data)
        self.save('appliances',{**data,'name':'Renamed'},key)
        self.assertEqual(list(self.entry.options['usages']),[key])
        self.save('appliances',{},key,'remove')
        self.assertFalse(self.entry.options['usages'])
        self.assertEqual(len(self.writes),3)

    def test_revision_is_required_and_old_revision_never_overwrites(self):
        rev=self.entry.modified_at.isoformat()
        self.save('solar',{'solar_power':'sensor.other'})
        with self.assertRaisesRegex(settings.SettingsError,'conflict'):
            self.save('solar',{},revision=rev)
        self.assertEqual(len(self.writes),1)

    def test_invalid_units_sources_targets_and_tariffs_do_not_write(self):
        payloads=[('solar',{'solar_power':'sensor.fridge_day'},None),('solar',{'solar_power':[]},None),('solar',{'solar_power':'sensor.home'},None),('solar',{'injected':'secret'},None),('daily',{'tariff_eur_kwh':float('nan')},None),('daily',{'tariff_eur_kwh':True},None),('appliances',{'name':'Fridge','power':'sensor.fridge','included_in_home':False},None)]
        for section,values,identifier in payloads:
            with self.assertRaises(settings.SettingsError):self.save(section,values,identifier)
        with self.assertRaises(settings.SettingsError):self.save('batteries',{},'missing','remove')
        self.assertFalse(self.writes)

    def test_home_calculation_cannot_be_enabled_without_complete_ac_boundary(self):
        with self.assertRaises(settings.SettingsError):
            self.save('home',{'home_power_mode':'calculated','home_boundary_confirmed':True})
        self.assertFalse(self.writes)

    def test_daily_reuses_existing_submeter_without_double_count_and_clears_price(self):
        self.save('daily',{'home':'sensor.fridge_day','tariff_eur_kwh':.215})
        self.assertEqual(self.entry.options['daily']['home'],'sensor.fridge_day')
        self.save('daily',{'home':'sensor.fridge_day'})
        self.assertIsNone(self.entry.options['tariff_eur_kwh'])
        self.assertEqual(self.entry.options['home_power'],'sensor.home')

    def test_signed_home_without_import_export_and_change_only_freshness(self):
        self.entry.data.update(grid_power='sensor.other')
        self.save('home',{'home_power_mode':'calculated','home_grid_mode':'signed','home_has_solar':False,'home_has_storage':False,'home_boundary_confirmed':True,'home_max_age_seconds':0})
        self.assertEqual(self.entry.options['home_grid_mode'],'signed')
        self.assertIsNone(self.entry.options['home_power'])
        self.assertEqual(self.entry.options['grid_power'],'sensor.other')
        self.assertEqual(self.entry.options['home_max_age_seconds'],0)
        for value in (1,29,-1,3601):
            with self.assertRaises(settings.SettingsError):
                self.save('home',{'home_power_mode':'calculated','home_boundary_confirmed':True,'home_max_age_seconds':value})

    def test_stock_override_is_explicit_and_preserves_capacity_checks(self):
        self.states['sensor.stock']=state('1.8','kWh')
        self.states['sensor.stock'].attributes['state_class']='total_increasing'
        values={'name':'Portable storage','role':'backup','coupling':'ac','remaining_energy':'sensor.stock','capacity_kwh':2.3}
        with self.assertRaises(settings.SettingsError):self.save('batteries',values)
        result=self.save('batteries',{**values,'remaining_energy_is_stock':True})
        self.assertTrue(self.entry.options['batteries'][result['identifier']]['remaining_energy_is_stock'])
        self.states['sensor.stock'].state='9'
        with self.assertRaises(settings.SettingsError):self.save('batteries',{**values,'remaining_energy_is_stock':True},result['identifier'])

    def test_weather_mapping_is_scoped_and_validated(self):
        self.states['weather.home']=state('cloudy',None)
        self.save('daily',{'weather_entity':'weather.home'})
        self.assertEqual(self.entry.options['weather_entity'],'weather.home')
        self.assertEqual(self.entry.options['home_power'],'sensor.home')
        with self.assertRaises(settings.SettingsError):self.save('daily',{'weather_entity':'sensor.home'})
