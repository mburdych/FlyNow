from datetime import datetime, timedelta

from custom_components.flynow.windows import build_windows


def test_build_windows_returns_expected_slots():
    now = datetime(2026, 4, 22, 10, 0, 0)
    sunrise = [now + timedelta(days=i, hours=-4) for i in range(4)]
    sunset = [now + timedelta(days=i, hours=10) for i in range(4)]
    windows = build_windows(now, sunrise, sunset, 90, 30)
    keys = {item["key"] for item in windows}
    assert "today_evening" in keys
    assert "tomorrow_morning" in keys
