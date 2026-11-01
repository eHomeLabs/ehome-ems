"""Conservation, bounds and configuration tests for hypothetical allocation."""
from copy import deepcopy
from datetime import datetime, timezone, timedelta
import importlib.util
from pathlib import Path
from random import Random
from types import SimpleNamespace
import unittest

spec = importlib.util.spec_from_file_location("scenario_test", Path(__file__).resolve().parents[1] / "custom_components/ehome_ems/simulation.py")
scenario = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scenario)


def mapping():
    return {"home_power": "sensor.sim_home", "batteries": {
        "active": {"name": "Storage", "role": "active", "coupling": "ac"},
        "backup": {"name": "Backup", "role": "backup", "coupling": "ac"},
        "dc": {"name": "DC", "role": "active", "coupling": "dc"}},
        "usages": {"heater": {"name": "Heater", "kind": "solar_router"}, "car": {"name": "EV", "kind": "ev_charger"}}}


def target(identifier, minimum, maximum, enabled=True):
    return {"id": identifier, "enabled": enabled, "min_w": minimum, "max_w": maximum}


def configured(targets):
    result = mapping()
    result["simulation"] = {"schema_version": 1, "targets": targets}
    return result


class SimulationTests(unittest.TestCase):
    def test_defaults_never_enable_devices_or_include_backup_and_dc(self):
        result = scenario.plan(mapping())
        self.assertEqual([item["id"] for item in result["targets"]], ["battery:active", "usage:heater", "usage:car"])
        self.assertFalse(any(item["enabled"] for item in result["targets"]))
        self.assertEqual(scenario.allocate(mapping(), 2000)["remaining_w"], 2000)

    def test_priority_budget_is_not_allocated_twice_and_mapping_is_unchanged(self):
        value = configured([target("battery:active", 0, 1000), target("usage:heater", 800, 1800), target("usage:car", 1400, 7000)])
        before = deepcopy(value)
        result = scenario.allocate(value, 2100)
        self.assertEqual([item["allocated_w"] for item in result["targets"]], [1000, 1100, 0])
        self.assertEqual(result["remaining_w"], 0)
        self.assertFalse(result["commands_sent"])
        self.assertEqual(value, before)

    def test_below_minimum_is_skipped_for_next_priority(self):
        value = configured([target("usage:heater", 800, 1800), target("battery:active", 0, 1000), target("usage:car", 1400, 7000)])
        result = scenario.allocate(value, 500)
        self.assertEqual([item["allocated_w"] for item in result["targets"]], [0, 500, 0])
        self.assertEqual(result["targets"][0]["reason"], "below_minimum")

    def test_disabled_and_ceiling_leave_explicit_remainder(self):
        value = configured([target("battery:active", 0, 1000, False), target("usage:heater", 800, 1800), target("usage:car", 1400, 7000, False)])
        result = scenario.allocate(value, 2500)
        self.assertEqual(result["allocated_w"], 1800)
        self.assertEqual(result["remaining_w"], 700)

    def test_unknown_duplicate_missing_and_ineligible_ids_rejected(self):
        baseline = [target("battery:active", 0, 1000), target("usage:heater", 800, 1800), target("usage:car", 1400, 7000)]
        for replacement in ["battery:backup", "battery:dc", "usage:absent", "usage:heater"]:
            invalid = deepcopy(baseline)
            invalid[0]["id"] = replacement
            with self.assertRaises(ValueError):
                scenario.validate_targets(mapping(), invalid)
        with self.assertRaises(ValueError):
            scenario.validate_targets(mapping(), baseline[:-1])

    def test_invalid_limits_and_types_rejected(self):
        baseline = [target("battery:active", 0, 1000), target("usage:heater", 800, 1800), target("usage:car", 1400, 7000)]
        for key, value in [("min_w", -1), ("min_w", 1001), ("max_w", 0), ("max_w", 1000001), ("max_w", True), ("max_w", 1.5), ("enabled", "true")]:
            invalid = deepcopy(baseline)
            invalid[0][key] = value
            with self.assertRaises(ValueError):
                scenario.validate_targets(mapping(), invalid)

    def test_invalid_budgets_never_coerce_to_watts(self):
        for budget in [-1, 1000001, True, 1.2, "100", None, float("nan"), float("inf")]:
            with self.assertRaises(ValueError):
                scenario.allocate(mapping(), budget)

    def test_removed_targets_dropped_and_new_targets_disabled(self):
        value = configured([target("usage:gone", 0, 1000), target("usage:heater", 800, 1800)])
        result = scenario.plan(value)["targets"]
        self.assertEqual(result[0]["id"], "usage:heater")
        self.assertTrue(result[0]["enabled"])
        self.assertFalse(result[1]["enabled"])
        self.assertFalse(result[2]["enabled"])
        for corrupt in [None, {"schema_version": 1, "targets": None}, {"schema_version": 1, "targets": [{"id": []}]}, {"schema_version": 9, "targets": []}]:
            value["simulation"] = corrupt
            self.assertFalse(any(item["enabled"] for item in scenario.plan(value)["targets"]))

    def test_save_preserves_sources_and_refuses_stale_revision(self):
        entry = SimpleNamespace(data=mapping(), options={}, modified_at=datetime.now(timezone.utc))
        writes = []
        def update(entry, options):
            writes.append(options)
            entry.options = options
            entry.modified_at += timedelta(seconds=1)
        hass = SimpleNamespace(config_entries=SimpleNamespace(async_update_entry=update))
        targets = [target("battery:active", 0, 1000), target("usage:heater", 800, 1800), target("usage:car", 1400, 7000)]
        revision = entry.modified_at.isoformat()
        scenario.save_plan(hass, entry, targets, revision)
        self.assertEqual(writes[0]["home_power"], "sensor.sim_home")
        self.assertNotIn("simulation", entry.data)
        with self.assertRaisesRegex(ValueError, "conflict"):
            scenario.save_plan(hass, entry, targets, revision)
        self.assertEqual(len(writes), 1)

    def test_many_scenarios_conserve_budget_and_respect_each_limit(self):
        random = Random(17)
        for _ in range(200):
            targets = []
            for identifier in ["battery:active", "usage:heater", "usage:car"]:
                maximum = random.randint(1, 10000)
                targets.append(target(identifier, random.randint(0, maximum), maximum, random.choice([True, False])))
            random.shuffle(targets)
            value = configured(scenario.validate_targets(mapping(), targets))
            budget = random.randint(0, 30000)
            result = scenario.allocate(value, budget)
            self.assertEqual(sum(item["allocated_w"] for item in result["targets"]) + result["remaining_w"], budget)
            for item in result["targets"]:
                self.assertLessEqual(item["allocated_w"], item["max_w"])
                if item["allocated_w"]:
                    self.assertTrue(item["enabled"])
                    self.assertGreaterEqual(item["allocated_w"], item["min_w"])
