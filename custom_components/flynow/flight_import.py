"""GPX/CSV import parsing and canonical validation."""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from io import StringIO
from typing import Any
import xml.etree.ElementTree as ET

from .const import IMPORT_MAX_FILE_SIZE_BYTES, IMPORT_MAX_POINTS

_REQUIRED_CSV_HEADERS = ("timestamp", "latitude", "longitude")


class ImportValidationError(ValueError):
    """Raised when the whole import payload is invalid."""


def parse_import_payload(
    file_format: str,
    raw_payload: str,
    source_name: str,
) -> dict[str, Any]:
    """Parse GPX/CSV import payload and return normalized points."""
    if len(raw_payload.encode("utf-8")) > IMPORT_MAX_FILE_SIZE_BYTES:
        raise ImportValidationError("Import payload exceeds configured file size limit.")

    format_key = file_format.strip().lower()
    if format_key == "csv":
        points, warnings = _parse_csv(raw_payload, source_name=source_name)
    elif format_key == "gpx":
        points, warnings = _parse_gpx(raw_payload)
    else:
        raise ImportValidationError(f"Unsupported import format: {file_format}")

    if not points:
        if warnings:
            first_message = str(warnings[0].get("message") or "").lower()
            if "timezone" in first_message:
                raise ImportValidationError(
                    "Point timestamp must include timezone offset (UTC or explicit offset)."
                )
        raise ImportValidationError("Import produced no valid points.")

    return {
        "format": format_key,
        "source_name": source_name,
        "points": points,
        "warnings": warnings,
    }


def _parse_csv(raw_payload: str, source_name: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    reader = csv.DictReader(StringIO(raw_payload))
    headers = tuple(reader.fieldnames or ())
    if not headers:
        raise ImportValidationError("CSV import is missing header row.")
    for required in _REQUIRED_CSV_HEADERS:
        if required not in headers:
            raise ImportValidationError(f"CSV import missing required column: {required}")

    points: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    for row_index, row in enumerate(reader, start=2):
        if len(points) >= IMPORT_MAX_POINTS:
            raise ImportValidationError("Import exceeds maximum allowed point count.")
        try:
            points.append(
                _normalize_point(
                    row["timestamp"],
                    row["latitude"],
                    row["longitude"],
                    row.get("altitude_m"),
                )
            )
        except ImportValidationError as err:
            warnings.append(
                {
                    "code": "invalid_point",
                    "row": row_index,
                    "message": _sanitize_echo(str(err)),
                    "source": source_name,
                }
            )

    return points, warnings


def _parse_gpx(raw_payload: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    try:
        root = ET.fromstring(raw_payload)
    except ET.ParseError as err:
        raise ImportValidationError("GPX payload is not valid XML.") from err

    namespace = {"gpx": "http://www.topografix.com/GPX/1/1"}
    points: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    for index, point in enumerate(root.findall(".//gpx:trkpt", namespace), start=1):
        if len(points) >= IMPORT_MAX_POINTS:
            raise ImportValidationError("Import exceeds maximum allowed point count.")
        latitude = point.attrib.get("lat")
        longitude = point.attrib.get("lon")
        elevation = point.findtext("gpx:ele", default=None, namespaces=namespace)
        timestamp = point.findtext("gpx:time", default=None, namespaces=namespace)
        try:
            points.append(_normalize_point(timestamp, latitude, longitude, elevation))
        except ImportValidationError as err:
            warnings.append(
                {
                    "code": "invalid_point",
                    "row": index,
                    "message": _sanitize_echo(str(err)),
                    "source": "gpx",
                }
            )
    return points, warnings


def _normalize_point(
    timestamp_value: str | None,
    latitude_value: str | None,
    longitude_value: str | None,
    altitude_value: str | None,
) -> dict[str, Any]:
    if timestamp_value is None:
        raise ImportValidationError("Point timestamp is required.")
    timestamp = _normalize_timestamp(timestamp_value)
    try:
        latitude = float(latitude_value)  # type: ignore[arg-type]
        longitude = float(longitude_value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as err:
        raise ImportValidationError("Point latitude/longitude must be numeric.") from err

    if not -90 <= latitude <= 90:
        raise ImportValidationError("Point latitude out of range.")
    if not -180 <= longitude <= 180:
        raise ImportValidationError("Point longitude out of range.")

    altitude_m: float | None = None
    if altitude_value not in (None, ""):
        try:
            altitude_m = float(altitude_value)
        except ValueError as err:
            raise ImportValidationError("Point altitude must be numeric when present.") from err

    return {
        "timestamp_utc": timestamp.astimezone(UTC).isoformat(),
        "latitude": latitude,
        "longitude": longitude,
        "altitude_m": altitude_m,
    }


def _normalize_timestamp(value: str) -> datetime:
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as err:
        raise ImportValidationError("Point timestamp must use ISO-8601 format.") from err

    if parsed.tzinfo is None:
        raise ImportValidationError(
            "Point timestamp must include timezone offset (UTC or explicit offset)."
        )
    return parsed


def _sanitize_echo(value: str) -> str:
    if not value:
        return "Unknown point validation failure."
    if value[0] in ("=", "+", "-", "@"):
        return "'" + value
    return value
