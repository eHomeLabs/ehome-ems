"""Guided, manual energy source mapping for eHome EMS v0.1."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from .const import DOMAIN, CONF_GRID_POWER, CONF_SOLAR_POWER, CONF_HOME_POWER

class EhomeEmsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure a single local energy mapping."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Ask for optional power sensors already available in Home Assistant."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            if not any(user_input.values()):
                return self.async_show_form(step_id="user", data_schema=self._schema(), errors={"base": "select_source"})
            return self.async_create_entry(title="eHome EMS", data=user_input)
        return self.async_show_form(step_id="user", data_schema=self._schema())

    @staticmethod
    def _schema():
        power_selector = selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", device_class="power"))
        return vol.Schema({
            vol.Optional(CONF_GRID_POWER): power_selector,
            vol.Optional(CONF_SOLAR_POWER): power_selector,
            vol.Optional(CONF_HOME_POWER): power_selector,
        })

    @staticmethod
    def async_get_options_flow(config_entry):
        return EhomeEmsOptionsFlow()

class EhomeEmsOptionsFlow(config_entries.OptionsFlow):
    """Allow mappings to be revised without reinstalling."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        existing = {**self.config_entry.data, **self.config_entry.options}
        power_selector = selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", device_class="power"))
        schema = vol.Schema({vol.Optional(k, description={"suggested_value": existing.get(k)}): power_selector for k in (CONF_GRID_POWER, CONF_SOLAR_POWER, CONF_HOME_POWER)})
        return self.async_show_form(step_id="init", data_schema=schema)
