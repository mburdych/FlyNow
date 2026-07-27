"""Strict-AND worst-case analyzer for FlyNow windows."""

from __future__ import annotations

from typing import Any


def _metric(
    value: float | None,
    threshold: float | None,
    compare: str,
    *,
    ok_override: bool | None = None,
    reason: str | None = None,
    blocking: bool = True,
) -> dict[str, Any]:
    if ok_override is None:
        if value is None or threshold is None:
            ok = False
        else:
            ok = value <= threshold if compare == "max" else value >= threshold
    else:
        ok = ok_override
    result: dict[str, Any] = {
        "value": value,
        "threshold": threshold,
        "ok": ok,
        "blocking": blocking,
    }
    if reason:
        result["reason"] = reason
    return result


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


def _max_or_none(values: list[Any] | None) -> float | None:
    cleaned = _clean_numeric(values)
    if not cleaned:
        return None
    return max(cleaned)


def _fog_risk(hourly_slice: dict[str, list[Any]]) -> dict[str, Any]:
    vis_values = _clean_numeric(hourly_slice.get("visibility"))
    vis_km = [v / 1000.0 for v in vis_values]
    min_vis = min(vis_km) if vis_km else None

    humidity_max = _max_or_none(hourly_slice.get("relative_humidity_2m"))
    temp_values = _clean_numeric(hourly_slice.get("temperature_2m"))
    dew_values = _clean_numeric(hourly_slice.get("dew_point_2m"))
    spread_values = [
        t - d for t, d in zip(temp_values, dew_values, strict=False) if t is not None and d is not None
    ]
    min_spread = min(spread_values) if spread_values else None

    if min_vis is not None and min_vis <= 1.0:
        risk = "high"
    elif min_vis is not None and min_vis <= 3.0:
        risk = "medium"
    elif humidity_max is not None and min_spread is not None and humidity_max >= 95 and min_spread <= 1.5:
        risk = "medium"
    elif humidity_max is not None and min_spread is not None and humidity_max >= 90 and min_spread <= 2.5:
        risk = "low-medium"
    else:
        risk = "low"

    trend = "stable"
    if len(vis_km) >= 2 and len(spread_values) >= 2:
        vis_delta = vis_km[-1] - vis_km[0]
        spread_delta = spread_values[-1] - spread_values[0]
        if vis_delta >= 1.5 and spread_delta >= 0.8:
            trend = "improving"
        elif vis_delta <= -1.0 and spread_delta <= -0.5:
            trend = "worsening"

    return {
        "value": risk,
        "threshold": "informational",
        "ok": True,
        "blocking": False,
        "trend": trend,
        "min_visibility_km": min_vis,
        "max_relative_humidity_pct": humidity_max,
        "min_temp_dew_spread_c": min_spread,
    }


def _safe_mean(values: list[Any] | None) -> float | None:
    cleaned = _clean_numeric(values)
    if not cleaned:
        return None
    return sum(cleaned) / len(cleaned)


def _slice_hours(
    hourly: dict[str, list[Any]],
    from_dt: "datetime",
    to_dt: "datetime",
) -> dict[str, list[Any]]:
    """Return hourly sub-lists whose hour buckets overlap [from_dt, to_dt).

    Open-Meteo timestamps are hour starts (e.g. 19:00 means [19:00, 20:00)).
    A short launch window like 19:11–19:41 must still pick the 19:00 sample —
    point-in-range matching on exact hour stamps would return an empty slice
    and force surface_wind to n/a → hard NO-GO.
    """
    from datetime import datetime as _dt
    from datetime import timedelta

    times = hourly.get("time", [])
    indices: list[int] = []
    for i, stamp in enumerate(times):
        hour_start = _dt.fromisoformat(stamp)
        hour_end = hour_start + timedelta(hours=1)
        if hour_start < to_dt and hour_end > from_dt:
            indices.append(i)
    return {key: [vals[i] for i in indices] for key, vals in hourly.items() if key != "time"}


def analyze_window(
    hourly: dict[str, list[Any]],
    config: dict[str, float],
    launch_start: "datetime",
    launch_end: "datetime",
    flight_end: "datetime",
) -> dict[str, Any]:
    """Analyze window using time-aware slices.

    surface_wind  — mean over launch window (decision time)
    altitude_wind — mean over full flight (launch_start..flight_end), averaged across layers
    precip/vis    — worst-case over entire window (launch_start..flight_end)
    """
    from datetime import datetime as _dt  # noqa: F401 — imported for _slice_hours closure

    launch_slice = _slice_hours(hourly, launch_start, launch_end)
    flight_slice = _slice_hours(hourly, launch_start, flight_end)

    surface_wind = _safe_mean(launch_slice.get("wind_speed_10m"))

    altitude_layers = [
        _clean_numeric(flight_slice.get("wind_speed_850hPa")),
        _clean_numeric(flight_slice.get("wind_speed_925hPa")),
        _clean_numeric(flight_slice.get("wind_speed_975hPa")),
    ]
    all_altitude_values = [v for layer in altitude_layers for v in layer]
    altitude_wind = (sum(all_altitude_values) / len(all_altitude_values)) if all_altitude_values else None

    precip_prob = _safe_max(flight_slice.get("precipitation_probability"))
    visibility_km = _safe_min(flight_slice.get("visibility"), default=0.0) / 1000.0

    checks = {
        "surface_wind_ms": _metric(surface_wind, config["max_surface_wind_ms"], "max"),
        "altitude_wind_ms": _metric(altitude_wind, config["max_altitude_wind_ms"], "max"),
        "precip_prob": _metric(precip_prob, config["max_precip_prob_pct"], "max"),
        "visibility_km": _metric(visibility_km, config["min_visibility_km"], "min"),
        "fog_risk": _fog_risk(flight_slice),
    }
    blocking = [item["ok"] for item in checks.values() if item.get("blocking", True)]
    return {"go": all(blocking), "conditions": checks}
