"""Scoped configuration writes, never equipment commands or arbitrary entry writes."""
from copy import deepcopy
from math import isfinite
from uuid import uuid4
import voluptuous as vol

from .const import SOURCES, HOME_SETTINGS, DAILY_SOURCES
from .config_flow import PowerWizard, battery_schema, usage_schema, positive_capacity
from .home_balance import home_sources


class SettingsError(ValueError):
    def __init__(self, reason, fields=None):
        super().__init__(reason)
        self.fields = fields or {}


def update_settings(hass, entry, section, action, values, identifier, revision):
    """Validate a whole scoped edit and preserve all unrelated settings and IDs."""
    if entry.modified_at.isoformat() != revision:
        raise SettingsError("conflict")
    if not isinstance(values, dict) or action not in ("save", "remove"):
        raise SettingsError("invalid_settings")
    candidate = deepcopy(dict(entry.options or entry.data))
    try:
        if section in ("batteries", "usages", "appliances"):
            collection = "batteries" if section == "batteries" else "usages"
            items = candidate.setdefault(collection, {})
            if identifier and identifier not in items:
                raise SettingsError("target_missing")
            if identifier and collection == "usages" and (items[identifier].get("kind") == "appliance") != (section == "appliances"):
                raise SettingsError("invalid_target")
            if action == "remove":
                if not identifier:
                    raise SettingsError("target_missing")
                del items[identifier]
            else:
                if collection == "batteries":
                    clean = battery_schema(items.get(identifier, {}))(values)
                    if clean.get("capacity_kwh") is not None:
                        clean["capacity_kwh"] = positive_capacity(clean["capacity_kwh"])
                    sources = ("charge_power", "discharge_power", "soc", "remaining_energy")
                else:
                    values = dict(values)
                    if section == "appliances":
                        values["kind"] = "appliance"
                    elif values.get("kind") == "appliance":
                        raise SettingsError("invalid_target")
                    clean = usage_schema(items.get(identifier, {}))(values)
                    if not clean.get("included_in_home"):
                        raise SettingsError("outside_home")
                    sources = ("power", "energy", "status", "temperature")
                if not any(clean.get(key) for key in sources):
                    raise SettingsError("select_source")
                identifier = identifier or uuid4().hex
                items[identifier] = clean
        elif action == "save" and section in ("grid", "solar", "home", "daily"):
            allowed = {"grid": {"grid_power", "grid_import", "grid_export"}, "solar": {"solar_power"},
                       "home": {"home_power", *HOME_SETTINGS}, "daily": {*DAILY_SOURCES, "tariff_eur_kwh"}}[section]
            if set(values) - allowed:
                raise SettingsError("invalid_settings")
            if section == "daily":
                tariff = values.get("tariff_eur_kwh")
                if tariff is not None and (isinstance(tariff, bool) or not isinstance(tariff, (int, float)) or not isfinite(tariff) or not 0 <= tariff <= 10):
                    raise SettingsError("invalid_tariff")
                candidate["daily"] = {key: values[key] for key in DAILY_SOURCES if values.get(key)}
                candidate["tariff_eur_kwh"] = tariff
            else:
                for key in allowed:
                    candidate[key] = values.get(key)
                if section == "home":
                    mode = values.get("home_power_mode", "existing")
                    if mode not in ("existing", "calculated"):
                        raise SettingsError("invalid_settings")
                    candidate["home_power_mode"] = mode
                    if mode == "calculated":
                        candidate["home_power"] = None
                    for key in HOME_SETTINGS[1:4]:
                        if type(values.get(key, False)) is not bool:
                            raise SettingsError("invalid_settings")
                        candidate[key] = values.get(key, False)
                    age = values.get("home_max_age_seconds", 300)
                    if type(age) is not int or not 30 <= age <= 3600:
                        raise SettingsError("invalid_settings")
                    candidate["home_max_age_seconds"] = age
        else:
            raise SettingsError("invalid_settings")
    except (vol.Invalid, TypeError, KeyError, OverflowError) as error:
        raise SettingsError("invalid_settings") from error
    # Only entity strings or empty slots can reach the registry.
    from .config_flow import source_items
    for _, source, _ in source_items(candidate):
        if source is not None and (not isinstance(source, str) or not source.startswith(("sensor.", "binary_sensor.", "switch.", "select."))):
            raise SettingsError("invalid_source")
    validator = PowerWizard()
    validator.hass = hass
    if errors := validator._errors(candidate):
        raise SettingsError("invalid_sources", errors)
    if candidate.get("home_power_mode") == "calculated":
        _, reason = home_sources(candidate)
        if reason:
            raise SettingsError(reason)
    if not any(source for _, source, _ in source_items(candidate)):
        raise SettingsError("select_source")
    hass.config_entries.async_update_entry(entry, options=candidate)
    return {"updated": True, "identifier": identifier}
