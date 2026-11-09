"""Expose generated configuration as response data, without storage writes."""
from math import isfinite
from copy import deepcopy
import voluptuous as vol

from homeassistant.core import SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, VERSION, SOURCES, CONF_BATTERIES, BATTERY_SOURCES
from .const import CONF_USAGES, USAGE_SOURCES
from .dashboard import build_dashboard
from .source_editor import binding_metadata
from .home_balance import grid_sources
from .simulation import plan

SERVICE_GENERATE = "generate_dashboard"


def power_scale(value):
    value = vol.Coerce(float)(value)
    if not isfinite(value) or not 100 <= value <= 1000000:
        raise vol.Invalid("max_power_w must be between 100 and 1000000")
    return value


def dashboard_snapshot(hass, entry_id=None, language=None, max_power_w=10000):
    """Resolve current mapping and mirror IDs through public HA registries."""
    entries = hass.config_entries.async_entries(DOMAIN)
    entries = [entry for entry in entries if not entry_id or entry.entry_id == entry_id]
    if len(entries) != 1:
        raise HomeAssistantError("Choose one configured eHome EMS entry.")
    entry = entries[0]
    mapping = entry.options or entry.data
    registry = er.async_get(hass)
    suffixes = [key for key in SOURCES if mapping.get(key)]
    if mapping.get("home_power_mode") == "calculated" and "home_power" not in suffixes:
        suffixes.append("home_power")
    network, _ = grid_sources(mapping)
    if mapping.get("home_power_mode") == "calculated" and network and network[0][0] == "grid_power":
        suffixes += [key for key in ("grid_import", "grid_export") if key not in suffixes]
    suffixes += [
        f"{battery_id}_{key}"
        for battery_id, battery in mapping.get(CONF_BATTERIES, {}).items()
        for key in BATTERY_SOURCES if battery.get(key)
    ]
    suffixes += [
        f"usage_{usage_id}_{key}" for usage_id, usage in mapping.get(CONF_USAGES, {}).items()
        for key in USAGE_SOURCES if usage.get(key)
    ]
    entities = {}
    for suffix in suffixes:
        entity_id = registry.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_{suffix}")
        registered = registry.async_get(entity_id) if entity_id else None
        if registered and not registered.disabled_by and registered.config_entry_id == entry.entry_id:
            entities[suffix] = entity_id
    language = (language or hass.config.language or "fr").split("-")[0]
    result = build_dashboard(mapping, entities, language=language, max_power_w=max_power_w)
    result["version"] = VERSION
    result["managed_url"] = f"/ehome-ems-{entry.entry_id.lower()}"
    if result["dashboard"]["views"]:
        fr = language == "fr"
        result["dashboard"]["views"][0]["cards"].insert(0, {
            "type": "markdown", "content": (
                "Le flux animé est disponible dans la [vue eHome EMS automatique]"
                if fr else "The animated flow is available in the [automatic eHome EMS view]"
            ) + f"({result['managed_url']}). " + (
                "Cette copie conserve ses cartes natives indépendantes."
                if fr else "This copy keeps its independent native cards."
            ),
        })
    result["bindings"] = binding_metadata(mapping, entities)
    runtime = getattr(hass, "data", {}).get(DOMAIN, {}).get("energy_goal_runtime", {}).get(entry.entry_id)
    result["energy_goals"] = list(runtime.results.values()) if runtime else []
    result["simulation"] = plan(mapping)
    result["simulation_history"] = list(getattr(hass, "data", {}).get(DOMAIN, {}).get("simulation_history", {}).get(entry.entry_id, []))
    result["flow"] = {
        "entities": {key: entities.get(key) for key in SOURCES},
        "photovoltaic": [{"id":identifier, **item} for identifier,item in mapping.get("photovoltaic",{}).items()],
        "home_calculated": mapping.get("home_power_mode") == "calculated",
        "batteries": [{"id": identifier, "name": battery["name"], "role": battery["role"],
                       "coupling": battery["coupling"],
                       **{key: entities.get(f"{identifier}_{key}") for key in BATTERY_SOURCES}}
                      for identifier, battery in mapping.get(CONF_BATTERIES, {}).items()],
        "usages": [{"id": identifier, "name": usage["name"], "kind": usage.get("kind", "other"),
                    "icon": usage.get("icon", "auto"),
                    **{key:usage.get(key) for key in ("router_connection","router_action","router_http_enabled","router_type","router_output","router_url","router_mqtt_topic","router_mqtt_enabled","router_protocol_confirmed")},
                    "daily_energy_goal_kwh": usage.get("daily_energy_goal_kwh"),
                    "control_enabled": usage.get("control_enabled", False),
                    "control_entity": usage.get("control_entity"),
                    "energy_period": usage.get("energy_period", "total"),
                    **{key: usage.get(key) for key in ("ev_tariff_mode", "ev_tariff_flat", "ev_tariff_hp", "ev_tariff_hc", "ev_hc_start", "ev_hc_end")},
                    **{key: entities.get(f"usage_{identifier}_{key}") for key in USAGE_SOURCES}}
                   for identifier, usage in mapping.get(CONF_USAGES, {}).items()],
    }
    ev_runtime = getattr(hass, "data", {}).get(DOMAIN, {}).get("ev_runtime", {}).get(entry.entry_id)
    if ev_runtime:
        for usage in result["flow"]["usages"]:
            tracker = ev_runtime.trackers.get(usage["id"])
            if tracker:
                usage["ev_session"] = tracker.snapshot()
    native = getattr(hass, "data", {}).get(DOMAIN, {}).get("router_http", {}).get(entry.entry_id, {})
    for usage in result["flow"]["usages"]:
        if usage["id"] in native:
            coordinator = native[usage["id"]]
            data = coordinator.data or {}
            usage["router_native"] = {"available": coordinator.last_update_success,
                "actions": data.get("actions", []), "config_token": data.get("config_token"),
                "temperatures": data.get("temperatures", []) if coordinator.last_update_success else []}
            usage["router_entities"] = {key: registry.async_get_entity_id("sensor", DOMAIN,
                f"{entry.entry_id}_router_{usage['id']}_{key}") for key in
                ("probe_power", "probe_energy_total_kwh", "grid_import_power", "grid_export_power", "opening", "force_minutes", "status", "connection", *(f"temperature_{i}" for i in range(4)))}
    result["settings"] = deepcopy(dict(mapping))
    result["weather_entity"] = mapping.get("weather_entity")
    result["time_zone"] = getattr(hass.config, "time_zone", "UTC")
    result["daily"] = dict(mapping.get("daily", {}))
    result["tariff_eur_kwh"] = mapping.get("tariff_eur_kwh")
    result["revision"] = entry.modified_at.isoformat() if hasattr(entry, "modified_at") else ""
    return result



def register_dashboard_service(hass):
    """Register once at domain setup; usable after an entry reload."""
    if hass.services.has_service(DOMAIN, SERVICE_GENERATE):
        return

    async def generate(call):
        return dashboard_snapshot(hass, **call.data)

    hass.services.async_register(
        DOMAIN, SERVICE_GENERATE, generate,
        schema=vol.Schema({
            vol.Optional("entry_id"): str,
            vol.Optional("language"): vol.In(["fr", "en"]),
            vol.Optional("max_power_w", default=10000): power_scale,
        }),
        supports_response=SupportsResponse.ONLY,
    )
