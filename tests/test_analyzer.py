from datetime import datetime

from custom_components.flynow.analyzer import _slice_hours, analyze_window


def _cfg() -> dict[str, float]:
    return {
        "max_surface_wind_ms": 4.0,
        "max_altitude_wind_ms": 10.0,
        "max_precip_prob_pct": 20.0,
        "min_visibility_km": 5.0,
    }


def test_slice_hours_uses_overlapping_hour_for_short_window():
    """Evening decision window 19:11–19:41 must include the 19:00 Open-Meteo sample."""
    hourly = {
        "time": [
            "2026-07-27T18:00",
            "2026-07-27T19:00",
            "2026-07-27T20:00",
            "2026-07-27T21:00",
        ],
        "wind_speed_10m": [7.2, 7.18, 4.85, 2.08],
    }
    sliced = _slice_hours(
        hourly,
        datetime.fromisoformat("2026-07-27T19:11:00"),
        datetime.fromisoformat("2026-07-27T19:41:00"),
    )
    assert sliced["wind_speed_10m"] == [7.18]


def test_analyzer_short_evening_window_has_surface_wind():
    hourly = {
        "time": [
            "2026-07-27T18:00",
            "2026-07-27T19:00",
            "2026-07-27T20:00",
            "2026-07-27T21:00",
        ],
        "wind_speed_10m": [7.2, 7.18, 4.85, 2.08],
        "wind_speed_850hPa": [12.0, 12.5, 13.0, 11.0],
        "wind_speed_925hPa": [11.0, 11.5, 12.0, 10.0],
        "wind_speed_975hPa": [10.0, 10.5, 11.0, 9.0],
        "precipitation_probability": [0, 0, 0, 0],
        "visibility": [40000, 42000, 41000, 40000],
        "relative_humidity_2m": [50, 55, 60, 65],
        "temperature_2m": [28.0, 27.0, 25.0, 23.0],
        "dew_point_2m": [12.0, 13.0, 14.0, 14.0],
    }
    result = analyze_window(
        hourly,
        _cfg(),
        launch_start=datetime.fromisoformat("2026-07-27T19:11:00"),
        launch_end=datetime.fromisoformat("2026-07-27T19:41:00"),
        flight_end=datetime.fromisoformat("2026-07-27T21:11:00"),
    )
    surface = result["conditions"]["surface_wind_ms"]
    assert surface["value"] == 7.18
    assert surface["ok"] is False  # above 4 m/s limit
    assert result["go"] is False


def test_analyzer_strict_and_logic():
    hourly = {
        "time": ["2026-07-27T18:00", "2026-07-27T19:00"],
        "wind_speed_10m": [3.0, 4.5],
        "wind_speed_975hPa": [8.0, 11.0],
        "wind_speed_925hPa": [7.0, 9.0],
        "wind_speed_850hPa": [8.0, 10.0],
        "precipitation_probability": [5, 10],
        "visibility": [9000, 7000],
    }
    result = analyze_window(
        hourly,
        _cfg(),
        launch_start=datetime.fromisoformat("2026-07-27T18:00:00"),
        launch_end=datetime.fromisoformat("2026-07-27T18:30:00"),
        flight_end=datetime.fromisoformat("2026-07-27T20:00:00"),
    )
    assert result["go"] is False
    assert result["conditions"]["altitude_wind_ms"]["ok"] is False
    assert "fog_risk" in result["conditions"]


def test_analyzer_handles_none_values_without_crash():
    hourly = {
        "time": ["2026-07-27T06:00", "2026-07-27T07:00", "2026-07-27T08:00"],
        "wind_speed_10m": [None, 3.5, None],
        "wind_speed_975hPa": [None, 9.0, 8.0],
        "wind_speed_925hPa": [None, 8.5, 8.0],
        "wind_speed_850hPa": [None, 9.0, 8.5],
        "precipitation_probability": [None, 10, 5],
        "visibility": [None, 7000, 8000],
    }
    result = analyze_window(
        hourly,
        _cfg(),
        launch_start=datetime.fromisoformat("2026-07-27T07:00:00"),
        launch_end=datetime.fromisoformat("2026-07-27T07:30:00"),
        flight_end=datetime.fromisoformat("2026-07-27T09:00:00"),
    )
    assert result["conditions"]["surface_wind_ms"]["value"] == 3.5
    assert result["go"] is True


def test_analyzer_reports_fog_risk_metadata():
    hourly = {
        "time": ["2026-07-27T06:00", "2026-07-27T07:00"],
        "wind_speed_10m": [1.5, 2.0],
        "wind_speed_975hPa": [5.0, 5.5],
        "wind_speed_925hPa": [4.5, 5.0],
        "wind_speed_850hPa": [5.0, 5.5],
        "precipitation_probability": [0, 0],
        "visibility": [1200, 4000],
        "relative_humidity_2m": [98, 92],
        "temperature_2m": [8.0, 10.0],
        "dew_point_2m": [7.5, 7.0],
    }
    cfg = {
        "max_surface_wind_ms": 4.0,
        "max_altitude_wind_ms": 10.0,
        "max_precip_prob_pct": 20.0,
        "min_visibility_km": 1.0,
    }
    result = analyze_window(
        hourly,
        cfg,
        launch_start=datetime.fromisoformat("2026-07-27T06:00:00"),
        launch_end=datetime.fromisoformat("2026-07-27T06:30:00"),
        flight_end=datetime.fromisoformat("2026-07-27T08:00:00"),
    )
    fog = result["conditions"]["fog_risk"]
    assert fog["blocking"] is False
    assert fog["ok"] is True
    assert fog["value"] in {"high", "medium", "low-medium", "low"}
    assert fog["trend"] in {"improving", "stable", "worsening"}
