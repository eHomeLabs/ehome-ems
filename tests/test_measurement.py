"""Run with python -m unittest discover -s tests -v; no HA dependency."""
import importlib.util
from pathlib import Path
import sys
import unittest

path = Path(__file__).resolve().parents[1] / "custom_components/ehome_ems/measurement.py"
spec = importlib.util.spec_from_file_location("ems_measurement", path)
measurement = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = measurement
spec.loader.exec_module(measurement)
normalize = measurement.normalize_power


class PowerNormalizationTests(unittest.TestCase):
    def test_kw_and_signed_grid(self):
        self.assertEqual(normalize("-1.25", "kW", "grid_power").value, -1250)
        self.assertEqual(normalize("0", "W", "home_power").value, 0)

    def test_export_accepts_both_conventions(self):
        for value in ("250", "-250"):
            self.assertEqual(normalize(value, "W", "grid_export").value, 250)

    def test_direction_errors_are_not_zero(self):
        for role in ("grid_import", "solar_power", "home_power"):
            reading = normalize("-1", "W", role)
            self.assertIsNone(reading.value)
            self.assertEqual(reading.quality, "unexpected_direction")

    def test_unavailable_is_not_zero(self):
        for raw in (None, "unknown", "unavailable"):
            self.assertEqual(normalize(raw, "W", "grid_power").quality, "unavailable")

    def test_invalid_and_nonfinite_values(self):
        for raw in ("abc", "nan", "inf", "-inf", "1e999", object()):
            reading = normalize(raw, "W", "grid_power")
            self.assertIsNone(reading.value)
            self.assertEqual(reading.quality, "invalid_value")

    def test_energy_and_missing_units_rejected(self):
        for unit in ("Wh", "kWh", None, "MW"):
            self.assertEqual(normalize("1", unit, "solar_power").quality, "unsupported_unit")

    def test_rounding_after_conversion(self):
        self.assertEqual(normalize("1.234567", "kW", "home_power").value, 1234.57)

    def test_battery_soc_range_and_units(self):
        for raw in ("0", "100", "52.5"):
            self.assertEqual(measurement.normalize_battery(raw, "%", "soc").value, float(raw))
        for raw in ("-1", "101"):
            self.assertEqual(measurement.normalize_battery(raw, "%", "soc").quality, "out_of_range")
        self.assertEqual(measurement.normalize_battery("50", "W", "soc").quality, "unsupported_unit")

    def test_battery_energy_is_normalized_without_soc_estimation(self):
        self.assertEqual(measurement.normalize_battery("2500", "Wh", "remaining_energy").value, 2.5)
        self.assertEqual(measurement.normalize_battery("2.5", "kWh", "remaining_energy").value, 2.5)
        self.assertEqual(measurement.normalize_battery("-1", "kWh", "remaining_energy").quality, "out_of_range")
        self.assertEqual(measurement.normalize_battery("unknown", "kWh", "remaining_energy").quality, "unavailable")

    def test_separate_battery_power_never_guesses_negative_direction(self):
        for role in ("charge_power", "discharge_power"):
            self.assertEqual(measurement.normalize_battery("1.5", "kW", role).value, 1500)
            self.assertEqual(measurement.normalize_battery("-1", "W", role).quality, "unexpected_direction")

    def test_battery_invalid_values_are_not_zero(self):
        for role, unit in (("soc", "%"), ("remaining_energy", "kWh")):
            for raw in ("nan", "inf", "abc"):
                reading = measurement.normalize_battery(raw, unit, role)
                self.assertIsNone(reading.value)
                self.assertEqual(reading.quality, "invalid_value")

    def test_remaining_energy_rejects_declared_cumulative_counters(self):
        for state_class in ("total", "total_increasing"):
            reading = measurement.normalize_battery(
                "1", "kWh", "remaining_energy", capacity_kwh=8.2, state_class=state_class
            )
            self.assertIsNone(reading.value)
            self.assertEqual(reading.quality, "cumulative_energy")

    def test_remaining_energy_capacity_check_and_tolerance(self):
        for raw, unit in (("305.799", "kWh"), ("305799", "Wh")):
            reading = measurement.normalize_battery(raw, unit, "remaining_energy", capacity_kwh=8.2)
            self.assertEqual(reading.quality, "exceeds_capacity")
        self.assertEqual(measurement.normalize_battery(
            "8.5", "kWh", "remaining_energy", capacity_kwh=8.2
        ).quality, "valid")
        self.assertEqual(measurement.normalize_battery(
            "2", "kWh", "remaining_energy", state_class="measurement"
        ).quality, "valid")


if __name__ == "__main__":
    unittest.main()
