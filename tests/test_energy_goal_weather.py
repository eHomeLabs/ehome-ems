from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from custom_components.ehome_ems.energy_goal import daytime_weather_target, cycle


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
