from pathlib import Path


CARD_SOURCE = Path("lovelace/flynow-card/src/flynow-card.ts")


def _card_text() -> str:
    return CARD_SOURCE.read_text(encoding="utf-8")


def test_card_renders_multi_site_comparison_section() -> None:
    source = _card_text()
    assert "sites-summary" in source
    assert "LZMADA - Maly Madaras" in source
    assert "Luka pri Katarinke" in source
    assert "Luka pri Nitre" in source
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
