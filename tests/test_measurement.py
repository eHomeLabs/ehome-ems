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


if __name__ == "__main__":
    unittest.main()
