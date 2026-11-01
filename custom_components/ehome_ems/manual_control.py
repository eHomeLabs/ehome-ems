"""Explicit manual commands only; never called by observation or simulation."""
from .const import DOMAIN

CONTROL_DOMAINS = {"switch", "input_boolean", "light", "fan"}


async def async_control(hass, entry, identifier, desired_on, expected_state, revision, context):
    if entry.modified_at.isoformat() != revision:
        raise ValueError("conflict")
    if type(desired_on) is not bool or expected_state not in ("on", "off"):
        raise ValueError("invalid_command")
    usage = (entry.options or entry.data).get("usages", {}).get(identifier, {})
    target = usage.get("control_entity")
    if not usage.get("control_enabled") or not isinstance(target, str) or target.split(".")[0] not in CONTROL_DOMAINS:
        raise ValueError("control_not_enabled")
    state = hass.states.get(target)
    if state is None or state.state not in ("on", "off"):
        raise ValueError("target_unavailable")
    if state.state != expected_state:
        raise ValueError("state_changed")
    domain, service = target.split(".")[0], "turn_on" if desired_on else "turn_off"
    if not hass.services.has_service(domain, service):
        raise ValueError("unsupported_action")
    busy = hass.data.setdefault(DOMAIN, {}).setdefault("manual_control_busy", set())
    if target in busy:
        raise ValueError("command_in_progress")
    busy.add(target)
    try:
        await hass.services.async_call(domain, service, {"entity_id": target}, blocking=True, context=context)
    finally:
        busy.discard(target)
    return {"command_sent": True, "entity_id": target, "requested_state": "on" if desired_on else "off"}
