"""HA-owned polling and manual commands for native F1ATB connections."""
import asyncio
from datetime import timedelta
import logging

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .f1atb_http import F1atbClient, RouterError, actions, bounded_int, config_token, base_url

_LOGGER = logging.getLogger(__name__)


class RouterCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry, host):
        super().__init__(hass, _LOGGER, name="eHome EMS F1ATB", config_entry=entry,
                         update_interval=timedelta(seconds=15))
        self.client = F1atbClient(async_get_clientsession(hass), host)
        # Serialize reads/writes across all EMS entries targeting the same host.
        locks = hass.data.setdefault(DOMAIN, {}).setdefault("router_http_locks", {})
        self.lock = locks.setdefault(self.client.base.lower(), asyncio.Lock())

    async def _async_update_data(self):
        async with self.lock:
            try:
                return await self.client.read()
            except RouterError as err:
                raise UpdateFailed(str(err)) from err


async def async_setup_routers(hass, entry):
    mapping = entry.options or entry.data
    coordinators, by_host = {}, {}
    for identifier, usage in mapping.get("usages", {}).items():
        if usage.get("kind") != "solar_router" or usage.get("router_type") != "f1atb" or usage.get("router_connection", "mqtt") != "http":
            continue
        host = base_url(usage.get("router_url"))
        if host not in by_host:
            coordinator = by_host[host] = RouterCoordinator(hass, entry, host)
            # An offline router does not prevent the EMS entry from loading.
            await coordinator.async_refresh()
        coordinators[identifier] = by_host[host]
    cache = hass.data.setdefault(DOMAIN, {}).setdefault("router_http", {})
    cache[entry.entry_id] = coordinators
    def unload():
        cache.pop(entry.entry_id, None)
    entry.async_on_unload(unload)
    return coordinators


async def async_http_command(hass, entry, identifier, revision, action, values):
    usage = (entry.options or entry.data).get("usages", {}).get(identifier, {})
    if (usage.get("kind") != "solar_router" or usage.get("router_type") != "f1atb"
            or usage.get("router_connection") != "http" or not usage.get("router_http_enabled")):
        raise RouterError("router_not_enabled")
    runtime = hass.data.get(DOMAIN, {}).get("energy_goal_runtime", {}).get(entry.entry_id)
    if runtime:
        await runtime.async_manual_override(identifier)
    coordinator = hass.data.get(DOMAIN, {}).get("router_http", {}).get(entry.entry_id, {}).get(identifier)
    if not coordinator:
        raise RouterError("router_unavailable")
    if coordinator.lock.locked():
        raise RouterError("command_in_progress")
    async with coordinator.lock:
        # Recheck after acquiring the lock and after network I/O.
        def check_revision():
            if entry.modified_at.isoformat() != revision:
                raise RouterError("conflict")
        check_revision()
        config = await coordinator.client.read_config()
        check_revision()
        index = bounded_int(usage.get("router_action", 0), 0, len(actions(config)) - 1)
        if not isinstance(values, dict):
            raise RouterError("invalid_router_parameters")
        target = actions(config)[index]
        if action == "http_parameters":
            if values.get("config_token") != config_token(config):
                raise RouterError("router_config_conflict")
            expected = await coordinator.client.patch(config, index, values)
            try:
                actual = await coordinator.client.read_config()
                confirmed = actions(actual)[index] == actions(expected)[index]
            except RouterError:
                confirmed = False
        else:
            if action == "boost_hour" and set(values) == {"config_token"}:
                if values["config_token"] != config_token(config):
                    raise RouterError("router_config_conflict")
                if target.get("Actif") not in range(1,6):
                    raise RouterError("router_action_inactive")
                if target.get("ForceOuvre") != 100:
                    expected=await coordinator.client.patch(config,index,{"config_token":values["config_token"],"forced_opening":100})
                    actual=await coordinator.client.read_config()
                    if actions(actual)[index] != actions(expected)[index]:
                        raise RouterError("router_opening_unconfirmed")
                    check_revision()
                minutes=60
            elif action in ("force_on", "force_off") and set(values) == {"minutes"}:
                minutes = bounded_int(values["minutes"], 1, 1440) * (1 if action == "force_on" else -1)
            elif action == "release" and not values:
                minutes = 0
            else:
                raise RouterError("invalid_router_parameters")
            if target.get("Actif") not in range(1, 6):
                raise RouterError("router_action_inactive")
            await coordinator.client.force(index, minutes)
            try:
                actual = await coordinator.client.read()
                remaining = actual.get("live_actions", {}).get(index, {}).get("force_minutes")
                confirmed = (remaining is not None and ((minutes == 0 and remaining == 0)
                    or (minutes * remaining > 0 and abs(minutes - remaining) <= 1)))
            except RouterError:
                confirmed = False
    # Refresh never sends another write. Failure does not imply the write was undone.
    await coordinator.async_refresh()
    return {"sent": True, "confirmed_by_router": confirmed, "persistent": action in ("http_parameters","boost_hour")}
