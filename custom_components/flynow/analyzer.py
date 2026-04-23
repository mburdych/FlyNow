"""Strict-AND worst-case analyzer for FlyNow windows."""

from __future__ import annotations

from typing import Any


def _metric(value: float, threshold: float, compare: str) -> dict[str, Any]:
    ok = value <= threshold if compare == "max" else value >= threshold
    return {"value": value, "threshold": threshold, "ok": ok}


def analyze_window(hourly_slice: dict[str, list[float]], config: dict[str, float]) -> dict[str, Any]:
    """Analyze one window using worst-case values over the full duration."""
    surface_wind = max(hourly_slice["wind_speed_10m"])
    altitude_wind = max(
        max(hourly_slice["wind_speed_975hPa"]), max(hourly_slice["wind_speed_925hPa"])
    )
    precip_prob = max(hourly_slice["precipitation_probability"])
    ceiling_m = min(hourly_slice["ceiling"])
    visibility_km = min(hourly_slice["visibility"]) / 1000.0

    checks = {
        "surface_wind_ms": _metric(surface_wind, config["max_surface_wind_ms"], "max"),
        "altitude_wind_ms": _metric(altitude_wind, config["max_altitude_wind_ms"], "max"),
        "precip_prob": _metric(precip_prob, config["max_precip_prob_pct"], "max"),
        "ceiling_m": _metric(ceiling_m, config["min_ceiling_m"], "min"),
        "visibility_km": _metric(visibility_km, config["min_visibility_km"], "min"),
    }
    return {"go": all(item["ok"] for item in checks.values()), "conditions": checks}
