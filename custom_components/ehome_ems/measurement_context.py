"""Preparation only: explicit load boundary and dated export observations.

Not wired to the integration or simulator. A healthy export snapshot is not
reallocatable power, a solar-origin certificate or permission to control a load.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from math import floor

from .home_balance import home_sources
from .measurement import PowerReading, normalize_power


@dataclass(frozen=True)
class SourceSample:
    raw: object
    unit: str | None
    published_at: datetime | None


def _utc(value):
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise ValueError("aware_timestamp_required")
    return value.astimezone(timezone.utc)


def _window(now, max_age_seconds):
    _utc(now)
    if type(max_age_seconds) is not int or not 30 <= max_age_seconds <= 3600:
        raise ValueError("invalid_max_age")


def fresh_power(source_id, role, samples, *, now, max_age_seconds=300):
    """Use publication time, never last_changed; never fabricate missing zero."""
    _window(now, max_age_seconds)
    if not isinstance(source_id, str) or not source_id:
        return PowerReading(None, "missing_source")
    sample = samples.get(source_id)
    if not isinstance(sample, SourceSample):
        return PowerReading(None, "unavailable")
    try:
        age = (_utc(now) - _utc(sample.published_at)).total_seconds()
    except ValueError:
        return PowerReading(None, "unknown_age")
    if age < 0:
        return PowerReading(None, "future_timestamp")
    if age > max_age_seconds:
        return PowerReading(None, "stale_source")
    if isinstance(sample.raw, bool):
        return PowerReading(None, "invalid_value")
    if not isinstance(sample.unit, str):
        return PowerReading(None, "unsupported_unit")
    return normalize_power(sample.raw, sample.unit, role)


def _home_result(quality, *, source_w=None, total_w=None, origin=None, sources=()):
    return {"quality": quality, "source_w": source_w, "total_w": total_w,
            "origin": origin, "sources": list(sources)}


def home_total(mapping, samples, *, now, max_age_seconds=300):
    """Reconstruct only a declared, non-overlapping external-meter boundary.

    Future home_boundary settings: mode total/excludes_usages, confirmed, and
    excluded_usage_ids. Exclusions additionally require disjoint_confirmed.
    Confirmation covers house loads excluding storage charge, and AC scope.
    """
    _window(now, max_age_seconds)
    boundary = mapping.get("home_boundary", {})
    if not isinstance(boundary, dict):
        return _home_result("invalid_boundary")
    if mapping.get("home_power_mode") == "calculated":
        if boundary.get("mode") not in (None, "total") or boundary.get("excluded_usage_ids"):
            return _home_result("calculated_boundary_conflict")
        specs, reason = home_sources(mapping)
        if reason:
            return _home_result(reason)
        total = 0
        for role, source, coefficient in specs:
            value = fresh_power(source, role, samples, now=now, max_age_seconds=max_age_seconds)
            if value.value is None:
                return _home_result(value.quality)
            total += value.value * coefficient
        if total < 0:
            return _home_result("negative_balance")
        return _home_result("valid", total_w=round(total, 2), origin="ac_balance",
                            sources=[source for _, source, _ in specs])
    if boundary.get("confirmed") is not True:
        return _home_result("boundary_unconfirmed")
    mode = boundary.get("mode")
    excluded = boundary.get("excluded_usage_ids", [])
    if mode not in ("total", "excludes_usages") or not isinstance(excluded, list):
        return _home_result("invalid_boundary")
    if any(not isinstance(identifier, str) for identifier in excluded) or len(set(excluded)) != len(excluded):
        return _home_result("duplicate_exclusion")
    if (mode == "total" and excluded) or (mode == "excludes_usages" and not excluded):
        return _home_result("invalid_boundary")
    if excluded and boundary.get("disjoint_confirmed") is not True:
        return _home_result("overlap_unconfirmed")
    source = mapping.get("home_power")
    base = fresh_power(source, "home_power", samples, now=now, max_age_seconds=max_age_seconds)
    if base.value is None:
        return _home_result(base.quality)
    total, sources = base.value, [source]
    for identifier in excluded:
        usage = mapping.get("usages", {}).get(identifier)
        if not isinstance(usage, dict):
            return _home_result("unknown_excluded_usage")
        source_id = usage.get("power")
        if source_id in sources:
            return _home_result("duplicate_source")
        value = fresh_power(source_id, "home_power", samples, now=now, max_age_seconds=max_age_seconds)
        if value.value is None:
            return _home_result(value.quality)
        total += value.value
        sources.append(source_id)
    return _home_result("valid", source_w=base.value, total_w=round(total, 2),
                        origin="external_total" if mode == "total" else "external_plus_exclusions", sources=sources)


def export_context(mapping, samples, *, now, max_age_seconds=300, max_span_seconds=30, tolerance_w=50):
    """Return a dated export ceiling for a FUTURE explicit scenario, not control.

    No battery charge or routed load is added back to export. Topology, boundary,
    freshness, report spread and an AC balance are prerequisites, not proof of
    sampling synchrony or physical wiring. Tolerance is diagnostic only.
    """
    _window(now, max_age_seconds)
    if type(max_span_seconds) is not int or not 0 <= max_span_seconds <= max_age_seconds:
        raise ValueError("invalid_report_span")
    if type(tolerance_w) is not int or not 0 <= tolerance_w <= 10000:
        raise ValueError("invalid_balance_tolerance")
    export = fresh_power(mapping.get("grid_export"), "grid_export", samples, now=now, max_age_seconds=max_age_seconds)
    result = {"quality": export.quality, "export_observed_w": export.value, "home_total_w": None,
              "balance_residual_w": None, "report_span_seconds": None,
              "scenario_export_ceiling_w": None, "reallocatable_power_w": None,
              "commands_allowed": False}
    if export.value is None:
        return result
    specs, reason = home_sources(mapping)
    if reason:
        return {**result, "quality": reason}
    home = home_total(mapping, samples, now=now, max_age_seconds=max_age_seconds)
    if home["total_w"] is None:
        return {**result, "quality": home["quality"]}
    result["home_total_w"] = home["total_w"]
    role_values, expected = {}, 0
    for role, source, coefficient in specs:
        value = fresh_power(source, role, samples, now=now, max_age_seconds=max_age_seconds)
        if value.value is None:
            return {**result, "quality": value.quality}
        role_values.setdefault(role, []).append(value.value)
        expected += coefficient * value.value
    source_ids = [source for _, source, _ in specs]
    if mapping.get("home_power_mode") != "calculated":
        if set(source_ids).intersection(home["sources"]):
            return {**result, "quality": "duplicate_source"}
        source_ids += home["sources"]
    times = [_utc(samples[source].published_at) for source in source_ids]
    span = (max(times) - min(times)).total_seconds()
    result["report_span_seconds"] = span
    if span > max_span_seconds:
        return {**result, "quality": "reports_not_aligned"}
    if expected < 0:
        return {**result, "quality": "negative_balance"}
    residual = round(home["total_w"] - expected, 2)
    result["balance_residual_w"] = residual
    if abs(residual) > tolerance_w:
        return {**result, "quality": "balance_mismatch"}
    # The 10 W animation threshold deliberately has NO role in these checks.
    if export.value > 0 and any(value > 0 for value in role_values.get("grid_import", [])):
        return {**result, "quality": "simultaneous_exchange"}
    if export.value > 0 and any(value > 0 for value in role_values.get("discharge_power", [])):
        return {**result, "quality": "battery_origin_uncertain"}
    return {**result, "quality": "valid_export_snapshot", "scenario_export_ceiling_w": floor(export.value)}
