"""Flight log services and atomic JSON persistence."""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
import tempfile
import time as time_module
from datetime import UTC, date, datetime, time
from pathlib import Path
from typing import Any
from uuid import uuid4

import voluptuous as vol

from .const import (
    BALLOON_IDS,
    DOMAIN,
    FLIGHT_HISTORY_LIMIT,
    FLIGHT_LOG_FILENAME,
    FLIGHT_OUTCOMES,
    SERVICE_IMPORT_FLIGHT,
    SERVICE_LIST_FLIGHTS,
    SERVICE_LOG_FLIGHT,
    SITE_IDS,
)
from .flight_import import parse_import_payload
from .flight_sidecar_store import FlightSidecarStore

try:
    from homeassistant.core import SupportsResponse
except ImportError:  # pragma: no cover
    class SupportsResponse:
        ONLY = "only"


_LOGGER = logging.getLogger(__name__)
_STORE_KEY = "flight_log_store"
_SIDECAR_STORE_KEY = "flight_sidecar_store"

LOG_FLIGHT_SCHEMA = vol.Schema(
    {
        vol.Required("date"): vol.Coerce(str),
        vol.Required("balloon"): vol.In(BALLOON_IDS),
        vol.Required("launch_time"): vol.Coerce(str),
        vol.Optional("duration_min", default=90): vol.All(
            vol.Coerce(int), vol.Range(min=15, max=300)
        ),
        vol.Required("site"): vol.In(SITE_IDS),
        vol.Required("outcome"): vol.In(FLIGHT_OUTCOMES),
        vol.Optional("notes", default=""): vol.Any(None, vol.All(str, vol.Length(max=2000))),
    },
    extra=vol.PREVENT_EXTRA,
)

LIST_FLIGHTS_SCHEMA = vol.Schema({}, extra=vol.PREVENT_EXTRA)
IMPORT_FLIGHT_SCHEMA = vol.Schema(
    {
        vol.Required("format"): vol.In(("csv", "gpx")),
        vol.Required("source_name"): vol.All(str, vol.Length(min=1, max=255)),
        vol.Required("raw_payload"): vol.All(str, vol.Length(min=1)),
        vol.Optional("flight_id"): vol.All(str, vol.Length(min=1, max=128)),
    },
    extra=vol.PREVENT_EXTRA,
)


def _validate_date(value: str) -> str:
    date.fromisoformat(value)
    return value


def _validate_time(value: str) -> str:
    parsed = time.fromisoformat(value)
    return parsed.strftime("%H:%M")


class FlightLogStore:
    """Read/write flight log records with atomic persistence."""

    def __init__(self, hass: Any) -> None:
        self._hass = hass
        self._path = Path(hass.config.path(FLIGHT_LOG_FILENAME))
        self._lock = asyncio.Lock()
        self._loaded = False
        self._entries: list[dict[str, Any]] = []

    async def async_append(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with self._lock:
            await self._async_load_locked()
            entry = self._normalize(payload)
            next_entries = [*self._entries, entry]
            await self._async_write(next_entries)
            self._entries = next_entries
            return entry

    async def async_list(self) -> list[dict[str, Any]]:
        async with self._lock:
            await self._async_load_locked()
            newest = list(reversed(self._entries))
            return newest[:FLIGHT_HISTORY_LIMIT]

    async def _async_load_locked(self) -> None:
        if self._loaded:
            return
        self._entries = await self._hass.async_add_executor_job(self._load_entries_sync)
        self._loaded = True

    def _load_entries_sync(self) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        try:
            with self._path.open(encoding="utf-8") as handle:
                data = json.load(handle)
        except json.JSONDecodeError:
            backup_path = self._path.with_name(
                f"{FLIGHT_LOG_FILENAME}.corrupt-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
            )
            shutil.move(str(self._path), str(backup_path))
            _LOGGER.warning(
                "Malformed flight log recovered by moving file to %s", backup_path
            )
            return []
        if not isinstance(data, list):
            return []
        return [entry for entry in data if isinstance(entry, dict)]

    async def _async_write(self, entries: list[dict[str, Any]]) -> None:
        await self._hass.async_add_executor_job(self._write_entries_sync, entries)

    def _write_entries_sync(self, entries: list[dict[str, Any]]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=self._path.parent,
            delete=False,
            suffix=".tmp",
        ) as handle:
            json.dump(entries, handle, ensure_ascii=False, indent=2)
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
        normalized_date = _validate_date(str(payload["date"]))
        normalized_time = _validate_time(str(payload["launch_time"]))
        return {
            "id": str(uuid4()),
            "created_at": datetime.now(UTC).isoformat(),
            "schema_version": 1,
            "date": normalized_date,
            "balloon": str(payload["balloon"]),
            "launch_time": normalized_time,
            "duration_min": int(payload["duration_min"]),
            "site": str(payload["site"]),
            "outcome": str(payload["outcome"]),
            "notes": str(payload.get("notes") or ""),
        }


async def async_register_services(hass: Any) -> None:
    """Register flight log domain services once."""
    hass.data.setdefault(DOMAIN, {})
    if hass.services.has_service(DOMAIN, SERVICE_LOG_FLIGHT):
        return

    store = FlightLogStore(hass)
    sidecar_store = FlightSidecarStore(hass)
    hass.data[DOMAIN][_STORE_KEY] = store
    hass.data[DOMAIN][_SIDECAR_STORE_KEY] = sidecar_store

    async def _handle_log_flight(call: Any) -> dict[str, Any]:
        candidate_payload = dict(call.data)
        if candidate_payload.get("notes") is None:
            candidate_payload["notes"] = ""
        payload = LOG_FLIGHT_SCHEMA(candidate_payload)
        entry = await store.async_append(payload)
        return {"entry": entry}

    async def _handle_list_flights(call: Any) -> dict[str, Any]:
        LIST_FLIGHTS_SCHEMA(dict(call.data))
        flights = await store.async_list()
        return {"flights": flights}

    async def _handle_import_flight(call: Any) -> dict[str, Any]:
        payload = IMPORT_FLIGHT_SCHEMA(dict(call.data))
        flight_id = payload.get("flight_id") or str(uuid4())
        normalized = parse_import_payload(
            str(payload["format"]),
            str(payload["raw_payload"]),
            source_name=str(payload["source_name"]),
        )
        sidecar_record = await sidecar_store.async_upsert(
            {
                "flight_id": flight_id,
                "import_source": payload["source_name"],
                "points": normalized["points"],
                "warnings": normalized["warnings"],
            }
        )
        return {
            "flight_id": flight_id,
            "schema_version": sidecar_record["schema_version"],
            "imported_point_count": sidecar_record["summary"]["point_count"],
            "warnings": normalized["warnings"],
            "sidecar_linked": True,
            "weather_missing": True,
            "weather_missing_reason": "snapshot_not_captured_yet",
        }

    hass.services.async_register(
        DOMAIN,
        SERVICE_LOG_FLIGHT,
        _handle_log_flight,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_LIST_FLIGHTS,
        _handle_list_flights,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_IMPORT_FLIGHT,
        _handle_import_flight,
        supports_response=SupportsResponse.ONLY,
    )
