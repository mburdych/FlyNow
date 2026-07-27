"""Window construction for FlyNow."""

from __future__ import annotations

from datetime import datetime, timedelta

from .const import SLOVAK_DAY_NAMES

# Earliest allowed evening launch regardless of EASA deadline
EVENING_EARLIEST_LAUNCH_HOUR = 18
EVENING_EARLIEST_LAUNCH_MINUTE = 30

# Decision window before launch: crew decides go/no-go during this period
DECISION_WINDOW_MIN = 30


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
    """Build 4 evening + 3 morning windows using EASA civil twilight day limits.

    Each window carries datetime objects (launch_start_dt, launch_end_dt, flight_end_dt)
    for time-aware weather slicing in the analyzer, plus HH:MM strings for display.

    Evening logic:
      - launch_end_dt   = civil_dusk - flight_duration  (latest possible launch)
      - launch_start_dt = max(earliest_allowed, launch_end_dt - decision_window)
      - flight_end_dt   = civil_dusk  (worst-case flight end)
    """
    windows: list[dict] = []
    for offset in range(4):
        day_end = day_end_by_day[offset]
        latest_launch = day_end - timedelta(minutes=flight_duration_min)
        base_date = day_end.replace(hour=0, minute=0, second=0, microsecond=0)
        earliest_allowed = base_date.replace(
            hour=EVENING_EARLIEST_LAUNCH_HOUR,
            minute=EVENING_EARLIEST_LAUNCH_MINUTE,
        )
        earliest_launch = max(earliest_allowed, latest_launch - timedelta(minutes=DECISION_WINDOW_MIN))
        if now_local <= latest_launch and earliest_launch < latest_launch:
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
                    "launch_start": earliest_launch.strftime("%H:%M"),
                    "launch_end": latest_launch.strftime("%H:%M"),
                    "launch_start_dt": earliest_launch,
                    "launch_end_dt": latest_launch,
                    "flight_end_dt": day_end,
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
                    "launch_end": (earliest_launch + timedelta(minutes=DECISION_WINDOW_MIN)).strftime("%H:%M"),
                    "launch_start_dt": earliest_launch,
                    "launch_end_dt": earliest_launch + timedelta(minutes=DECISION_WINDOW_MIN),
                    "flight_end_dt": earliest_launch + timedelta(minutes=DECISION_WINDOW_MIN + flight_duration_min),
                }
            )
    return windows
