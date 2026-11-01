"""Read-only usage readings; no actuator or EMS control code."""
from math import isfinite
from .measurement import PowerReading, normalize_power


def normalize_usage(raw, unit, role):
    if role == "power":
        return normalize_power(raw, unit, "home_power")
    if raw is None or raw in ("unknown", "unavailable"):
        return PowerReading(None, "unavailable")
    if role == "status":
        return PowerReading(str(raw), "valid")
    if role == "temperature":
        try:
            value = float(raw)
            if unit == "°F":
                value = (value - 32) * 5 / 9
            elif unit != "°C":
                return PowerReading(None, "unsupported_unit")
            return PowerReading(round(value, 1), "valid") if isfinite(value) and -100 <= value <= 200 else PowerReading(None, "invalid_value")
        except (ValueError, TypeError, OverflowError):
            return PowerReading(None, "invalid_value")
    factor = {"Wh": 0.001, "kWh": 1}.get(unit)
    if factor is None:
        return PowerReading(None, "unsupported_unit")
    try:
        value = float(raw) * factor
    except (ValueError, TypeError, OverflowError):
        return PowerReading(None, "invalid_value")
    if not isfinite(value) or value < 0:
        return PowerReading(None, "invalid_value")
    return PowerReading(round(value, 3), "valid")
