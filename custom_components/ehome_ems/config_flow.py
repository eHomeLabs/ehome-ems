"""Read-only guided power mapping, shared by setup and options."""
import voluptuous as vol
from html import escape
from collections import Counter
from copy import deepcopy
from math import isfinite
from uuid import uuid4

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er, selector

from .const import DOMAIN, SOURCES, CONF_BATTERIES, BATTERY_SOURCES, HOME_MODE, HOME_SETTINGS
from .home_balance import home_sources, calculate_home
from .const import CONF_USAGES, USAGE_SOURCES, DAILY_SOURCES
from .usage import normalize_usage
from .measurement import normalize_power, normalize_battery

GROUPS = {
    "grid": ("grid_power", "grid_import", "grid_export"),
    "solar": ("solar_power",),
    "home": ("home_power",),
}


def positive_capacity(value):
    """Reject NaN/infinite and non-positive configured capacities."""
    value = vol.Coerce(float)(value)
    if not isfinite(value) or value <= 0:
        raise vol.Invalid("invalid_capacity")
    return value


def battery_schema(existing):
    """Separate charge/discharge sources; no vendor-specific sign guesses."""
    schema = {
        vol.Required("name", default=existing.get("name", "Battery")): vol.All(str, vol.Length(min=1, max=80)),
        vol.Required("role", default=existing.get("role", "backup")): selector.SelectSelector(
            selector.SelectSelectorConfig(options=["backup", "active"], translation_key="battery_role")
        ),
        vol.Required("coupling", default=existing.get("coupling", "ac")): selector.SelectSelector(
            selector.SelectSelectorConfig(options=["ac", "dc"], translation_key="battery_coupling")
        ),
        vol.Optional("capacity_kwh", description={"suggested_value": existing["capacity_kwh"]}
                     if existing.get("capacity_kwh") else None): vol.All(
                         vol.Coerce(float), vol.Range(min=0.001)
                     ),
    }
    schema[vol.Optional("remaining_energy_is_stock", default=existing.get("remaining_energy_is_stock", False))] = bool
    for key in BATTERY_SOURCES:
        device_class = "battery" if key == "soc" else "energy" if key == "remaining_energy" else "power"
        schema[vol.Optional(key, description={"suggested_value": existing[key]}
                            if existing.get(key) else None)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor", device_class=device_class)
        )
    return vol.Schema(schema)


def source_items(candidate):
    """Yield every configured source once with its stable configuration path."""
    for key in SOURCES:
        yield key, candidate.get(key), key
    for battery_id, battery in candidate.get(CONF_BATTERIES, {}).items():
        for key in BATTERY_SOURCES:
            yield f"batteries.{battery_id}.{key}", battery.get(key), key
    for key, entity in candidate.get("daily", {}).items():
        if key in DAILY_SOURCES:
            yield f"daily.{key}", entity, "usage_energy"
    for usage_id, usage in candidate.get(CONF_USAGES, {}).items():
        for key in USAGE_SOURCES:
            yield f"usages.{usage_id}.{key}", usage.get(key), f"usage_{key}"


def usage_schema(existing):
    schema = {
        vol.Required("name", default=existing.get("name", "Usage")): vol.All(str, vol.Length(min=1, max=80)),
        vol.Required("kind", default=existing.get("kind", "solar_router")): selector.SelectSelector(
            selector.SelectSelectorConfig(options=["solar_router", "ev_charger", "other", "appliance"],
                                          translation_key="usage_kind")),
        vol.Optional("icon", default=existing.get("icon", "auto")): selector.SelectSelector(selector.SelectSelectorConfig(options=["auto","mdi:power-plug","mdi:washing-machine","mdi:dishwasher","mdi:tumble-dryer","mdi:fridge","mdi:radiator","mdi:air-conditioner","mdi:pool","mdi:coffee-maker","mdi:printer-3d-nozzle","mdi:lightbulb","mdi:television","mdi:desktop-classic","mdi:water-boiler","mdi:ev-station"])),
        vol.Required("energy_period", default=existing.get("energy_period", "total")): selector.SelectSelector(
            selector.SelectSelectorConfig(options=["today", "session", "total"], translation_key="usage_energy_period")),
        vol.Required("included_in_home", default=existing.get("included_in_home", False)): bool,
    }
    for key in USAGE_SOURCES:
        config = {"domain": ["sensor", "binary_sensor", "switch", "select"]} if key == "status" else {
            "domain": "sensor", "device_class": "power" if key == "power" else "temperature" if key == "temperature" else "energy"
        }
        schema[vol.Optional(key, description={"suggested_value": existing[key]} if existing.get(key) else None)] = (
            selector.EntitySelector(selector.EntitySelectorConfig(**config))
        )
    return vol.Schema(schema)


def source_schema(keys, existing):
    """Suggest saved values without making cleared fields mandatory."""
    power = selector.EntitySelector(
        selector.EntitySelectorConfig(domain="sensor", device_class="power")
    )
    return vol.Schema({
        vol.Optional(
            key, description={"suggested_value": existing[key]} if existing.get(key) else None
        ): power
        for key in keys
    })


class PowerWizard:
    """Keep draft changes in memory until explicit confirmation."""

    def _start(self, existing=None):
        self._draft = {key: (existing or {}).get(key) for key in SOURCES}
        self._draft[CONF_BATTERIES] = deepcopy((existing or {}).get(CONF_BATTERIES, {}))
        self._draft[CONF_USAGES] = deepcopy((existing or {}).get(CONF_USAGES, {}))
        self._draft["daily"] = deepcopy((existing or {}).get("daily", {}))
        self._draft["tariff_eur_kwh"] = (existing or {}).get("tariff_eur_kwh")
        self._draft["weather_entity"] = (existing or {}).get("weather_entity")
        if "simulation" in (existing or {}):
            self._draft["simulation"] = deepcopy(existing["simulation"])
        for key in HOME_SETTINGS:
            if key in (existing or {}):
                self._draft[key] = existing[key]
        self._reviewing = False
        self._editing_battery = None
        self._editing_usage = None

    def _errors(self, candidate):
        errors = {}
        registry = er.async_get(self.hass)
        items = list(source_items(candidate))
        counts = Counter(entity_id for key, entity_id, _ in items if entity_id and not key.startswith("daily."))
        for key, entity_id, role in items:
            if not entity_id:
                continue
            state = self.hass.states.get(entity_id)
            registered = registry.async_get(entity_id)
            units = ("°C", "°F") if role == "usage_temperature" else ("%",) if role == "soc" else ("Wh", "kWh") if role in ("remaining_energy", "usage_energy") else ("W", "kW")
            if not key.startswith("daily.") and counts[entity_id] > 1:
                errors[key] = "duplicate_source"
            elif registered and registered.platform == DOMAIN:
                errors[key] = "recursive_source"
            elif state is None:
                errors[key] = "missing_source"
            elif role != "usage_status" and not (
                state.attributes.get("unit_of_measurement") in units or
                role in ("remaining_energy", "usage_energy") and str(state.attributes.get("unit_of_measurement", "")).strip().lower() in ("wh", "kwh")
            ):
                errors[key] = "unsupported_unit"
            elif role == "remaining_energy":
                battery = candidate[CONF_BATTERIES][key.split(".")[1]]
                reading = normalize_battery(
                    state.state, state.attributes.get("unit_of_measurement"), role,
                    capacity_kwh=battery.get("capacity_kwh"),
                    state_class=state.attributes.get("state_class"),
                    stock_confirmed=battery.get("remaining_energy_is_stock", False),
                )
                if reading.quality in ("cumulative_energy", "exceeds_capacity"):
                    errors[key] = reading.quality
        return errors

    async def _power_step(self, step, next_step, user_input):
        keys = GROUPS[step]
        errors = {}
        if user_input is not None:
            candidate = {**self._draft, **{key: user_input.get(key) for key in keys}}
            all_errors = self._errors(candidate)
            errors = {key: reason for key, reason in all_errors.items() if key in keys}
            if not errors:
                self._draft = candidate
                if self._reviewing:
                    return await self.async_step_review()
                return await getattr(self, f"async_step_{next_step}")()
        return self.async_show_form(
            step_id=step,
            data_schema=source_schema(keys, user_input if user_input is not None else self._draft),
            errors=errors,
        )

    async def async_step_grid(self, user_input=None):
        return await self._power_step("grid", "solar", user_input)

    async def async_step_solar(self, user_input=None):
        return await self._power_step("solar", "home", user_input)

    async def async_step_home(self, user_input=None):
        existing = self._draft
        errors = {}
        if user_input is not None:
            mode = user_input.get(HOME_MODE, "existing")
            candidate = {**self._draft, HOME_MODE: mode,
                         "home_power": user_input.get("home_power") if mode == "existing" else None}
            for key in HOME_SETTINGS[1:4]:
                candidate[key] = user_input.get(key, False)
            candidate["home_freshness_policy"] = user_input.get("home_freshness_policy", "warn")
            candidate["home_grid_mode"] = user_input.get("home_grid_mode", "auto")
            candidate["home_max_age_seconds"] = user_input.get("home_max_age_seconds", 300)
            errors = {key: reason for key, reason in self._errors(candidate).items()
                      if key == "home_power"}
            if mode == "calculated" and not candidate["home_boundary_confirmed"]:
                errors["home_boundary_confirmed"] = "boundary_unconfirmed"
            if not errors:
                self._draft = candidate
                return await (self.async_step_review() if self._reviewing else self.async_step_batteries())
            existing = candidate
        schema = source_schema(GROUPS["home"], existing).schema
        schema[vol.Required(HOME_MODE, default=existing.get(HOME_MODE, "existing"))] = selector.SelectSelector(
            selector.SelectSelectorConfig(options=["existing", "calculated"], translation_key="home_power_mode")
        )
        defaults = {
            "home_has_solar": bool(existing.get("solar_power")),
            "home_has_storage": any(b["role"] == "active" for b in existing.get(CONF_BATTERIES, {}).values()),
            "home_boundary_confirmed": False,
        }
        for key, default in defaults.items():
            schema[vol.Optional(key, default=existing.get(key, default))] = bool
        schema[vol.Optional("home_freshness_policy", default=existing.get("home_freshness_policy", "warn"))] = selector.SelectSelector(
            selector.SelectSelectorConfig(options=["warn", "strict"], translation_key="home_freshness_policy")
        )
        schema[vol.Optional("home_grid_mode", default=existing.get("home_grid_mode", "auto"))] = selector.SelectSelector(
            selector.SelectSelectorConfig(options=["auto", "signed", "separate"], translation_key="home_grid_mode")
        )
        schema[vol.Optional("home_max_age_seconds", default=existing.get("home_max_age_seconds", 300))] = vol.All(
            vol.Coerce(int), vol.Any(0, vol.Range(min=30, max=3600))
        )
        return self.async_show_form(step_id="home", data_schema=vol.Schema(schema), errors=errors)

    async def async_step_batteries(self, user_input=None):
        """Add any number of independent batteries or skip storage."""
        menu = ["add_battery"]
        if self._draft[CONF_BATTERIES]:
            menu += ["edit_battery", "remove_battery"]
        menu += ["usages"]
        return self.async_show_menu(
            step_id="batteries", menu_options=menu,
            description_placeholders={"summary": self._preview()},
        )

    async def async_step_add_battery(self, user_input=None):
        if user_input is None:
            self._editing_battery = uuid4().hex
        return await self._battery_form("add_battery", user_input)

    async def _battery_form(self, step, user_input):
        battery_id = self._editing_battery
        existing = self._draft[CONF_BATTERIES].get(battery_id, {})
        errors = {}
        if user_input is not None:
            # Validate scalar fields even when called outside the UI.
            try:
                battery = battery_schema(existing)(user_input)
                if "capacity_kwh" in battery:
                    battery["capacity_kwh"] = positive_capacity(battery["capacity_kwh"])
            except vol.Invalid:
                errors = {"base": "invalid_battery"}
            else:
                candidate = deepcopy(self._draft)
                candidate[CONF_BATTERIES][battery_id] = battery
                prefix = f"batteries.{battery_id}."
                errors = {path.removeprefix(prefix): reason
                          for path, reason in self._errors(candidate).items()
                          if path.startswith(prefix)}
                if not any(battery.get(key) for key in BATTERY_SOURCES):
                    errors["base"] = "select_source"
                if not errors:
                    self._draft = candidate
                    return await self.async_step_batteries()
        return self.async_show_form(
            step_id=step, data_schema=battery_schema(user_input if user_input is not None else existing),
            errors=errors,
        )

    def _battery_choice_schema(self):
        return vol.Schema({vol.Required("battery_id"): selector.SelectSelector(
            selector.SelectSelectorConfig(options=[
                {"value": key, "label": battery["name"]}
                for key, battery in self._draft[CONF_BATTERIES].items()
            ])
        )})

    async def async_step_edit_battery(self, user_input=None):
        if not self._draft[CONF_BATTERIES]:
            return await self.async_step_batteries()
        if user_input is not None:
            battery_id = user_input.get("battery_id")
            if battery_id in self._draft[CONF_BATTERIES]:
                self._editing_battery = battery_id
                return await self.async_step_battery_details()
        return self.async_show_form(step_id="edit_battery", data_schema=self._battery_choice_schema())

    async def async_step_battery_details(self, user_input=None):
        return await self._battery_form("battery_details", user_input)

    async def async_step_remove_battery(self, user_input=None):
        if not self._draft[CONF_BATTERIES]:
            return await self.async_step_batteries()
        if user_input is not None:
            battery_id = user_input.get("battery_id")
            if battery_id in self._draft[CONF_BATTERIES]:
                del self._draft[CONF_BATTERIES][battery_id]
                return await self.async_step_batteries()
        return self.async_show_form(step_id="remove_battery", data_schema=self._battery_choice_schema())

    async def async_step_usages(self, user_input=None):
        menu = ["add_usage"]
        if self._draft[CONF_USAGES]:
            menu += ["edit_usage", "remove_usage"]
        menu += ["appliances", "daily", "review"]
        return self.async_show_menu(step_id="usages", menu_options=menu,
                                    description_placeholders={"summary": self._preview()})

    async def async_step_appliances(self, user_input=None):
        menu = ["add_appliance"]
        if any(u.get("kind") == "appliance" for u in self._draft[CONF_USAGES].values()):
            menu += ["edit_appliance", "remove_appliance"]
        menu += ["daily", "review"]
        return self.async_show_menu(step_id="appliances", menu_options=menu)

    async def async_step_add_appliance(self, user_input=None):
        if user_input is None:
            self._editing_usage = uuid4().hex
        return await self._usage_form("add_appliance", user_input)

    async def async_step_edit_appliance(self, user_input=None):
        return await self._choose_appliance("edit_appliance", user_input)

    async def async_step_remove_appliance(self, user_input=None):
        return await self._choose_appliance("remove_appliance", user_input)

    async def _choose_appliance(self, step, user_input):
        choices = {k: u for k, u in self._draft[CONF_USAGES].items() if u.get("kind") == "appliance"}
        if user_input and user_input.get("usage_id") in choices:
            self._editing_usage = user_input["usage_id"]
            if step == "remove_appliance":
                del self._draft[CONF_USAGES][self._editing_usage]
                return await self.async_step_appliances()
            return await self.async_step_appliance_details()
        return self.async_show_form(step_id=step, data_schema=vol.Schema({vol.Required("usage_id"):
            selector.SelectSelector(selector.SelectSelectorConfig(options=[
                {"value": k, "label": u["name"]} for k, u in choices.items()]))}))

    async def async_step_appliance_details(self, user_input=None):
        return await self._usage_form("appliance_details", user_input)

    async def async_step_daily(self, user_input=None):
        errors = {}
        existing = {**self._draft.get("daily", {}), "tariff_eur_kwh": self._draft.get("tariff_eur_kwh"), "weather_entity": self._draft.get("weather_entity")}
        if user_input is not None:
            candidate = deepcopy(self._draft)
            candidate["daily"] = {k: user_input[k] for k in DAILY_SOURCES if user_input.get(k)}
            tariff = user_input.get("tariff_eur_kwh")
            if tariff is not None and (isinstance(tariff, bool) or not isinstance(tariff, (int, float)) or not isfinite(tariff) or not 0 <= tariff <= 10):
                errors["tariff_eur_kwh"] = "invalid_tariff"
            candidate["tariff_eur_kwh"] = tariff
            weather = user_input.get("weather_entity")
            if weather and (not isinstance(weather,str) or not weather.startswith("weather.") or not self.hass.states.get(weather)):
                errors["weather_entity"] = "invalid_weather"
            candidate["weather_entity"] = weather
            errors.update({k.removeprefix("daily."): v for k, v in self._errors(candidate).items() if k.startswith("daily.")})
            if not errors:
                self._draft = candidate
                return await self.async_step_review()
            existing = user_input
        schema = {vol.Optional(k, description={"suggested_value": existing[k]} if existing.get(k) else None):
                  selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", device_class="energy")) for k in DAILY_SOURCES}
        schema[vol.Optional("tariff_eur_kwh", description={"suggested_value": existing["tariff_eur_kwh"]} if existing.get("tariff_eur_kwh") is not None else None)] = vol.All(vol.Coerce(float), vol.Range(min=0, max=10))
        schema[vol.Optional("weather_entity", description={"suggested_value": existing["weather_entity"]} if existing.get("weather_entity") else None)] = selector.EntitySelector(selector.EntitySelectorConfig(domain="weather"))
        return self.async_show_form(step_id="daily", data_schema=vol.Schema(schema), errors=errors)

    async def async_step_add_usage(self, user_input=None):
        if user_input is None:
            self._editing_usage = uuid4().hex
        return await self._usage_form("add_usage", user_input)

    async def _usage_form(self, step, user_input):
        usage_id = self._editing_usage
        existing = self._draft[CONF_USAGES].get(usage_id, {})
        appliance = step in ("add_appliance", "appliance_details")
        if appliance:
            existing = {**existing, "kind": "appliance"}
            if user_input is not None:
                user_input = {**user_input, "kind": "appliance"}
        errors = {}
        if user_input is not None:
            try:
                usage = usage_schema(existing)(user_input)
            except vol.Invalid:
                errors = {"base": "invalid_usage"}
            else:
                candidate = deepcopy(self._draft)
                candidate[CONF_USAGES][usage_id] = usage
                prefix = f"usages.{usage_id}."
                errors = {path.removeprefix(prefix): reason for path, reason in self._errors(candidate).items()
                          if path.startswith(prefix)}
                if not any(usage.get(key) for key in USAGE_SOURCES):
                    errors["base"] = "select_source"
                if not usage.get("included_in_home"):
                    errors["included_in_home"] = "outside_home"
                if not errors:
                    self._draft = candidate
                    return await (self.async_step_appliances() if appliance else self.async_step_usages())
        schema = usage_schema(user_input if user_input is not None else existing).schema
        if appliance:
            schema = {k: v for k, v in schema.items() if k.schema not in ("kind", "temperature")}
        return self.async_show_form(step_id=step, data_schema=vol.Schema(schema), errors=errors)

    def _usage_choice_schema(self):
        return vol.Schema({vol.Required("usage_id"): selector.SelectSelector(selector.SelectSelectorConfig(
            options=[{"value": key, "label": usage["name"]} for key, usage in self._draft[CONF_USAGES].items()]
        ))})

    async def async_step_edit_usage(self, user_input=None):
        if not self._draft[CONF_USAGES]:
            return await self.async_step_usages()
        if user_input and user_input.get("usage_id") in self._draft[CONF_USAGES]:
            self._editing_usage = user_input["usage_id"]
            return await self.async_step_usage_details()
        return self.async_show_form(step_id="edit_usage", data_schema=self._usage_choice_schema())

    async def async_step_usage_details(self, user_input=None):
        return await self._usage_form("usage_details", user_input)

    async def async_step_remove_usage(self, user_input=None):
        if not self._draft[CONF_USAGES]:
            return await self.async_step_usages()
        if user_input and user_input.get("usage_id") in self._draft[CONF_USAGES]:
            del self._draft[CONF_USAGES][user_input["usage_id"]]
            return await self.async_step_usages()
        return self.async_show_form(step_id="remove_usage", data_schema=self._usage_choice_schema())

    def _preview(self):
        rows = []
        for key, entity_id, role in source_items(self._draft):
            if not entity_id:
                continue
            state = self.hass.states.get(entity_id)
            if key.startswith("daily."):
                reading = normalize_usage(state.state if state else None, state.attributes.get("unit_of_measurement") if state else None, "energy")
                rows.append(f"- Today / {key}: {entity_id} (Wh/kWh, daily source declared) [{reading.quality}]")
                continue
            if key.startswith("usages."):
                usage = self._draft[CONF_USAGES][key.split(".")[1]]
                field = role.removeprefix("usage_")
                reading = normalize_usage(state.state if state else None,
                                          state.attributes.get("unit_of_measurement") if state else None, field)
                unit = "W" if field == "power" else "kWh" if field == "energy" else "°C" if field == "temperature" else ""
                rows.append(f"- {usage['name']} / {field}: {reading.value if reading.value is not None else '—'} {unit} [{reading.quality}]")
                continue
            is_battery = key.startswith("batteries.")
            normalize = normalize_battery if is_battery else normalize_power
            battery = self._draft[CONF_BATTERIES][key.split(".")[1]] if is_battery else None
            details = {
                "capacity_kwh": battery.get("capacity_kwh"),
                "state_class": state.attributes.get("state_class") if state else None,
                "stock_confirmed": battery.get("remaining_energy_is_stock", False),
            } if battery else {}
            reading = normalize(
                state.state if state else None,
                state.attributes.get("unit_of_measurement") if state else None,
                role,
                **details,
            )
            unit = "%" if role == "soc" else "kWh" if role == "remaining_energy" else "W"
            value = f"{reading.value:g} {unit}" if reading.value is not None else "—"
            if is_battery:
                battery = self._draft[CONF_BATTERIES][key.split(".")[1]]
                key = f"{battery['name']} ({battery['role']}, {battery['coupling']}) / {role}"
            rows.append(f"- {key}: {entity_id} → {value} [{reading.quality}]")
        if self._draft.get(HOME_MODE) == "calculated":
            inputs = {}
            sources, _ = home_sources(self._draft)
            for _, source, _ in sources:
                state = self.hass.states.get(source)
                inputs[source] = (state.state, state.attributes.get("unit_of_measurement")) if state else (None, None)
            reading = calculate_home(self._draft, inputs)
            value = f"{reading.value:g} W" if reading.value is not None else "—"
            rows.append(f"- Maison / Home (calcul EMS): {value} [{reading.quality}]")
        colored = []
        for row in rows:
            text = escape(row)
            if text.endswith("]") and " [" in text:
                prefix, quality = text.rsplit(" [", 1)
                color = "#51d593" if quality == "valid]" else "#ff6565"
                text = f'{prefix} <font color="{color}">[{quality}</font>'
            colored.append(text)
        return "\n".join(colored) or "—"

    async def async_step_review(self, user_input=None):
        self._reviewing = True
        return self.async_show_menu(
            step_id="review",
            menu_options=["grid", "solar", "home", "batteries", "usages", "appliances", "daily", "confirm"],
            description_placeholders={"summary": self._preview()},
        )

    async def async_step_confirm(self, user_input=None):
        if user_input and user_input.get("back_to_review"):
            return await self.async_step_review()
        errors = self._errors(self._draft)
        if self._draft.get(HOME_MODE) == "calculated":
            _, reason = home_sources(self._draft)
            if reason:
                errors = {"base": reason}
        if not any(entity_id for _, entity_id, _ in source_items(self._draft)):
            errors = {"base": "select_source"}
        elif errors and "base" not in errors:
            errors = {"base": "sources_changed"}
        if user_input is not None and not errors:
            return self.async_create_entry(title=self._entry_title, data=deepcopy(self._draft))
        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({vol.Optional("back_to_review", default=False): bool}),
            errors=errors,
            description_placeholders={"summary": self._preview()},
        )


class EhomeEmsConfigFlow(PowerWizard, config_entries.ConfigFlow, domain=DOMAIN):
    """Configure a single installation without changing any equipment."""

    VERSION = 1
    _entry_title = "eHome EMS"

    async def async_step_user(self, user_input=None):
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        self._start()
        return await self.async_step_grid(user_input)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return EhomeEmsOptionsFlow()


class EhomeEmsOptionsFlow(PowerWizard, config_entries.OptionsFlow):
    """Reuse V0.1 flat keys and the existing entry reload listener."""

    _entry_title = ""

    async def async_step_init(self, user_input=None):
        existing = self.config_entry.options or self.config_entry.data
        self._start(existing)
        return await self.async_step_grid(user_input)
