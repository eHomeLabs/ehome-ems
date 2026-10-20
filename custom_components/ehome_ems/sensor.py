"""Read-only Home Assistant power sensor mapping."""
from math import isfinite

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import SOURCES, CONF_GRID_POWER, CONF_SOLAR_POWER, CONF_HOME_POWER

LABELS = {
    CONF_GRID_POWER: "Grid power",
    CONF_SOLAR_POWER: "Solar power",
    CONF_HOME_POWER: "Home power",
}


async def async_setup_entry(hass, entry, async_add_entities):
    """Create mirrors only for mapped power sensors."""
    mapping = entry.options if entry.options else entry.data
    async_add_entities([
        MappedPowerSensor(entry.entry_id, key, mapping[key])
        for key in SOURCES if mapping.get(key)
    ])


class MappedPowerSensor(SensorEntity):
    """Mirror a selected HA sensor, preserving its sign convention."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = "W"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, entry_id, key, source):
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_name = f"eHome EMS {LABELS[key]}"
        self._source = source
        self._attr_native_value = None
        self._attr_available = False

    async def async_added_to_hass(self):
        """Subscribe to updates, cleaned up automatically on unload."""
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
        if state is None or state.state in ("unknown", "unavailable"):
            return
        factor = {"W": 1, "kW": 1000}.get(
            state.attributes.get("unit_of_measurement")
        )
        if factor is None:
            return
        try:
            value = float(state.state) * factor
        except (ValueError, TypeError, OverflowError):
            return
        if not isfinite(value):
            return
        self._attr_native_value = round(value, 2)
        self._attr_available = True
        self._attr_extra_state_attributes = {"source_entity_id": self._source}
