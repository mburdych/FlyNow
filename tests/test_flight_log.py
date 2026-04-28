from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import voluptuous as vol

from custom_components.flynow.const import (
    FLIGHT_HISTORY_LIMIT,
    SERVICE_IMPORT_FLIGHT,
    SERVICE_LIST_FLIGHTS,
    SERVICE_LOG_FLIGHT,
)
from custom_components.flynow.flight_log import (
    LIST_FLIGHTS_SCHEMA,
    LOG_FLIGHT_SCHEMA,
    async_register_services,
)


class _Services:
    def __init__(self) -> None:
        self._handlers: dict[tuple[str, str], Any] = {}

    def has_service(self, domain: str, service: str) -> bool:
        return (domain, service) in self._handlers

    def async_register(
        self,
        domain: str,
        service: str,
        handler: Any,
        supports_response: str | None = None,
    ) -> None:
        self._handlers[(domain, service)] = handler

    async def call(self, domain: str, service: str, data: dict[str, Any]) -> dict[str, Any]:
        handler = self._handlers[(domain, service)]
        return await handler(SimpleNamespace(data=data))


class _Config:
    def __init__(self, root: Path) -> None:
        self._root = root

    def path(self, name: str) -> str:
        return str(self._root / name)


class _Hass:
    def __init__(self, root: Path) -> None:
        self.config = _Config(root)
        self.services = _Services()
        self.data: dict[str, Any] = {}

    async def async_add_executor_job(self, target: Any, *args: Any) -> Any:
        return target(*args)


def _payload(**overrides: Any) -> dict[str, Any]:
    data = {
        "date": "2026-04-24",
        "balloon": "OM-0007",
        "launch_time": "06:15",
        "duration_min": 90,
        "site": "lzmada",
        "outcome": "flown",
        "notes": "Smooth flight",
    }
    data.update(overrides)
    return data


def test_log_flight_schema_rejects_missing_required_fields() -> None:
    for missing in ("date", "balloon", "launch_time", "site", "outcome"):
        payload = _payload()
        payload.pop(missing)
        with pytest.raises(vol.Invalid):
            LOG_FLIGHT_SCHEMA(payload)


def test_log_flight_schema_defaults_duration() -> None:
    payload = _payload()
    payload.pop("duration_min")
    result = LOG_FLIGHT_SCHEMA(payload)
    assert result["duration_min"] == 90


def test_log_flight_schema_locks_outcome_enum() -> None:
    with pytest.raises(vol.Invalid):
        LOG_FLIGHT_SCHEMA(_payload(outcome="aborted"))


def test_log_flight_schema_enforces_time_format() -> None:
    result = LOG_FLIGHT_SCHEMA(_payload(launch_time="6:5"))
    with pytest.raises(ValueError):
        # normalization path must reject non-24-hour HH:MM input
        from custom_components.flynow.flight_log import _validate_time

        _validate_time(result["launch_time"])


def test_list_flights_schema_rejects_payload() -> None:
    with pytest.raises(vol.Invalid):
        LIST_FLIGHTS_SCHEMA({"unexpected": 1})


@pytest.mark.anyio
async def test_log_and_list_services_persist_and_respond(tmp_path: Path) -> None:
    hass = _Hass(tmp_path)
    await async_register_services(hass)

    response = await hass.services.call("flynow", SERVICE_LOG_FLIGHT, _payload(notes=None))
    entry = response["entry"]
    assert entry["launch_time"] == "06:15"
    assert entry["notes"] == ""
    assert entry["schema_version"] == 1

    disk_file = tmp_path / "flynow_flights.json"
    stored = json.loads(disk_file.read_text(encoding="utf-8"))
    assert len(stored) == 1
    assert stored[0]["date"] == "2026-04-24"

    listed = await hass.services.call("flynow", SERVICE_LIST_FLIGHTS, {})
    assert listed["flights"][0]["id"] == entry["id"]


@pytest.mark.anyio
async def test_history_limit_is_bounded_and_newest_first(tmp_path: Path) -> None:
    hass = _Hass(tmp_path)
    await async_register_services(hass)

    for idx in range(FLIGHT_HISTORY_LIMIT + 10):
        await hass.services.call(
            "flynow",
            SERVICE_LOG_FLIGHT,
            _payload(date=f"2026-04-{(idx % 28) + 1:02d}", launch_time=f"{(idx % 24):02d}:00"),
        )

    listed = await hass.services.call("flynow", SERVICE_LIST_FLIGHTS, {})
    flights = listed["flights"]
    assert len(flights) == FLIGHT_HISTORY_LIMIT
    assert flights[0]["created_at"] >= flights[-1]["created_at"]


@pytest.mark.anyio
async def test_malformed_file_is_backed_up_and_recovered(tmp_path: Path) -> None:
    broken = tmp_path / "flynow_flights.json"
    broken.write_text("{not json", encoding="utf-8")

    hass = _Hass(tmp_path)
    await async_register_services(hass)

    listed = await hass.services.call("flynow", SERVICE_LIST_FLIGHTS, {})
    assert listed["flights"] == []

    backups = list(tmp_path.glob("flynow_flights.json.corrupt-*"))
    assert len(backups) == 1

    await hass.services.call("flynow", SERVICE_LOG_FLIGHT, _payload())
    repaired = json.loads((tmp_path / "flynow_flights.json").read_text(encoding="utf-8"))
    assert len(repaired) == 1


@pytest.mark.anyio
async def test_import_flight_service_returns_uuid_linkage_and_warnings(tmp_path: Path) -> None:
    hass = _Hass(tmp_path)
    await async_register_services(hass)

    imported = await hass.services.call(
        "flynow",
        SERVICE_IMPORT_FLIGHT,
        {
            "format": "csv",
            "source_name": "mixed.csv",
            "raw_payload": (
                "timestamp,latitude,longitude,altitude_m\n"
                "2026-04-24T05:00:00Z,48.1429,17.3776,130\n"
                "2026-04-24T05:15:00Z,bad-value,17.3900,160\n"
                "2026-04-24T05:30:00+00:00,48.1800,17.4100,220\n"
            ),
        },
    )

    assert imported["flight_id"]
    assert imported["sidecar_linked"] is True
    assert imported["imported_point_count"] == 2
    assert len(imported["warnings"]) == 1
    assert imported["warnings"][0]["code"] == "invalid_point"
    assert imported["weather_snapshot"]["weather_missing"] is True
    assert imported["weather_snapshot"]["weather_missing_reason"]

    listed = await hass.services.call("flynow", SERVICE_LIST_FLIGHTS, {})
    assert listed["flights"] == []
