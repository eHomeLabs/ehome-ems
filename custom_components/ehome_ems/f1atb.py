"""Bounded manual F1ATB MQTT commands, following the documented V15+ protocol."""
import json
from math import isfinite
from urllib.parse import urlsplit
from .const import DOMAIN

MODES={"ssr":("Inactif","OnOff","Demi","Multi","Train"),"triac":("Inactif","Decoupe","Demi","Multi","Train"),"pwm":("Inactif","PWM")}


def valid_web_url(url):
    if not url:return True
    if not isinstance(url,str) or len(url)>2048 or any(ord(c)<32 for c in url):return False
    try:
        parsed=urlsplit(url)
        _ = parsed.port
        return parsed.scheme in ("http","https") and bool(parsed.hostname) and parsed.username is None and parsed.password is None
    except ValueError:return False


def valid_topic(topic):
    return isinstance(topic,str) and 0<len(topic)<=255 and topic.count("/")==1 and all(part.strip() for part in topic.split("/")) and not topic.startswith("$") and not any(c in topic for c in "+#") and not any(ord(c)<32 for c in topic)


def has_router_target(usage):
    return usage.get("kind")=="solar_router" and usage.get("router_type")=="f1atb" and bool(usage.get("router_url") or valid_topic(usage.get("router_mqtt_topic")))


def router_error(usage):
    if not valid_web_url(usage.get("router_url")):return "invalid_router_url"
    if usage.get("router_mqtt_enabled"):
        if usage.get("kind")!="solar_router" or usage.get("router_type")!="f1atb" or not usage.get("router_protocol_confirmed") or not valid_topic(usage.get("router_mqtt_topic")):return "router_configuration"
    return None


def integer(value,minimum,maximum):
    if type(value) is not int or not minimum<=value<=maximum:raise ValueError("invalid_router_parameters")
    return value


def router_payload(usage, action, values):
    if not isinstance(values,dict):raise ValueError("invalid_router_parameters")
    if action in ("force_on","force_off"):
        if set(values)!={"minutes"}:raise ValueError("invalid_router_parameters")
        duration=integer(values["minutes"],1,1440)
        return {"tOnOff":duration if action=="force_on" else -duration}
    if action=="release" and not values:return {"tOnOff":0}
    if action!="parameters" or not values or set(values)-{"period","mode","opening_max","threshold_on","threshold_off"}:raise ValueError("invalid_router_parameters")
    result={"Periode":integer(values.get("period"),0,7)}
    if "mode" in values:
        mode=values["mode"]
        if mode not in MODES.get(usage.get("router_output","ssr"),()):raise ValueError("invalid_router_mode")
        result["Mode"]=mode
    for key,native,minimum,maximum in (("opening_max","OuvreMax",0,100),("threshold_on","SeuilOn",-100000,100000),("threshold_off","SeuilOff",-100000,100000)):
        if key in values:
            value=values[key]
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not isfinite(value) or not minimum<=value<=maximum:raise ValueError("invalid_router_parameters")
            result[native]=value
    if len(result)==1:raise ValueError("invalid_router_parameters")
    return result


async def async_router_command(hass, entry, identifier, revision, action, values, context):
    if entry.modified_at.isoformat()!=revision:raise ValueError("conflict")
    usage=(entry.options or entry.data).get("usages",{}).get(identifier,{})
    if router_error(usage) or not usage.get("router_mqtt_enabled"):raise ValueError("router_not_enabled")
    if not hass.services.has_service("mqtt","publish"):raise ValueError("mqtt_unavailable")
    payload=router_payload(usage,action,values); topic=usage["router_mqtt_topic"]
    busy=hass.data.setdefault(DOMAIN,{}).setdefault("router_busy",set())
    if topic in busy:raise ValueError("command_in_progress")
    busy.add(topic)
    try:
        await hass.services.async_call("mqtt","publish",{"topic":topic,"payload":json.dumps(payload,allow_nan=False),"qos":0,"retain":False},blocking=True,context=context)
    finally:busy.discard(topic)
    return {"published":True,"payload":payload,"confirmed_by_router":False}
