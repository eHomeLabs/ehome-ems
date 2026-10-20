"""Guided manual energy mapping for eHome EMS v0.1."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from .const import DOMAIN, SOURCES


def source_schema(existing=None):
    """Build optional power sensor selectors."""
    existing = existing or {}
    power = selector.EntitySelector(
        selector.EntitySelectorConfig(domain="sensor", device_class="power")
    )
    schema = {}
    for key in SOURCES:
        description = {"suggested_value": existing[key]} if existing.get(key) else None
        schema[vol.Optional(key, description=description)] = power
    return vol.Schema(schema)


class EhomeEmsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure one eHome EMS installation."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Associate existing HA power sensors."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            if not any(user_input.values()):
                return self.async_show_form(
                    step_id="user", data_schema=source_schema(),
                    errors={"base": "select_source"}
                )
            return self.async_create_entry(title="eHome EMS", data=user_input)
        return self.async_show_form(step_id="user", data_schema=source_schema())

    @staticmethod
    def async_get_options_flow(config_entry):
        """Expose options without creating another integration."""
        return EhomeEmsOptionsFlow()


class EhomeEmsOptionsFlow(config_entries.OptionsFlow):
    """Edit sensor associations and reload mapped entities."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            if not any(user_input.values()):
                return self.async_show_form(
                    step_id="init", data_schema=source_schema(),
                    errors={"base": "select_source"}
                )
            return self.async_create_entry(
                title="", data={key: user_input.get(key) for key in SOURCES}
            )
        existing = (
            self.config_entry.options
            if self.config_entry.options
            else self.config_entry.data
        )
        return self.async_show_form(
            step_id="init", data_schema=source_schema(existing)
        )
