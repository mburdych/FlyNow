"""Immutable weather snapshot primitives for flight correlation."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from typing import Any, Awaitable, Callable

ObservedProvider = Callable[[], Awaitable[dict[str, object] | None]]


def freeze_forecast_snapshot(
    flight_id: str,
    forecast_summary: dict[str, Any],
    frozen_at: datetime | None = None,
) -> dict[str, Any]:
    """Create immutable baseline snapshot payload."""
    ts = frozen_at or datetime.now(UTC)
    return {
        "flight_id": flight_id,
        "frozen_at": ts.astimezone(UTC).isoformat(),
        "forecast": deepcopy(forecast_summary),
        "observed": None,
        "observed_source": None,
        "weather_missing": False,
        "weather_missing_reason": None,
        "corrections": [],
    }


def append_snapshot_correction(
    baseline_snapshot: dict[str, Any],
    source: str,
    reason: str,
    patch: dict[str, Any],
) -> dict[str, Any]:
    """Return new snapshot with append-only correction record."""
    updated = deepcopy(baseline_snapshot)
    corrections = list(updated.get("corrections", []))
    corrections.append(
        {
            "source": source,
            "reason": reason,
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "patch": deepcopy(patch),
        }
    )
    updated["corrections"] = corrections
    return updated


async def resolve_observed_weather(
    metar_provider: ObservedProvider,
    archive_provider: ObservedProvider,
    manual_entry: dict[str, Any] | None,
) -> dict[str, Any]:
    """Resolve observed weather by deterministic source chain."""
    metar_data = await metar_provider()
    if metar_data:
        return {
            "observed": dict(metar_data),
            "observed_source": "metar",
            "weather_missing": False,
            "weather_missing_reason": None,
        }

    archive_data = await archive_provider()
    if archive_data:
        return {
            "observed": dict(archive_data),
            "observed_source": "archive",
            "weather_missing": False,
            "weather_missing_reason": None,
        }

    if manual_entry:
        return {
            "observed": dict(manual_entry),
            "observed_source": "manual",
            "weather_missing": False,
            "weather_missing_reason": None,
        }

    return {
        "observed": None,
        "observed_source": None,
        "weather_missing": True,
        "weather_missing_reason": "no_observed_weather_source_available",
    }
