"""Read-only guided power mapping, shared by setup and options."""
import voluptuous as vol
from collections import Counter
from copy import deepcopy
from math import isfinite
from uuid import uuid4

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er, selector

from .const import DOMAIN, SOURCES, CONF_BATTERIES, BATTERY_SOURCES
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
        self._reviewing = False
        self._editing_battery = None

    def _errors(self, candidate):
        errors = {}
        registry = er.async_get(self.hass)
        items = list(source_items(candidate))
        counts = Counter(entity_id for _, entity_id, _ in items if entity_id)
        for key, entity_id, role in items:
            if not entity_id:
                continue
            state = self.hass.states.get(entity_id)
            registered = registry.async_get(entity_id)
            units = ("%",) if role == "soc" else ("Wh", "kWh") if role == "remaining_energy" else ("W", "kW")
            if counts[entity_id] > 1:
                errors[key] = "duplicate_source"
            elif registered and registered.platform == DOMAIN:
                errors[key] = "recursive_source"
            elif state is None:
                errors[key] = "missing_source"
            elif state.attributes.get("unit_of_measurement") not in units:
                errors[key] = "unsupported_unit"
            elif role == "remaining_energy":
                battery = candidate[CONF_BATTERIES][key.split(".")[1]]
                reading = normalize_battery(
                    state.state, state.attributes.get("unit_of_measurement"), role,
                    capacity_kwh=battery.get("capacity_kwh"),
                    state_class=state.attributes.get("state_class"),
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
        return await self._power_step("home", "batteries", user_input)

    async def async_step_batteries(self, user_input=None):
        """Add any number of independent batteries or skip storage."""
        menu = ["add_battery"]
        if self._draft[CONF_BATTERIES]:
            menu += ["edit_battery", "remove_battery"]
        menu += ["review"]
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

    def _preview(self):
        rows = []
        for key, entity_id, role in source_items(self._draft):
            if not entity_id:
                continue
            state = self.hass.states.get(entity_id)
            is_battery = key.startswith("batteries.")
            normalize = normalize_battery if is_battery else normalize_power
            battery = self._draft[CONF_BATTERIES][key.split(".")[1]] if is_battery else None
            details = {
                "capacity_kwh": battery.get("capacity_kwh"),
                "state_class": state.attributes.get("state_class") if state else None,
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
        return "\n".join(rows) or "—"

    async def async_step_review(self, user_input=None):
        self._reviewing = True
        return self.async_show_menu(
            step_id="review",
            menu_options=["confirm", "grid", "solar", "home", "batteries"],
            description_placeholders={"summary": self._preview()},
        )

    async def async_step_confirm(self, user_input=None):
        if user_input and user_input.get("back_to_review"):
            return await self.async_step_review()
        errors = self._errors(self._draft)
        if not any(entity_id for _, entity_id, _ in source_items(self._draft)):
            errors = {"base": "select_source"}
        elif errors:
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
