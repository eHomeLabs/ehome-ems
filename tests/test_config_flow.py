"""Wizard contract tests with real schemas and small HA API doubles.

These tests exercise flow transitions and persistence boundaries, not a running HA.
"""
import importlib
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

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
        if not isinstance(value, str) or not value.startswith("sensor."):
            raise ValueError(value)
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
        return await self.flow.async_step_home({"home_power": "sensor.home"})

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
