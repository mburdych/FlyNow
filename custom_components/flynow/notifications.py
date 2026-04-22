"""Notification orchestration for GO transitions."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from .const import (
    CONF_CALENDAR_ENTITY,
    CONF_CREW_NOTIFIER,
    CONF_PILOT_NOTIFIER,
    CONF_SITE_NAME,
    CONF_WHATSAPP_NOTIFIER,
    NOTIF_DEDUP_COOLDOWN_SEC,
    NOTIF_WINDOW_ID_FORMAT,
)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _window_identity(window_key: str, launch_start: str) -> str:
    return NOTIF_WINDOW_ID_FORMAT.format(window_key=window_key, launch_start=launch_start)


def _find_transition_to_go(
    previous_windows: dict[str, dict[str, Any]], current_windows: dict[str, dict[str, Any]]
) -> tuple[str, dict[str, Any]] | None:
    for key, current in current_windows.items():
        prev_go = bool(previous_windows.get(key, {}).get("go"))
        curr_go = bool(current.get("go"))
        if not prev_go and curr_go:
            return key, current
    return None


def _in_cooldown(last_sent: datetime, now_utc: datetime) -> bool:
    delta = (now_utc - last_sent).total_seconds()
    return delta < NOTIF_DEDUP_COOLDOWN_SEC


def _build_message(site_name: str, window_key: str, window: dict[str, Any]) -> str:
    launch_start = window.get("launch_start", "n/a")
    launch_end = window.get("launch_end", "n/a")
    conditions = window.get("conditions", {})
    surface = conditions.get("surface_wind_ms", {})
    altitude = conditions.get("altitude_wind_ms", {})
    precip = conditions.get("precip_prob_pct", {})
    return (
        f"FlyNow GO for {site_name}: {window_key} "
        f"{launch_start}-{launch_end}. "
        f"Wind { _safe_float(surface.get('value')):.1f}/{_safe_float(surface.get('threshold')):.1f} m/s, "
        f"Alt { _safe_float(altitude.get('value')):.1f}/{_safe_float(altitude.get('threshold')):.1f} m/s, "
        f"Precip {_safe_float(precip.get('value')):.0f}/{_safe_float(precip.get('threshold')):.0f}%."
    )


async def _send_notify(
    hass: Any, notifier_entity: str, message: str, title: str, channel_name: str
) -> str:
    await hass.services.async_call(
        "notify",
        "send_message",
        {"entity_id": notifier_entity, "message": message, "title": title},
        blocking=True,
    )
    return channel_name


async def _send_calendar(
    hass: Any, calendar_entity: str, summary: str, start: str, end: str
) -> str:
    await hass.services.async_call(
        "calendar",
        "create_event",
        {
            "entity_id": calendar_entity,
            "summary": summary,
            "start_date_time": start,
            "end_date_time": end,
        },
        blocking=True,
    )
    return "calendar"


async def _run_channel(channel: str, coro: Any) -> tuple[str, Exception | None]:
    try:
        await coro
        return channel, None
    except Exception as err:  # pragma: no cover - covered via behavior test
        return channel, err


async def dispatch_go_transition_notifications(
    hass: Any,
    config: dict[str, Any],
    previous_windows: dict[str, dict[str, Any]],
    current_windows: dict[str, dict[str, Any]],
    dedup_store: dict[str, datetime],
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """Send notifications for NO-GO -> GO transitions with cooldown dedup."""
    now = now_utc or datetime.now(UTC)
    transition = _find_transition_to_go(previous_windows, current_windows)
    if not transition:
        return {"sent": False, "blocked": False, "reason": "no_transition", "errors": []}

    window_key, current_window = transition
    launch_start = str(current_window.get("launch_start", "")).strip()
    launch_end = str(current_window.get("launch_end", "")).strip()
    if not launch_start or not launch_end:
        return {"sent": False, "blocked": True, "reason": "missing_launch_time", "errors": []}

    dedup_key = _window_identity(window_key, launch_start)
    previous_sent = dedup_store.get(dedup_key)
    if previous_sent and _in_cooldown(previous_sent, now):
        return {"sent": False, "blocked": True, "reason": "cooldown", "errors": []}

    site_name = str(config.get(CONF_SITE_NAME, "FlyNow")).strip() or "FlyNow"
    message = _build_message(site_name, window_key, current_window)
    title = f"FlyNow GO: {window_key}"

    tasks = [
        _run_channel(
            "crew_notifier",
            _send_notify(hass, str(config[CONF_CREW_NOTIFIER]), message, title, "crew_notifier"),
        ),
        _run_channel(
            "pilot_notifier",
            _send_notify(
                hass, str(config[CONF_PILOT_NOTIFIER]), message, title, "pilot_notifier"
            ),
        ),
        _run_channel(
            "whatsapp_notifier",
            _send_notify(
                hass,
                str(config[CONF_WHATSAPP_NOTIFIER]),
                message,
                title,
                "whatsapp_notifier",
            ),
        ),
        _run_channel(
            "calendar",
            _send_calendar(
                hass,
                str(config[CONF_CALENDAR_ENTITY]),
                title,
                launch_start,
                launch_end,
            ),
        ),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    successes: list[str] = []
    errors: list[str] = []
    for result in results:
        if isinstance(result, Exception):
            errors.append(f"fanout_task: {result}")
            continue
        channel, err = result
        if err:
            errors.append(f"{channel}: {err}")
            continue
        successes.append(channel)

    if successes:
        dedup_store[dedup_key] = now

    return {
        "sent": bool(successes),
        "blocked": False,
        "reason": "sent" if successes else "all_failed",
        "window_key": window_key,
        "dedup_key": dedup_key,
        "channels": successes,
        "errors": errors,
    }
