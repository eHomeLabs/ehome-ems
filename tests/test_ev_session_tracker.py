"""EV session tracker behavior tests (runs without Home Assistant)."""
import importlib.util
import sys
import types
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parents[1] / "custom_components" / "ehome_ems"
package = types.ModuleType("ev_test")
package.__path__ = [str(BASE)]
sys.modules.setdefault("ev_test", package)
for name in ("ev_session_math", "ev_session_tracker"):
    spec = importlib.util.spec_from_file_location(f"ev_test.{name}", BASE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

EVSessionTracker = sys.modules["ev_test.ev_session_tracker"].EVSessionTracker
TZ = ZoneInfo("Europe/Paris")
TARIFF = {"mode": "flat", "flat": 0.2}


def test_session_crosses_midnight_and_survives_restore():
    t = EVSessionTracker(idle_seconds=60)
    at = datetime(2026, 11, 9, 23, 55, tzinfo=TZ)
    t.observe(at, 4000, 100, TARIFF)
    t = EVSessionTracker(t.snapshot(), idle_seconds=60)
    t.observe(at + timedelta(minutes=10), 4326, 110, TARIFF)
    t.observe(at + timedelta(minutes=11), 1, 110.5, TARIFF)
    result = t.observe(at + timedelta(minutes=13), 1, 110.5, TARIFF)
    assert result["active"] is False
    assert result["last_session"]["peak_w"] == 4326
    assert abs(result["last_session"]["energy_kwh"] - 10.5) < 1e-9
    assert abs(result["last_session"]["cost_eur"] - 2.1) < 1e-9


def test_counter_reset_flags_incomplete():
    t = EVSessionTracker(idle_seconds=60)
    at = datetime(2026, 11, 9, 23, 55, tzinfo=TZ)
    t.observe(at, 2000, 100, TARIFF)
    t.observe(at + timedelta(minutes=1), 2000, 2, TARIFF)
    t.observe(at + timedelta(minutes=2), 0, 3, TARIFF)
    result = t.observe(at + timedelta(minutes=4), 0, 3, TARIFF)
    assert result["last_session"]["incomplete"] is True
    assert result["last_session"]["energy_kwh"] is None
