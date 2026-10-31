"""Response-only action contract tests; no running Home Assistant."""
import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch
import voluptuous as vol

modules = {name: ModuleType(name) for name in (
    "homeassistant", "homeassistant.core", "homeassistant.exceptions",
    "homeassistant.helpers", "homeassistant.helpers.entity_registry", "ems_action_test",
)}
modules["ems_action_test"].__path__ = [
    str(Path(__file__).resolve().parents[1] / "custom_components/ehome_ems")
]
modules["homeassistant.core"].SupportsResponse = SimpleNamespace(ONLY="only")
modules["homeassistant.exceptions"].HomeAssistantError = RuntimeError
modules["homeassistant.helpers.entity_registry"].async_get = lambda hass: hass.registry
with patch.dict(sys.modules, modules):
    service = importlib.import_module("ems_action_test.dashboard_service")


class Services:
    def __init__(self):
        self.registered = []

    def has_service(self, domain, name):
        return bool(self.registered)

    def async_register(self, domain, name, handler, **kwargs):
        self.registered.append((domain, name, handler, kwargs))


class DashboardServiceTests(IsolatedAsyncioTestCase):
    def setUp(self):
        self.entry = SimpleNamespace(entry_id="entry", options={}, data={"home_power": "sensor.source"})
        self.entries = [self.entry]
        self.registered = SimpleNamespace(disabled_by=None, config_entry_id="entry")
        self.hass = SimpleNamespace(
            services=Services(),
            config_entries=SimpleNamespace(async_entries=lambda domain: self.entries),
            config=SimpleNamespace(language="en"),
            registry=SimpleNamespace(
                async_get_entity_id=lambda domain, platform, uid: "sensor.renamed",
                async_get=lambda entity_id: self.registered,
            ),
        )
        service.register_dashboard_service(self.hass)
        _, _, self.handler, self.settings = self.hass.services.registered[0]

    async def test_response_only_registration_is_idempotent(self):
        service.register_dashboard_service(self.hass)
        self.assertEqual(len(self.hass.services.registered), 1)
        self.assertEqual(self.settings["supports_response"], "only")

    async def test_current_registry_ids_and_locale_are_used(self):
        result = await self.handler(SimpleNamespace(data={}))
        self.assertIn("sensor.renamed", str(result))
        self.assertEqual(result["dashboard"]["views"][0]["title"], "Overview")
        self.assertEqual(self.entry.data, {"home_power": "sensor.source"})
        self.assertEqual(result["version"], "0.2.0b9")
        self.assertEqual(result["managed_url"], "/ehome-ems-entry")
        self.assertIn("/ehome-ems-entry", result["dashboard"]["views"][0]["cards"][0]["content"])

    async def test_disabled_or_other_entry_entities_are_reported_missing(self):
        for disabled, entry_id in (("user", "entry"), (None, "other")):
            self.registered.disabled_by = disabled
            self.registered.config_entry_id = entry_id
            result = await self.handler(SimpleNamespace(data={}))
            self.assertEqual(result["missing_entities"], ["home_power"])
            self.assertNotIn("sensor.source", str(result))

    async def test_no_entry_and_wrong_entry_fail_clearly(self):
        with self.assertRaises(RuntimeError):
            await self.handler(SimpleNamespace(data={"entry_id": "other"}))
        self.entries.clear()
        with self.assertRaises(RuntimeError):
            await self.handler(SimpleNamespace(data={}))

    async def test_options_override_original_sources(self):
        self.entry.options = {"solar_power": "sensor.new_source"}
        self.hass.registry.async_get_entity_id = lambda domain, platform, uid: None
        result = await self.handler(SimpleNamespace(data={}))
        self.assertEqual(result["missing_entities"], ["solar_power"])

    async def test_computed_home_suffix_is_resolved(self):
        self.entry.options = {"home_power_mode": "calculated", "home_power": None}
        result = await self.handler(SimpleNamespace(data={}))
        self.assertIn("sensor.renamed", str(result))
        self.assertEqual(result["flow"]["entities"]["home_power"], "sensor.renamed")
        self.assertTrue(result["flow"]["home_calculated"])

    async def test_flow_uses_mirror_ids_and_keeps_equipment_separate(self):
        self.entry.options = {"home_power": "sensor.external", "batteries": {
            "a": {"name": "Storage", "role": "backup", "coupling": "dc", "soc": "sensor.raw_soc"}},
            "usages": {"b": {"name": "Heater", "kind": "solar_router", "power": "sensor.raw_heater"}}}
        result = await self.handler(SimpleNamespace(data={}))
        self.assertFalse(result["flow"]["home_calculated"])
        self.assertEqual(result["flow"]["batteries"][0]["role"], "backup")
        self.assertEqual(result["flow"]["usages"][0]["power"], "sensor.renamed")
        self.assertNotIn("sensor.raw_heater", str(result["flow"]))

    async def test_display_scale_and_language_schema(self):
        schema = self.settings["schema"]
        self.assertEqual(schema({"max_power_w": 5000})["max_power_w"], 5000)
        for value in ("nan", "inf", 0, -1, 1000001):
            with self.assertRaises(vol.Invalid):
                schema({"max_power_w": value})
        with self.assertRaises(vol.Invalid):
            schema({"language": "invalid"})
