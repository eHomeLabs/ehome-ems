"""Automatic managed panel and authenticated read-only dashboard endpoint."""
from pathlib import Path
from datetime import datetime, timezone
import voluptuous as vol
from homeassistant.components import frontend, panel_custom, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import callback, Context
from homeassistant.exceptions import HomeAssistantError

from .dashboard_service import dashboard_snapshot, power_scale
from .const import DOMAIN, VERSION
from .manual_control import async_control
from .f1atb import async_router_command
from .source_editor import remap_source
from .simulation import save_plan, allocate
from .settings import update_settings, SettingsError

PANEL_URL = f"/ehome_ems_panel_{VERSION}.js"
PANEL_TAG = f"ehome-ems-panel-{VERSION.replace('.', '-')}"


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
    if not connection.user.is_admin:
        result.pop("settings", None)
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


@websocket_api.require_admin
@websocket_api.websocket_command({
    "type": "ehome_ems/manage_settings", "entry_id": str, "revision": str,
    "section": vol.In(["grid", "solar", "home", "daily", "batteries", "usages", "appliances", "photovoltaic"]),
    "action": vol.In(["save", "remove"]), vol.Optional("identifier"): vol.Any(str, None),
    vol.Optional("values", default={}): dict,
})
@callback
def websocket_manage_settings(hass, connection, msg):
    entry = hass.config_entries.async_get_entry(msg["entry_id"])
    if entry is None or entry.domain != DOMAIN:
        connection.send_error(msg["id"], "not_ready", "eHome EMS is not ready.")
        return
    try:
        result = update_settings(hass, entry, msg["section"], msg["action"], msg["values"], msg.get("identifier"), msg["revision"])
    except SettingsError as error:
        connection.send_error(msg["id"], str(error), "Settings rejected; check sources and refresh. " + ", ".join(f"{field}: {reason}" for field,reason in error.fields.items()))
        return
    connection.send_result(msg["id"], result)


async def async_setup_panel_domain(hass):
    await hass.http.async_register_static_paths([
        StaticPathConfig(PANEL_URL, str(Path(__file__).parent / "frontend/ehome-panel.mjs"), False),
        StaticPathConfig("/ehome_ems_assets", str(Path(__file__).parent / "frontend/assets"), False),
    ])
    websocket_api.async_register_command(hass, websocket_alerts)
    websocket_api.async_register_command(hass, websocket_save_alerts)
    websocket_api.async_register_command(hass, websocket_dashboard)
    websocket_api.async_register_command(hass, websocket_remap)
    websocket_api.async_register_command(hass, websocket_manage_settings)
    websocket_api.async_register_command(hass, websocket_manual_control)
    websocket_api.async_register_command(hass, websocket_router_command)
    websocket_api.async_register_command(hass, websocket_router_discover)
    websocket_api.async_register_command(hass, websocket_save_energy_goal)
    websocket_api.async_register_command(hass, websocket_energy_goals)
    websocket_api.async_register_command(hass, websocket_rearm_energy_goal)
    websocket_api.async_register_command(hass, websocket_save_simulation)
    websocket_api.async_register_command(hass, websocket_simulate)


@websocket_api.require_admin
@websocket_api.websocket_command({
    "type": "ehome_ems/save_simulation", "entry_id": str, "revision": str,
    "targets": vol.All(list, vol.Length(max=100)),
})
@callback
def websocket_save_simulation(hass, connection, msg):
    entry = hass.config_entries.async_get_entry(msg["entry_id"])
    if entry is None or entry.domain != DOMAIN:
        connection.send_error(msg["id"], "not_ready", "eHome EMS is not ready.")
        return
    try:
        save_plan(hass, entry, msg["targets"], msg["revision"])
    except ValueError as error:
        connection.send_error(msg["id"], str(error), "Scenario settings rejected; refresh or check limits.")
        return
    connection.send_result(msg["id"], {"updated": True})


@websocket_api.websocket_command({
    "type": "ehome_ems/simulate", "entry_id": str, "revision": str, "budget_w": int,
})
@callback
def websocket_simulate(hass, connection, msg):
    entry = hass.config_entries.async_get_entry(msg["entry_id"])
    if entry is None or entry.domain != DOMAIN:
        connection.send_error(msg["id"], "not_ready", "eHome EMS is not ready.")
        return
    if entry.modified_at.isoformat() != msg["revision"]:
        connection.send_error(msg["id"], "conflict", "Settings changed; refresh before simulating.")
        return
    try:
        result = allocate(entry.options or entry.data, msg["budget_w"])
    except ValueError as error:
        connection.send_error(msg["id"], str(error), "Invalid hypothetical budget.")
        return
    result["created_at"] = datetime.now(timezone.utc).isoformat()
    result["revision"] = msg["revision"]
    history = hass.data.setdefault(DOMAIN, {}).setdefault("simulation_history", {}).setdefault(entry.entry_id, [])
    history.append(result)
    del history[:-20]
    connection.send_result(msg["id"], result)


async def async_setup_entry_panel(hass, entry):
    path = panel_path(entry.entry_id)
    if frontend.async_panel_exists(hass, path):
        raise HomeAssistantError("The eHome EMS panel path is already in use.")
    await panel_custom.async_register_panel(
        hass, frontend_url_path=path, webcomponent_name=PANEL_TAG,
        sidebar_title="eHome EMS", sidebar_icon="mdi:home-lightning-bolt",
        module_url=PANEL_URL,
        config={"entry_id": entry.entry_id, "revision": entry.modified_at.isoformat()},
    )
    entry.async_on_unload(lambda: frontend.async_remove_panel(hass, path))


@websocket_api.require_admin
@websocket_api.websocket_command({
    "type": "ehome_ems/manual_control", "entry_id": str, "identifier": str,
    "desired_on": bool, "expected_state": vol.In(["on", "off"]), "revision": str,
})
@websocket_api.async_response
async def websocket_manual_control(hass, connection, msg):
    entry = hass.config_entries.async_get_entry(msg["entry_id"])
    if entry is None or entry.domain != DOMAIN:
        connection.send_error(msg["id"], "not_ready", "eHome EMS is not ready.")
        return
    try:
        result = await async_control(hass, entry, msg["identifier"], msg["desired_on"],
                                     msg["expected_state"], msg["revision"], Context(user_id=connection.user.id))
    except ValueError as error:
        connection.send_error(msg["id"], str(error), "Manual command rejected; refresh and check configuration.")
    except HomeAssistantError:
        connection.send_error(msg["id"], "command_failed", "Home Assistant could not execute the manual command.")
    else:
        connection.send_result(msg["id"], result)


@websocket_api.require_admin
@websocket_api.websocket_command({"type":"ehome_ems/router_command","entry_id":str,"identifier":str,"revision":str,"action":vol.In(["force_on","force_off","release","parameters","http_parameters","boost_hour","boost_duration"]),"values":dict})
@websocket_api.async_response
async def websocket_router_command(hass, connection, msg):
    entry=hass.config_entries.async_get_entry(msg["entry_id"])
    if entry is None or entry.domain!=DOMAIN:
        connection.send_error(msg["id"],"not_ready","eHome EMS is not ready.")
        return
    try:
        result=await async_router_command(hass,entry,msg["identifier"],msg["revision"],msg["action"],msg["values"],Context(user_id=connection.user.id))
    except ValueError as error:
        connection.send_error(msg["id"],str(error),"Router command rejected; check saved configuration.")
    except HomeAssistantError:
        connection.send_error(msg["id"],"command_failed","Router communication failed.")
    else:connection.send_result(msg["id"],result)


@websocket_api.require_admin
@websocket_api.websocket_command({"type": "ehome_ems/router_discover", "host": str})
@websocket_api.async_response
async def websocket_router_discover(hass, connection, msg):
    """Read-only discovery before saving. Never expose raw router configuration."""
    from homeassistant.helpers.aiohttp_client import async_get_clientsession
    from .f1atb_http import F1atbClient, RouterError, public_config
    try:
        result = public_config(await F1atbClient(async_get_clientsession(hass), msg["host"]).read_config())
    except RouterError as error:
        connection.send_error(msg["id"], str(error), "Cannot read F1ATB configuration.")
    else:
        connection.send_result(msg["id"], result)


@websocket_api.require_admin
@websocket_api.websocket_command({"type":"ehome_ems/save_energy_goal", "entry_id":str,
    "identifier":str, "revision":str, "values":dict, vol.Optional("remove",default=False):bool})
@callback
def websocket_save_energy_goal(hass, connection, msg):
    from .energy_goal import save_goal
    entry=hass.config_entries.async_get_entry(msg["entry_id"])
    if entry is None or entry.domain!=DOMAIN:
        connection.send_error(msg["id"],"not_ready","eHome EMS is not ready.")
        return
    try:
        save_goal(hass,entry,msg["identifier"],msg["values"],msg["revision"],msg["remove"])
    except (ValueError,TypeError,KeyError) as error:
        connection.send_error(msg["id"],str(error),"Energy goal settings rejected.")
    else:
        connection.send_result(msg["id"],{"saved":True})


@websocket_api.websocket_command({"type":"ehome_ems/energy_goals", "entry_id":str})
@callback
def websocket_energy_goals(hass, connection, msg):
    entry=hass.config_entries.async_get_entry(msg["entry_id"])
    if entry is None or entry.domain!=DOMAIN:
        connection.send_error(msg["id"],"not_ready","eHome EMS is not ready.")
        return
    runtime=hass.data.get(DOMAIN,{}).get("energy_goal_runtime",{}).get(entry.entry_id)
    connection.send_result(msg["id"],list(runtime.results.values()) if runtime else [])


@websocket_api.require_admin
@websocket_api.websocket_command({"type":"ehome_ems/rearm_energy_goal", "entry_id":str,
    "identifier":str,"revision":str})
@websocket_api.async_response
async def websocket_rearm_energy_goal(hass, connection, msg):
    entry=hass.config_entries.async_get_entry(msg["entry_id"])
    if entry is None or entry.domain!=DOMAIN or entry.modified_at.isoformat()!=msg["revision"]:
        connection.send_error(msg["id"],"conflict","Configuration changed.")
        return
    runtime=hass.data.get(DOMAIN,{}).get("energy_goal_runtime",{}).get(entry.entry_id)
    if not runtime or msg["identifier"] not in runtime.goals:
        connection.send_error(msg["id"],"not_ready","Energy goal is not ready.")
        return
    await runtime.async_rearm(msg["identifier"])
    connection.send_result(msg["id"],{"rearmed":True})


@websocket_api.websocket_command({"type":"ehome_ems/alerts", "entry_id":str})
@callback
def websocket_alerts(hass, connection, msg):
    entry=hass.config_entries.async_get_entry(msg["entry_id"])
    if entry is None or entry.domain != DOMAIN:
        connection.send_error(msg["id"],"not_ready","eHome EMS is not ready.")
        return
    runtime=hass.data.get(DOMAIN,{}).get("alerts_runtime",{}).get(entry.entry_id)
    result={"journal":list(runtime.journal) if runtime else []}
    if connection.user.is_admin:
        result["rules"]=(entry.options or entry.data).get("alerts",[])
        result["notify_services"]=["persistent_notification.create"]+["notify."+name for name in hass.services.async_services().get("notify",{})]
    connection.send_result(msg["id"],result)


@websocket_api.require_admin
@websocket_api.websocket_command({"type":"ehome_ems/save_alerts", "entry_id":str,"revision":str,"rules":vol.All(list,vol.Length(max=20))})
@callback
def websocket_save_alerts(hass,connection,msg):
    from .alerts import save_alerts
    entry=hass.config_entries.async_get_entry(msg["entry_id"])
    if entry is None or entry.domain != DOMAIN:
        connection.send_error(msg["id"],"not_ready","eHome EMS is not ready.")
        return
    try:save_alerts(hass,entry,msg["rules"],msg["revision"])
    except (ValueError,TypeError,KeyError) as error:
        connection.send_error(msg["id"],str(error),"Alert settings rejected.")
    else:connection.send_result(msg["id"],{"saved":True})
