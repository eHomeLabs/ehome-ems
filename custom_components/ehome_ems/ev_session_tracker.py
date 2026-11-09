"""State machine for EV charging sessions.

Independent of Home Assistant. Persist the result of snapshot() in HA storage.
Energy is sampled from a monotonically increasing meter in kWh; no midnight reset.
"""
from datetime import datetime
from math import isfinite

from .ev_session_math import energy_delta, interval_cost


class EVSessionTracker:
    def __init__(self, snapshot=None, *, threshold_w=100, idle_seconds=180):
        self.data = dict(snapshot or {})
        self.threshold_w = threshold_w
        self.idle_seconds = idle_seconds

    def snapshot(self):
        return dict(self.data)

    def observe(self, when, power_w, meter_kwh, tariff):
        """Update session from one sample and return a serializable snapshot.

        Power >= threshold starts a session. Idle for idle_seconds ends it.
        Unavailable samples are ignored, not treated as zero. A counter reset
        marks cost/energy incomplete rather than silently inventing consumption.
        """
        if not isinstance(when, datetime) or when.tzinfo is None:
            raise ValueError("timestamp_requires_timezone")
        if isinstance(power_w, bool) or not isinstance(power_w, (int, float)) or not isfinite(power_w):
            return self.snapshot()
        if isinstance(meter_kwh, bool) or not isinstance(meter_kwh, (int, float)) or not isfinite(meter_kwh) or meter_kwh < 0:
            return self.snapshot()
        stamp = when.isoformat()
        active = power_w >= self.threshold_w
        d = self.data
        if not d.get("active"):
            if not active:
                return self.snapshot()
            d.update(active=True, started=stamp, last_at=stamp, last_meter=meter_kwh,
                     energy_kwh=0.0, cost_eur=0.0, peak_w=float(power_w),
                     incomplete=False, idle_since=None)
            return self.snapshot()
        previous_at = datetime.fromisoformat(d["last_at"])
        if when <= previous_at:
            return self.snapshot()
        delta = energy_delta(d["last_meter"], meter_kwh)
        if delta is None:
            d["incomplete"] = True
        elif not d["incomplete"]:
            try:
                cost = interval_cost(previous_at, when, delta, **tariff)
            except (ValueError, TypeError):
                d["incomplete"] = True
            else:
                d["energy_kwh"] += delta
                d["cost_eur"] += cost
        d["last_meter"] = meter_kwh
        d["last_at"] = stamp
        if active:
            d["peak_w"] = max(d["peak_w"], float(power_w))
            d["idle_since"] = None
        else:
            if not d.get("idle_since"):
                d["idle_since"] = stamp
            elif (when - datetime.fromisoformat(d["idle_since"])).total_seconds() >= self.idle_seconds:
                d["last_session"] = {
                    "started": d["started"], "ended": stamp,
                    "energy_kwh": None if d["incomplete"] else d["energy_kwh"],
                    "cost_eur": None if d["incomplete"] else d["cost_eur"],
                    "peak_w": d["peak_w"],
                    "incomplete": d["incomplete"],
                }
                d["active"] = False
        return self.snapshot()
