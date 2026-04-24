"""Strict-AND worst-case analyzer for FlyNow windows."""

from __future__ import annotations

from typing import Any


def _metric(value: float, threshold: float, compare: str) -> dict[str, Any]:
    ok = value <= threshold if compare == "max" else value >= threshold
    return {"value": value, "threshold": threshold, "ok": ok}


def _clean_numeric(values: list[Any] | None) -> list[float]:
    if not values:
        return []
    cleaned: list[float] = []
    for value in values:
        if value is None:
            continue
        cleaned.append(float(value))
    return cleaned


def _safe_max(values: list[Any] | None) -> float:
    cleaned = _clean_numeric(values)
    if not cleaned:
        return float("inf")
    return max(cleaned)


def _safe_min(values: list[Any] | None, default: float = 0.0) -> float:
    cleaned = _clean_numeric(values)
    if not cleaned:
        return default
    return min(cleaned)


def analyze_window(hourly_slice: dict[str, list[Any]], config: dict[str, float]) -> dict[str, Any]:
    """Analyze one window using worst-case values over the full duration."""
    surface_wind = _safe_max(hourly_slice.get("wind_speed_10m"))
    altitude_wind = max(
        _safe_max(hourly_slice.get("wind_speed_975hPa")),
        _safe_max(hourly_slice.get("wind_speed_925hPa")),
    )
    precip_prob = _safe_max(hourly_slice.get("precipitation_probability"))
    ceiling_values = hourly_slice.get("cloud_base") or hourly_slice.get("ceiling") or [0.0]
    ceiling_m = _safe_min(ceiling_values, default=0.0)
    visibility_km = _safe_min(hourly_slice.get("visibility"), default=0.0) / 1000.0

    checks = {
        "surface_wind_ms": _metric(surface_wind, config["max_surface_wind_ms"], "max"),
        "altitude_wind_ms": _metric(altitude_wind, config["max_altitude_wind_ms"], "max"),
        "precip_prob": _metric(precip_prob, config["max_precip_prob_pct"], "max"),
        "ceiling_m": _metric(ceiling_m, config["min_ceiling_m"], "min"),
        "visibility_km": _metric(visibility_km, config["min_visibility_km"], "min"),
    }
    return {"go": all(item["ok"] for item in checks.values()), "conditions": checks}
