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
