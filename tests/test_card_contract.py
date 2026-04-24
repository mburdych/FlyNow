from pathlib import Path


CARD_SOURCE = Path("lovelace/flynow-card/src/flynow-card.ts")


def _card_text() -> str:
    return CARD_SOURCE.read_text(encoding="utf-8")


def test_card_renders_multi_site_comparison_section() -> None:
    source = _card_text()
    assert "sites-summary" in source
    assert "LZMADA — Malý Madaras" in source
    assert "Lúka pri Katarínke" in source
    assert "Lúka pri Nitre" in source
    assert "sites_summary" in source
    assert "selected_site_id" in source


def test_card_renders_condition_threshold_rows() -> None:
    source = _card_text()
    assert "surface_wind" in source
    assert "altitude_wind" in source
    assert "precipitation_probability" in source
    assert "visibility" in source
    assert "threshold" in source
    assert "PASS" in source
    assert "FAIL" in source


def test_card_renders_launch_window_phrase() -> None:
    source = _card_text()
    assert "Launch by" in source
    assert "to" in source


def test_card_keeps_detail_section_below_comparison() -> None:
    source = _card_text()
    assert "selected-site-details" in source
    assert "Condition thresholds" in source


def test_card_has_reactive_hass_setter_for_cache_updates() -> None:
    source = _card_text()
    assert "set hass(" in source
    assert "lastKnownAttributes" in source


def test_card_surfaces_stale_badge_when_using_cache() -> None:
    source = _card_text()
    assert "stale-badge" in source
    assert "showing last known values" in source
    assert "unavailable" in source
    assert "unknown" in source


def test_card_exposes_flight_log_required_fields() -> None:
    source = _card_text()
    assert "Flight log" in source
    assert "Date" in source
    assert "Balloon" in source
    assert "Launch time" in source
    assert "Duration (min)" in source
    assert "Site" in source
    assert "Outcome" in source
    assert "Notes (optional)" in source


def test_card_uses_24h_time_picker_and_service_calls() -> None:
    source = _card_text()
    assert 'type="time"' in source
    assert 'callService<LogFlightResponse>(' in source
    assert '"flynow",' in source
    assert '"log_flight"' in source
    assert 'callService<ListFlightsResponse>(' in source
    assert '"list_flights"' in source
    assert "true" in source


def test_card_renders_history_section_markers() -> None:
    source = _card_text()
    assert "Previous flights" in source
    assert "Showing newest 200 entries" in source
    assert "No flights logged yet." in source
