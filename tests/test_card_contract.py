from pathlib import Path


CARD_SOURCE = Path("lovelace/flynow-card/src/flynow-card.ts")


def _card_text() -> str:
    return CARD_SOURCE.read_text(encoding="utf-8")


def test_card_renders_two_window_first_sections() -> None:
    source = _card_text()
    assert "Today's Evening" in source
    assert "Tomorrow Morning" in source
    assert "window-summary" in source
    assert "today_evening" in source
    assert "tomorrow_morning" in source


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
