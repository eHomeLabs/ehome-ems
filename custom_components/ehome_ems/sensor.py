"""Read-only Home Assistant power sensor mapping."""
from .measurement import normalize_power, normalize_battery

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    SOURCES, CONF_GRID_POWER, CONF_GRID_IMPORT, CONF_GRID_EXPORT,
    CONF_SOLAR_POWER, CONF_HOME_POWER,
    CONF_BATTERIES, BATTERY_SOURCES,
)

LABELS = {
    CONF_GRID_POWER: "Grid power",
    CONF_GRID_IMPORT: "Grid import",
    CONF_GRID_EXPORT: "Grid export",
    CONF_SOLAR_POWER: "Solar power",
    CONF_HOME_POWER: "Home power",
    "charge_power": "Charge power",
    "discharge_power": "Discharge power",
    "soc": "State of charge",
    "remaining_energy": "Remaining energy",
}


async def async_setup_entry(hass, entry, async_add_entities):
    """Create read-only mirrors of mapped power sensors."""
    mapping = entry.options if entry.options else entry.data
    entities = [
        MappedPowerSensor(entry.entry_id, key, mapping[key])
        for key in SOURCES if mapping.get(key)
    ]
    for battery_id, battery in mapping.get(CONF_BATTERIES, {}).items():
        entities.extend(
            MappedPowerSensor(entry.entry_id, key, battery[key],
                              battery=battery, battery_id=battery_id)
            for key in BATTERY_SOURCES if battery.get(key)
        )
    async_add_entities(entities)


class MappedPowerSensor(SensorEntity):
    """Mirror an existing HA sensor without issuing any commands."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = "W"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_should_poll = False

    def __init__(self, entry_id, key, source, *, battery=None, battery_id=None):
        suffix = f"{battery_id}_{key}" if battery_id else key
        self._attr_unique_id = f"{entry_id}_{suffix}"
        label = LABELS.get(key, key)
        self._attr_name = f"eHome EMS {battery['name']} {label}" if battery else f"eHome EMS {label}"
        self._battery = battery
        self._battery_id = battery_id
        if battery and key == "soc":
            self._attr_device_class = SensorDeviceClass.BATTERY
            self._attr_native_unit_of_measurement = "%"
        elif battery and key == "remaining_energy":
            # Stored energy is a stock, never a cumulative energy counter.
            self._attr_device_class = SensorDeviceClass.ENERGY
            self._attr_native_unit_of_measurement = "kWh"
        self._source = source
        self._role = key
        self._attr_native_value = None
        self._attr_available = False

    async def async_added_to_hass(self):
        """Subscribe to source changes and remove subscription on unload."""
        self._update_from_source()

        @callback
        def on_change(event):
            self._update_from_source()
            self.async_write_ha_state()

        self.async_on_remove(
            async_track_state_change_event(self.hass, [self._source], on_change)
        )

    @callback
    def _update_from_source(self):
        state = self.hass.states.get(self._source)
        self._attr_available = False
        self._attr_native_value = None
        normalize = normalize_battery if self._battery else normalize_power
        reading = normalize(
            state.state if state else None,
            state.attributes.get("unit_of_measurement") if state else None,
            self._role,
        )
        self._attr_extra_state_attributes = {
            "source_entity_id": self._source,
            "data_quality": reading.quality,
            "value_origin": "measured",
            "source_unit": state.attributes.get("unit_of_measurement") if state else None,
        }
        if self._battery:
            self._attr_extra_state_attributes.update({
                "battery_id": self._battery_id,
                "battery_role": self._battery["role"],
                "coupling": self._battery["coupling"],
                "capacity_kwh": self._battery.get("capacity_kwh"),
                "eligible_for_ac_balance": (
                    self._battery["role"] == "active" and self._battery["coupling"] == "ac"
                ),
                "energy_origin": "unknown",
            })
        self._attr_native_value = reading.value
        self._attr_available = reading.value is not None
