"""Reserve-aware energy budget. Never switches or configures physical batteries."""
from math import isfinite


def reserve_budget(config, soc):
    """Only energy above BOTH the hardware minimum and backup reserve is usable.

    SOC/capacity are estimates. Unknown or invalid data never authorizes spending.
    This budget does not implement electrical transfer or change a native BMS.
    """
    def number(value, low, high):
        if isinstance(value, bool):
            raise ValueError("invalid_battery_value")
        value = float(value)
        if not isfinite(value) or not low <= value <= high:
            raise ValueError("invalid_battery_value")
        return value
    try:
        reserve = number(config.get("backup_reserve_percent", 30), 0, 100)
        minimum = number(config.get("minimum_soc_percent", 10), 0, 100)
        floor = max(reserve, minimum)
        charge = number(soc, 0, 100)
    except (ValueError, TypeError, OverflowError):
        return {"quality": "unavailable", "usable_kwh": None, "can_discharge": False}
    usable_percent = max(0, charge - floor)
    try:
        capacity = number(config.get("capacity_kwh"), .001, 1000000)
        usable = round(capacity * usable_percent / 100, 4)
    except (ValueError, TypeError, OverflowError):
        usable = None
    return {"quality": "valid", "floor_percent": floor, "usable_percent": usable_percent,
            "usable_kwh": usable, "can_discharge": usable is not None and usable > 0}
