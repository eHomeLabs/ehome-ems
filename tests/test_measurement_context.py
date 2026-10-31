"""Preparation tests: no HA instance, services, timers or real entity inventory."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import importlib
from pathlib import Path
import sys
from types import ModuleType
from unittest import TestCase
from zoneinfo import ZoneInfo

package = ModuleType("ems_context_test")
package.__path__ = [str(Path(__file__).resolve().parents[1] / "custom_components/ehome_ems")]
sys.modules[package.__name__] = package
context = importlib.import_module("ems_context_test.measurement_context")
NOW = datetime(2026, 10, 31, 12, tzinfo=timezone.utc)


def sample(value, unit="W", age=0):
    return context.SourceSample(value, unit, NOW - timedelta(seconds=age))


def fixture():
    mapping = {"home_power_mode": "existing", "home_power": "sensor.test_home",
               "grid_import": "sensor.test_import", "grid_export": "sensor.test_export",
               "solar_power": "sensor.test_solar", "home_has_solar": True,
               "home_has_storage": True, "home_boundary_confirmed": True,
               "home_boundary": {"mode": "excludes_usages", "confirmed": True,
                                 "excluded_usage_ids": ["heater"], "disjoint_confirmed": True},
               "batteries": {"active": {"name": "Storage", "role": "active", "coupling": "ac",
                                          "charge_power": "sensor.test_charge", "discharge_power": "sensor.test_discharge"}},
               "usages": {"heater": {"power": "sensor.test_heater"}}}
    readings = {"sensor.test_home": sample(500), "sensor.test_heater": sample(700),
                "sensor.test_import": sample(0), "sensor.test_export": sample(200),
                "sensor.test_solar": sample(2.4, "kW"), "sensor.test_charge": sample(1000),
                "sensor.test_discharge": sample(0)}
    return mapping, readings


class MeasurementContextTests(TestCase):
    def test_external_home_excluding_heater_is_reconstructed_once(self):
        mapping, readings = fixture()
        before = deepcopy(mapping), deepcopy(readings)
        result = context.home_total(mapping, readings, now=NOW)
        self.assertEqual((result["source_w"], result["total_w"]), (500, 1200))
        self.assertEqual(result["origin"], "external_plus_exclusions")
        self.assertEqual((mapping, readings), before)

    def test_declared_total_does_not_add_submeters(self):
        mapping, readings = fixture()
        mapping["home_boundary"] = {"mode": "total", "confirmed": True}
        readings["sensor.test_home"] = sample(1200)
        self.assertEqual(context.home_total(mapping, readings, now=NOW)["total_w"], 1200)

    def test_boundary_and_overlap_must_be_confirmed(self):
        for key, reason in [("confirmed", "boundary_unconfirmed"), ("disjoint_confirmed", "overlap_unconfirmed")]:
            mapping, readings = fixture()
            mapping["home_boundary"][key] = False
            result = context.home_total(mapping, readings, now=NOW)
            self.assertEqual(result["quality"], reason)
            self.assertIsNone(result["total_w"])

    def test_duplicate_or_unknown_exclusions_block_reconstruction(self):
        for ids, reason in [(["heater", "heater"], "duplicate_exclusion"), (["unknown"], "unknown_excluded_usage")]:
            mapping, readings = fixture()
            mapping["home_boundary"]["excluded_usage_ids"] = ids
            self.assertEqual(context.home_total(mapping, readings, now=NOW)["quality"], reason)
        mapping["home_boundary"]["excluded_usage_ids"] = ["heater"]
        mapping["usages"]["heater"]["power"] = "sensor.test_home"
        self.assertEqual(context.home_total(mapping, readings, now=NOW)["quality"], "duplicate_source")

    def test_missing_heater_never_becomes_zero(self):
        mapping, readings = fixture()
        readings.pop("sensor.test_heater")
        result = context.home_total(mapping, readings, now=NOW)
        self.assertIsNone(result["total_w"])
        self.assertEqual(result["quality"], "unavailable")

    def test_unavailable_wrong_unit_negative_and_boolean_refused(self):
        for value, unit, reason in [("unavailable", "W", "unavailable"), (700, "kWh", "unsupported_unit"),
                                    (-1, "W", "unexpected_direction"), (True, "W", "invalid_value")]:
            mapping, readings = fixture()
            readings["sensor.test_heater"] = sample(value, unit)
            self.assertEqual(context.home_total(mapping, readings, now=NOW)["quality"], reason)

    def test_stale_unknown_future_and_naive_publication_times_block(self):
        for stamp, reason in [(NOW - timedelta(seconds=301), "stale_source"),
                              (NOW + timedelta(seconds=1), "future_timestamp"),
                              (None, "unknown_age"), (NOW.replace(tzinfo=None), "unknown_age")]:
            mapping, readings = fixture()
            readings["sensor.test_heater"] = context.SourceSample(700, "W", stamp)
            self.assertEqual(context.home_total(mapping, readings, now=NOW)["quality"], reason)

    def test_freshness_bound_is_inclusive(self):
        _, readings = fixture()
        readings["sensor.test_heater"] = sample(700, age=300)
        self.assertEqual(context.fresh_power("sensor.test_heater", "home_power", readings, now=NOW).value, 700)

    def test_daylight_saving_fold_is_measured_in_utc(self):
        paris = ZoneInfo("Europe/Paris")
        reported = datetime(2026, 10, 25, 2, 30, tzinfo=paris, fold=0)
        now = datetime(2026, 10, 25, 2, 30, tzinfo=paris, fold=1)
        result = context.fresh_power("sensor.a", "home_power", {"sensor.a": context.SourceSample(700, "W", reported)}, now=now)
        self.assertEqual(result.quality, "stale_source")

    def test_calculated_home_already_includes_heater(self):
        mapping, readings = fixture()
        mapping["home_power_mode"] = "calculated"
        mapping.pop("home_boundary")
        self.assertEqual(context.home_total(mapping, readings, now=NOW)["total_w"], 1200)
        mapping["home_boundary"] = {"mode": "excludes_usages", "excluded_usage_ids": ["heater"]}
        self.assertEqual(context.home_total(mapping, readings, now=NOW)["quality"], "calculated_boundary_conflict")

    def test_export_is_not_increased_by_storage_charge_or_routed_loads(self):
        mapping, readings = fixture()
        result = context.export_context(mapping, readings, now=NOW)
        self.assertEqual(result["quality"], "valid_export_snapshot")
        self.assertEqual(result["scenario_export_ceiling_w"], 200)
        self.assertEqual(result["balance_residual_w"], 0)
        self.assertIsNone(result["reallocatable_power_w"])
        self.assertFalse(result["commands_allowed"])

    def test_export_sign_is_normalized_without_guessing_import_convention(self):
        mapping, readings = fixture()
        readings["sensor.test_export"] = sample(-200)
        self.assertEqual(context.export_context(mapping, readings, now=NOW)["scenario_export_ceiling_w"], 200)
        readings["sensor.test_import"] = sample(-1)
        self.assertEqual(context.export_context(mapping, readings, now=NOW)["quality"], "unexpected_direction")

    def test_report_spread_blocks_even_when_each_sample_is_fresh(self):
        mapping, readings = fixture()
        readings["sensor.test_export"] = sample(200, age=31)
        result = context.export_context(mapping, readings, now=NOW)
        self.assertEqual(result["quality"], "reports_not_aligned")
        self.assertIsNone(result["scenario_export_ceiling_w"])

    def test_balance_mismatch_is_diagnostic_not_corrected_to_zero(self):
        mapping, readings = fixture()
        readings["sensor.test_home"] = sample(600)
        result = context.export_context(mapping, readings, now=NOW)
        self.assertEqual((result["quality"], result["balance_residual_w"]), ("balance_mismatch", 100))
        self.assertIsNone(result["scenario_export_ceiling_w"])

    def test_even_one_watt_of_battery_discharge_does_not_certify_solar_export(self):
        mapping, readings = fixture()
        readings["sensor.test_discharge"] = sample(1)
        readings["sensor.test_home"] = sample(501)
        self.assertEqual(context.export_context(mapping, readings, now=NOW)["quality"], "battery_origin_uncertain")

    def test_simultaneous_exchange_is_not_supported_by_simple_context(self):
        mapping, readings = fixture()
        readings["sensor.test_import"] = sample(1)
        readings["sensor.test_home"] = sample(501)
        self.assertEqual(context.export_context(mapping, readings, now=NOW)["quality"], "simultaneous_exchange")

    def test_zero_export_with_charging_storage_is_zero_not_hidden_surplus(self):
        mapping, readings = fixture()
        readings["sensor.test_export"] = sample(0)
        readings["sensor.test_home"] = sample(700)
        result = context.export_context(mapping, readings, now=NOW)
        self.assertEqual(result["scenario_export_ceiling_w"], 0)
        self.assertIsNone(result["reallocatable_power_w"])

    def test_backup_excluded_dc_and_duplicate_measurements_block(self):
        mapping, readings = fixture()
        mapping["batteries"]["backup"] = {"role": "backup", "coupling": "dc"}
        self.assertEqual(context.export_context(mapping, readings, now=NOW)["quality"], "valid_export_snapshot")
        mapping["batteries"]["active"]["coupling"] = "dc"
        self.assertEqual(context.export_context(mapping, readings, now=NOW)["quality"], "unsupported_topology")
        mapping["batteries"]["active"]["coupling"] = "ac"
        mapping["home_power"] = "sensor.test_import"
        self.assertEqual(context.export_context(mapping, readings, now=NOW)["quality"], "duplicate_source")

    def test_invalid_time_and_windows_are_rejected(self):
        mapping, readings = fixture()
        for options in [{"max_age_seconds": True}, {"max_age_seconds": 29}, {"max_span_seconds": -1},
                        {"max_span_seconds": 301}, {"tolerance_w": -1}, {"tolerance_w": True}]:
            with self.assertRaises(ValueError):
                context.export_context(mapping, readings, now=NOW, **options)
        with self.assertRaises(ValueError):
            context.home_total(mapping, readings, now=NOW.replace(tzinfo=None))

    def test_report_span_and_balance_tolerance_boundaries(self):
        mapping, readings = fixture()
        readings["sensor.test_export"] = sample(200, age=30)
        readings["sensor.test_home"] = sample(550)
        self.assertEqual(context.export_context(mapping, readings, now=NOW)["quality"], "valid_export_snapshot")
        readings["sensor.test_home"] = sample(550.01)
        self.assertEqual(context.export_context(mapping, readings, now=NOW)["quality"], "balance_mismatch")

    def test_fractional_export_is_never_rounded_up_into_integer_scenario(self):
        mapping, readings = fixture()
        readings["sensor.test_export"] = sample(200.99)
        readings["sensor.test_home"] = sample(499.01)
        result = context.export_context(mapping, readings, now=NOW)
        self.assertEqual(result["scenario_export_ceiling_w"], 200)
        self.assertEqual(result["export_observed_w"], 200.99)

    def test_missing_or_malformed_export_never_yields_a_budget(self):
        for invalid in [None, context.SourceSample(200, [], NOW), context.SourceSample(200, None, NOW)]:
            mapping, readings = fixture()
            readings["sensor.test_export"] = invalid
            result = context.export_context(mapping, readings, now=NOW)
            self.assertIsNone(result["scenario_export_ceiling_w"])
            self.assertIsNone(result["reallocatable_power_w"])
            self.assertFalse(result["commands_allowed"])
