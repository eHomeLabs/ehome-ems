"""Expose generated configuration as response data, without storage writes."""
from math import isfinite
import voluptuous as vol

from homeassistant.core import SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, VERSION, SOURCES, CONF_BATTERIES, BATTERY_SOURCES
from .const import CONF_USAGES, USAGE_SOURCES
from .dashboard import build_dashboard
from .source_editor import binding_metadata
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
    result["simulation"] = plan(mapping)
    result["simulation_history"] = list(getattr(hass, "data", {}).get(DOMAIN, {}).get("simulation_history", {}).get(entry.entry_id, []))
    result["flow"] = {
        "entities": {key: entities.get(key) for key in SOURCES},
        "home_calculated": mapping.get("home_power_mode") == "calculated",
        "batteries": [{"name": battery["name"], "role": battery["role"],
                       "coupling": battery["coupling"],
                       **{key: entities.get(f"{identifier}_{key}") for key in BATTERY_SOURCES}}
                      for identifier, battery in mapping.get(CONF_BATTERIES, {}).items()],
        "usages": [{"name": usage["name"], "kind": usage.get("kind", "other"),
                    **{key: entities.get(f"usage_{identifier}_{key}") for key in USAGE_SOURCES}}
                   for identifier, usage in mapping.get(CONF_USAGES, {}).items()],
    }
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
