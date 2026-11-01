"""Explicit AC-only home-load power balance, independent of Home Assistant."""
from .const import CONF_BATTERIES
from .measurement import PowerReading, normalize_power


def home_sources(mapping):
    """Return required (role, entity_id, coefficient) inputs or a setup reason."""
    if not mapping.get("home_boundary_confirmed"):
        return [], "boundary_unconfirmed"
    sources = [("grid_import", mapping.get("grid_import"), 1),
               ("grid_export", mapping.get("grid_export"), -1)]
    solar = bool(mapping.get("home_has_solar"))
    if bool(mapping.get("solar_power")) != solar:
        return [], "solar_configuration"
    if solar:
        sources.append(("solar_power", mapping["solar_power"], 1))
    active = [b for b in mapping.get(CONF_BATTERIES, {}).values() if b["role"] == "active"]
    if bool(active) != bool(mapping.get("home_has_storage")):
        return [], "storage_configuration"
    for battery in active:
        if battery["coupling"] != "ac":
            return [], "unsupported_topology"
        sources.extend([
            ("charge_power", battery.get("charge_power"), -1),
            ("discharge_power", battery.get("discharge_power"), 1),
        ])
    if any(not source for _, source, _ in sources):
        return [], "missing_source"
    ids = [source for _, source, _ in sources]
    if len(ids) != len(set(ids)):
        return [], "duplicate_source"
    return sources, None


def calculate_home(mapping, readings):
    """readings maps source IDs to (raw value, unit); never fill gaps with zero."""
    sources, reason = home_sources(mapping)
    if reason:
        return PowerReading(None, reason)
    total = 0
    for role, source, coefficient in sources:
        raw, unit = readings.get(source, (None, None))
        reading = normalize_power(raw, unit, role)
        if reading.value is None:
            return PowerReading(None, reading.quality)
        total += reading.value * coefficient
    if total < 0:
        return PowerReading(None, "negative_balance")
    return PowerReading(round(total, 2), "valid")
