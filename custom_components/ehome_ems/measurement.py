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
