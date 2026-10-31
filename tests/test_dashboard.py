"""Dashboard generation contracts using simulated mappings and registered IDs."""
from copy import deepcopy
import importlib
from pathlib import Path
import sys
from types import ModuleType
from unittest import TestCase
from unittest.mock import patch

package = ModuleType("ems_dashboard_test")
package.__path__ = [str(Path(__file__).resolve().parents[1] / "custom_components/ehome_ems")]
with patch.dict(sys.modules, {"ems_dashboard_test": package}):
    build = importlib.import_module("ems_dashboard_test.dashboard").build_dashboard


def cards(config):
    for view in config["dashboard"]["views"]:
        yield from walk_cards(view["cards"])


def walk_cards(items):
    for card in items:
        yield card
        yield from walk_cards(card.get("cards", []))


class DashboardTests(TestCase):
    def test_renamed_mirrors_are_used_instead_of_sources(self):
        config = build({"grid_power": "sensor.original"}, {"grid_power": "sensor.renamed_mirror"})
        gauges = [card for card in cards(config) if card["type"] == "gauge"]
        self.assertEqual(gauges[0]["entity"], "sensor.renamed_mirror")
        self.assertEqual((gauges[0]["min"], gauges[0]["max"]), (-10000, 10000))
        self.assertNotIn("sensor.original", str(config))

    def test_empty_modules_and_missing_mirrors_are_not_invented(self):
        config = build({"solar_power": "sensor.original"}, {})
        self.assertEqual(config["missing_entities"], ["solar_power"])
        self.assertEqual(len(config["dashboard"]["views"]), 1)
        self.assertFalse(any(card["type"] == "gauge" for card in cards(config)))

    def test_battery_scales_do_not_mix_power_soc_and_energy(self):
        mapping = {"batteries": {"stable": {"name": "Storage", "role": "backup",
                   "coupling": "ac", "capacity_kwh": 5.2, "soc": "sensor.original",
                   "remaining_energy": "sensor.energy", "charge_power": "sensor.charge"}}}
        entities = {"stable_soc": "sensor.soc_mirror", "stable_remaining_energy": "sensor.energy_mirror",
                    "stable_charge_power": "sensor.charge_mirror"}
        config = build(mapping, entities, max_power_w=8000)
        gauges = {card["entity"]: card for card in cards(config) if card["type"] == "gauge"}
        self.assertEqual(gauges["sensor.soc_mirror"]["max"], 100)
        self.assertEqual(gauges["sensor.energy_mirror"]["max"], 5.2)
        self.assertEqual(gauges["sensor.charge_mirror"]["max"], 8000)
        history = [card for card in cards(config) if card["type"] == "history-graph"][0]
        self.assertEqual(history["entities"], ["sensor.charge_mirror"])
        self.assertIn("Secours", str(config))

    def test_remaining_energy_without_capacity_is_still_visible_without_a_fake_gauge(self):
        mapping = {"batteries": {"id": {"name": "Storage", "role": "active", "coupling": "dc",
                                      "remaining_energy": "sensor.original"}}}
        config = build(mapping, {"id_remaining_energy": "sensor.mirror"})
        self.assertIn("sensor.mirror", str(config))
        self.assertFalse(any(card["type"] == "gauge" for card in cards(config)))
        self.assertIn("Stockage", config["dashboard"]["views"][0]["cards"][-1]["content"])

    def test_generation_never_mutates_its_inputs_or_returns_shared_lists(self):
        mapping = {"home_power": "sensor.source"}
        entities = {"home_power": "sensor.mirror"}
        before = deepcopy((mapping, entities))
        first = build(mapping, entities)
        first["dashboard"]["views"].clear()
        second = build(mapping, entities)
        self.assertEqual((mapping, entities), before)
        self.assertTrue(second["dashboard"]["views"])

    def test_export_is_an_editable_native_dashboard_with_no_commands(self):
        config = build({"home_power": "sensor.original"}, {"home_power": "sensor.mirror"})
        self.assertIn("title", config["dashboard"])
        self.assertNotIn("strategy", config["dashboard"])
        self.assertNotIn("call-service", str(config))
        self.assertNotIn("perform-action", str(config))
        self.assertFalse(any(card["type"].startswith("custom:") for card in cards(config)))

    def test_language_is_selected_and_falls_back(self):
        self.assertEqual(build({}, {}, language="en")["dashboard"]["views"][0]["title"], "Overview")
        self.assertEqual(build({}, {}, language="unknown")["dashboard"]["views"][0]["title"], "Synthèse")

    def test_history_and_quality_keep_unavailable_readings_as_entity_references(self):
        config = build({"home_power": "sensor.source"}, {"home_power": "sensor.mirror"})
        self.assertNotIn("state", str(config))
        attributes = [row for card in cards(config) for row in card.get("entities", [])
                      if isinstance(row, dict) and row.get("type") == "attribute"]
        self.assertEqual(attributes[0]["attribute"], "data_quality")
        self.assertEqual(attributes[0]["entity"], "sensor.mirror")
