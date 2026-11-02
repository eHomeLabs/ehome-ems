"""eHome EMS: energy monitoring and explicitly enabled equipment controls."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from .const import DOMAIN
from .dashboard_service import register_dashboard_service
from .panel import async_setup_panel_domain, async_setup_entry_panel

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration domain."""
    register_dashboard_service(hass)
    await async_setup_panel_domain(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up an entry and its mapped sensors."""
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    try:
        await async_setup_entry_panel(hass, entry)
        if (entry.options or entry.data).get("energy_goals"):
            from .energy_goal_runtime import async_setup_goals
            await async_setup_goals(hass, entry)
    except Exception:
        await hass.config_entries.async_unload_platforms(entry, ["sensor"])
        raise
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload entities after a mapping is changed."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload mapped sensors and registered listeners."""
    # HA runs entry.async_on_unload callbacks after the platforms unload.
    # Calling ConfigEntry.async_unload here would recurse into its lifecycle.
    runtime = hass.data.get(DOMAIN, {}).get("energy_goal_runtime", {}).get(entry.entry_id)
    if runtime:
        await runtime.async_stop()
    return await hass.config_entries.async_unload_platforms(entry, ["sensor"])


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Forget the bounded in-memory scenario journal when an entry is removed."""
    hass.data.get(DOMAIN, {}).get("simulation_history", {}).pop(entry.entry_id, None)
