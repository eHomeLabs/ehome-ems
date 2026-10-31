"""Read-only guided power mapping, shared by setup and options."""
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er, selector

from .const import DOMAIN, SOURCES
from .measurement import normalize_power

GROUPS = {
    "grid": ("grid_power", "grid_import", "grid_export"),
    "solar": ("solar_power",),
    "home": ("home_power",),
}


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
        self._reviewing = False

    def _errors(self, candidate):
        errors = {}
        registry = er.async_get(self.hass)
        seen = set()
        for key, entity_id in candidate.items():
            if not entity_id:
                continue
            state = self.hass.states.get(entity_id)
            registered = registry.async_get(entity_id)
            if entity_id in seen:
                errors[key] = "duplicate_source"
            elif registered and registered.platform == DOMAIN:
                errors[key] = "recursive_source"
            elif state is None:
                errors[key] = "missing_source"
            elif state.attributes.get("unit_of_measurement") not in ("W", "kW"):
                errors[key] = "unsupported_unit"
            seen.add(entity_id)
        return errors

    async def _power_step(self, step, next_step, user_input):
        keys = GROUPS[step]
        errors = {}
        if user_input is not None:
            candidate = {**self._draft, **{key: user_input.get(key) for key in keys}}
            all_errors = self._errors(candidate)
            errors = {key: reason for key, reason in all_errors.items() if key in keys}
            if all_errors and not errors:
                errors = {"base": "sources_changed"}
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
        return await self._power_step("home", "review", user_input)

    def _preview(self):
        rows = []
        for key, entity_id in self._draft.items():
            if not entity_id:
                continue
            state = self.hass.states.get(entity_id)
            reading = normalize_power(
                state.state if state else None,
                state.attributes.get("unit_of_measurement") if state else None,
                key,
            )
            value = f"{reading.value:g} W" if reading.value is not None else "—"
            rows.append(f"- {key}: {entity_id} → {value} [{reading.quality}]")
        return "\n".join(rows) or "—"

    async def async_step_review(self, user_input=None):
        self._reviewing = True
        return self.async_show_menu(
            step_id="review",
            menu_options=["confirm", "grid", "solar", "home"],
            description_placeholders={"summary": self._preview()},
        )

    async def async_step_confirm(self, user_input=None):
        if user_input and user_input.get("back_to_review"):
            return await self.async_step_review()
        errors = self._errors(self._draft)
        if not any(self._draft.values()):
            errors = {"base": "select_source"}
        elif errors:
            errors = {"base": "sources_changed"}
        if user_input is not None and not errors:
            return self.async_create_entry(title=self._entry_title, data=dict(self._draft))
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
