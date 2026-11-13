"""Opt-in energy deadline scheduler. Observation and scenario allocation never write.

Automatic control v1 uses native F1ATB HTTP only, with 2-minute leases.
The router remains responsible for its thermostat, protection and regulation.
"""
import asyncio
from datetime import datetime, timedelta, timezone, time
from zoneinfo import ZoneInfo
from functools import partial

from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store

from .const import DOMAIN
from .energy_goal import cycle, counter_kwh, progress, evaluate, allowed_windows, daytime_weather_target, wall
from .f1atb_http import RouterError

LEASE_MINUTES = 2


async def history_baseline(hass, entity_id, start, end):
    """Read cumulative energy at the cycle boundary and detect observed resets."""
    try:
        from homeassistant.components.recorder import get_instance, history
        rows = await get_instance(hass).async_add_executor_job(partial(
            history.get_significant_states, hass, start, end, [entity_id],
            include_start_time_state=True, significant_changes_only=False,
            minimal_response=False, no_attributes=False))
        rows = rows.get(entity_id, [])
    except Exception:
        return None, None, "history_unavailable"
    if not rows or rows[0].last_updated > start:
        return None, None, "baseline_missing"
    baseline = counter_kwh(rows[0].state, rows[0].attributes.get("unit_of_measurement"))
    if baseline is None:
        return None, None, "baseline_missing"
    previous = baseline
    for row in rows[1:]:
        value = counter_kwh(row.state, row.attributes.get("unit_of_measurement"))
        if value is not None:
            if value + 1e-9 < previous:
                return None, None, "counter_reset"
            previous = value
    return baseline, previous, "valid"


class EnergyGoalRuntime:
    def __init__(self, hass, entry, *, history_reader=None, now=None):
        self.hass, self.entry = hass, entry
        self.mapping = entry.options or entry.data
        self.revision = entry.modified_at.isoformat()
        self.goals = self.mapping.get("energy_goals", {})
        self.history_reader = history_reader or history_baseline
        self.now = now or (lambda: datetime.now(timezone.utc))
        self.zone = hass.config.time_zone
        self.store = Store(hass, 1, f"{DOMAIN}_energy_goals_{entry.entry_id}")
        self.faults, self.records, self.owned, self.results = {}, {}, {}, {}
        self.day_records = {}
        self.weather_cache = {}
        self.manual_full = set()
        self.lock, self.stopped, self.unsubscribers = asyncio.Lock(), False, []

    async def async_start(self):
        data = await self.store.async_load()
        if isinstance(data, dict) and isinstance(data.get("faults"), dict):
            self.faults = {key: value for key, value in data["faults"].items() if key in self.goals and isinstance(value, dict)}
        self.unsubscribers = [
            async_track_time_interval(self.hass, self.async_tick, timedelta(seconds=30)),
            self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, self.async_stop),
        ]
        await self.async_tick()

    async def persist(self):
        await self.store.async_save({"faults": self.faults})

    def coordinator(self, goal):
        return self.hass.data.get(DOMAIN, {}).get("router_http", {}).get(self.entry.entry_id, {}).get(goal["router_usage"])

    async def fault(self, identifier, cycle_id, reason):
        self.faults[identifier] = {"cycle": cycle_id, "reason": reason}
        await self.persist()

    async def async_rearm(self, identifier):
        async with self.lock:
            self.faults.pop(identifier, None)
            await self.persist()
        # A separate scheduled tick evaluates the permission and actual state.

    async def async_full_override(self, identifier):
        """Manual full target, bounded by the existing energy goal and deadline."""
        if identifier not in self.goals or self.goals[identifier].get("mode") != "auto":
            raise ValueError("goal_not_automatic")
        async with self.lock:
            goal = self.goals[identifier]
            result = await self.reading(identifier, goal, self.now())
            if result["quality"] != "valid" or result.get("warning") or result.get("missing_kwh") is None:
                raise ValueError("energy_counter_not_ready")
            if result["missing_kwh"] <= 0:
                raise ValueError("target_reached")
            self.faults.pop(identifier, None)
            await self.persist()
            self.manual_full.add(identifier)

    def manual_goal(self, identifier, goal, now):
        if identifier not in self.manual_full:
            return goal
        local = now.astimezone(ZoneInfo(self.zone))
        return {**goal, "window_start": local.strftime("%H:%M"),
                "window_end": goal["deadline"], "_manual_full": True}

    async def async_manual_override(self, router_identifier):
        """Any EMS manual router command takes priority for the rest of this cycle."""
        async with self.lock:
            for identifier, goal in self.goals.items():
                if goal.get("router_usage") == router_identifier and goal.get("mode") == "auto":
                    self.owned.pop(identifier, None)
                    self.manual_full.discard(identifier)
                    await self.fault(identifier, cycle(goal, self.now(), self.zone)[1].isoformat(), "manual_override")

    async def async_stop(self, _event=None):
        if self.stopped:
            return
        self.stopped = True
        for unsubscribe in self.unsubscribers:
            unsubscribe()
        self.unsubscribers = []
        try:
            async with asyncio.timeout(15):
                async with self.lock:
                    for identifier in list(self.owned):
                        await self.release(identifier)
        except (TimeoutError, RouterError):
            # No retry on shutdown. An outstanding router lease expires itself.
            pass
        claims = self.hass.data.get(DOMAIN, {}).get("goal_claims", {})
        for key, owner in list(claims.items()):
            if owner[0] == self.entry.entry_id:
                del claims[key]
        cache = self.hass.data.get(DOMAIN, {}).get("energy_goal_runtime", {})
        if cache.get(self.entry.entry_id) is self:
            cache.pop(self.entry.entry_id, None)

    async def release(self, identifier):
        owned = self.owned.pop(identifier, None)
        if not owned:
            return
        coordinator = owned["coordinator"]
        async with coordinator.lock:
            live = await coordinator.client.read()
            remaining = live.get("live_actions", {}).get(owned["index"], {}).get("force_minutes")
            # Never cancel a different manual or external long override.
            if remaining == 0:
                return
            if not (remaining is not None and 0 < remaining <= LEASE_MINUTES and self.now() <= owned["expires"]):
                await self.fault(identifier, owned["cycle"], "manual_override")
                return
            await self.fault(identifier, owned["cycle"], "command_unconfirmed")
            await coordinator.client.force(owned["index"], 0)
            state = await coordinator.client.read()
            if state.get("live_actions", {}).get(owned["index"], {}).get("force_minutes") == 0:
                self.faults.pop(identifier, None)
                await self.persist()

    async def daily_reading(self, goal, now, current):
        local=now.astimezone(ZoneInfo(self.zone))
        start=datetime.combine(local.date(),time.min,tzinfo=local.tzinfo).astimezone(timezone.utc)
        key=(goal["energy_entity"],start.isoformat())
        record=self.day_records.get(key)
        if record is None or now >= record["retry_at"]:
            baseline,previous,quality=await self.history_reader(self.hass,goal["energy_entity"],start,now)
            record=self.day_records[key]={"baseline":baseline,"previous":previous,"quality":quality,"retry_at":now+timedelta(minutes=1)}
            self.day_records={k:v for k,v in self.day_records.items() if k[1]==start.isoformat()}
        value,quality=progress(record["baseline"],record["previous"],current)
        if record["quality"]!="valid":return None,record["quality"]
        if quality=="counter_reset":record["quality"]=quality
        if current is not None:record["previous"]=current
        return value,quality

    async def weather_goal(self, identifier, goal, now):
        """Use hourly HA forecast; missing/stale forecast never triggers heating."""
        if not goal.get("weather_enabled") or goal.get("mode") != "auto":
            return goal
        zone = ZoneInfo(self.zone)
        local = now.astimezone(zone)
        midday_start = wall(local.date(), goal["weather_window_start"], zone).astimezone(timezone.utc)
        midday_end = wall(local.date(), goal["weather_window_end"], zone).astimezone(timezone.utc)
        start, deadline = cycle(goal, now, self.zone)
        if not (start <= midday_start < midday_end <= deadline and now < midday_end):
            return goal
        entity = goal.get("weather_entity")
        cached = self.weather_cache.get(entity)
        if cached is None or now >= cached["expires"]:
            try:
                response = await self.hass.services.async_call(
                    "weather", "get_forecasts", {"entity_id": entity, "type": "hourly"},
                    blocking=True, return_response=True)
                forecast = response.get(entity, {}).get("forecast", [])
                if not isinstance(forecast, list):
                    forecast = []
            except Exception:
                forecast = []
            cached = {"forecast": forecast, "expires": now + timedelta(minutes=30)}
            self.weather_cache[entity] = cached
        forecast = cached["forecast"]
        selected = None
        for item in forecast:
            try:
                stamp = datetime.fromisoformat(item["datetime"].replace("Z", "+00:00"))
                if stamp.tzinfo is None:
                    continue
                if stamp <= midday_start and (midday_start - stamp) <= timedelta(hours=1):
                    selected = item
                    break
            except (KeyError, TypeError, ValueError, AttributeError):
                continue
        if selected is None:
            return goal
        # Forecast decision uses only predicted weather, never current condition.
        rain = selected.get("precipitation_probability")
        try:
            rain = float(rain) if rain is not None else None
        except (ValueError, TypeError):
            rain = None
        condition = selected.get("condition")
        if daytime_weather_target(goal["goal_kwh"], goal["weather_fraction"], 0, condition, rain) in (None, 0):
            return goal
        return {**goal, "goal_kwh": goal["goal_kwh"] * goal["weather_fraction"],
                "window_start": goal["weather_window_start"], "window_end": goal["weather_window_end"],
                "_weather_stage": True}

    async def reading(self, identifier, goal, now):
        start, end = cycle(goal, now, self.zone)
        key = (end.isoformat(), goal["energy_entity"])
        record = self.records.get(identifier)
        if record is None or record["key"] != key:
            baseline, previous, quality = await self.history_reader(self.hass, goal["energy_entity"], start, now)
            record = self.records[identifier] = {"key": key, "baseline": baseline, "previous": previous,
                                                  "quality": quality, "retry_at": now + timedelta(minutes=1)}
        elif record["quality"] in ("history_unavailable", "baseline_missing") and now >= record["retry_at"]:
            self.records.pop(identifier)
            return await self.reading(identifier, goal, now)
        now = self.now()
        if cycle(goal, now, self.zone)[1].isoformat() != key[0]:
            return await self.reading(identifier, goal, now)
        state = self.hass.states.get(goal["energy_entity"])
        current = counter_kwh(state.state, state.attributes.get("unit_of_measurement")) if state else None
        consumed, quality = progress(record["baseline"], record["previous"], current)
        if record["quality"] != "valid":
            consumed, quality = None, record["quality"]
        if quality == "counter_reset":
            record["quality"] = quality
        if current is not None:
            record["previous"] = current
        result = evaluate(goal, now, self.zone, consumed, running=identifier in self.owned)
        if goal.get("_manual_full") and result.get("missing_kwh") is not None:
            if result["missing_kwh"] > 0:
                result.update(should_heat=True, reason="manual_full_due")
            else:
                self.manual_full.discard(identifier)
        result.update(id=identifier, name=self.mapping.get("usages", {}).get(identifier, {}).get("name", identifier), quality=quality)
        daily,daily_quality=await self.daily_reading(goal,now,current)
        result.update(day_energy_kwh=daily,day_quality=daily_quality,energy_entity=goal["energy_entity"],router_usage=goal["router_usage"])
        reported = getattr(state, "last_reported", None) if state else None
        if quality != "valid":
            result.update(reason=quality, should_heat=False)
        elif reported is None or (now - reported).total_seconds() > goal["max_age_seconds"] or reported > now + timedelta(seconds=5):
            # A cumulative energy sensor may legitimately remain unchanged while
            # the heater is idle. A fresh, independent power reading can confirm
            # the idle state, but cannot replace the energy counter during heating.
            usage = self.mapping.get("usages", {}).get(identifier, {})
            power_entity = usage.get("power")
            power_state = self.hass.states.get(power_entity) if power_entity else None
            power_reported = getattr(power_state, "last_reported", None) if power_state else None
            try:
                power_w = float(power_state.state) * (1000 if power_state.attributes.get("unit_of_measurement") == "kW" else 1)
                power_valid = power_state.attributes.get("unit_of_measurement") in ("W", "kW") and 0 <= power_w < 100
            except (TypeError, ValueError, AttributeError, OverflowError):
                power_valid = False
            power_fresh = (power_reported is not None and
                           timedelta(0) <= now - power_reported <= timedelta(seconds=goal["max_age_seconds"]))
            if power_valid and power_fresh and identifier not in self.owned:
                # Keep scheduling visible, but never issue a heater command on
                # stale energy data: a fresh cumulative counter is required.
                result.update(reason="stale_energy_idle_confirmed", warning="stale_energy", should_heat=False)
            else:
                result.update(reason="target_reached" if result["reason"]=="target_reached" else "stale_energy",
                              warning="stale_energy", should_heat=False)
        return result

    async def control(self, identifier, goal, result, now):
        cycle_id = result["deadline"]
        previous_fault = self.faults.get(identifier, {})
        if previous_fault.get("cycle") == cycle_id:
            result.update(reason=previous_fault["reason"], should_heat=False)
        if goal["mode"] != "auto" or not result["should_heat"]:
            await self.release(identifier)
            return
        if self.entry.modified_at.isoformat() != self.revision:
            result.update(reason="configuration_changed", should_heat=False)
            await self.release(identifier)
            return
        coordinator = self.coordinator(goal)
        router = self.mapping.get("usages", {}).get(goal["router_usage"], {})
        index = router.get("router_action", 0)
        if not coordinator or not router.get("router_http_enabled"):
            result.update(reason="router_unavailable", should_heat=False)
            await self.release(identifier)
            return
        target = (coordinator.client.base.lower(), index)
        claims = self.hass.data.setdefault(DOMAIN, {}).setdefault("goal_claims", {})
        owner = (self.entry.entry_id, identifier)
        if claims.get(target, owner) != owner:
            result.update(reason="router_already_managed", should_heat=False)
            return
        claims[target] = owner
        owned = self.owned.get(identifier)
        if owned and (now - owned["sent"]).total_seconds() < 60:
            return
        async with coordinator.lock:
            live = await coordinator.client.read()
            if self.stopped or self.entry.modified_at.isoformat() != self.revision:
                result.update(reason="configuration_changed", should_heat=False)
                return
            latest = await self.reading(identifier, goal, self.now())
            result.update(latest)
            if not latest["should_heat"] or latest["deadline"] != cycle_id:
                return
            now = self.now()
            windows = allowed_windows(goal, now, cycle(goal, now, self.zone)[1], self.zone)
            seconds_left = (windows[0][1] - now).total_seconds() if windows and windows[0][0] == now else 0
            lease_minutes = min(LEASE_MINUTES, int((seconds_left - 15) // 60))
            if lease_minutes < 1:
                result.update(reason="lease_too_short", should_heat=False)
                return
            action = next((a for a in live.get("actions", []) if a["index"] == index), {})
            remaining = live.get("live_actions", {}).get(index, {}).get("force_minutes")
            if action.get("mode") not in range(1, 6) or action.get("forced_opening") != 100:
                result.update(reason="router_requires_full_opening", should_heat=False)
                return
            if remaining is None or (not owned and remaining != 0) or (owned and not 0 < remaining <= LEASE_MINUTES):
                self.owned.pop(identifier, None)
                await self.fault(identifier, cycle_id, "manual_override")
                result.update(reason="manual_override", should_heat=False)
                return
            # Persist intent before sending: a crash or lost response cannot cause
            # repeated automatic writes after a reload in this cycle.
            await self.fault(identifier, cycle_id, "command_unconfirmed")
            if self.stopped or self.entry.modified_at.isoformat() != self.revision:
                self.faults.pop(identifier, None)
                await self.persist()
                result.update(reason="configuration_changed", should_heat=False)
                return
            # Saving the intent may itself be delayed by I/O. Recheck both the
            # measured target and the allowed deadline immediately before send.
            latest = await self.reading(identifier, goal, self.now())
            result.update(latest)
            if not latest["should_heat"] or latest["deadline"] != cycle_id:
                self.faults.pop(identifier, None)
                await self.persist()
                return
            now = self.now()
            windows = allowed_windows(goal, now, cycle(goal, now, self.zone)[1], self.zone)
            seconds_left = (windows[0][1] - now).total_seconds() if windows and windows[0][0] == now else 0
            lease_minutes = min(LEASE_MINUTES, latest["needed_minutes"], int((seconds_left - 15) // 60))
            if lease_minutes < 1:
                self.faults.pop(identifier, None)
                await self.persist()
                result.update(reason="lease_too_short", should_heat=False)
                return
            await coordinator.client.force(index, lease_minutes)
            readback = await coordinator.client.read()
            if readback.get("live_actions", {}).get(index, {}).get("force_minutes") not in range(1, lease_minutes + 1):
                self.owned.pop(identifier, None)
                result.update(reason="command_unconfirmed", should_heat=False)
                return
            self.owned[identifier] = {"coordinator": coordinator, "index": index, "cycle": cycle_id,
                                      "sent": now, "expires": now + timedelta(minutes=lease_minutes)}
            self.faults.pop(identifier, None)
            await self.persist()

    async def async_tick(self, _now=None):
        if self.stopped or self.lock.locked():
            return
        async with self.lock:
            for identifier, goal in self.goals.items():
                if self.stopped:
                    break
                now = self.now()
                try:
                    if identifier in self.owned and self.owned[identifier]["cycle"] != cycle(goal, now, self.zone)[1].isoformat():
                        await self.release(identifier)
                    stage_goal = self.manual_goal(identifier, goal, now) if identifier in self.manual_full else await self.weather_goal(identifier, goal, now)
                    result = await self.reading(identifier, stage_goal, now)
                    result["weather_stage"] = bool(stage_goal.get("_weather_stage"))
                    result["manual_full"] = bool(stage_goal.get("_manual_full"))
                    await self.control(identifier, stage_goal, result, now)
                    if not result["should_heat"] and identifier in self.owned:
                        await self.release(identifier)
                    result["running"] = identifier in self.owned
                    result["updated_at"] = self.now().isoformat()
                    self.results[identifier] = result
                except Exception:
                    # Keep the timer alive without leaking router configuration.
                    cycle_id = cycle(goal, now, self.zone)[1].isoformat()
                    try:
                        await self.release(identifier)
                    except (RouterError, TimeoutError):
                        self.owned.pop(identifier, None)
                    if goal["mode"] == "auto":
                        await self.fault(identifier, cycle_id, "runtime_unavailable")
                    self.results[identifier] = {"id": identifier, "name": self.mapping.get("usages", {}).get(identifier, {}).get("name", identifier),
                        "mode": goal["mode"], "deadline": cycle_id, "reason": "runtime_unavailable",
                        "running": False, "updated_at": now.isoformat()}


async def async_setup_goals(hass, entry):
    if not (entry.options or entry.data).get("energy_goals"):
        return
    runtime = EnergyGoalRuntime(hass, entry)
    hass.data.setdefault(DOMAIN, {}).setdefault("energy_goal_runtime", {})[entry.entry_id] = runtime
    entry.async_on_unload(runtime.async_stop)
    await runtime.async_start()
