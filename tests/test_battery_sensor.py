"""Entity lifecycle contract tests using minimal HA API doubles."""
import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class EntityDouble:
    def async_on_remove(self, remove):
        self.removers.append(remove)

    def async_write_ha_state(self):
        self.writes += 1


def load_sensor():
    modules = {name: ModuleType(name) for name in (
        "homeassistant", "homeassistant.components", "homeassistant.components.sensor",
        "homeassistant.core", "homeassistant.helpers", "homeassistant.helpers.event",
        "ems_sensor_test",
    )}
    modules["ems_sensor_test"].__path__ = [str(ROOT / "custom_components/ehome_ems")]
    sensors = modules["homeassistant.components.sensor"]
    sensors.SensorEntity = EntityDouble
    sensors.SensorDeviceClass = SimpleNamespace(POWER="power", BATTERY="battery", ENERGY="energy")
    sensors.SensorStateClass = SimpleNamespace(MEASUREMENT="measurement")
    modules["homeassistant.core"].callback = lambda f: f

    def subscribe(hass, entity_ids, callback):
        hass.listeners.append(callback)
        return lambda: hass.listeners.remove(callback)

    modules["homeassistant.helpers.event"].async_track_state_change_event = subscribe
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
