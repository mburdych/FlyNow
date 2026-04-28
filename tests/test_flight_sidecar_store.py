from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from custom_components.flynow.flight_sidecar_store import FlightSidecarStore


class _Config:
    def __init__(self, root: Path) -> None:
        self._root = root

    def path(self, name: str) -> str:
        return str(self._root / name)


class _Hass:
    def __init__(self, root: Path) -> None:
        self.config = _Config(root)

    async def async_add_executor_job(self, target: Any, *args: Any) -> Any:
        return target(*args)


def _sample_payload(flight_id: str, source_name: str = "sample.csv") -> dict[str, Any]:
    return {
        "flight_id": flight_id,
        "import_source": source_name,
        "points": [
            {
                "timestamp_utc": "2026-04-24T05:00:00+00:00",
                "latitude": 48.1429,
                "longitude": 17.3776,
                "altitude_m": 130.0,
            },
            {
                "timestamp_utc": "2026-04-24T05:15:00+00:00",
                "latitude": 48.15,
                "longitude": 17.39,
                "altitude_m": 160.0,
            },
        ],
        "warnings": [{"code": "invalid_point", "row": 3}],
    }


@pytest.mark.anyio
async def test_sidecar_upsert_creates_uuid_keyed_record(tmp_path: Path) -> None:
    store = FlightSidecarStore(_Hass(tmp_path))

    saved = await store.async_upsert(_sample_payload("flight-001"))

    assert saved["flight_id"] == "flight-001"
    assert saved["summary"]["point_count"] == 2
    assert saved["summary"]["warning_count"] == 1

    disk_file = tmp_path / "flynow_flight_sidecar.json"
    persisted = json.loads(disk_file.read_text(encoding="utf-8"))
    assert persisted["records"]["flight-001"]["summary"]["point_count"] == 2


@pytest.mark.anyio
async def test_sidecar_upsert_replaces_existing_uuid_record(tmp_path: Path) -> None:
    store = FlightSidecarStore(_Hass(tmp_path))
    await store.async_upsert(_sample_payload("flight-002"))

    updated_payload = _sample_payload("flight-002", source_name="track.gpx")
    updated_payload["warnings"] = []
    updated_payload["points"] = updated_payload["points"][:1]
    saved = await store.async_upsert(updated_payload)

    assert saved["import_source"] == "track.gpx"
    assert saved["summary"]["point_count"] == 1
    assert saved["summary"]["warning_count"] == 0
