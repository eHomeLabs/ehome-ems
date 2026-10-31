"""Wizard contract tests with real schemas and small HA API doubles.

These tests exercise flow transitions and persistence boundaries, not a running HA.
"""
import importlib
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch
import voluptuous as vol

ROOT = Path(__file__).resolve().parents[1]


class FlowDouble:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()

    def async_show_form(self, **kwargs):
        return {"type": "form", **kwargs}

    def async_show_menu(self, **kwargs):
        return {"type": "menu", **kwargs}

    def async_create_entry(self, **kwargs):
        return {"type": "create_entry", **kwargs}

    async def async_set_unique_id(self, unique_id):
        self.unique_id = unique_id

    def _abort_if_unique_id_configured(self):
        pass


class SelectorDouble:
    def __init__(self, config):
        self.config = config

    def __call__(self, value):
        if not isinstance(value, str) or not value.startswith(("sensor.", "binary_sensor.", "switch.", "select.")):
            raise ValueError(value)
        return value


class SelectDouble(SelectorDouble):
    def __call__(self, value):
        choices = [option["value"] if isinstance(option, dict) else option
                   for option in self.config["options"]]
        if value not in choices:
            raise vol.Invalid("invalid selection")
        return value


def load_flow():
    modules = {}
    for name in (
        "homeassistant", "homeassistant.config_entries", "homeassistant.core",
        "homeassistant.helpers", "homeassistant.helpers.entity_registry",
        "homeassistant.helpers.selector", "ems_flow_test",
    ):
        modules[name] = ModuleType(name)
    modules["ems_flow_test"].__path__ = [str(ROOT / "custom_components/ehome_ems")]
    entries = modules["homeassistant.config_entries"]
    entries.ConfigFlow = entries.OptionsFlow = FlowDouble
    modules["homeassistant.core"].callback = lambda f: f
    modules["homeassistant.helpers.entity_registry"].async_get = lambda hass: hass.registry
    selectors = modules["homeassistant.helpers.selector"]
    selectors.EntitySelector = SelectorDouble
    selectors.EntitySelectorConfig = lambda **kwargs: kwargs
    selectors.SelectSelector = SelectDouble
    selectors.SelectSelectorConfig = lambda **kwargs: kwargs
    with patch.dict(sys.modules, modules):
        return importlib.import_module("ems_flow_test.config_flow")


flow_module = load_flow()


def state(value="100", unit="W"):
    return SimpleNamespace(state=value, attributes={"unit_of_measurement": unit})


class WizardTests(IsolatedAsyncioTestCase):
    def setUp(self):
        self.states = {"sensor.grid": state("-200"), "sensor.pv": state("1.5", "kW"),
                       "sensor.home": state("1300")}
        self.registered = {}
        self.hass = SimpleNamespace(
            states=SimpleNamespace(get=self.states.get),
            registry=SimpleNamespace(async_get=self.registered.get),
        )
        self.flow = flow_module.EhomeEmsConfigFlow()
        self.flow.hass = self.hass

    async def walk_to_review(self):
        self.assertEqual((await self.flow.async_step_user())["step_id"], "grid")
        self.assertEqual((await self.flow.async_step_grid({"grid_power": "sensor.grid"}))["step_id"], "solar")
        self.assertEqual((await self.flow.async_step_solar({"solar_power": "sensor.pv"}))["step_id"], "home")
        self.assertEqual((await self.flow.async_step_home({"home_power": "sensor.home"}))["step_id"], "batteries")
        return await self.flow.async_step_review()

    async def test_confirmation_is_the_only_persistence_point(self):
        review = await self.walk_to_review()
        self.assertEqual(review["type"], "menu")
        self.assertIn("1500 W", review["description_placeholders"]["summary"])
        self.assertEqual((await self.flow.async_step_confirm())["type"], "form")
        result = await self.flow.async_step_confirm({})
        self.assertEqual(result["type"], "create_entry")
        self.assertEqual(result["data"]["grid_power"], "sensor.grid")

    async def test_optional_modules_can_be_skipped(self):
        await self.flow.async_step_user()
        await self.flow.async_step_grid({})
        await self.flow.async_step_solar({"solar_power": "sensor.pv"})
        await self.flow.async_step_home({})
        result = await self.flow.async_step_confirm({})
        self.assertIsNone(result["data"]["home_power"])

    async def test_empty_installation_cannot_be_saved_and_can_go_back(self):
        await self.flow.async_step_user()
        result = await self.flow.async_step_confirm({})
        self.assertEqual(result["errors"]["base"], "select_source")
        result = await self.flow.async_step_confirm({"back_to_review": True})
        self.assertEqual(result["step_id"], "review")

    async def test_options_keep_legacy_values_and_do_not_mutate_entry(self):
        original = {"grid_power": "sensor.grid", "solar_power": "sensor.pv"}
        entry = SimpleNamespace(data=original.copy(), options={})
        options = flow_module.EhomeEmsOptionsFlow()
        options.hass = self.hass
        options.config_entry = entry
        form = await options.async_step_init()
        suggested = {key.schema: key.description for key in form["data_schema"].schema}
        self.assertEqual(suggested["grid_power"]["suggested_value"], "sensor.grid")
        await options.async_step_grid({})
        self.assertIsNone(options._draft["grid_power"])
        self.assertEqual(options._draft["solar_power"], "sensor.pv")
        self.assertEqual(entry.data, original)
        self.assertEqual(entry.options, {})

    async def test_saved_options_take_precedence_including_cleared_keys(self):
        options = flow_module.EhomeEmsOptionsFlow()
        options.hass = self.hass
        options.config_entry = SimpleNamespace(
            data={"grid_power": "sensor.grid"},
            options={"grid_power": None, "solar_power": "sensor.pv"},
        )
        await options.async_step_init()
        self.assertIsNone(options._draft["grid_power"])

    async def test_duplicate_mapping_is_rejected_across_steps(self):
        await self.flow.async_step_user()
        await self.flow.async_step_grid({"grid_power": "sensor.grid"})
        result = await self.flow.async_step_solar({"solar_power": "sensor.grid"})
        self.assertEqual(result["errors"]["solar_power"], "duplicate_source")
        self.assertIsNone(self.flow._draft["solar_power"])

    async def test_wrong_unit_and_missing_sensor_are_rejected(self):
        await self.flow.async_step_user()
        self.states["sensor.energy"] = state("1", "kWh")
        for entity, error in (("sensor.energy", "unsupported_unit"), ("sensor.gone", "missing_source")):
            result = await self.flow.async_step_grid({"grid_power": entity})
            self.assertEqual(result["errors"]["grid_power"], error)

    async def test_ems_mirror_cannot_be_a_source_even_after_rename(self):
        await self.flow.async_step_user()
        self.registered["sensor.grid"] = SimpleNamespace(platform="ehome_ems")
        result = await self.flow.async_step_grid({"grid_power": "sensor.grid"})
        self.assertEqual(result["errors"]["grid_power"], "recursive_source")

    async def test_unavailable_reading_is_visible_and_does_not_become_zero(self):
        self.states["sensor.pv"] = state("unavailable", "W")
        review = await self.walk_to_review()
        self.assertIn("→ — [unavailable]", review["description_placeholders"]["summary"])
        self.assertEqual((await self.flow.async_step_confirm({}))["type"], "create_entry")

    async def test_source_removed_before_save_blocks_commit_and_allows_correction(self):
        await self.walk_to_review()
        del self.states["sensor.pv"]
        result = await self.flow.async_step_confirm({})
        self.assertEqual(result["errors"]["base"], "sources_changed")
        await self.flow.async_step_confirm({"back_to_review": True})
        result = await self.flow.async_step_solar({})
        self.assertEqual(result["step_id"], "review")
        self.assertEqual((await self.flow.async_step_confirm({}))["type"], "create_entry")

    async def test_edit_from_review_preserves_other_groups(self):
        await self.walk_to_review()
        result = await self.flow.async_step_home({})
        self.assertEqual(result["step_id"], "review")
        result = await self.flow.async_step_confirm({})
        self.assertEqual(result["data"]["solar_power"], "sensor.pv")
        self.assertIsNone(result["data"]["home_power"])

    async def add_battery(self, **overrides):
        self.states.update({"sensor.charge": state("0.5", "kW"),
                            "sensor.soc": state("65", "%")})
        await self.flow.async_step_add_battery()
        return await self.flow.async_step_add_battery(
            {"name": "Test battery", "charge_power": "sensor.charge",
             "soc": "sensor.soc", **overrides}
        )

    async def test_multiple_batteries_default_to_backup_with_stable_ids(self):
        await self.flow.async_step_user()
        await self.add_battery()
        first_id = next(iter(self.flow._draft["batteries"]))
        self.states["sensor.second_soc"] = state("30", "%")
        await self.flow.async_step_add_battery()
        result = await self.flow.async_step_add_battery(
            {"name": "Second battery", "soc": "sensor.second_soc", "role": "active"}
        )
        self.assertEqual(result["step_id"], "batteries")
        self.assertEqual(len(self.flow._draft["batteries"]), 2)
        self.assertEqual(self.flow._draft["batteries"][first_id]["role"], "backup")
        await self.flow.async_step_edit_battery({"battery_id": first_id})
        await self.flow.async_step_battery_details(
            {"name": "Renamed battery", "soc": "sensor.soc"}
        )
        self.assertEqual(self.flow._draft["batteries"][first_id]["name"], "Renamed battery")
        self.assertNotIn("charge_power", self.flow._draft["batteries"][first_id])

    async def test_battery_only_configuration_and_measured_units(self):
        await self.flow.async_step_user()
        self.states["sensor.energy"] = state("2500", "Wh")
        await self.add_battery(remaining_energy="sensor.energy", capacity_kwh=5.2)
        preview = (await self.flow.async_step_review())["description_placeholders"]["summary"]
        self.assertIn("65 %", preview)
        self.assertIn("2.5 kWh", preview)
        result = await self.flow.async_step_confirm({})
        self.assertEqual(result["type"], "create_entry")

    async def test_duplicate_sources_across_batteries_are_rejected(self):
        await self.flow.async_step_user()
        await self.add_battery()
        await self.flow.async_step_add_battery()
        result = await self.flow.async_step_add_battery({"name": "Duplicate", "soc": "sensor.soc"})
        self.assertEqual(result["errors"]["soc"], "duplicate_source")
        self.assertEqual(len(self.flow._draft["batteries"]), 1)

    async def test_battery_duplicate_with_house_and_wrong_soc_unit_rejected(self):
        await self.flow.async_step_user()
        await self.flow.async_step_grid({"grid_power": "sensor.grid"})
        result = await self.add_battery(charge_power="sensor.grid", soc="sensor.home")
        self.assertEqual(result["errors"]["charge_power"], "duplicate_source")
        self.assertEqual(result["errors"]["soc"], "unsupported_unit")

    async def test_battery_without_sources_and_invalid_capacity_are_rejected(self):
        await self.flow.async_step_user()
        await self.flow.async_step_add_battery()
        result = await self.flow.async_step_add_battery({"name": "Empty"})
        self.assertEqual(result["errors"]["base"], "select_source")
        for value in (0, -1, "nan", "inf", "abc"):
            result = await self.flow.async_step_add_battery(
                {"name": "Bad capacity", "capacity_kwh": value}
            )
            self.assertEqual(result["errors"]["base"], "invalid_battery")

    async def test_battery_edit_and_removal_do_not_mutate_saved_options(self):
        await self.flow.async_step_user()
        await self.add_battery()
        saved = (await self.flow.async_step_confirm({}))["data"]
        battery_id = next(iter(saved["batteries"]))
        options = flow_module.EhomeEmsOptionsFlow()
        options.hass = self.hass
        options.config_entry = SimpleNamespace(data={}, options=saved)
        await options.async_step_init()
        await options.async_step_remove_battery({"battery_id": battery_id})
        self.assertIn(battery_id, saved["batteries"])
        self.assertEqual(options._draft["batteries"], {})
        self.assertEqual((await options.async_step_confirm({}))["errors"]["base"], "select_source")

    async def test_remaining_energy_mapping_rejects_lifetime_energy(self):
        await self.flow.async_step_user()
        self.states["sensor.lifetime"] = state("2", "kWh")
        self.states["sensor.lifetime"].attributes["state_class"] = "total_increasing"
        result = await self.add_battery(remaining_energy="sensor.lifetime", capacity_kwh=8.2)
        self.assertEqual(result["errors"]["remaining_energy"], "cumulative_energy")
        self.assertEqual(self.flow._draft["batteries"], {})

    async def test_remaining_energy_mapping_rejects_stock_above_capacity(self):
        await self.flow.async_step_user()
        self.states["sensor.lifetime"] = state("305.799", "kWh")
        result = await self.add_battery(remaining_energy="sensor.lifetime", capacity_kwh=8.2)
        self.assertEqual(result["errors"]["remaining_energy"], "exceeds_capacity")

    async def test_saved_incoherent_energy_is_visible_and_can_be_cleared(self):
        await self.flow.async_step_user()
        self.states["sensor.energy"] = state("2", "kWh")
        await self.add_battery(remaining_energy="sensor.energy", capacity_kwh=8.2)
        battery_id = next(iter(self.flow._draft["batteries"]))
        self.states["sensor.energy"].state = "305.799"
        review = await self.flow.async_step_review()
        self.assertIn("[exceeds_capacity]", review["description_placeholders"]["summary"])
        self.assertEqual((await self.flow.async_step_confirm({}))["errors"]["base"], "sources_changed")
        await self.flow.async_step_edit_battery({"battery_id": battery_id})
        await self.flow.async_step_battery_details({"name": "Corrected", "soc": "sensor.soc"})
        self.assertEqual((await self.flow.async_step_confirm({}))["type"], "create_entry")

    async def test_home_mode_is_opt_in_and_legacy_sensor_is_preserved(self):
        await self.walk_to_review()
        result = await self.flow.async_step_confirm({})
        self.assertEqual(result["data"]["home_power_mode"], "existing")
        self.assertEqual(result["data"]["home_power"], "sensor.home")

    async def test_calculated_home_requires_boundary_confirmation(self):
        await self.flow.async_step_user()
        result = await self.flow.async_step_home({"home_power_mode": "calculated"})
        self.assertEqual(result["errors"]["home_boundary_confirmed"], "boundary_unconfirmed")

    async def test_calculated_home_preserves_settings_and_checks_missing_grid(self):
        await self.walk_to_review()
        await self.flow.async_step_home({"home_power_mode": "calculated", "home_has_solar": True,
                                        "home_has_storage": False, "home_boundary_confirmed": True})
        self.assertIsNone(self.flow._draft["home_power"])
        result = await self.flow.async_step_confirm({})
        self.assertEqual(result["errors"]["base"], "missing_source")

    async def test_usages_support_router_and_ev_and_keep_stable_ids(self):
        await self.flow.async_step_user()
        self.states.update({"sensor.router": state("350"), "sensor.ev": state("2", "kW"),
                            "switch.router": state("on", None)})
        for name, kind, source in (("Router", "solar_router", "sensor.router"), ("EV", "ev_charger", "sensor.ev")):
            await self.flow.async_step_add_usage()
            result = await self.flow.async_step_add_usage(
                {"name": name, "kind": kind, "power": source, "included_in_home": True}
            )
            self.assertEqual(result["step_id"], "usages")
        usage_id = next(iter(self.flow._draft["usages"]))
        await self.flow.async_step_edit_usage({"usage_id": usage_id})
        await self.flow.async_step_usage_details(
            {"name": "Renamed router", "kind": "solar_router", "status": "switch.router", "included_in_home": True}
        )
        self.assertEqual(len(self.flow._draft["usages"]), 2)
        self.assertEqual(self.flow._draft["usages"][usage_id]["name"], "Renamed router")
        self.assertNotIn("power", self.flow._draft["usages"][usage_id])

    async def test_usage_boundary_sources_and_period_are_checked(self):
        await self.flow.async_step_user()
        self.states["sensor.load"] = state("100")
        await self.flow.async_step_add_usage()
        result = await self.flow.async_step_add_usage({"name": "No boundary", "power": "sensor.load"})
        self.assertEqual(result["errors"]["included_in_home"], "outside_home")
        result = await self.flow.async_step_add_usage({"name": "No reading", "included_in_home": True})
        self.assertEqual(result["errors"]["base"], "select_source")
        result = await self.flow.async_step_add_usage(
            {"name": "Bad energy", "energy": "sensor.load", "included_in_home": True}
        )
        self.assertEqual(result["errors"]["energy"], "unsupported_unit")

    async def test_usage_removal_is_only_saved_at_confirmation(self):
        await self.flow.async_step_user()
        self.states["sensor.load"] = state("100")
        await self.flow.async_step_add_usage()
        await self.flow.async_step_add_usage({"name": "Load", "power": "sensor.load", "included_in_home": True})
        saved = (await self.flow.async_step_confirm({}))["data"]
        usage_id = next(iter(saved["usages"]))
        options = flow_module.EhomeEmsOptionsFlow()
        options.hass = self.hass
        options.config_entry = SimpleNamespace(data={}, options=saved)
        await options.async_step_init()
        await options.async_step_remove_usage({"usage_id": usage_id})
        self.assertIn(usage_id, saved["usages"])
        self.assertEqual(options._draft["usages"], {})
