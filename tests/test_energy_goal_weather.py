from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import importlib
from pathlib import Path
import sys
from types import ModuleType
from unittest.mock import patch

package = ModuleType("ems_goal_weather_test")
package.__path__ = [str(Path(__file__).resolve().parents[1] / "custom_components/ehome_ems")]
with patch.dict(sys.modules, {"ems_goal_weather_test": package}):
    goal = importlib.import_module("ems_goal_weather_test.energy_goal")
daytime_weather_target, cycle = goal.daytime_weather_target, goal.cycle


def test_daytime_weather_top_up_uses_total_cycle_energy():
    assert daytime_weather_target(3, .5, 1, "rainy") == .5
    assert daytime_weather_target(3, .5, 1.8, "rainy") == 0
    assert daytime_weather_target(3, .5, 0, "sunny") == 0


def test_missing_forecast_does_not_trigger_grid_heat():
    assert daytime_weather_target(3, .5, 1, None) is None
    assert daytime_weather_target(3, .5, None, "rainy") is None
    assert daytime_weather_target(3, .5, 1, "partlycloudy", 80) == .5


def test_cycle_crosses_midnight_without_reset():
    goal = {"deadline": "07:00"}
    before = cycle(goal, datetime(2026, 11, 13, 23, 50, tzinfo=timezone.utc), "Europe/Paris")
    after = cycle(goal, datetime(2026, 11, 14, 0, 10, tzinfo=timezone.utc), "Europe/Paris")
    assert before == after
