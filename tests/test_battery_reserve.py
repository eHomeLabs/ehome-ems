"""An optimization budget may never spend the protected battery reserve."""
import importlib.util
from pathlib import Path
from unittest import TestCase

spec = importlib.util.spec_from_file_location('reserve', Path(__file__).resolve().parents[1] / 'custom_components/ehome_ems/battery_reserve.py')
reserve = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reserve)


class ReserveTests(TestCase):
    def test_defaults_and_hardware_floor_are_independent(self):
        config = {'capacity_kwh': 10}
        self.assertEqual(reserve.reserve_budget(config, 50)['usable_kwh'], 2)
        for soc in (0, 10, 29, 30):
            result = reserve.reserve_budget(config, soc)
            self.assertFalse(result['can_discharge'])
            self.assertEqual(result['usable_kwh'], 0)
        result = reserve.reserve_budget({**config, 'backup_reserve_percent': 5}, 50)
        self.assertEqual(result['floor_percent'], 10)
        self.assertEqual(result['usable_kwh'], 4)
        self.assertEqual(config, {'capacity_kwh': 10})

    def test_unknown_never_authorizes_discharge(self):
        for soc in (None, 'unknown', 'unavailable', True, float('nan'), float('inf'), -1, 101):
            self.assertFalse(reserve.reserve_budget({'capacity_kwh': 10}, soc)['can_discharge'])
        for capacity in (None, 0, -1, True, float('nan')):
            self.assertFalse(reserve.reserve_budget({'capacity_kwh': capacity}, 80)['can_discharge'])

    def test_custom_reserve_and_minimum_use_higher_floor(self):
        result = reserve.reserve_budget({'capacity_kwh': 8, 'backup_reserve_percent': 45, 'minimum_soc_percent': 50}, '75')
        self.assertEqual(result['usable_kwh'], 2)
        self.assertEqual(result['floor_percent'], 50)
