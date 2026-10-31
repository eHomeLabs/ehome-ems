"""Automatic managed panel and authenticated read-only dashboard endpoint."""
from pathlib import Path
import voluptuous as vol
from homeassistant.components import frontend, panel_custom, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError

from .dashboard_service import dashboard_snapshot, power_scale
from .const import DOMAIN
from .source_editor import remap_source

PANEL_URL = "/ehome_ems_panel.js"


def panel_path(entry_id):
    return f"ehome-ems-{entry_id.lower()}"


@websocket_api.websocket_command({
    "type": "ehome_ems/dashboard",
    "entry_id": str,
    vol.Optional("language"): vol.In(["fr", "en"]),
    vol.Optional("max_power_w", default=10000): power_scale,
})
@callback
def websocket_dashboard(hass, connection, msg):
    try:
        result = dashboard_snapshot(hass, msg["entry_id"], msg.get("language"), msg["max_power_w"])
    except HomeAssistantError:
        connection.send_error(msg["id"], "not_ready", "eHome EMS is not ready.")
        return
    connection.send_result(msg["id"], result)


@websocket_api.require_admin
@websocket_api.websocket_command({
    "type": "ehome_ems/remap_source", "entry_id": str, "entity_id": str, "source_id": str,
    "expected_source": vol.Any(str, None), "revision": str,
})
@callback
def websocket_remap(hass, connection, msg):
    entry = hass.config_entries.async_get_entry(msg["entry_id"])
    if entry is None or entry.domain != DOMAIN:
        connection.send_error(msg["id"], "not_ready", "eHome EMS is not ready.")
        return
    reason = remap_source(hass, entry, msg["entity_id"], msg["source_id"],
                          msg["expected_source"], msg["revision"])
    if reason:
        connection.send_error(msg["id"], reason, "Source rejected; refresh and check the selected reading.")
    else:
        connection.send_result(msg["id"], {"updated": True})


async def async_setup_panel_domain(hass):
    await hass.http.async_register_static_paths([
        StaticPathConfig(PANEL_URL, str(Path(__file__).parent / "frontend/ehome-panel.mjs"), False)
    ])
    websocket_api.async_register_command(hass, websocket_dashboard)
    websocket_api.async_register_command(hass, websocket_remap)


async def async_setup_entry_panel(hass, entry):
    path = panel_path(entry.entry_id)
    if frontend.async_panel_exists(hass, path):
        raise HomeAssistantError("The eHome EMS panel path is already in use.")
    await panel_custom.async_register_panel(
        hass, frontend_url_path=path, webcomponent_name="ehome-ems-panel",
        sidebar_title="eHome EMS", sidebar_icon="mdi:home-lightning-bolt",
        module_url=f"{PANEL_URL}?v=0.2.0b6",
        config={"entry_id": entry.entry_id, "revision": entry.modified_at.isoformat()},
    )
    entry.async_on_unload(lambda: frontend.async_remove_panel(hass, path))
