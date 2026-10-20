"""Read-only mirror of mapped Home Assistant power sensors."""
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity
from .const import CONF_GRID_POWER, CONF_SOLAR_POWER, CONF_HOME_POWER

LABELS = {CONF_GRID_POWER: "Grid power", CONF_SOLAR_POWER: "Solar power", CONF_HOME_POWER: "Home power"}

async def async_setup_entry(hass, entry, async_add_entities):
    mapping = {**entry.data, **entry.options}
    async_add_entities([MappedPowerSensor(entry.entry_id, key, entity_id) for key, entity_id in mapping.items() if key in LABELS and entity_id])

class MappedPowerSensor(SensorEntity):
    """Display the numeric value of a selected power entity without controlling it."""
    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = "W"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, entry_id, key, source):
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_name = f"EMS {LABELS[key]}"
        self._source = source
        self._attr_native_value = None
        self._attr_available = False

    async def async_added_to_hass(self):
        self._update_from_source()
        @callback
        def on_change(event):
            self._update_from_source()
            self.async_write_ha_state()
        self.async_on_remove(async_track_state_change_event(self.hass, [self._source], on_change))

    @callback
    def _update_from_source(self):
        state = self.hass.states.get(self._source)
        self._attr_available = False
        self._attr_native_value = None
        if state is None or state.state in ("unknown", "unavailable"):
            return
        unit = state.attributes.get("unit_of_measurement")
        factor = {"W": 1, "kW": 1000}.get(unit)
        if factor is None:
            return
        try:
            value = float(state.state) * factor
            if not __import__("math").isfinite(value):
                return
        except (ValueError, TypeError):
            return
        self._attr_native_value = round(value, 2)
        self._attr_available = True
