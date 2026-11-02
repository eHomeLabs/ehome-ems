"""Native local F1ATB protocol. No dependency on another HA integration.

Protocol references: F1ATB/Solar-Router-F1ATB Server.ino and Stockage.ino;
WillSpecIm/Integration-f1atb was studied as an interoperability reference.
"""
import asyncio
from copy import deepcopy
from hashlib import sha256
import json
from math import isfinite
from urllib.parse import urlsplit

from aiohttp import ClientError

GS, RS = chr(29), chr(30)
MAX_RESPONSE = 256 * 1024


class RouterError(ValueError):
    """Stable, non-sensitive error code for the panel."""


def base_url(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 2048:
        raise RouterError("invalid_router_url")
    value = value.strip()
    if "://" not in value:
        value = "http://" + value
    try:
        url = urlsplit(value)
        _ = url.port
    except ValueError as err:
        raise RouterError("invalid_router_url") from err
    if (url.scheme not in ("http", "https") or not url.hostname or url.username is not None
            or url.password is not None or url.port == 0 or url.path not in ("", "/") or url.query or url.fragment
            or any(c.isspace() or ord(c) < 32 for c in value)):
        raise RouterError("invalid_router_url")
    # Canonical origin also shares the same lock for :80/:443 and case variants.
    hostname = url.hostname.lower()
    if ":" in hostname:
        hostname = "[" + hostname + "]"
    port = url.port
    authority = hostname + (f":{port}" if port and port != (80 if url.scheme == "http" else 443) else "")
    return f"{url.scheme}://{authority}"


def number(value):
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if isfinite(result) else None


def bounded_int(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise RouterError("invalid_router_parameters")
    return value


def config_token(config):
    return sha256(json.dumps(config, sort_keys=True, ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def actions(config):
    result = config.get("Actions") if isinstance(config, dict) else None
    if not isinstance(result, list) or not result or len(result) > 64 or any(not isinstance(a, dict) for a in result):
        raise RouterError("unsupported_router_config")
    return result


def periods(action):
    value = action.get("Periodes", action.get("Périodes", []))
    if not isinstance(value, list) or any(not isinstance(p, dict) for p in value):
        raise RouterError("unsupported_router_config")
    return value


def public_config(config):
    """Expose only action settings, never Wi-Fi/MQTT credentials from ParaFixe."""
    return {"config_token": config_token(config), "actions": [
        {"index": i, "name": str(a.get("Titre", f"Action {i}"))[:80],
         "mode": a.get("Actif"), "forced_opening": a.get("ForceOuvre"),
         "periods": [{key: p.get(key) for key in ("Type", "Hfin", "Vmin", "Vmax")}
                     for p in periods(a)]}
        for i, a in enumerate(actions(config))]}


def parse_live(text, state_text):
    groups = text.split(GS)
    if len(groups) < 3 or groups[0].split(RS)[0] != "Deb":
        raise RouterError("unsupported_router_data")
    house, probe = groups[1].split(RS), groups[2].split(RS)
    if len(house) < 8:
        raise RouterError("unsupported_router_data")
    def field(row, i):
        value = number(row[i]) if i < len(row) else None
        return value if value is not None and value >= 0 else None
    temps = groups[0].split(RS)
    temperatures = [number(t) for t in temps[5].split("|")] if len(temps) > 5 else []
    state_groups = state_text.split(GS)
    if len(state_groups) < 4 or number(state_groups[3]) is None:
        raise RouterError("unsupported_router_data")
    live_actions = {}
    for row in state_groups[4:]:
        if not row.strip():
            continue
        cells = row.split(RS)
        if len(cells) < 4:
            raise RouterError("unsupported_router_data")
        idx = number(cells[0])
        if idx is None or idx != int(idx) or not 0 <= idx < 64:
            raise RouterError("unsupported_router_data")
        opening = {"On": 100, "Off": 0}.get(cells[2], number(cells[2]))
        force = number(cells[3])
        live_actions[int(idx)] = {"opening": opening if opening is not None and 0 <= opening <= 100 else None,
                                  "force_minutes": force}
    return {"grid_import_power": field(house, 0), "grid_export_power": field(house, 1),
            "probe_power": field(probe, 0), "probe_energy_total_kwh":
                field(probe, 6) / 1000 if field(probe, 6) is not None else None,
            "temperatures": [t if t is not None and -100 < t < 150 else None for t in temperatures],
            "live_actions": live_actions}


class F1atbClient:
    def __init__(self, session, host):
        self.session, self.base = session, base_url(host)

    async def request(self, path, *, body=None):
        try:
            async with asyncio.timeout(10):
                kwargs = {"allow_redirects": False}
                if body is not None:
                    kwargs.update(data=json.dumps(body, ensure_ascii=False, allow_nan=False).encode(),
                                  headers={"Content-Type": "text/plain"})
                method = self.session.post if body is not None else self.session.get
                async with method(self.base + path, **kwargs) as response:
                    if response.status != 200:
                        raise RouterError("router_http_error")
                    raw = bytearray()
                    async for chunk in response.content.iter_chunked(8192):
                        raw.extend(chunk)
                        if len(raw) > MAX_RESPONSE:
                            raise RouterError("router_response_too_large")
                    return raw.decode("utf-8")
        except (ClientError, TimeoutError, UnicodeError) as err:
            raise RouterError("router_unavailable") from err

    async def read_config(self):
        text = await self.request("/ParaFixe")
        try:
            def reject_constant(_):
                raise ValueError("non_finite")
            config = json.loads(text, parse_constant=reject_constant)
        except (ValueError, TypeError) as err:
            raise RouterError("unsupported_router_config") from err
        public_config(config)
        return config

    async def read(self):
        config = await self.read_config()
        live = parse_live(await self.request("/ajax_data"), await self.request("/ajax_etatActions"))
        return {**public_config(config), **live}

    async def force(self, index, minutes):
        await self.request(f"/ForceAction?NumAction={index}&Force={minutes}")

    async def patch(self, config, index, values):
        """Edit only supported existing fields, retain every other config field."""
        updated = deepcopy(config)
        target = actions(updated)[index]
        supplied = set(values) - {"config_token"}
        if not supplied or supplied - {"mode", "forced_opening", "period", "opening_max"}:
            raise RouterError("invalid_router_parameters")
        if "mode" in values:
            if "Actif" not in target:
                raise RouterError("unsupported_router_config")
            target["Actif"] = bounded_int(values["mode"], 0, 5)
        if "forced_opening" in values:
            if "ForceOuvre" not in target:
                raise RouterError("unsupported_router_config")
            target["ForceOuvre"] = bounded_int(values["forced_opening"], 0, 100)
        if ("period" in values) != ("opening_max" in values):
            raise RouterError("invalid_router_parameters")
        if "period" in values:
            ps = periods(target)
            p = bounded_int(values["period"], 0, len(ps) - 1)
            # In relay On/Off, Vmax is a W threshold, not a percentage.
            if target.get("Actif") in (0, 1) and index != 0 or ps[p].get("Type") != 4 or "Vmax" not in ps[p]:
                raise RouterError("unsupported_router_period")
            ps[p]["Vmax"] = bounded_int(values["opening_max"], 0, 100)
        await self.request("/ParaNew", body=updated)
        return updated
