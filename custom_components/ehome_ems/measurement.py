"""Power normalization independent of Home Assistant.

Only a signed grid reading and export accept negative values. Export may
be reported with either sign; the mapped export is always a magnitude.
No unavailable or invalid reading is converted to zero.
"""
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class PowerReading:
    """Normalized value and an explicit quality reason."""

    value: float | None
    quality: str


def normalize_power(raw: object, unit: str | None, role: str) -> PowerReading:
    """Convert W/kW to W without guessing unsupported units or directions."""
    if raw is None or raw in ("unknown", "unavailable"):
        return PowerReading(None, "unavailable")
    factor = {"W": 1, "kW": 1000}.get(unit)
    if factor is None:
        return PowerReading(None, "unsupported_unit")
    try:
        value = float(raw) * factor
    except (ValueError, TypeError, OverflowError):
        return PowerReading(None, "invalid_value")
    if not isfinite(value):
        return PowerReading(None, "invalid_value")
    if role == "grid_export":
        value = abs(value)
    elif role != "grid_power" and value < 0:
        return PowerReading(None, "unexpected_direction")
    return PowerReading(round(value, 2), "valid")


def normalize_battery(raw: object, unit: str | None, role: str) -> PowerReading:
    """Normalize separate positive power, SOC %, or measured stored energy kWh."""
    if role in ("charge_power", "discharge_power"):
        return normalize_power(raw, unit, role)
    if raw is None or raw in ("unknown", "unavailable"):
        return PowerReading(None, "unavailable")
    factors = {"%": 1} if role == "soc" else {"Wh": 0.001, "kWh": 1}
    factor = factors.get(unit)
    if factor is None:
        return PowerReading(None, "unsupported_unit")
    try:
        value = float(raw) * factor
    except (ValueError, TypeError, OverflowError):
        return PowerReading(None, "invalid_value")
    if not isfinite(value):
        return PowerReading(None, "invalid_value")
    if value < 0 or (role == "soc" and value > 100):
        return PowerReading(None, "out_of_range")
    return PowerReading(round(value, 3), "valid")
