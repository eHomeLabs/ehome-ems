"""Bounded, hypothetical watt allocation. No live-budget inference or commands."""
from copy import deepcopy

CONF_SIMULATION = "simulation"
MAX_WATTS = 1_000_000
MAX_TARGETS = 100


def candidates(mapping):
    result = []
    for identifier, battery in mapping.get("batteries", {}).items():
        if battery.get("role") == "active" and battery.get("coupling") == "ac":
            result.append({"id": f"battery:{identifier}", "name": battery["name"], "kind": "battery"})
    for identifier, usage in mapping.get("usages", {}).items():
        if usage.get("kind") == "appliance":
            continue
        result.append({"id": f"usage:{identifier}", "name": usage["name"], "kind": usage.get("kind", "other")})
    return result


def watts(value):
    if type(value) is not int or not 0 <= value <= MAX_WATTS:
        raise ValueError("invalid_watts")
    return value


def validate_targets(mapping, targets):
    allowed = {item["id"] for item in candidates(mapping)}
    if not isinstance(targets, list) or len(targets) > MAX_TARGETS or len(targets) != len(allowed):
        raise ValueError("targets_changed")
    seen, clean = set(), []
    for target in targets:
        if not isinstance(target, dict) or set(target) != {"id", "enabled", "min_w", "max_w"}:
            raise ValueError("invalid_target")
        identifier = target["id"]
        if not isinstance(identifier, str) or identifier not in allowed or identifier in seen:
            raise ValueError("targets_changed")
        seen.add(identifier)
        minimum, maximum = watts(target["min_w"]), watts(target["max_w"])
        if type(target["enabled"]) is not bool or minimum > maximum or (target["enabled"] and maximum == 0):
            raise ValueError("invalid_limits")
        clean.append({"id": identifier, "enabled": target["enabled"], "min_w": minimum, "max_w": maximum})
    return clean


def plan(mapping):
    """Follow saved order, drop removed devices, append new ones disabled."""
    available = {item["id"]: item for item in candidates(mapping)}
    settings = mapping.get(CONF_SIMULATION, {})
    saved = settings.get("targets", []) if isinstance(settings, dict) and settings.get("schema_version") == 1 else []
    if not isinstance(saved, list):
        saved = []
    ordered, seen = [], set()
    for item in saved:
        identifier = item.get("id") if isinstance(item, dict) else None
        if not isinstance(identifier, str) or identifier not in available or identifier in seen:
            continue
        try:
            minimum, maximum = watts(item.get("min_w")), watts(item.get("max_w"))
            enabled = item.get("enabled") is True and maximum > 0 and minimum <= maximum
        except ValueError:
            minimum = maximum = 0
            enabled = False
        if minimum > maximum:
            minimum = maximum = 0
        ordered.append({**available[identifier], "enabled": enabled, "min_w": minimum, "max_w": maximum})
        seen.add(identifier)
    for identifier, item in available.items():
        if identifier not in seen:
            ordered.append({**item, "enabled": False, "min_w": 0, "max_w": 0})
    return {"schema_version": 1, "targets": ordered, "mode": "manual_scenario"}


def allocate(mapping, budget_w):
    """Allocate one explicit integer budget once, by saved priority and limits."""
    remaining = watts(budget_w)
    rows = []
    targets = plan(mapping)["targets"]
    if len(targets) > MAX_TARGETS:
        raise ValueError("too_many_targets")
    for item in targets:
        allocated = 0
        if not item["enabled"]:
            reason = "disabled"
        elif remaining == 0:
            reason = "budget_exhausted"
        elif remaining < item["min_w"]:
            reason = "below_minimum"
        else:
            allocated = min(item["max_w"], remaining)
            remaining -= allocated
            reason = "ceiling_reached" if allocated == item["max_w"] else "allocated"
        rows.append({**item, "allocated_w": allocated, "reason": reason})
    return {"mode": "manual_scenario", "budget_w": budget_w, "allocated_w": budget_w - remaining,
            "remaining_w": remaining, "targets": rows, "commands_sent": False}


def save_plan(hass, entry, targets, revision):
    if entry.modified_at.isoformat() != revision:
        raise ValueError("conflict")
    mapping = deepcopy(dict(entry.options or entry.data))
    clean = validate_targets(mapping, targets)
    mapping[CONF_SIMULATION] = {"schema_version": 1, "targets": clean}
    hass.config_entries.async_update_entry(entry, options=mapping)
