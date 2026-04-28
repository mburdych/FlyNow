"""Flight sidecar persistence keyed by stable flight UUID."""

from __future__ import annotations

import asyncio
import json
import shutil
import tempfile
import time as time_module
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .const import FLIGHT_SIDECAR_FILENAME


class FlightSidecarStore:
    """Store raw import payloads with derived summaries in atomic sidecar file."""

    def __init__(self, hass: Any) -> None:
        self._hass = hass
        self._path = Path(hass.config.path(FLIGHT_SIDECAR_FILENAME))
        self._lock = asyncio.Lock()
        self._loaded = False
        self._records: dict[str, dict[str, Any]] = {}

    async def async_upsert(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with self._lock:
            await self._async_load_locked()
            record = self._normalize(payload)
            self._records[record["flight_id"]] = record
            await self._hass.async_add_executor_job(self._write_records_sync, self._records)
            return record

    async def async_get(self, flight_id: str) -> dict[str, Any] | None:
        async with self._lock:
            await self._async_load_locked()
            record = self._records.get(flight_id)
            return dict(record) if record else None

    async def _async_load_locked(self) -> None:
        if self._loaded:
            return
        self._records = await self._hass.async_add_executor_job(self._load_records_sync)
        self._loaded = True

    def _load_records_sync(self) -> dict[str, dict[str, Any]]:
        if not self._path.exists():
            return {}
        try:
            with self._path.open(encoding="utf-8") as handle:
                raw = json.load(handle)
        except json.JSONDecodeError:
            backup_path = self._path.with_name(
                f"{FLIGHT_SIDECAR_FILENAME}.corrupt-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
            )
            shutil.move(str(self._path), str(backup_path))
            return {}
        if not isinstance(raw, dict):
            return {}
        records = raw.get("records", {})
        if not isinstance(records, dict):
            return {}
        return {
            str(key): value
            for key, value in records.items()
            if isinstance(key, str) and isinstance(value, dict)
        }

    def _write_records_sync(self, records: dict[str, dict[str, Any]]) -> None:
        payload = {
            "schema_version": 1,
            "updated_at": datetime.now(UTC).isoformat(),
            "records": records,
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=self._path.parent,
            delete=False,
            suffix=".tmp",
        ) as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            temp_path = Path(handle.name)
        for attempt in range(5):
            try:
                temp_path.replace(self._path)
                break
            except PermissionError:
                if attempt == 4:
                    raise
                time_module.sleep(0.02 * (attempt + 1))

    def _normalize(self, payload: dict[str, Any]) -> dict[str, Any]:
        flight_id = str(payload["flight_id"])
        points = [dict(point) for point in payload.get("points", []) if isinstance(point, dict)]
        warnings = [
            dict(warning)
            for warning in payload.get("warnings", [])
            if isinstance(warning, dict)
        ]

        first_point = points[0] if points else {}
        last_point = points[-1] if points else {}
        return {
            "flight_id": flight_id,
            "schema_version": 1,
            "created_at": datetime.now(UTC).isoformat(),
            "import_source": str(payload.get("import_source", "unknown")),
            "warnings": warnings,
            "points": points,
            "summary": {
                "point_count": len(points),
                "warning_count": len(warnings),
                "start_timestamp_utc": first_point.get("timestamp_utc"),
                "end_timestamp_utc": last_point.get("timestamp_utc"),
                "start_coordinate": {
                    "latitude": first_point.get("latitude"),
                    "longitude": first_point.get("longitude"),
                }
                if first_point
                else None,
                "end_coordinate": {
                    "latitude": last_point.get("latitude"),
                    "longitude": last_point.get("longitude"),
                }
                if last_point
                else None,
            },
        }
