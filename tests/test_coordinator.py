from __future__ import annotations

from typing import Any

import pytest

import custom_components.flynow.coordinator as coordinator_mod
from custom_components.flynow.coordinator import FlyNowCoordinator


def test_coordinator_class_exists():
    assert FlyNowCoordinator is not None


class _Services:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def async_call(
        self, domain: str, service: str, service_data: dict[str, Any], blocking: bool = True
    ) -> None:
        self.calls.append((domain, service, service_data))


class _Hass:
    def __init__(self) -> None:
        self.services = _Services()


@pytest.mark.anyio
async def test_coordinator_dispatches_notifications_on_go_transition(monkeypatch) -> None:
    go_state = {"value": False}

    async def _fake_fetch_forecast(session, latitude: float, longitude: float) -> dict[str, Any]:
        return {
            "daily": {
                "sunrise": [
                    "2026-04-23T05:00:00",
                    "2026-04-24T05:00:00",
                    "2026-04-25T05:00:00",
                    "2026-04-26T05:00:00",
                ],
                "sunset": [
                    "2026-04-23T19:00:00",
                    "2026-04-24T19:00:00",
                    "2026-04-25T19:00:00",
                    "2026-04-26T19:00:00",
                ],
            },
            "hourly": {},
        }

    def _fake_build_windows(**kwargs) -> list[dict[str, Any]]:
        return [
            {
                "key": "tomorrow_morning",
                "type": "morning",
                "launch_start": "2026-04-23T06:00:00",
                "launch_end": "2026-04-23T07:30:00",
            }
        ]

    def _fake_analyze_window(hourly: dict[str, Any], thresholds: dict[str, float]) -> dict[str, Any]:
        return {"go": go_state["value"], "conditions": {}}

    monkeypatch.setattr(coordinator_mod, "fetch_forecast", _fake_fetch_forecast)
    monkeypatch.setattr(coordinator_mod, "build_windows", _fake_build_windows)
    monkeypatch.setattr(coordinator_mod, "analyze_window", _fake_analyze_window)

    config = {
        "latitude": 48.1,
        "longitude": 17.3,
        "flight_duration_min": 90,
        "prep_time_min": 30,
        "update_interval_min": 60,
        "max_surface_wind_ms": 4.0,
        "max_altitude_wind_ms": 10.0,
        "max_precip_prob_pct": 20,
        "min_ceiling_m": 500,
        "min_visibility_km": 5.0,
        "crew_notifier": "notify.crew_phone",
        "pilot_notifier": "notify.pilot_phone",
        "whatsapp_notifier": "notify.whatsapp_group",
        "calendar_entity": "calendar.flynow",
        "site_name": "Test Site",
    }
    coordinator = FlyNowCoordinator(_Hass(), config)

    go_state["value"] = False
    await coordinator._async_update_data()
    assert coordinator.hass.services.calls == []

    go_state["value"] = True
    result = await coordinator._async_update_data()
    assert result["notification_result"]["sent"] is True
    assert result["data_last_updated_utc"]
    assert len(coordinator.hass.services.calls) == 4


@pytest.mark.anyio
async def test_coordinator_returns_three_site_projection(monkeypatch) -> None:
    seen_coords: list[tuple[float, float]] = []

    async def _fake_fetch_forecast(session, latitude: float, longitude: float) -> dict[str, Any]:
        seen_coords.append((latitude, longitude))
        return {
            "daily": {
                "sunrise": [
                    "2026-04-23T05:00:00",
                    "2026-04-24T05:00:00",
                    "2026-04-25T05:00:00",
                    "2026-04-26T05:00:00",
                ],
                "sunset": [
                    "2026-04-23T19:00:00",
                    "2026-04-24T19:00:00",
                    "2026-04-25T19:00:00",
                    "2026-04-26T19:00:00",
                ],
            },
            "hourly": {},
        }

    def _fake_build_windows(**kwargs) -> list[dict[str, Any]]:
        return [
            {
                "key": "tomorrow_morning",
                "type": "morning",
                "launch_start": "2026-04-23T06:00:00",
                "launch_end": "2026-04-23T07:30:00",
            }
        ]

    def _fake_analyze_window(hourly: dict[str, Any], thresholds: dict[str, float]) -> dict[str, Any]:
        return {"go": True, "conditions": {}}

    monkeypatch.setattr(coordinator_mod, "fetch_forecast", _fake_fetch_forecast)
    monkeypatch.setattr(coordinator_mod, "build_windows", _fake_build_windows)
    monkeypatch.setattr(coordinator_mod, "analyze_window", _fake_analyze_window)

    config = {
        "latitude": 99.0,
        "longitude": 99.0,
        "flight_duration_min": 90,
        "prep_time_min": 30,
        "update_interval_min": 60,
        "max_surface_wind_ms": 4.0,
        "max_altitude_wind_ms": 10.0,
        "max_precip_prob_pct": 20,
        "min_ceiling_m": 500,
        "min_visibility_km": 5.0,
        "site_name": "Legacy Site",
    }
    coordinator = FlyNowCoordinator(_Hass(), config)
    result = await coordinator._async_update_data()

    assert result["selected_site_id"] == "lzmada"
    assert set(result["sites"]) == {"lzmada", "katarinka", "nitra-luka"}
    assert set(result["sites_summary"]) == {"lzmada", "katarinka", "nitra-luka"}
    assert len(seen_coords) == 3
