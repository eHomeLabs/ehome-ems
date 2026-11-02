"""Exercise real Home Assistant APIs in a temporary, simulated installation.

Run in an environment with a supported Home Assistant version installed.
Never connects to or loads a user's Home Assistant configuration.
"""
import asyncio
from datetime import datetime, timedelta, timezone
import json
from importlib.metadata import version
from pathlib import Path
import shutil
import tempfile
import socket
from unittest.mock import patch
import aiohttp

from homeassistant import loader, bootstrap
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import config_validation as cv
from probatio import to_field_list
from homeassistant.components import frontend

ROOT = Path(__file__).resolve().parents[1]


async def validate(config_dir):
    hass = HomeAssistant(config_dir)
    hass.config.skip_pip = True
    loader.async_setup(hass)
    try:
        with socket.socket() as port_socket:
            port_socket.bind(("127.0.0.1", 0))
            port = port_socket.getsockname()[1]
        config = {"http": {"server_host": "127.0.0.1", "server_port": port},
                  "recorder": {"db_url": "sqlite:///" + hass.config.path("simulated-goal-history.db"), "auto_purge": False, "commit_interval": 0}}
        assert await bootstrap.async_from_config_dict(config, hass) is hass
        await hass.async_start()
        assert await async_setup_component(hass, "ehome_ems", {})
        hass.states.async_set("sensor.sim_grid", "-250", {"unit_of_measurement": "W", "device_class": "power"})
        hass.states.async_set("sensor.sim_solar", "1.5", {"unit_of_measurement": "kW", "device_class": "power"})
        hass.states.async_set("sensor.sim_home", "1250", {"unit_of_measurement": "W", "device_class": "power"})
        hass.states.async_set("sensor.sim_soc", "65", {"unit_of_measurement": "%", "device_class": "battery"})
        hass.states.async_set("sensor.sim_charge", "250", {"unit_of_measurement": "W", "device_class": "power"})
        hass.states.async_set("sensor.sim_energy", "3250", {"unit_of_measurement": "Wh", "device_class": "energy"})
        result = await hass.config_entries.flow.async_init("ehome_ems", context={"source": "user"})
        flow_id = result["flow_id"]
        assert result["step_id"] == "grid", result
        result = await hass.config_entries.flow.async_configure(flow_id, {"grid_power": "sensor.sim_grid"})
        assert result["step_id"] == "solar", result
        result = await hass.config_entries.flow.async_configure(flow_id, {"solar_power": "sensor.sim_solar"})
        assert result["step_id"] == "home", result
        result = await hass.config_entries.flow.async_configure(flow_id, {"home_power": "sensor.sim_home"})
        assert result["step_id"] == "batteries", result
        result = await hass.config_entries.flow.async_configure(flow_id, {"next_step_id": "add_battery"})
        assert result["step_id"] == "add_battery", result
        # Use the same serializer as HA's HTTP flow API, not just Python schemas.
        json.dumps(to_field_list(result["data_schema"], custom_serializer=cv.custom_serializer))
        result = await hass.config_entries.flow.async_configure(flow_id, {
            "name": "Simulated battery", "role": "backup", "coupling": "ac",
            "capacity_kwh": 5, "soc": "sensor.sim_soc",
            "charge_power": "sensor.sim_charge", "remaining_energy": "sensor.sim_energy",
        })
        assert result["step_id"] == "batteries", result
        result = await hass.config_entries.flow.async_configure(flow_id, {"next_step_id": "usages"})
        assert result["step_id"] == "usages", result
        hass.states.async_set("sensor.sim_router_power", "350", {"unit_of_measurement": "W", "device_class": "power"})
        hass.states.async_set("sensor.sim_router_energy", "1250", {"unit_of_measurement": "Wh", "device_class": "energy"})
        hass.states.async_set("switch.sim_router", "on")
        hass.states.async_set("input_number.sim_water_max", "51", {"unit_of_measurement":"°C"})
        result = await hass.config_entries.flow.async_configure(flow_id, {"next_step_id": "add_usage"})
        json.dumps(to_field_list(result["data_schema"], custom_serializer=cv.custom_serializer))
        result = await hass.config_entries.flow.async_configure(flow_id, {
            "name": "Simulated router", "kind": "solar_router", "power": "sensor.sim_router_power",
            "energy": "sensor.sim_router_energy", "energy_period": "today", "status": "switch.sim_router",
            "temperature": "input_number.sim_water_max",
            "included_in_home": True,
        })
        assert result["step_id"] == "usages", result
        hass.states.async_set("sensor.sim_ev_power", "0", {"unit_of_measurement": "W", "device_class": "power"})
        await hass.config_entries.flow.async_configure(flow_id, {"next_step_id": "add_usage"})
        result = await hass.config_entries.flow.async_configure(flow_id, {
            "name": "Simulated EV", "kind": "ev_charger", "power": "sensor.sim_ev_power",
            "included_in_home": True,
        })
        assert result["step_id"] == "usages", result
        # b11 appliance and daily settings through HA's real schema serializer.
        hass.states.async_set("sensor.sim_fridge", "85", {"unit_of_measurement": "W", "device_class": "power"})
        hass.states.async_set("sensor.sim_fridge_day", "800", {"unit_of_measurement": "Wh", "device_class": "energy"})
        await hass.config_entries.flow.async_configure(flow_id, {"next_step_id": "appliances"})
        result = await hass.config_entries.flow.async_configure(flow_id, {"next_step_id": "add_appliance"})
        json.dumps(to_field_list(result["data_schema"], custom_serializer=cv.custom_serializer))
        result = await hass.config_entries.flow.async_configure(flow_id, {"name": "Simulated fridge", "power": "sensor.sim_fridge", "energy": "sensor.sim_fridge_day", "energy_period": "today", "included_in_home": True})
        assert result["step_id"] == "appliances", result
        result = await hass.config_entries.flow.async_configure(flow_id, {"next_step_id": "daily"})
        json.dumps(to_field_list(result["data_schema"], custom_serializer=cv.custom_serializer))
        result = await hass.config_entries.flow.async_configure(flow_id, {"home": "sensor.sim_fridge_day", "tariff_eur_kwh": .215})
        assert result["step_id"] == "review", result
        assert result["step_id"] == "review", result
        result = await hass.config_entries.flow.async_configure(flow_id, {"next_step_id": "confirm"})
        assert result["step_id"] == "confirm", result
        result = await hass.config_entries.flow.async_configure(flow_id, {})
        assert result["type"] == "create_entry", result
        entry = result["result"]
        await hass.async_block_till_done()
        assert entry.state.value == "loaded", entry.state
        from custom_components.ehome_ems.panel import panel_path, PANEL_TAG, PANEL_URL
        automatic_path = panel_path(entry.entry_id)
        assert frontend.async_panel_exists(hass, automatic_path)
        registry = er.async_get(hass)

        def mirror(suffix):
            entity_id = registry.async_get_entity_id("sensor", "ehome_ems", f"{entry.entry_id}_{suffix}")
            assert entity_id, suffix
            value = hass.states.get(entity_id)
            assert value is not None, entity_id
            return entity_id, value

        grid_id, grid = mirror("grid_power")
        assert float(grid.state) == -250, grid
        solar_id, solar = mirror("solar_power")
        assert float(solar.state) == 1500, solar
        battery_id = next(iter(entry.data["batteries"]))
        original_home_id, _ = mirror("home_power")
        appliance_id = next(key for key, usage in entry.data["usages"].items() if usage["kind"] == "appliance")
        assert float(mirror(f"usage_{appliance_id}_energy")[1].state) == .8
        assert entry.data["daily"]["home"] == "sensor.sim_fridge_day"
        router_id = next(key for key, usage in entry.data["usages"].items() if usage["kind"] == "solar_router")
        temp_id, temp = mirror(f"usage_{router_id}_temperature")
        assert float(temp.state) == 51
        hass.states.async_set("input_number.sim_water_max", "140", {"unit_of_measurement":"°F"})
        await hass.async_block_till_done()
        assert float(hass.states.get(temp_id).state) == 60
        hass.states.async_set("input_number.sim_water_max", "unavailable", {"unit_of_measurement":"°C"})
        await hass.async_block_till_done()
        assert hass.states.get(temp_id).state == "unavailable"
        hass.states.async_set("input_number.sim_water_max", "52", {"unit_of_measurement":"°C"})
        await hass.async_block_till_done()
        assert float(hass.states.get(temp_id).state) == 52
        router_energy_id, router_energy = mirror(f"usage_{router_id}_energy")
        assert float(router_energy.state) == 1.25
        assert router_energy.attributes["energy_period"] == "today"
        router_status_id, router_status = mirror(f"usage_{router_id}_status")
        assert router_status.state == "on"
        hass.states.async_set("switch.sim_router", "off")
        await hass.async_block_till_done()
        assert hass.states.get(router_status_id).state == "off"
        _, soc = mirror(f"{battery_id}_soc")
        assert soc.attributes["unit_of_measurement"] == "%"
        _, energy = mirror(f"{battery_id}_remaining_energy")
        assert float(energy.state) == 3.25
        assert energy.attributes["state_class"] == "measurement"
        assert not energy.attributes["eligible_for_ac_balance"]
        energy_id, _ = mirror(f"{battery_id}_remaining_energy")
        hass.states.async_set("sensor.sim_energy", "305799", {"unit_of_measurement": "Wh"})
        await hass.async_block_till_done()
        assert hass.states.get(energy_id).state == "unavailable"
        # HA omits extra attributes while an entity is unavailable.
        # Detailed rejection reasons are checked in configuration and unit tests.
        hass.states.async_set("sensor.sim_energy", "3250", {"unit_of_measurement": "Wh"})
        await hass.async_block_till_done()
        assert float(hass.states.get(energy_id).state) == 3.25

        # Real source events must propagate, including unavailable and recovery.
        hass.states.async_set("sensor.sim_solar", "unavailable", {"unit_of_measurement": "kW"})
        await hass.async_block_till_done()
        assert hass.states.get(solar_id).state == "unavailable"
        hass.states.async_set("sensor.sim_solar", "2", {"unit_of_measurement": "kW"})
        await hass.async_block_till_done()
        assert float(hass.states.get(solar_id).state) == 2000

        renamed_id = "sensor.sim_renamed_grid_mirror"
        registry.async_update_entity(grid_id, new_entity_id=renamed_id)
        await hass.async_block_till_done()
        response = await hass.services.async_call(
            "ehome_ems", "generate_dashboard", {"language": "fr"}, blocking=True, return_response=True,
        )
        assert renamed_id in json.dumps(response)
        assert response["missing_entities"] == [], response
        assert len(response["dashboard"]["views"]) == 5
        assert router_energy_id in json.dumps(response)

        # Options must use actual HA flow APIs and reload the existing entry.
        options = await hass.config_entries.options.async_init(entry.entry_id)
        options_id = options["flow_id"]
        assert options["step_id"] == "grid", options
        await hass.config_entries.options.async_configure(options_id, {"grid_power": "sensor.sim_grid"})
        await hass.config_entries.options.async_configure(options_id, {"solar_power": "sensor.sim_solar"})
        await hass.config_entries.options.async_configure(options_id, {})
        await hass.config_entries.options.async_configure(options_id, {"next_step_id": "usages"})
        await hass.config_entries.options.async_configure(options_id, {"next_step_id": "review"})
        await hass.config_entries.options.async_configure(options_id, {"next_step_id": "confirm"})
        saved = await hass.config_entries.options.async_configure(options_id, {})
        assert saved["type"] == "create_entry", saved
        await hass.async_block_till_done()
        assert entry.options["home_power"] is None
        assert entry.state.value == "loaded", entry.state
        assert mirror("grid_power")[0] == renamed_id
        assert mirror(f"{battery_id}_soc")[1].state == "65.0"

        # Switch to an EMS-computed balance through real options, preserving the ID.
        hass.states.async_set("sensor.sim_import", "0", {"unit_of_measurement": "W", "device_class": "power"})
        hass.states.async_set("sensor.sim_export", "50", {"unit_of_measurement": "W", "device_class": "power"})
        hass.states.async_set("sensor.sim_discharge", "0", {"unit_of_measurement": "W", "device_class": "power"})
        options = await hass.config_entries.options.async_init(entry.entry_id)
        options_id = options["flow_id"]
        await hass.config_entries.options.async_configure(options_id, {
            "grid_power": "sensor.sim_grid", "grid_import": "sensor.sim_import", "grid_export": "sensor.sim_export",
        })
        form = await hass.config_entries.options.async_configure(options_id, {"solar_power": "sensor.sim_solar"})
        json.dumps(to_field_list(form["data_schema"], custom_serializer=cv.custom_serializer))
        await hass.config_entries.options.async_configure(options_id, {
            "home_power_mode": "calculated", "home_has_solar": True, "home_has_storage": True,
            "home_boundary_confirmed": True, "home_max_age_seconds": 300,
        })
        await hass.config_entries.options.async_configure(options_id, {"next_step_id": "edit_battery"})
        await hass.config_entries.options.async_configure(options_id, {"battery_id": battery_id})
        await hass.config_entries.options.async_configure(options_id, {
            "name": "Simulated battery", "role": "active", "coupling": "ac", "capacity_kwh": 5,
            "soc": "sensor.sim_soc", "charge_power": "sensor.sim_charge",
            "discharge_power": "sensor.sim_discharge", "remaining_energy": "sensor.sim_energy",
        })
        await hass.config_entries.options.async_configure(options_id, {"next_step_id": "usages"})
        await hass.config_entries.options.async_configure(options_id, {"next_step_id": "review"})
        await hass.config_entries.options.async_configure(options_id, {"next_step_id": "confirm"})
        saved = await hass.config_entries.options.async_configure(options_id, {})
        assert saved["type"] == "create_entry", saved
        await hass.async_block_till_done()
        home_id, home = mirror("home_power")
        assert home_id == original_home_id
        assert float(home.state) == 1700, home
        # The 350 W router submeter is already part of loads, not added again.
        assert float(mirror(f"usage_{router_id}_power")[1].state) == 350
        assert home.attributes["value_origin"] == "calculated"
        hass.states.async_set("sensor.sim_charge", "500", {"unit_of_measurement": "W"})
        await hass.async_block_till_done()
        assert float(hass.states.get(home_id).state) == 1450
        hass.states.async_set("sensor.sim_solar", "unavailable", {"unit_of_measurement": "kW"})
        await hass.async_block_till_done()
        assert hass.states.get(home_id).state == "unavailable"
        hass.states.async_set("sensor.sim_solar", "2", {"unit_of_measurement": "kW"})
        await hass.async_block_till_done()
        assert float(hass.states.get(home_id).state) == 1450
        response = await hass.services.async_call(
            "ehome_ems", "generate_dashboard", {"language": "fr"}, blocking=True, return_response=True,
        )
        assert home_id in json.dumps(response)

        # Exercise authenticated WS and native dashboard creation/storage, not internals.
        user = await hass.auth.async_create_user("Simulated admin", group_ids=["system-admin"])
        refresh = await hass.auth.async_create_refresh_token(user, client_id="https://example.local")
        token = hass.auth.async_create_access_token(refresh)
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(f"http://127.0.0.1:{port}/api/websocket") as ws:
                assert (await ws.receive_json())["type"] == "auth_required"
                await ws.send_json({"type": "auth", "access_token": token})
                assert (await ws.receive_json())["type"] == "auth_ok"
                command_id = 0
                async def command(payload, success=True):
                    nonlocal command_id
                    command_id += 1
                    await ws.send_json({"id": command_id, **payload})
                    while (answer := await ws.receive_json()).get("id") != command_id:
                        pass
                    assert answer["success"] is success, answer
                    return answer.get("result")
                snapshot = await command({"type": "ehome_ems/dashboard", "entry_id": entry.entry_id})
                copy_path = "ehome-test-copy-" + entry.entry_id.lower()
                await command({"type": "lovelace/dashboards/create", "title": "Independent copy",
                               "url_path": copy_path, "require_admin": True})
                await command({"type": "lovelace/config/save", "url_path": copy_path,
                               "config": {**snapshot["dashboard"], "title": "Preserved custom title"}})
                await command({"type": "lovelace/dashboards/create", "title": "Must not replace",
                               "url_path": copy_path}, success=False)
                assert await hass.config_entries.async_reload(entry.entry_id)
                await hass.async_block_till_done()
                preserved = await command({"type": "lovelace/config", "url_path": copy_path})
                assert preserved["title"] == "Preserved custom title"
                asset = await session.get(f"http://127.0.0.1:{port}/ehome_ems_panel_0.2.5.js")
                assert asset.status == 200
                assert "javascript" in asset.headers.get("Content-Type", "")
                assert "ehome-ems-panel" in await asset.text()
                brand = await session.get(
                    f"http://127.0.0.1:{port}/api/brands/integration/ehome_ems/icon.png?placeholder=no",
                    headers={"Authorization": "Bearer " + token})
                assert brand.status == 200
                assert await brand.read() == (ROOT / "custom_components/ehome_ems/brand/icon.png").read_bytes()
                house_asset = await session.get(f"http://127.0.0.1:{port}/ehome_ems_assets/house.webp")
                assert house_asset.status == 200
                assert house_asset.headers["Content-Type"].startswith("image/webp")
                assert await house_asset.read() == (ROOT / "custom_components/ehome_ems/frontend/assets/house.webp").read_bytes()
                snapshot = await command({"type": "ehome_ems/dashboard", "entry_id": entry.entry_id})
                assert solar_id in snapshot["bindings"]
                assert snapshot["version"] == "0.2.5"
                assert PANEL_TAG == "ehome-ems-panel-0-2-5"
                assert PANEL_URL == "/ehome_ems_panel_0.2.5.js"
                assert snapshot["flow"]["entities"]["solar_power"] == solar_id
                hass.states.async_set("sensor.sim_pv_new", "2.1", {"unit_of_measurement": "kW", "device_class": "power"})
                old_revision = snapshot["revision"]
                await command({"type": "ehome_ems/remap_source", "entry_id": entry.entry_id,
                               "entity_id": solar_id, "source_id": "sensor.sim_pv_new",
                               "expected_source": "sensor.sim_solar", "revision": old_revision})
                await hass.async_block_till_done()
                assert float(hass.states.get(solar_id).state) == 2100
                assert float(mirror("home_power")[1].state) == 1550
                await command({"type": "ehome_ems/remap_source", "entry_id": entry.entry_id,
                               "entity_id": solar_id, "source_id": "sensor.sim_solar",
                               "expected_source": "sensor.sim_solar", "revision": old_revision}, success=False)
                assert entry.options["solar_power"] == "sensor.sim_pv_new"
                # b12 scoped administrator CRUD: IDs and unrelated mappings survive reload.
                hass.states.async_set("sensor.sim_coffee", "35", {"unit_of_measurement": "W", "device_class": "power"})
                hass.states.async_set("sensor.sim_coffee_day", ".123456789", {"unit_of_measurement": "kWh", "device_class": "energy"})
                before = await command({"type": "ehome_ems/dashboard", "entry_id": entry.entry_id})
                assert "settings" in before
                old_revision = before["revision"]
                values = {"name": "Simulated coffee", "power": "sensor.sim_coffee", "energy": "sensor.sim_coffee_day", "energy_period": "today", "included_in_home": True}
                changes = []
                stop_changes = hass.bus.async_listen("call_service", lambda event: changes.append(event.data))
                created = await command({"type": "ehome_ems/manage_settings", "entry_id": entry.entry_id, "revision": old_revision, "section": "appliances", "action": "save", "values": values})
                await hass.async_block_till_done()
                appliance = created["identifier"]
                stable_id, power = mirror(f"usage_{appliance}_power")
                assert float(power.state) == 35
                await command({"type": "ehome_ems/manage_settings", "entry_id": entry.entry_id, "revision": old_revision, "section": "appliances", "action": "remove", "identifier": appliance}, success=False)
                await command({"type": "ehome_ems/manage_settings", "entry_id": entry.entry_id, "revision": entry.modified_at.isoformat(), "section": "appliances", "action": "save", "identifier": appliance, "values": {**values, "name": "Renamed coffee"}})
                await hass.async_block_till_done()
                assert mirror(f"usage_{appliance}_power")[0] == stable_id
                assert entry.options["solar_power"] == "sensor.sim_pv_new"
                await command({"type": "ehome_ems/manage_settings", "entry_id": entry.entry_id, "revision": entry.modified_at.isoformat(), "section": "appliances", "action": "remove", "identifier": appliance})
                await hass.async_block_till_done()
                assert appliance not in entry.options["usages"]
                # b13 exact reference: signed grid only, heater/EV remain included.
                hass.states.async_set("sensor.sim_grid", "-300", {"unit_of_measurement": "W"})
                hass.states.async_set("sensor.sim_pv_new", "2000", {"unit_of_measurement": "W"})
                hass.states.async_set("sensor.sim_charge", "500", {"unit_of_measurement": "W"})
                await command({"type":"ehome_ems/manage_settings","entry_id":entry.entry_id,"revision":entry.modified_at.isoformat(),"section":"grid","action":"save","values":{"grid_power":"sensor.sim_grid"}})
                await hass.async_block_till_done()
                await command({"type":"ehome_ems/manage_settings","entry_id":entry.entry_id,"revision":entry.modified_at.isoformat(),"section":"home","action":"save","values":{"home_power_mode":"calculated","home_grid_mode":"signed","home_has_solar":True,"home_has_storage":True,"home_boundary_confirmed":True,"home_max_age_seconds":0}})
                await hass.async_block_till_done()
                assert mirror("home_power")[0] == original_home_id
                assert float(mirror("home_power")[1].state) == 1200
                assert mirror("home_power")[1].attributes["grid_representation"] == "signed"
                assert not mirror("home_power")[1].attributes["freshness_check_enabled"]
                assert float(mirror("grid_import")[1].state) == 0
                assert float(mirror("grid_export")[1].state) == 300
                assert len(mirror("home_power")[1].attributes["balance_inputs"]) == 4
                hass.states.async_set("sensor.sim_grid", "100", {"unit_of_measurement": "W"})
                await hass.async_block_till_done()
                assert float(mirror("home_power")[1].state) == 1600
                assert float(mirror("grid_import")[1].state) == 100
                assert float(mirror("grid_export")[1].state) == 0
                hass.states.async_set("sensor.sim_grid", "unavailable", {"unit_of_measurement": "W"})
                await hass.async_block_till_done()
                assert mirror("home_power")[1].state == "unavailable"
                assert mirror("grid_export")[1].state == "unavailable"
                hass.states.async_set("sensor.sim_grid", "-300", {"unit_of_measurement": "W"})
                await hass.async_block_till_done()
                assert float(mirror("home_power")[1].state) == 1200
                # b14 stable sources remain visible in observation; real errors still block.
                await command({"type":"ehome_ems/manage_settings","entry_id":entry.entry_id,"revision":entry.modified_at.isoformat(),"section":"home","action":"save","values":{"home_power_mode":"calculated","home_grid_mode":"signed","home_has_solar":True,"home_has_storage":True,"home_boundary_confirmed":True,"home_max_age_seconds":300,"home_freshness_policy":"warn"}})
                await hass.async_block_till_done()
                with patch("custom_components.ehome_ems.sensor.datetime") as clock:
                    clock.now.return_value=datetime.now(timezone.utc)+timedelta(hours=1)
                    hass.states.async_set("sensor.sim_grid","-301",{"unit_of_measurement":"W"})
                    await hass.async_block_till_done()
                    assert float(mirror("home_power")[1].state)==1199
                    assert mirror("home_power")[1].attributes["source_age_warning"]
                    assert mirror("home_power")[1].attributes["freshness_policy"]=="warn"
                hass.states.async_set("sensor.sim_grid","-300",{"unit_of_measurement":"W"})
                await hass.async_block_till_done()
                assert float(mirror("home_power")[1].state)==1200
                hass.states.async_set("sensor.sim_portable_stock","1.8",{"unit_of_measurement":"kWh","device_class":"energy","state_class":"total_increasing"})
                portable={"name":"Portable storage","role":"backup","coupling":"ac","capacity_kwh":2.3,"remaining_energy":"sensor.sim_portable_stock"}
                denied=await command({"type":"ehome_ems/manage_settings","entry_id":entry.entry_id,"revision":entry.modified_at.isoformat(),"section":"batteries","action":"save","values":portable},success=False)
                added=await command({"type":"ehome_ems/manage_settings","entry_id":entry.entry_id,"revision":entry.modified_at.isoformat(),"section":"batteries","action":"save","values":{**portable,"remaining_energy_is_stock":True}})
                await hass.async_block_till_done()
                assert float(mirror(added["identifier"]+"_remaining_energy")[1].state)==1.8
                hass.states.async_set("weather.sim_home","cloudy",{"temperature":16,"temperature_unit":"°C"})
                await command({"type":"ehome_ems/manage_settings","entry_id":entry.entry_id,"revision":entry.modified_at.isoformat(),"section":"daily","action":"save","values":{**entry.options.get("daily",{}),"tariff_eur_kwh":.215,"weather_entity":"weather.sim_home"}})
                await hass.async_block_till_done()
                assert (await command({"type":"ehome_ems/dashboard","entry_id":entry.entry_id}))["weather_entity"]=="weather.sim_home"
                stop_changes()
                assert not changes, changes
                day = await session.get(f"http://127.0.0.1:{port}/ehome_ems_assets/house-day.webp")
                assert day.status == 200 and day.headers["Content-Type"].startswith("image/webp")
                snapshot = await command({"type": "ehome_ems/dashboard", "entry_id": entry.entry_id})
                targets = [{"id": item["id"], "enabled": True, "min_w": 0 if item["kind"] == "battery" else 800,
                            "max_w": 1000 if item["kind"] == "battery" else 1800}
                           for item in snapshot["simulation"]["targets"]]
                assert len(targets) >= 2
                previous_revision = snapshot["revision"]
                await command({"type": "ehome_ems/save_simulation", "entry_id": entry.entry_id,
                               "revision": previous_revision, "targets": targets})
                await hass.async_block_till_done()
                assert entry.options["solar_power"] == "sensor.sim_pv_new"
                await command({"type": "ehome_ems/save_simulation", "entry_id": entry.entry_id,
                               "revision": previous_revision, "targets": targets}, success=False)
                service_events = []
                remove_listener = hass.bus.async_listen("call_service", lambda event: service_events.append(event.data))
                scenario = await command({"type": "ehome_ems/simulate", "entry_id": entry.entry_id,
                                          "revision": entry.modified_at.isoformat(), "budget_w": 2100})
                assert scenario["allocated_w"] == 2100 and scenario["remaining_w"] == 0
                assert not scenario["commands_sent"]
                assert sum(item["allocated_w"] for item in scenario["targets"]) == 2100
                await command({"type": "ehome_ems/simulate", "entry_id": entry.entry_id,
                               "revision": previous_revision, "budget_w": 2100}, success=False)
                for index in range(22):
                    await command({"type": "ehome_ems/simulate", "entry_id": entry.entry_id,
                                   "revision": entry.modified_at.isoformat(), "budget_w": index})
                await hass.async_block_till_done()
                remove_listener()
                assert not service_events, service_events
                assert await hass.config_entries.async_reload(entry.entry_id)
                await hass.async_block_till_done()
                snapshot = await command({"type": "ehome_ems/dashboard", "entry_id": entry.entry_id})
                assert len(snapshot["simulation_history"]) == 20
                assert snapshot["simulation_history"][-1]["budget_w"] == 21
                assert snapshot["simulation"]["targets"][0]["enabled"]
                # Explicit manual control, using a simulated service only.
                hass.states.async_set("switch.sim_manual", "off")
                manual_calls = []
                async def manual_service(call):
                    manual_calls.append(call)
                    hass.states.async_set("switch.sim_manual", "on" if call.service == "turn_on" else "off")
                hass.services.async_register("switch", "turn_on", manual_service)
                hass.services.async_register("switch", "turn_off", manual_service)
                values = {"name":"Simulated manual load","power":"sensor.sim_coffee","energy":"sensor.sim_coffee_day","energy_period":"today","included_in_home":True,"control_entity":"switch.sim_manual","control_enabled":True,"daily_energy_goal_kwh":3}
                created = await command({"type":"ehome_ems/manage_settings","entry_id":entry.entry_id,"revision":entry.modified_at.isoformat(),"section":"appliances","action":"save","values":values})
                await hass.async_block_till_done()
                manual_identifier = created["identifier"]
                hass.states.async_set("sensor.sim_coffee", "-5", {"unit_of_measurement":"W","device_class":"power"})
                await hass.async_block_till_done()
                power = mirror(f"usage_{manual_identifier}_power")[1]
                assert float(power.state) == 0 and power.attributes["negative_offset_corrected"]
                assert power.attributes["source_raw_value"] == "-5"
                payload = {"type":"ehome_ems/manual_control","entry_id":entry.entry_id,"identifier":manual_identifier,"revision":entry.modified_at.isoformat(),"desired_on":True,"expected_state":"off"}
                await command({**payload,"revision":"old"}, success=False)
                assert not manual_calls
                await command(payload)
                assert len(manual_calls) == 1 and manual_calls[0].context.user_id is not None
                assert hass.states.get("switch.sim_manual").state == "on"
                await command(payload, success=False)  # stale expected state, no duplicate
                assert len(manual_calls) == 1
                hass.states.async_set("switch.sim_manual", "unavailable")
                await command({**payload,"expected_state":"on","desired_on":False}, success=False)
                assert len(manual_calls) == 1
                # PV equipment is monitoring-only, even if its source is the solar total.
                from custom_components.ehome_ems.photovoltaic import photovoltaic_schema
                json.dumps(to_field_list(photovoltaic_schema({}), custom_serializer=cv.custom_serializer))
                previous_home = mirror("home_power")[1].state
                pv_created = await command({"type":"ehome_ems/manage_settings","entry_id":entry.entry_id,"revision":entry.modified_at.isoformat(),"section":"photovoltaic","action":"save","values":{"name":"Demo hybrid","kind":"hybrid_inverter","power":"sensor.sim_pv_new","energy_period":"total"}})
                await hass.async_block_till_done()
                assert mirror("home_power")[1].state == previous_home
                pv_snapshot = await command({"type":"ehome_ems/dashboard","entry_id":entry.entry_id})
                assert pv_snapshot["flow"]["photovoltaic"][0]["id"] == pv_created["identifier"]
                mqtt_calls = []
                async def simulated_publish(call):mqtt_calls.append(call)
                hass.services.async_register("mqtt","publish",simulated_publish)
                router_created = await command({"type":"ehome_ems/manage_settings","entry_id":entry.entry_id,"revision":entry.modified_at.isoformat(),"section":"usages","action":"save","values":{"name":"Demo F1ATB","kind":"solar_router","power":"sensor.sim_coffee","included_in_home":True,"router_type":"f1atb","router_mqtt_topic":"demo_router/SSR","router_protocol_confirmed":True,"router_mqtt_enabled":True}} , success=False)
                # Use a distinct source: duplicate consumption mappings must still be rejected.
                hass.states.async_set("sensor.sim_router_extra","100",{"unit_of_measurement":"W"})
                router_created = await command({"type":"ehome_ems/manage_settings","entry_id":entry.entry_id,"revision":entry.modified_at.isoformat(),"section":"usages","action":"save","values":{"name":"Demo F1ATB","kind":"solar_router","power":"sensor.sim_router_extra","included_in_home":True,"router_type":"f1atb","router_mqtt_topic":"demo_router/SSR","router_protocol_confirmed":True,"router_mqtt_enabled":True}})
                await hass.async_block_till_done()
                router_identifier=router_created["identifier"]
                router_msg={"type":"ehome_ems/router_command","entry_id":entry.entry_id,"identifier":router_identifier,"revision":entry.modified_at.isoformat(),"action":"force_on","values":{"minutes":30}}
                assert not mqtt_calls
                await command(router_msg)
                assert len(mqtt_calls)==1 and not mqtt_calls[0].data["retain"]
                assert json.loads(mqtt_calls[0].data["payload"])=={"tOnOff":30}
                assert mqtt_calls[0].context.user_id is not None
                await command({**router_msg,"action":"parameters","values":{"period":0,"mode":"Decoupe"}},success=False)
                await command({**router_msg,"action":"release","values":{}})
                assert json.loads(mqtt_calls[-1].data["payload"])=={"tOnOff":0}
                from validate_f1atb_ha import validate_native_router
                await validate_native_router(hass, entry, command)
            ordinary = await hass.auth.async_create_user("Simulated reader", group_ids=["system-users"])
            refresh = await hass.auth.async_create_refresh_token(ordinary, client_id="https://example.local")
            access = hass.auth.async_create_access_token(refresh)
            async with session.ws_connect(f"http://127.0.0.1:{port}/api/websocket") as ws:
                await ws.receive_json()
                await ws.send_json({"type": "auth", "access_token": access})
                assert (await ws.receive_json())["type"] == "auth_ok"
                await ws.send_json({"id": 1, "type": "lovelace/dashboards/create",
                                   "title": "Denied copy", "url_path": "ehome-denied-copy"})
                denied = await ws.receive_json()
                assert not denied["success"], denied
                await ws.send_json({"id": 2, "type": "ehome_ems/remap_source", "entry_id": entry.entry_id,
                                   "entity_id": solar_id, "source_id": "sensor.sim_solar",
                                   "expected_source": "sensor.sim_pv_new", "revision": entry.modified_at.isoformat()})
                assert not (await ws.receive_json())["success"]
                await ws.send_json({"id": 3, "type": "ehome_ems/save_simulation", "entry_id": entry.entry_id,
                                   "revision": entry.modified_at.isoformat(), "targets": targets})
                assert not (await ws.receive_json())["success"]
                await ws.send_json({"id": 4, "type": "ehome_ems/simulate", "entry_id": entry.entry_id,
                                   "revision": entry.modified_at.isoformat(), "budget_w": 500})
                scenario = await ws.receive_json()
                assert scenario["success"] and not scenario["result"]["commands_sent"]
                await ws.send_json({"id": 5, "type": "ehome_ems/manage_settings", "entry_id": entry.entry_id, "revision": entry.modified_at.isoformat(), "section": "daily", "action": "save", "values": {"tariff_eur_kwh": .2}})
                assert not (await ws.receive_json())["success"]
                await ws.send_json({"id": 6, "type": "ehome_ems/dashboard", "entry_id": entry.entry_id})
                public_snapshot = await ws.receive_json()
                assert public_snapshot["success"] and "settings" not in public_snapshot["result"]
                await ws.send_json({"id":7,"type":"ehome_ems/manual_control","entry_id":entry.entry_id,"identifier":manual_identifier,"revision":entry.modified_at.isoformat(),"desired_on":True,"expected_state":"off"})
                assert not (await ws.receive_json())["success"]
                assert len(manual_calls) == 1
                await ws.send_json({"id":8,**router_msg})
                assert not (await ws.receive_json())["success"]
                assert len(mqtt_calls)==2
                await ws.send_json({"id":9,"type":"ehome_ems/router_discover","host":"http://router.example.local"})
                assert not (await ws.receive_json())["success"]
                await ws.send_json({"id":10,"type":"ehome_ems/save_energy_goal","entry_id":entry.entry_id,"identifier":"denied","revision":entry.modified_at.isoformat(),"values":{}})
                assert not (await ws.receive_json())["success"]
                await ws.send_json({"id":11,"type":"ehome_ems/rearm_energy_goal","entry_id":entry.entry_id,"identifier":"denied","revision":entry.modified_at.isoformat()})
                assert not (await ws.receive_json())["success"]
                await ws.send_json({"id":12,"type":"ehome_ems/energy_goals","entry_id":entry.entry_id})
                assert (await ws.receive_json())["success"]


        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
        assert not frontend.async_panel_exists(hass, automatic_path)
        unloaded = hass.states.get(renamed_id)
        assert unloaded is None or unloaded.state == "unavailable", unloaded
        hass.states.async_set("sensor.sim_grid", "500", {"unit_of_measurement": "W"})
        await hass.async_block_till_done()
        unloaded = hass.states.get(renamed_id)
        assert unloaded is None or unloaded.state == "unavailable", unloaded
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert frontend.async_panel_exists(hass, automatic_path)
        assert float(mirror("grid_power")[1].state) == 500

        # Original V0.1-shaped data remains accepted by the real platform.
        old_entry_data = {key: entry.data.get(key) for key in (
            "grid_power", "grid_import", "grid_export", "solar_power", "home_power"
        )}
        assert await hass.config_entries.async_unload(entry.entry_id)
        hass.config_entries.async_update_entry(entry, data=old_entry_data, options={})
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert float(mirror("grid_power")[1].state) == 500
        print(f"PASS HA {version('homeassistant')}: flow, sensors, events, rename, dashboard action, options, reload/unload and V0.1 data")
    finally:
        await hass.async_stop()


def main():
    with tempfile.TemporaryDirectory(prefix="ehome-ha-smoke-") as config_dir:
        shutil.copytree(ROOT / "custom_components/ehome_ems",
                        Path(config_dir) / "custom_components/ehome_ems",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        # Test host only: no real adapters or outbound source-IP probing.
        with patch("ifaddr.get_adapters", return_value=[]), patch(
            "homeassistant.components.network.util.async_get_source_ip", return_value="127.0.0.1"
        ):
            asyncio.run(validate(config_dir))


if __name__ == "__main__":
    main()
