"""Energy-by-deadline planning: pure functions, no equipment commands."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from math import isfinite, ceil
from zoneinfo import ZoneInfo
import re

FIELDS = {"mode", "goal_kwh", "deadline", "window_start", "window_end", "nominal_power_w",
          "margin_minutes", "energy_entity", "counter_confirmed", "router_usage", "max_age_seconds"}
WEATHER_FIELDS = {"weather_enabled", "weather_entity", "weather_window_start", "weather_window_end", "weather_fraction"}


def clock(value):
    if not isinstance(value, str) or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value):
        raise ValueError("invalid_goal_time")
    return value


def finite(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or not low <= value <= high:
        raise ValueError("invalid_goal_value")
    return float(value)


def validate_goal(mapping, identifier, values, states):
    usage = mapping.get("usages", {}).get(identifier, {})
    if usage.get("kind") not in ("water_heater", "solar_router"):
        raise ValueError("goal_target_missing")
    if not isinstance(values, dict) or not FIELDS.issubset(values) or set(values) - FIELDS - WEATHER_FIELDS or values.get("mode") not in ("observe", "auto"):
        raise ValueError("invalid_goal_settings")
    clean = {**values}
    clean.setdefault("weather_enabled", False)
    clean.setdefault("weather_entity", "")
    clean.setdefault("weather_window_start", "12:30")
    clean.setdefault("weather_window_end", "14:30")
    clean.setdefault("weather_fraction", 0.5)
    if type(clean["weather_enabled"]) is not bool:
        raise ValueError("invalid_weather_settings")
    clean["weather_window_start"] = clock(clean["weather_window_start"])
    clean["weather_window_end"] = clock(clean["weather_window_end"])
    if clean["weather_window_start"] >= clean["weather_window_end"]:
        raise ValueError("invalid_weather_window")
    clean["weather_fraction"] = finite(clean["weather_fraction"], .01, 1)
    if clean["weather_enabled"]:
        weather = clean["weather_entity"]
        if not isinstance(weather, str) or not weather.startswith("weather.") or states.get(weather) is None:
            raise ValueError("invalid_weather_source")
    for key in ("deadline", "window_start", "window_end"):
        clean[key] = clock(values[key])
    for key, low, high in (("goal_kwh", .01, 100), ("nominal_power_w", 100, 15000),
                           ("margin_minutes", 0, 120), ("max_age_seconds", 30, 3600)):
        clean[key] = finite(values[key], low, high)
    entity = values["energy_entity"]
    state = states.get(entity) if isinstance(entity, str) and entity.startswith("sensor.") else None
    if state is None or state.attributes.get("unit_of_measurement") not in ("Wh", "kWh"):
        raise ValueError("goal_energy_source")
    if values["counter_confirmed"] is not True:
        raise ValueError("goal_requires_cumulative_counter")
    # The declared lifetime counter is checked again at runtime for resets.
    if state.attributes.get("state_class") not in (None, "total", "total_increasing"):
        raise ValueError("goal_requires_cumulative_counter")
    if not isinstance(values["router_usage"], str):
        raise ValueError("invalid_goal_settings")
    router = mapping.get("usages", {}).get(values["router_usage"], {})
    if clean["mode"] == "auto" and not (router.get("kind") == "solar_router" and
            router.get("router_type") == "f1atb" and router.get("router_connection") == "http"
            and router.get("router_http_enabled")):
        raise ValueError("goal_requires_native_f1atb")
    for other, goal in mapping.get("energy_goals", {}).items():
        if other != identifier and goal.get("energy_entity") == entity:
            raise ValueError("goal_duplicate_counter")
        if other != identifier and clean["mode"] == goal.get("mode") == "auto" and goal.get("router_usage") == clean["router_usage"]:
            raise ValueError("goal_duplicate_router")
    return clean


def save_goal(hass, entry, identifier, values, revision, remove=False):
    if entry.modified_at.isoformat() != revision:
        raise ValueError("conflict")
    mapping = deepcopy(dict(entry.options or entry.data))
    goals = mapping.setdefault("energy_goals", {})
    if remove:
        goals.pop(identifier, None)
    else:
        if identifier not in goals and len(goals) >= 8:
            raise ValueError("too_many_goals")
        goals[identifier] = validate_goal(mapping, identifier, values, hass.states)
    hass.config_entries.async_update_entry(entry, options=mapping)


def wall(day, value, zone):
    """First occurrence in autumn; shift nonexistent spring times forward."""
    hour, minute = map(int, clock(value).split(":"))
    local = datetime(day.year, day.month, day.day, hour, minute, tzinfo=zone, fold=0)
    return local.astimezone(timezone.utc).astimezone(zone)


def cycle(goal, now, zone_name):
    zone = ZoneInfo(zone_name)
    local = now.astimezone(zone)
    end = wall(local.date(), goal["deadline"], zone)
    if end.astimezone(timezone.utc) <= now.astimezone(timezone.utc):
        end = wall(local.date() + timedelta(days=1), goal["deadline"], zone)
    start = wall(end.date() - timedelta(days=1), goal["deadline"], zone)
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


def allowed_windows(goal, now, end, zone_name):
    zone = ZoneInfo(zone_name)
    first = now.astimezone(zone).date() - timedelta(days=1)
    last = end.astimezone(zone).date()
    intervals = []
    while first <= last:
        start = wall(first, goal["window_start"], zone)
        finish = wall(first + timedelta(days=goal["window_end"] <= goal["window_start"]), goal["window_end"], zone)
        a, b = max(now, start.astimezone(timezone.utc)), min(end, finish.astimezone(timezone.utc))
        if b > a:
            intervals.append((a, b))
        first += timedelta(days=1)
    return intervals


def counter_kwh(raw, unit):
    factor = {"Wh": .001, "kWh": 1}.get(unit)
    try:
        result = float(raw) * factor if factor else None
    except (TypeError, ValueError, OverflowError):
        return None
    return result if result is not None and isfinite(result) and result >= 0 else None


def progress(baseline, previous, current):
    """Never turn an absent baseline, invalid counter or reset into zero energy."""
    if baseline is None or current is None:
        return None, "energy_unavailable"
    if current + 1e-9 < baseline or previous is not None and current + 1e-9 < previous:
        return None, "counter_reset"
    return max(0, current - baseline), "valid"


def evaluate(goal, now, zone_name, consumed_kwh, *, running=False):
    now = now.astimezone(timezone.utc)
    start, end = cycle(goal, now, zone_name)
    result = {"cycle_start": start.isoformat(), "deadline": end.isoformat(),
              "goal_kwh": goal["goal_kwh"], "consumed_kwh": consumed_kwh,
              "mode": goal["mode"], "should_heat": False}
    if consumed_kwh is None:
        return {**result, "reason": "energy_unavailable", "missing_kwh": None, "needed_minutes": None}
    missing = max(0, goal["goal_kwh"] - consumed_kwh)
    minutes = missing * 60000 / goal["nominal_power_w"]
    windows = allowed_windows(goal, now, end, zone_name)
    remaining = sum((b-a).total_seconds() for a, b in windows) / 60
    in_window = bool(windows and windows[0][0] == now)
    need_with_margin = minutes + goal["margin_minutes"]
    # Work backwards through the remaining allowed intervals, not calendar hours.
    latest, pending = None, need_with_margin
    for a, b in reversed(windows):
        duration = (b-a).total_seconds() / 60
        if pending <= duration:
            latest = b - timedelta(minutes=pending)
            break
        pending -= duration
    reached = missing <= 1e-6
    due = not reached and in_window and (running or remaining <= need_with_margin)
    reason = ("target_reached" if reached else "insufficient_window" if remaining < minutes else
              "complement_due" if due else "waiting_window" if not in_window else "solar_priority")
    return {**result, "reason": reason, "missing_kwh": round(missing, 4),
            "needed_minutes": ceil(minutes), "allowed_minutes": round(remaining, 1),
            "latest_start": latest.isoformat() if latest and not reached else None,
            "should_heat": due, "reachable": reached or remaining >= minutes}


def daytime_weather_target(goal_kwh, fraction, cycle_energy_kwh, forecast_condition, rain_probability=None):
    """Pure planning helper; does not authorize equipment commands.

    A wet/overcast forecast requests a minimum fraction of the *whole cycle*
    energy. Existing solar or grid heating counts toward that minimum.
    Missing forecast data must not be interpreted as bad weather.
    """
    wet = {"rainy", "pouring", "lightning-rainy", "snowy-rainy", "snowy"}
    dim = {"cloudy", "fog", "hail"}
    if cycle_energy_kwh is None or not 0 <= fraction <= 1:
        return None
    if not isinstance(forecast_condition, str):
        return None
    condition = forecast_condition.lower()
    adverse = condition in wet or condition in dim or (
        rain_probability is not None and 0 <= rain_probability <= 100 and rain_probability >= 60
    )
    if not adverse:
        return 0.0
    return round(max(0.0, goal_kwh * fraction - cycle_energy_kwh), 4)
