from custom_components.flynow.analyzer import analyze_window


def test_analyzer_strict_and_logic():
    hourly = {
        "wind_speed_10m": [3.0, 4.5],
        "wind_speed_975hPa": [8.0, 11.0],
        "wind_speed_925hPa": [7.0, 9.0],
        "precipitation_probability": [5, 10],
        "visibility": [9000, 7000],
    }
    cfg = {
        "max_surface_wind_ms": 4.0,
        "max_altitude_wind_ms": 10.0,
        "max_precip_prob_pct": 20.0,
        "min_visibility_km": 5.0,
    }
    result = analyze_window(hourly, cfg)
    assert result["go"] is False
    assert result["conditions"]["altitude_wind_ms"]["ok"] is False
    assert "fog_risk" in result["conditions"]


def test_analyzer_handles_none_values_without_crash():
    hourly = {
        "wind_speed_10m": [None, 3.5, None],
        "wind_speed_975hPa": [None, 9.0],
        "wind_speed_925hPa": [None, 8.5],
        "precipitation_probability": [None, 10],
        "cloud_base": [None, None],
        "visibility": [None, 7000],
    }
    cfg = {
        "max_surface_wind_ms": 4.0,
        "max_altitude_wind_ms": 10.0,
        "max_precip_prob_pct": 20.0,
        "min_visibility_km": 5.0,
    }

    result = analyze_window(hourly, cfg)
    assert result["go"] is True


def test_analyzer_reports_fog_risk_metadata():
    hourly = {
        "wind_speed_10m": [1.5, 2.0],
        "wind_speed_975hPa": [5.0, 5.5],
        "wind_speed_925hPa": [4.5, 5.0],
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
    result = analyze_window(hourly, cfg)
    fog = result["conditions"]["fog_risk"]
    assert fog["blocking"] is False
    assert fog["ok"] is True
    assert fog["value"] in {"high", "medium", "low-medium", "low"}
    assert fog["trend"] in {"improving", "stable", "worsening"}
