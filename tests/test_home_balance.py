"""AC load balance arithmetic, completeness and topology."""
import importlib
from pathlib import Path
import sys
from types import ModuleType
from unittest import TestCase
from unittest.mock import patch

package = ModuleType("ems_home_test")
package.__path__ = [str(Path(__file__).resolve().parents[1] / "custom_components/ehome_ems")]
with patch.dict(sys.modules, {"ems_home_test": package}):
    balance = importlib.import_module("ems_home_test.home_balance")


def config(**extra):
    return {"grid_import": "sensor.import", "grid_export": "sensor.export",
            "home_boundary_confirmed": True, "home_has_solar": False,
            "home_has_storage": False, **extra}


class HomeBalanceTests(TestCase):
    def test_grid_only_loads(self):
        result = balance.calculate_home(config(), {"sensor.import": ("0.8", "kW"), "sensor.export": ("0", "W")})
        self.assertEqual(result.value, 800)

    def test_usage_submeters_are_never_added_to_home_balance(self):
        mapping = config(usages={"load": {"power": "sensor.load", "included_in_home": True}})
        result = balance.calculate_home(mapping, {
            "sensor.import": ("800", "W"), "sensor.export": ("0", "W"), "sensor.load": ("500", "W"),
        })
        self.assertEqual(result.value, 800)

    def test_solar_and_storage_are_not_counted_twice(self):
        mapping = config(home_has_solar=True, solar_power="sensor.pv", home_has_storage=True,
                         batteries={"a": {"role": "active", "coupling": "ac",
                                          "charge_power": "sensor.charge", "discharge_power": "sensor.discharge"}})
        result = balance.calculate_home(mapping, {"sensor.import": ("0", "W"), "sensor.export": ("-47", "W"),
               "sensor.pv": ("719", "W"), "sensor.charge": ("247", "W"), "sensor.discharge": ("0", "W")})
        self.assertEqual(result.value, 425)

    def test_missing_reading_is_not_zero(self):
        result = balance.calculate_home(config(), {"sensor.import": ("500", "W")})
        self.assertIsNone(result.value)
        self.assertEqual(result.quality, "unavailable")

    def test_missing_association_is_not_zero(self):
        self.assertEqual(balance.home_sources(config(grid_export=None))[1], "missing_source")

    def test_signed_grid_is_not_used_without_convention(self):
        self.assertEqual(balance.home_sources(config(grid_import=None, grid_power="sensor.signed"))[1], "missing_source")

    def test_boundary_and_declarations_are_explicit(self):
        self.assertEqual(balance.home_sources(config(home_boundary_confirmed=False))[1], "boundary_unconfirmed")
        self.assertEqual(balance.home_sources(config(solar_power="sensor.pv"))[1], "solar_configuration")
        self.assertEqual(balance.home_sources(config(home_has_storage=True))[1], "storage_configuration")

    def test_dc_and_missing_active_battery_channels_are_refused(self):
        mapping = config(home_has_storage=True, batteries={"a": {"role": "active", "coupling": "dc"}})
        self.assertEqual(balance.home_sources(mapping)[1], "unsupported_topology")
        mapping["batteries"]["a"]["coupling"] = "ac"
        self.assertEqual(balance.home_sources(mapping)[1], "missing_source")

    def test_backups_are_excluded_from_daily_ac_balance(self):
        self.assertIsNone(balance.home_sources(config(batteries={
            "backup": {"role": "backup", "coupling": "ac", "charge_power": "sensor.backup"}
        }))[1])

    def test_duplicate_and_negative_balances_are_not_clamped(self):
        self.assertEqual(balance.home_sources(config(grid_export="sensor.import"))[1], "duplicate_source")
        result = balance.calculate_home(config(), {"sensor.import": ("0", "W"), "sensor.export": ("50", "W")})
        self.assertIsNone(result.value)
        self.assertEqual(result.quality, "negative_balance")

    def test_invalid_unit_and_nonfinite_values_are_rejected(self):
        for reading in (("nan", "W"), ("1", "kWh"), ("unavailable", "W")):
            self.assertIsNone(balance.calculate_home(
                config(), {"sensor.import": reading, "sensor.export": ("0", "W")}
            ).value)
