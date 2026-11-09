"""EV charging session accounting primitives.

A session is not a calendar day.  All prices are EUR/kWh.
This module has no Home Assistant imports so its arithmetic can be unit tested.
"""
from datetime import datetime, timedelta
from math import isfinite


def energy_delta(previous, current, *, reset_is_session=False):
    """Return energy increment in kWh, or None for an invalid counter reset.

    Callers must first convert their sensor readings to kWh.
    """
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not isfinite(v) or v < 0
           for v in (previous, current)):
        return None
    if current >= previous:
        return current - previous
    return current if reset_is_session else None


def rate_at(when, *, mode, flat=None, peak=None, offpeak=None,
            offpeak_start="22:00", offpeak_end="06:00"):
    """Resolve rate in the installation's *local* time (aware datetime).

    The caller supplies local timezone and handles daylight-saving conversion.
    The half-open off-peak interval can cross midnight.
    """
    if when.tzinfo is None:
        raise ValueError("timezone_required")
    if mode == "flat":
        rate = flat
    elif mode == "hp_hc":
        def minutes(value):
            hour, minute = map(int, value.split(":"))
            if not 0 <= hour < 24 or not 0 <= minute < 60:
                raise ValueError("invalid_time")
            return hour * 60 + minute
        start, end = minutes(offpeak_start), minutes(offpeak_end)
        if start == end:
            raise ValueError("empty_offpeak_interval")
        now = when.hour * 60 + when.minute
        hc = start <= now < end if start < end else (now >= start or now < end)
        rate = offpeak if hc else peak
    else:
        raise ValueError("invalid_tariff_mode")
    if isinstance(rate, bool) or not isinstance(rate, (int, float)) or not isfinite(rate) or not 0 <= rate <= 10:
        raise ValueError("invalid_tariff")
    return float(rate)


def interval_cost(start, end, energy_kwh, *, mode, flat=None, peak=None, offpeak=None,
                  offpeak_start="22:00", offpeak_end="06:00"):
    """Estimate cost for a *uniform-energy* interval by splitting local minutes.

    Exact HP/HC billing needs energy samples at each tariff transition.
    Use this only for short intervals bounded by successive meter readings.
    """
    if start.tzinfo is None or end.tzinfo is None or end <= start:
        raise ValueError("invalid_interval")
    if isinstance(energy_kwh, bool) or not isinstance(energy_kwh, (int, float)) or not isfinite(energy_kwh) or energy_kwh < 0:
        raise ValueError("invalid_energy")
    if mode == "flat":
        return energy_kwh * rate_at(start, mode=mode, flat=flat)
    elapsed = (end - start).total_seconds()
    cursor, cost = start, 0.0
    while cursor < end:
        following = min(end, cursor + timedelta(minutes=1))
        midpoint = cursor + (following - cursor) / 2
        rate = rate_at(midpoint, mode=mode, peak=peak, offpeak=offpeak,
                       offpeak_start=offpeak_start, offpeak_end=offpeak_end)
        cost += energy_kwh * ((following - cursor).total_seconds() / elapsed) * rate
        cursor = following
    return cost


def session_peak(samples, threshold_w=100):
    """Maximum valid charging power, excluding idle and negative noise."""
    valid = [float(value) for value in samples
             if not isinstance(value, bool) and isinstance(value, (int, float))
             and isfinite(value) and value >= threshold_w]
    return max(valid, default=None)
