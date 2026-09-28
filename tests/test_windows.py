from datetime import datetime, timedelta

from custom_components.flynow.windows import build_windows


def _bounds(base: datetime, dawn_h: int, dawn_m: int, dusk_h: int, dusk_m: int, days: int = 4):
    day0 = base.replace(hour=0, minute=0, second=0, microsecond=0)
    day_start = [
        day0 + timedelta(days=i, hours=dawn_h, minutes=dawn_m) for i in range(days)
    ]
    day_end = [
        day0 + timedelta(days=i, hours=dusk_h, minutes=dusk_m) for i in range(days)
    ]
    sunrise = [
        day0 + timedelta(days=i, hours=dawn_h, minutes=dawn_m + 30) for i in range(days)
    ]
    sunset = [
        day0 + timedelta(days=i, hours=dusk_h - 1, minutes=dusk_m + 29) for i in range(days)
    ]
    return day_start, day_end, sunrise, sunset


def test_build_windows_returns_expected_slots():
    now = datetime(2026, 4, 22, 10, 0, 0)
    day_start, day_end, sunrise, sunset = _bounds(now, 5, 30, 20, 30)
    windows = build_windows(now, day_start, day_end, sunrise, sunset, 90, 30)
    keys = {item["key"] for item in windows}
    assert "today_evening" in keys
    assert "tomorrow_morning" in keys


def test_autumn_afternoon_keeps_today_evening_not_tomorrow_morning():
    """Regression: early civil dusk + 18:30 floor used to drop all evenings."""
    now = datetime(2026, 9, 28, 14, 0, 0)
    # Matches live card: EASA day ~06:15–19:05, sunset ~18:34
    day_start, day_end, sunrise, sunset = _bounds(now, 6, 15, 19, 5)
    sunset = [
        now.replace(hour=0, minute=0, second=0, microsecond=0)
        + timedelta(days=i, hours=18, minutes=34)
        for i in range(4)
    ]
    windows = build_windows(now, day_start, day_end, sunrise, sunset, 90, 30)
    keys = [item["key"] for item in windows]
    assert "today_evening" in keys
    assert keys[0] == "today_evening"
    today = next(item for item in windows if item["key"] == "today_evening")
    # latest = 19:05 - 90min = 17:35; decision window starts 17:05 (before 18:30 floor)
    assert today["launch_end"] == "17:35"
    assert today["launch_start"] == "17:05"


def test_summer_evening_still_respects_1830_floor_when_dusk_allows():
    now = datetime(2026, 6, 21, 14, 0, 0)
    day_start, day_end, sunrise, sunset = _bounds(now, 4, 0, 21, 30)
    windows = build_windows(now, day_start, day_end, sunrise, sunset, 90, 30)
    today = next(item for item in windows if item["key"] == "today_evening")
    # latest = 21:30 - 90 = 20:00; decision start 19:30 (> 18:30 floor)
    assert today["launch_start"] == "19:30"
    assert today["launch_end"] == "20:00"
