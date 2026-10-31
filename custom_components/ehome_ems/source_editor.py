"""Targeted administrator source remapping; no device commands."""
from copy import deepcopy
from .const import DOMAIN, SOURCES, CONF_BATTERIES, BATTERY_SOURCES, CONF_USAGES, USAGE_SOURCES
from .home_balance import home_sources


def source_specs(mapping):
    for key in SOURCES:
        if mapping.get(key) or (key == "home_power" and mapping.get("home_power_mode") == "calculated"):
            yield key, [key], "power"
    for identifier, battery in mapping.get(CONF_BATTERIES, {}).items():
        for key in BATTERY_SOURCES:
            if battery.get(key):
                yield f"{identifier}_{key}", [CONF_BATTERIES, identifier, key], key
    for identifier, usage in mapping.get(CONF_USAGES, {}).items():
        for key in USAGE_SOURCES:
            if usage.get(key):
                yield f"usage_{identifier}_{key}", [CONF_USAGES, identifier, key], key


def source_value(mapping, path):
    value = mapping
    for part in path:
        value = value.get(part)
        if value is None:
            return None
    return value


def binding_metadata(mapping, entities):
    bindings = {}
    for suffix, path, role in source_specs(mapping):
        if suffix not in entities:
            continue
        units = ["%"] if role == "soc" else ["Wh", "kWh"] if role in ("remaining_energy", "energy") else ["W", "kW"]
        domains = ["sensor", "binary_sensor", "switch", "select"] if role == "status" else ["sensor"]
        bindings[entities[suffix]] = {
            "source": source_value(mapping, path), "domains": domains,
            "units": [] if role == "status" else units,
            "calculated_home": path == ["home_power"] and mapping.get("home_power_mode") == "calculated",
        }
    return bindings


def remap_source(hass, entry, mirror_id, source_id, expected_source, expected_revision):
    if entry.modified_at.isoformat() != expected_revision:
        return "conflict"
    from .dashboard_service import dashboard_snapshot
    bindings = dashboard_snapshot(hass, entry.entry_id).get("bindings", {})
    binding = bindings.get(mirror_id)
    if not binding or binding["source"] != expected_source:
        return "conflict"
    state = hass.states.get(source_id)
    if not state or source_id.split(".")[0] not in binding["domains"]:
        return "invalid_source"
    if binding["units"] and state.attributes.get("unit_of_measurement") not in binding["units"]:
        return "unsupported_unit"
    mapping = entry.options or entry.data
    # Resolve the mirror through the current registry, never a client-supplied path.
    from homeassistant.helpers import entity_registry as er
    registry = er.async_get(hass)
    target = None
    for suffix, path, _ in source_specs(mapping):
        if registry.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_{suffix}") == mirror_id:
            target = path
            break
    if target is None:
        return "invalid_source"
    candidate = deepcopy(dict(mapping))
    parent = candidate
    for part in target[:-1]:
        parent = parent[part]
    parent[target[-1]] = source_id
    if target == ["home_power"]:
        candidate["home_power_mode"] = "existing"
    from .config_flow import PowerWizard
    validator = PowerWizard()
    validator.hass = hass
    if errors := validator._errors(candidate):
        return next(iter(errors.values()))
    if candidate.get("home_power_mode") == "calculated":
        _, reason = home_sources(candidate)
        if reason:
            return reason
    hass.config_entries.async_update_entry(entry, options=candidate)
    return None
