"""PV equipment metadata and original HA readings; never added to the AC balance."""
from math import isfinite
import voluptuous as vol
from homeassistant.helpers import selector, entity_registry as er
from .const import DOMAIN

PV_FIELDS = {"power": ("W", "kW"), "dc_power": ("W", "kW"), "energy": ("Wh", "kWh"),
             "charge_power": ("W", "kW"), "discharge_power": ("W", "kW"), "temperature": ("°C", "°F"), "status": ()}


def photovoltaic_schema(existing):
    fields = {vol.Required("name", default=existing.get("name", "Onduleur")): vol.All(str, vol.Length(min=1,max=80)),
              vol.Required("kind", default=existing.get("kind", "micro_inverter")): selector.SelectSelector(selector.SelectSelectorConfig(options=["micro_inverter","dc_inverter","hybrid_inverter"])),
              vol.Required("energy_period", default=existing.get("energy_period","total")): selector.SelectSelector(selector.SelectSelectorConfig(options=["today","total","session"]))}
    for key in ("manufacturer","model"):
        fields[vol.Optional(key, description={"suggested_value":existing[key]} if existing.get(key) else None)] = vol.All(str,vol.Length(max=80))
    fields[vol.Optional("nominal_power_w", description={"suggested_value":existing["nominal_power_w"]} if existing.get("nominal_power_w") else None)] = vol.All(vol.Coerce(float),vol.Range(min=1,max=1000000))
    for key in PV_FIELDS:
        fields[vol.Optional(key, description={"suggested_value":existing[key]} if existing.get(key) else None)] = selector.EntitySelector(selector.EntitySelectorConfig(domain=["sensor","binary_sensor","switch","select"] if key=="status" else ["sensor"]))
    return vol.Schema(fields)


def photovoltaic_errors(hass, items):
    errors={}; seen=set(); registry=er.async_get(hass)
    for identifier,item in items.items():
        if not any(item.get(key) for key in PV_FIELDS):errors[f"photovoltaic.{identifier}"]="select_source"
        nominal=item.get("nominal_power_w")
        if nominal is not None and (isinstance(nominal,bool) or not isinstance(nominal,(float,int)) or not isfinite(nominal) or not 1<=nominal<=1000000):errors[f"photovoltaic.{identifier}.nominal_power_w"]="invalid_value"
        for key,units in PV_FIELDS.items():
            source=item.get(key)
            if not source:continue
            path=f"photovoltaic.{identifier}.{key}"
            if not isinstance(source,str) or source.split(".")[0] not in (["sensor","binary_sensor","switch","select"] if key=="status" else ["sensor"]):errors[path]="invalid_source";continue
            state=hass.states.get(source); registered=registry.async_get(source)
            if registered and registered.platform==DOMAIN:errors[path]="recursive_source"
            elif state is None:errors[path]="missing_source"
            elif units and state.attributes.get("unit_of_measurement") not in units:errors[path]="unsupported_unit"
            if key in ("power","dc_power"):
                if source in seen:errors[path]="duplicate_source"
                seen.add(source)
    return errors
