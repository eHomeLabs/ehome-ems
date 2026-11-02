"""Source-remapping validation contracts; full transport is tested in HA smoke."""
from datetime import datetime, timezone
import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
from test_config_flow import flow_module, state


class SourceEditorTests(TestCase):
    def setUp(self):
        package = ModuleType("ems_editor_test")
        package.__path__ = [str(Path(__file__).resolve().parents[1] / "custom_components/ehome_ems")]
        helper = ModuleType("ems_editor_test.dashboard_service")
        config = ModuleType("ems_editor_test.config_flow")
        config.PowerWizard = flow_module.PowerWizard
        registry_module = ModuleType("homeassistant.helpers.entity_registry")
        registry_module.async_get = lambda hass: hass.registry
        modules = {"ems_editor_test": package, "ems_editor_test.dashboard_service": helper,
                   "ems_editor_test.config_flow": config,
                   "homeassistant": ModuleType("homeassistant"),
                   "homeassistant.helpers": ModuleType("homeassistant.helpers"),
                   "homeassistant.helpers.entity_registry": registry_module}
        patches = patch.dict(sys.modules, modules)
        patches.start()
        self.addCleanup(patches.stop)
        self.editor = importlib.import_module("ems_editor_test.source_editor")
        self.entry = SimpleNamespace(entry_id="entry", modified_at=datetime.now(timezone.utc),
                                     options={}, data={"solar_power": "sensor.old", "home_power": "sensor.home"})
        self.states = {"sensor.old": state("100"), "sensor.new": state("250"),
                       "sensor.home": state("400"), "sensor.energy": state("1", "kWh"),
                       "sensor.mirror": state("100")}
        self.writes = []
        self.hass = SimpleNamespace(
            states=SimpleNamespace(get=self.states.get),
            registry=SimpleNamespace(
                async_get_entity_id=lambda domain, platform, uid: {
                    "entry_solar_power": "sensor.mirror", "entry_home_power": "sensor.home_mirror"
                }.get(uid),
                async_get=lambda entity: SimpleNamespace(platform="ehome_ems") if entity == "sensor.mirror" else None),
            config_entries=SimpleNamespace(async_update_entry=lambda entry, **kwargs: self.writes.append(kwargs)),
        )
        helper.dashboard_snapshot = lambda *args: {"bindings": self.editor.binding_metadata(
            self.entry.options or self.entry.data, {"solar_power": "sensor.mirror", "home_power": "sensor.home_mirror"})}

    def test_temperature_remapping_offers_helpers_without_expanding_power_domains(self):
        mapping={'usages':{'h':{'name':'Water heater','temperature':'sensor.water'}}}
        metadata=self.editor.binding_metadata(mapping,{'usage_h_temperature':'sensor.mirror'})
        self.assertEqual(metadata['sensor.mirror']['domains'],['sensor','input_number'])
        self.assertEqual(metadata['sensor.mirror']['units'],['°C','°F'])
        power=self.editor.binding_metadata({'home_power':'sensor.home'},{'home_power':'sensor.power'})
        self.assertEqual(power['sensor.power']['domains'],['sensor'])

    def remap(self, source="sensor.new", revision=None, expected="sensor.old", mirror="sensor.mirror"):
        return self.editor.remap_source(self.hass, self.entry, mirror, source, expected,
                                        revision or self.entry.modified_at.isoformat())

    def test_valid_replacement_preserves_original_data_and_other_associations(self):
        self.assertIsNone(self.remap())
        self.assertEqual(self.writes[0]["options"]["solar_power"], "sensor.new")
        self.assertEqual(self.writes[0]["options"]["home_power"], "sensor.home")
        self.assertEqual(self.entry.data["solar_power"], "sensor.old")

    def test_stale_revision_or_source_never_overwrites_changes(self):
        self.assertEqual(self.remap(revision="old"), "conflict")
        self.assertEqual(self.remap(expected="sensor.other"), "conflict")
        self.assertFalse(self.writes)

    def test_units_duplicates_and_own_mirrors_are_refused(self):
        self.assertEqual(self.remap("sensor.energy"), "unsupported_unit")
        self.assertEqual(self.remap("sensor.home"), "duplicate_source")
        self.assertEqual(self.remap("sensor.mirror"), "recursive_source")
        self.assertFalse(self.writes)

    def test_missing_sources_and_foreign_targets_are_refused(self):
        self.assertEqual(self.remap("sensor.missing"), "invalid_source")
        self.assertEqual(self.remap(mirror="sensor.not_ours"), "conflict")
        self.assertFalse(self.writes)

    def test_calculated_home_can_explicitly_switch_to_existing_source(self):
        self.entry.data = {"home_power_mode": "calculated", "home_power": None}
        self.assertIsNone(self.remap(mirror="sensor.home_mirror", expected=None))
        self.assertEqual(self.writes[0]["options"]["home_power_mode"], "existing")
        self.assertEqual(self.writes[0]["options"]["home_power"], "sensor.new")
