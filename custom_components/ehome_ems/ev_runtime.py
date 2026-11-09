"""Persistent EV charging sessions driven by Home Assistant state changes."""
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from datetime import timedelta
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .ev_session_tracker import EVSessionTracker


class EVRuntime:
    def __init__(self, hass, entry):
        self.hass, self.entry = hass, entry
        self.store = Store(hass, 1, f"{DOMAIN}_ev_{entry.entry_id}")
        self.trackers = {}
        self.unsubscribe = None
        self.unsubscribe_timer = None

    async def async_start(self):
        saved = await self.store.async_load() or {}
        usages = (self.entry.options or self.entry.data).get("usages", {})
        for key, cfg in usages.items():
            if cfg.get("kind") == "ev_charger" and cfg.get("power") and cfg.get("energy"):
                self.trackers[key] = EVSessionTracker(saved.get(key))
        sources = {cfg[field] for key, cfg in usages.items() if key in self.trackers
                   for field in ("power", "energy")}
        if sources:
            self.unsubscribe = async_track_state_change_event(self.hass, list(sources), self._changed)
            self.unsubscribe_timer = async_track_time_interval(self.hass, self._tick, timedelta(seconds=60))
            for key in self.trackers:
                self._sample(key)

    @callback
    def _tick(self, now):
        for key in self.trackers:
            self._sample(key)

    @callback
    def _changed(self, event):
        usages = (self.entry.options or self.entry.data).get("usages", {})
        for key in self.trackers:
            cfg = usages[key]
            if event.data["entity_id"] in (cfg["power"], cfg["energy"]):
                self._sample(key)

    @callback
    def _sample(self, key):
        cfg = (self.entry.options or self.entry.data)["usages"][key]
        power = self.hass.states.get(cfg["power"])
        energy = self.hass.states.get(cfg["energy"])
        if not power or not energy:
            return
        try:
            p, e = float(power.state), float(energy.state)
            if power.attributes.get("unit_of_measurement") == "kW":
                p *= 1000
            unit = str(energy.attributes.get("unit_of_measurement", "")).lower()
            if unit == "wh":
                e /= 1000
            elif unit != "kwh":
                return
            tariff = {"mode": cfg.get("ev_tariff_mode", "flat"),
                      "flat": cfg.get("ev_tariff_flat"),
                      "peak": cfg.get("ev_tariff_hp"),
                      "offpeak": cfg.get("ev_tariff_hc"),
                      "offpeak_start": cfg.get("ev_hc_start", "22:00"),
                      "offpeak_end": cfg.get("ev_hc_end", "06:00")}
            self.trackers[key].observe(dt_util.as_local(dt_util.utcnow()), p, e, tariff)
            self.store.async_delay_save(self._save, 30)
        except (ValueError, TypeError, OverflowError):
            return

    @callback
    def _save(self):
        return {key: tracker.snapshot() for key, tracker in self.trackers.items()}

    async def async_stop(self):
        if self.unsubscribe:
            self.unsubscribe()
            self.unsubscribe = None
        if self.unsubscribe_timer:
            self.unsubscribe_timer()
            self.unsubscribe_timer = None
        await self.store.async_save(self._save())


async def async_setup_ev(hass, entry):
    runtime = EVRuntime(hass, entry)
    await runtime.async_start()
    hass.data.setdefault(DOMAIN, {}).setdefault("ev_runtime", {})[entry.entry_id] = runtime
