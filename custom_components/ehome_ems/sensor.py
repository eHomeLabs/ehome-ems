"""Read-only Home Assistant power sensor mapping."""
from .measurement import normalize_power

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    SOURCES, CONF_GRID_POWER, CONF_GRID_IMPORT, CONF_GRID_EXPORT,
    CONF_SOLAR_POWER, CONF_HOME_POWER,
)

LABELS = {
    CONF_GRID_POWER: "Grid power",
    CONF_GRID_IMPORT: "Grid import",
    CONF_GRID_EXPORT: "Grid export",
    CONF_SOLAR_POWER: "Solar power",
    CONF_HOME_POWER: "Home power",
}


async def async_setup_entry(hass, entry, async_add_entities):
    """Create read-only mirrors of mapped power sensors."""
    mapping = entry.options if entry.options else entry.data
    async_add_entities([
        MappedPowerSensor(entry.entry_id, key, mapping[key])
        for key in SOURCES if mapping.get(key)
    ])


class MappedPowerSensor(SensorEntity):
    """Mirror an existing HA sensor without issuing any commands."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = "W"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, entry_id, key, source):
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_name = f"eHome EMS {LABELS[key]}"
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
        reading = normalize_power(
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
        self._attr_native_value = reading.value
        self._attr_available = reading.value is not None
