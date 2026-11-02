"""Native F1ATB measurements kept separate from the EMS energy balance."""
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity


class RouterSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry_id, identifier, usage, key):
        super().__init__(coordinator)
        self._key, self._index = key, usage.get("router_action", 0)
        self._attr_unique_id = f"{entry_id}_router_{identifier}_{key}"
        self._attr_name = f"eHome EMS {usage['name']} F1ATB {key}"
        self._attr_native_unit_of_measurement = {
            "probe_power": "W", "probe_energy_total_kwh": "kWh", "grid_import_power": "W",
            "grid_export_power": "W", "opening": "%", "force_minutes": "min", **{f"temperature_{i}": "°C" for i in range(4)}}.get(key)
        self._attr_device_class = (SensorDeviceClass.TEMPERATURE if key.startswith("temperature_") else SensorDeviceClass.POWER if key.endswith("power") else
                                  SensorDeviceClass.ENERGY if key.endswith("kwh") else None)
        self._attr_state_class = (SensorStateClass.TOTAL_INCREASING if key.endswith("kwh") else
                                  SensorStateClass.MEASUREMENT if key not in ("status", "connection") else None)

    @property
    def native_value(self):
        if self._key == "connection":
            return "online" if self.coordinator.last_update_success else "offline"
        data = self.coordinator.data or {}
        if self._key.startswith("temperature_"):
            temperatures = data.get("temperatures", [])
            i = int(self._key[-1])
            return temperatures[i] if i < len(temperatures) else None
        live = data.get("live_actions", {}).get(self._index, {})
        if self._key == "status":
            force = live.get("force_minutes")
            return None if force is None else "auto" if force == 0 else "forced_on" if force > 0 else "forced_off"
        return live.get(self._key) if self._key in ("opening", "force_minutes") else data.get(self._key)

    @property
    def available(self):
        return self._key == "connection" or (super().available and self.native_value is not None)


def router_sensors(coordinators, entry, mapping):
    return [RouterSensor(coordinator, entry.entry_id, identifier, mapping["usages"][identifier], key)
            for identifier, coordinator in coordinators.items()
            for key in ("probe_power", "probe_energy_total_kwh", "grid_import_power", "grid_export_power", "opening", "force_minutes", "status", "connection", *(f"temperature_{i}" for i in range(4)))]
