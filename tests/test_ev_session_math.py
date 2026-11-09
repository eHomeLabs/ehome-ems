"""Tests for EV charging session accounting; no Home Assistant runtime required."""
from datetime import datetime
from zoneinfo import ZoneInfo
import importlib.util
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / 'custom_components' / 'ehome_ems' / 'ev_session_math.py'
spec = importlib.util.spec_from_file_location('ev_session_math', MODULE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
energy_delta = module.energy_delta
interval_cost = module.interval_cost
rate_at = module.rate_at
session_peak = module.session_peak

PARIS = ZoneInfo("Europe/Paris")


def test_cross_midnight_session():
    assert energy_delta(200, 210.72) == 10.72 or abs(energy_delta(200, 210.72)-10.72) < 1e-9


def test_reset_is_not_silently_counted():
    assert energy_delta(30, 1) is None
    assert energy_delta(30, 1, reset_is_session=True) == 1


def test_hp_hc_cross_midnight():
    start = datetime(2026, 11, 9, 21, 0, tzinfo=PARIS)
    end = datetime(2026, 11, 10, 1, 0, tzinfo=PARIS)
    # 1 hour HP, 3 hours HC at uniform consumption.
    assert abs(interval_cost(start, end, 4, mode="hp_hc", peak=.3, offpeak=.15) - .75) < .001


def test_flat_rate_and_peak():
    start = datetime(2026, 11, 9, 23, 0, tzinfo=PARIS)
    end = datetime(2026, 11, 10, 2, 0, tzinfo=PARIS)
    assert interval_cost(start, end, 10.72, mode="flat", flat=.2) == 2.144
    assert session_peak([-5, 1, 1500, 4326, 2300]) == 4326
    assert session_peak([1, -1]) is None


def test_tariff_at_boundary():
    assert rate_at(datetime(2026, 11, 9, 22, 0, tzinfo=PARIS),
                   mode="hp_hc", peak=.3, offpeak=.1) == .1
