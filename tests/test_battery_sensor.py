"""Entity lifecycle contract tests using minimal HA API doubles."""
import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parents[1]


class EntityDouble:
    def async_on_remove(self, remove):
        self.removers.append(remove)

    def async_write_ha_state(self):
        self.writes += 1


def load_sensor():
    modules = {name: ModuleType(name) for name in (
        "homeassistant", "homeassistant.components", "homeassistant.components.sensor",
        "homeassistant.core", "homeassistant.helpers", "homeassistant.helpers.event", "homeassistant.helpers.restore_state",
        "ems_sensor_test",
    )}
    modules["ems_sensor_test"].__path__ = [str(ROOT / "custom_components/ehome_ems")]
    sensors = modules["homeassistant.components.sensor"]
    sensors.SensorEntity = EntityDouble
    sensors.SensorDeviceClass = SimpleNamespace(POWER="power", BATTERY="battery", ENERGY="energy")
    sensors.SensorStateClass = SimpleNamespace(MEASUREMENT="measurement", TOTAL_INCREASING="total_increasing")
    modules["homeassistant.core"].callback = lambda f: f
    modules["homeassistant.helpers.restore_state"].RestoreEntity = EntityDouble

    def subscribe(hass, entity_ids, callback):
        hass.listeners.append(callback)
        return lambda: hass.listeners.remove(callback)

    modules["homeassistant.helpers.event"].async_track_state_change_event = subscribe
    modules["homeassistant.helpers.event"].async_track_time_interval = lambda *args: lambda: None
    with patch.dict(sys.modules, modules):
        return importlib.import_module("ems_sensor_test.sensor")


sensor_module = load_sensor()


class BatterySensorTests(IsolatedAsyncioTestCase):
    def setUp(self):
        self.states = {"sensor.source": SimpleNamespace(
            state="2500", attributes={"unit_of_measurement": "Wh"}
        )}
        self.hass = SimpleNamespace(states=SimpleNamespace(get=self.states.get), listeners=[])
        self.battery = {"name": "Simulated storage", "role": "backup", "coupling": "ac",
                        "capacity_kwh": 5}

    def make_sensor(self, role="remaining_energy", battery_id="stable"):
        sensor = sensor_module.MappedPowerSensor(
            "entry", role, "sensor.source", battery=self.battery, battery_id=battery_id
        )
        sensor.hass = self.hass
        sensor.removers = []
        sensor.writes = 0
        return sensor

    async def test_usage_small_negative_offset_keeps_raw_value_and_outside_tolerance_invalid(self):
        usage={"name":"AC","kind":"appliance","power":"sensor.source","negative_power_tolerance_w":5}
        sensor=sensor_module.UsageSensor("entry","ac",usage,"power")
        sensor.hass=self.hass
        for raw,value in [("-1",0),("-5",0),("-6",None),("unavailable",None)]:
            self.states["sensor.source"]=SimpleNamespace(state=raw,attributes={"unit_of_measurement":"W"})
            sensor._update_from_source()
            self.assertEqual(sensor._attr_native_value,value)
            self.assertEqual(sensor._attr_extra_state_attributes["source_raw_value"],raw)
            self.assertEqual(sensor._attr_extra_state_attributes["negative_offset_corrected"],value == 0)

    async def test_energy_stock_uses_kwh_and_measurement_class(self):
        sensor = self.make_sensor()
        await sensor.async_added_to_hass()
        self.assertEqual(sensor._attr_native_value, 2.5)
        self.assertEqual(sensor._attr_device_class, "energy")
        self.assertEqual(sensor._attr_state_class, "measurement")
        self.assertEqual(sensor._attr_native_unit_of_measurement, "kWh")
        self.assertFalse(sensor._attr_extra_state_attributes["eligible_for_ac_balance"])
        self.assertEqual(sensor._attr_extra_state_attributes["energy_origin"], "unknown")

    async def test_backup_and_dc_are_never_eligible_for_simple_ac_balance(self):
        for role, coupling, expected in (
            ("backup", "ac", False), ("active", "dc", False), ("active", "ac", True)
        ):
            self.battery.update(role=role, coupling=coupling)
            sensor = self.make_sensor()
            sensor._update_from_source()
            self.assertEqual(sensor._attr_extra_state_attributes["eligible_for_ac_balance"], expected)

    async def test_stable_unique_ids_survive_renaming_and_distinguish_batteries(self):
        before = self.make_sensor()
        self.battery["name"] = "Renamed"
        after = self.make_sensor()
        other = self.make_sensor(battery_id="second")
        self.assertEqual(before._attr_unique_id, after._attr_unique_id)
        self.assertNotEqual(before._attr_unique_id, other._attr_unique_id)

    async def test_source_changes_unavailability_and_listener_cleanup(self):
        sensor = self.make_sensor()
        await sensor.async_added_to_hass()
        self.states["sensor.source"].state = "unavailable"
        self.hass.listeners[0](None)
        self.assertFalse(sensor._attr_available)
        self.assertIsNone(sensor._attr_native_value)
        self.assertEqual(sensor.writes, 1)
        sensor.removers[0]()
        self.assertEqual(self.hass.listeners, [])

    async def test_soc_is_percent_and_rejects_out_of_range(self):
        self.states["sensor.source"] = SimpleNamespace(
            state="101", attributes={"unit_of_measurement": "%"}
        )
        sensor = self.make_sensor("soc")
        sensor._update_from_source()
        self.assertEqual(sensor._attr_device_class, "battery")
        self.assertEqual(sensor._attr_native_unit_of_measurement, "%")
        self.assertIsNone(sensor._attr_native_value)
        self.assertEqual(sensor._attr_extra_state_attributes["data_quality"], "out_of_range")

    async def test_legacy_id_and_registration_are_preserved(self):
        created = []
        entry = SimpleNamespace(entry_id="entry", options={}, data={
            "grid_power": "sensor.grid",
            "batteries": {"stable": {**self.battery, "soc": "sensor.soc"}},
        })
        await sensor_module.async_setup_entry(self.hass, entry, created.extend)
        self.assertEqual([item._attr_unique_id for item in created],
                         ["entry_grid_power", "entry_stable_soc"])

    async def test_invalid_stored_energy_never_remains_displayed_as_a_valid_stock(self):
        sensor = self.make_sensor()
        await sensor.async_added_to_hass()
        self.states["sensor.source"].state = "305799"
        self.hass.listeners[0](None)
        self.assertIsNone(sensor._attr_native_value)
        self.assertEqual(sensor._attr_extra_state_attributes["data_quality"], "exceeds_capacity")
        self.states["sensor.source"].state = "2500"
        self.states["sensor.source"].attributes["state_class"] = "total_increasing"
        self.hass.listeners[0](None)
        self.assertEqual(sensor._attr_extra_state_attributes["data_quality"], "cumulative_energy")

    async def test_calculated_home_freshness_and_stable_id(self):
        now = datetime.now(timezone.utc)
        self.states = {
            "sensor.import": SimpleNamespace(state="500", attributes={"unit_of_measurement": "W"}, last_reported=now),
            "sensor.export": SimpleNamespace(state="0", attributes={"unit_of_measurement": "W"}, last_reported=now),
        }
        self.hass.states.get = self.states.get
        sensor = sensor_module.CalculatedHomePower("entry", {
            "grid_import": "sensor.import", "grid_export": "sensor.export",
            "home_boundary_confirmed": True, "home_has_solar": False, "home_has_storage": False, "home_freshness_policy": "strict",
        })
        sensor.hass = self.hass
        sensor.removers = []
        sensor.writes = 0
        await sensor.async_added_to_hass()
        self.assertEqual(sensor._attr_unique_id, "entry_home_power")
        self.assertEqual(sensor._attr_native_value, 500)
        self.states["sensor.import"].last_reported = now - timedelta(seconds=301)
        self.hass.listeners[0](None)
        self.assertIsNone(sensor._attr_native_value)
        self.assertEqual(sensor._attr_extra_state_attributes["data_quality"], "stale_source")
        for remove in sensor.removers:
            remove()
        self.assertEqual(self.hass.listeners, [])

    async def test_signed_grid_display_channels_and_lifecycle(self):
        self.states["sensor.grid"] = SimpleNamespace(state="-.3", attributes={"unit_of_measurement":"kW"})
        incoming = sensor_module.DerivedGridPower("entry", "grid_import", "sensor.grid")
        outgoing = sensor_module.DerivedGridPower("entry", "grid_export", "sensor.grid")
        for item in (incoming, outgoing):
            item.hass = self.hass; item.removers = []; item.writes = 0
            await item.async_added_to_hass()
        self.assertEqual((incoming._attr_native_value, outgoing._attr_native_value), (0,300))
        self.states["sensor.grid"].state = ".2"
        for callback in self.hass.listeners: callback(None)
        self.assertEqual((incoming._attr_native_value, outgoing._attr_native_value), (200,0))
        self.states["sensor.grid"].state = "unavailable"
        for callback in self.hass.listeners: callback(None)
        self.assertIsNone(incoming._attr_native_value)
        self.assertIsNone(outgoing._attr_native_value)
        for item in (incoming, outgoing):
            for remove in item.removers: remove()
        self.assertFalse(self.hass.listeners)

    async def test_home_diagnostics_explain_stale_and_explicit_timeout_disable(self):
        now = datetime.now(timezone.utc)
        self.states = {"sensor.grid": SimpleNamespace(state="-300", attributes={"unit_of_measurement": "W"}, last_reported=now),
                       "sensor.pv": SimpleNamespace(state="2000", attributes={"unit_of_measurement": "W"}, last_reported=now-timedelta(hours=1))}
        self.hass.states.get = self.states.get
        sensor = sensor_module.CalculatedHomePower("entry", {"grid_power": "sensor.grid", "home_grid_mode": "signed", "solar_power": "sensor.pv", "home_has_solar": True, "home_has_storage": False, "home_boundary_confirmed": True, "home_freshness_policy":"strict"})
        sensor.hass = self.hass
        sensor._update()
        a = sensor._attr_extra_state_attributes
        self.assertEqual(a["data_quality"], "stale_source")
        self.assertEqual(a["stale_source_entity_ids"], ["sensor.pv"])
        self.assertEqual(a["grid_representation"], "signed")
        self.assertEqual(a["balance_inputs"][0]["contribution_w"], -300)
        sensor._mapping["home_freshness_policy"] = "warn"
        sensor._update()
        self.assertEqual(sensor._attr_native_value, 1700)
        self.assertTrue(sensor._attr_extra_state_attributes["source_age_warning"])
        self.assertEqual(sensor._attr_extra_state_attributes["data_quality"], "valid")
        sensor._mapping["home_max_age_seconds"] = 0
        sensor._update()
        self.assertEqual(sensor._attr_native_value, 1700)
        self.assertFalse(sensor._attr_extra_state_attributes["freshness_check_enabled"])
        self.assertGreater(sensor._attr_extra_state_attributes["balance_inputs"][1]["age_seconds"], 3500)
        self.states["sensor.pv"].state = "unavailable"
        sensor._update()
        self.assertIsNone(sensor._attr_native_value)
        self.assertEqual(sensor._attr_extra_state_attributes["data_quality"], "unavailable")

    async def test_usage_mirrors_use_units_and_read_only_status(self):
        usage = {"name": "Router", "kind": "solar_router", "energy_period": "today",
                 "energy": "sensor.source", "status": "sensor.source", "included_in_home": True}
        energy = sensor_module.UsageSensor("entry", "stable", usage, "energy")
        energy.hass = self.hass
        energy._update_from_source()
        self.assertEqual(energy._attr_native_value, 2.5)
        self.assertEqual(energy._attr_native_unit_of_measurement, "kWh")
        self.assertEqual(energy._attr_extra_state_attributes["energy_period"], "today")
        self.states["sensor.source"].state = "on"
        status = sensor_module.UsageSensor("entry", "stable", usage, "status")
        status.hass = self.hass
        status._update_from_source()
        self.assertEqual(status._attr_native_value, "on")
        self.assertIsNone(status._attr_state_class)
        self.assertIsNone(status._attr_native_unit_of_measurement)
