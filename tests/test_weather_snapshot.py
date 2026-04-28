from __future__ import annotations

from datetime import UTC, datetime

import pytest

from custom_components.flynow.weather_snapshot import (
    append_snapshot_correction,
    freeze_forecast_snapshot,
    resolve_observed_weather,
)


def test_freeze_forecast_snapshot_creates_immutable_payload() -> None:
    snapshot = freeze_forecast_snapshot(
        flight_id="flight-001",
        forecast_summary={"wind_ms": 3.2, "visibility_km": 12},
        frozen_at=datetime(2026, 4, 24, 4, 30, tzinfo=UTC),
    )

    assert snapshot["flight_id"] == "flight-001"
    assert snapshot["forecast"]["wind_ms"] == 3.2
    assert snapshot["corrections"] == []
    assert snapshot["weather_missing"] is False


@pytest.mark.anyio
async def test_resolve_observed_weather_prefers_metar_over_archive() -> None:
    async def metar_provider() -> dict[str, object] | None:
        return {"wind_ms": 4.1, "visibility_km": 10, "station_id": "LZIB"}

    async def archive_provider() -> dict[str, object] | None:
        return {"wind_ms": 5.5, "visibility_km": 9}

    observed = await resolve_observed_weather(metar_provider, archive_provider, manual_entry=None)
    assert observed["observed_source"] == "metar"
    assert observed["weather_missing"] is False


@pytest.mark.anyio
async def test_resolve_observed_weather_falls_back_without_blocking() -> None:
    async def metar_provider() -> dict[str, object] | None:
        return None

    async def archive_provider() -> dict[str, object] | None:
        return None

    observed = await resolve_observed_weather(metar_provider, archive_provider, manual_entry=None)
    assert observed["weather_missing"] is True
    assert observed["weather_missing_reason"] == "no_observed_weather_source_available"


def test_append_snapshot_correction_keeps_base_immutable() -> None:
    baseline = freeze_forecast_snapshot(
        flight_id="flight-002",
        forecast_summary={"wind_ms": 3.2},
        frozen_at=datetime(2026, 4, 24, 4, 30, tzinfo=UTC),
    )
    updated = append_snapshot_correction(
        baseline,
        source="manual",
        reason="pilot_observation",
        patch={"wind_ms": 2.8},
    )
    assert baseline["corrections"] == []
    assert len(updated["corrections"]) == 1
