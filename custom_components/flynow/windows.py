"""Window construction for FlyNow."""

from __future__ import annotations

from datetime import datetime, timedelta

from .const import SLOVAK_DAY_NAMES


def _slovak_label(base_date: datetime, day_offset: int) -> str:
    if day_offset == 0:
        return "Dnes"
    if day_offset == 1:
        return "Zajtra"
    weekday = (base_date + timedelta(days=day_offset)).weekday()
    return SLOVAK_DAY_NAMES[weekday]


def build_windows(
    now_local: datetime,
    day_start_by_day: list[datetime],
    day_end_by_day: list[datetime],
    sunrise_by_day: list[datetime],
    sunset_by_day: list[datetime],
    flight_duration_min: int,
    prep_time_min: int,
) -> list[dict]:
    """Build 4 evening + 3 morning windows using EASA civil twilight day limits."""
    windows: list[dict] = []
    for offset in range(4):
        day_end = day_end_by_day[offset]
        latest_launch = day_end - timedelta(minutes=(flight_duration_min + prep_time_min))
        if now_local <= latest_launch:
            windows.append(
                {
                    "key": ["today", "tomorrow", "day2", "day3"][offset] + "_evening",
                    "label": _slovak_label(now_local, offset),
                    "type": "evening",
                    "look_ahead": offset >= 2,
                    "night_before": offset == 1,
                    "day_start": day_start_by_day[offset].strftime("%H:%M"),
                    "day_end": day_end.strftime("%H:%M"),
                    "sunrise": sunrise_by_day[offset].strftime("%H:%M"),
                    "sunset": sunset_by_day[offset].strftime("%H:%M"),
                    "launch_start": latest_launch.strftime("%H:%M"),
                    "launch_end": (latest_launch + timedelta(minutes=30)).strftime("%H:%M"),
                }
            )
    for offset in range(1, 4):
        day_start = day_start_by_day[offset]
        earliest_launch = day_start + timedelta(minutes=prep_time_min)
        if now_local <= earliest_launch:
            windows.append(
                {
                    "key": ["tomorrow", "day2", "day3"][offset - 1] + "_morning",
                    "label": _slovak_label(now_local, offset),
                    "type": "morning",
                    "look_ahead": offset >= 2,
                    "night_before": offset == 1,
                    "day_start": day_start.strftime("%H:%M"),
                    "day_end": day_end_by_day[offset].strftime("%H:%M"),
                    "sunrise": sunrise_by_day[offset].strftime("%H:%M"),
                    "sunset": sunset_by_day[offset].strftime("%H:%M"),
                    "launch_start": earliest_launch.strftime("%H:%M"),
                    "launch_end": (earliest_launch + timedelta(minutes=30)).strftime("%H:%M"),
                }
            )
    return windows
