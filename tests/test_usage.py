"""Load power, energy and raw status semantics."""
import importlib
from pathlib import Path
import sys
from types import ModuleType
from unittest import TestCase
from unittest.mock import patch

package = ModuleType("ems_usage_test")
package.__path__ = [str(Path(__file__).resolve().parents[1] / "custom_components/ehome_ems")]
with patch.dict(sys.modules, {"ems_usage_test": package}):
    normalize = importlib.import_module("ems_usage_test.usage").normalize_usage


class UsageTests(TestCase):
    def test_power_units_and_negative_consumption(self):
        self.assertEqual(normalize("1.8", "kW", "power").value, 1800)
        self.assertIsNone(normalize("-1", "W", "power").value)

    def test_energy_is_mirrored_without_period_conversion(self):
        self.assertEqual(normalize("1250", "Wh", "energy").value, 1.25)
        self.assertEqual(normalize("305.799", "kWh", "energy").value, 305.799)

    def test_invalid_energy_never_becomes_zero(self):
        for raw, unit in (("-1", "Wh"), ("nan", "kWh"), ("inf", "kWh"), ("1", "W")):
            self.assertIsNone(normalize(raw, unit, "energy").value)

    def test_status_is_read_only_raw_text_and_unavailable_is_preserved(self):
        self.assertEqual(normalize("charging", None, "status").value, "charging")
        self.assertIsNone(normalize("unavailable", None, "status").value)
