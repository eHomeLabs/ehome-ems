"""Read-only Home Assistant power sensor mapping."""
from .measurement import normalize_power, normalize_battery
from .home_balance import home_sources, calculate_home, grid_sources
from .usage import normalize_usage
from datetime import datetime, timedelta, timezone

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval

from .const import (
    SOURCES, CONF_GRID_POWER, CONF_GRID_IMPORT, CONF_GRID_EXPORT,
    CONF_SOLAR_POWER, CONF_HOME_POWER,
    CONF_BATTERIES, BATTERY_SOURCES, HOME_MODE,
    CONF_USAGES, USAGE_SOURCES,
)

LABELS = {
    CONF_GRID_POWER: "Grid power",
    CONF_GRID_IMPORT: "Grid import",
    CONF_GRID_EXPORT: "Grid export",
    CONF_SOLAR_POWER: "Solar power",
    CONF_HOME_POWER: "Conso Maison",
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
        and not (key == CONF_HOME_POWER and mapping.get(HOME_MODE) == "calculated")
    ]
    network, _ = grid_sources(mapping)
    if mapping.get(HOME_MODE) == "calculated" and network and network[0][0] == "grid_power":
        entities.extend(DerivedGridPower(entry.entry_id, key, mapping["grid_power"])
                        for key in (CONF_GRID_IMPORT, CONF_GRID_EXPORT) if not mapping.get(key))
    if mapping.get(HOME_MODE) == "calculated":
        entities.append(CalculatedHomePower(entry.entry_id, mapping))
    for battery_id, battery in mapping.get(CONF_BATTERIES, {}).items():
        entities.extend(
            MappedPowerSensor(entry.entry_id, key, battery[key],
                              battery=battery, battery_id=battery_id)
            for key in BATTERY_SOURCES if battery.get(key)
        )
    for usage_id, usage in mapping.get(CONF_USAGES, {}).items():
        entities.extend(
            UsageSensor(entry.entry_id, usage_id, usage, key)
            for key in USAGE_SOURCES if usage.get(key)
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
        details = {
            "capacity_kwh": self._battery.get("capacity_kwh"),
            "state_class": state.attributes.get("state_class") if state else None,
        } if self._battery else {}
        reading = normalize(
            state.state if state else None,
            state.attributes.get("unit_of_measurement") if state else None,
            self._role,
            **details,
        )
        self._attr_extra_state_attributes = {
            "source_entity_id": self._source,
            "data_quality": reading.quality,
            "value_origin": "external_source",
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


class DerivedGridPower(MappedPowerSensor):
    """Split a signed grid sensor for display; never add it again to the balance."""

    @callback
    def _update_from_source(self):
        state = self.hass.states.get(self._source)
        reading = normalize_power(state.state if state else None,
                                  state.attributes.get("unit_of_measurement") if state else None,
                                  "grid_power")
        self._attr_native_value = None if reading.value is None else max(0, reading.value if self._role == CONF_GRID_IMPORT else -reading.value)
        self._attr_available = self._attr_native_value is not None
        self._attr_extra_state_attributes = {
            "value_origin": "calculated_signed_grid", "data_quality": reading.quality,
            "source_entity_id": self._source, "sign_convention": "import_positive_export_negative",
        }


class CalculatedHomePower(SensorEntity):
    """Event-driven, AC-only home load power, with the same ID as its mirror."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = "W"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_should_poll = False

    def __init__(self, entry_id, mapping):
        self._attr_unique_id = f"{entry_id}_{CONF_HOME_POWER}"
        self._attr_name = "eHome EMS Conso Maison"
        self._mapping = mapping
        self._sources, self._setup_reason = home_sources(mapping)
        self._attr_available = False
        self._attr_native_value = None

    async def async_added_to_hass(self):
        self._update()

        @callback
        def changed(event):
            self._update()
            self.async_write_ha_state()

        if self._sources:
            self.async_on_remove(async_track_state_change_event(
                self.hass, [source for _, source, _ in self._sources], changed
            ))
        self.async_on_remove(async_track_time_interval(self.hass, changed, timedelta(seconds=30)))

    @callback
    def _update(self):
        values = {}
        details = []
        stale_sources = []
        now = datetime.now(timezone.utc)
        max_age = self._mapping.get("home_max_age_seconds", 300)
        for role, source, coefficient in self._sources:
            state = self.hass.states.get(source)
            if state:
                values[source] = (state.state, state.attributes.get("unit_of_measurement"))
            age = max(0, (now - state.last_reported).total_seconds()) if state else None
            normalized = normalize_power(*values.get(source, (None, None)), role)
            is_stale = bool(max_age and age is not None and age > max_age)
            if is_stale:
                stale_sources.append(source)
            details.append({"role": role, "entity_id": source, "coefficient": coefficient,
                            "value_w": normalized.value,
                            "contribution_w": normalized.value * coefficient if normalized.value is not None else None,
                            "age_seconds": round(age, 1) if age is not None else None,
                            "quality": "stale_source" if is_stale and normalized.value is not None else normalized.quality})
        reading = calculate_home(self._mapping, values)
        stale = bool(stale_sources) and reading.value is not None
        self._attr_native_value = None if stale else reading.value
        self._attr_available = self._attr_native_value is not None
        self._attr_extra_state_attributes = {
            "value_origin": "calculated",
            "data_quality": "stale_source" if stale else reading.quality,
            "source_entity_ids": [source for _, source, _ in self._sources],
            "max_source_age_seconds": max_age,
            "balance_topology": "ac_loads",
            "balance_formula": "solar + grid - battery_charge + battery_discharge",
            "home_includes": "all_household_loads_including_water_heater_and_ev",
            "grid_representation": "signed" if any(role == "grid_power" for role, _, _ in self._sources) else "separate",
            "balance_inputs": details,
            "stale_source_entity_ids": stale_sources,
            "freshness_check_enabled": bool(max_age),
        }


class UsageSensor(MappedPowerSensor):
    """A usage is a breakdown of home loads, never a new balance input."""

    def __init__(self, entry_id, usage_id, usage, key):
        super().__init__(entry_id, f"usage_{usage_id}_{key}", usage[key])
        self._usage = usage
        self._usage_id = usage_id
        self._usage_key = key
        self._attr_name = f"eHome EMS {usage['name']} {key}"
        if key == "energy":
            self._attr_device_class = SensorDeviceClass.ENERGY
            self._attr_native_unit_of_measurement = "kWh"
        elif key == "temperature":
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
            self._attr_native_unit_of_measurement = "°C"
        elif key == "status":
            self._attr_device_class = None
            self._attr_state_class = None
            self._attr_native_unit_of_measurement = None

    @callback
    def _update_from_source(self):
        state = self.hass.states.get(self._source)
        reading = normalize_usage(
            state.state if state else None,
            state.attributes.get("unit_of_measurement") if state else None,
            self._usage_key,
        )
        self._attr_native_value = reading.value
        self._attr_available = reading.value is not None
        self._attr_extra_state_attributes = {
            "source_entity_id": self._source, "data_quality": reading.quality,
            "value_origin": "external_source", "usage_id": self._usage_id,
            "usage_kind": self._usage["kind"], "included_in_home": True,
            "energy_period": self._usage.get("energy_period", "total") if self._usage_key == "energy" else None,
        }
