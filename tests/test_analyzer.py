from custom_components.flynow.analyzer import analyze_window


def test_analyzer_strict_and_logic():
    hourly = {
        "wind_speed_10m": [3.0, 4.5],
        "wind_speed_975hPa": [8.0, 11.0],
        "wind_speed_925hPa": [7.0, 9.0],
        "precipitation_probability": [5, 10],
        "ceiling": [800, 600],
        "visibility": [9000, 7000],
    }
    cfg = {
        "max_surface_wind_ms": 4.0,
        "max_altitude_wind_ms": 10.0,
        "max_precip_prob_pct": 20.0,
        "min_ceiling_m": 500.0,
        "min_visibility_km": 5.0,
    }
    result = analyze_window(hourly, cfg)
    assert result["go"] is False
    assert result["conditions"]["altitude_wind_ms"]["ok"] is False
