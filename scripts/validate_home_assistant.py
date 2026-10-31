"""Exercise real Home Assistant APIs in a temporary, simulated installation.

Run in an environment with a supported Home Assistant version installed.
Never connects to or loads a user's Home Assistant configuration.
"""
import asyncio
import json
from importlib.metadata import version
from pathlib import Path
import shutil
import tempfile

from homeassistant import loader, bootstrap
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import config_validation as cv
from probatio import to_field_list

ROOT = Path(__file__).resolve().parents[1]


async def validate(config_dir):
    hass = HomeAssistant(config_dir)
    hass.config.skip_pip = True
    loader.async_setup(hass)
    try:
        assert await bootstrap.async_from_config_dict({}, hass) is hass
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
        result = await hass.config_entries.flow.async_configure(flow_id, {"next_step_id": "review"})
        assert result["step_id"] == "review", result
        result = await hass.config_entries.flow.async_configure(flow_id, {"next_step_id": "confirm"})
        assert result["step_id"] == "confirm", result
        result = await hass.config_entries.flow.async_configure(flow_id, {})
        assert result["type"] == "create_entry", result
        entry = result["result"]
        await hass.async_block_till_done()
        assert entry.state.value == "loaded", entry.state
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
        assert len(response["dashboard"]["views"]) == 4

        # Options must use actual HA flow APIs and reload the existing entry.
        options = await hass.config_entries.options.async_init(entry.entry_id)
        options_id = options["flow_id"]
        assert options["step_id"] == "grid", options
        await hass.config_entries.options.async_configure(options_id, {"grid_power": "sensor.sim_grid"})
        await hass.config_entries.options.async_configure(options_id, {"solar_power": "sensor.sim_solar"})
        await hass.config_entries.options.async_configure(options_id, {})
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
        await hass.config_entries.options.async_configure(options_id, {"next_step_id": "review"})
        await hass.config_entries.options.async_configure(options_id, {"next_step_id": "confirm"})
        saved = await hass.config_entries.options.async_configure(options_id, {})
        assert saved["type"] == "create_entry", saved
        await hass.async_block_till_done()
        home_id, home = mirror("home_power")
        assert home_id == original_home_id
        assert float(home.state) == 1700, home
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

        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
        unloaded = hass.states.get(renamed_id)
        assert unloaded is None or unloaded.state == "unavailable", unloaded
        hass.states.async_set("sensor.sim_grid", "500", {"unit_of_measurement": "W"})
        await hass.async_block_till_done()
        unloaded = hass.states.get(renamed_id)
        assert unloaded is None or unloaded.state == "unavailable", unloaded
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
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
        asyncio.run(validate(config_dir))


if __name__ == "__main__":
    main()
