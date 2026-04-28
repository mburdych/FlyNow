from __future__ import annotations

from datetime import UTC, datetime

import pytest

from custom_components.flynow.flight_import import (
    ImportValidationError,
    parse_import_payload,
)


def _csv_payload(rows: list[str]) -> str:
    return "timestamp,latitude,longitude,altitude_m\n" + "\n".join(rows)


def test_parse_csv_accepts_timezone_safe_points() -> None:
    payload = _csv_payload(
        [
            "2026-04-24T05:00:00Z,48.1429,17.3776,130",
            "2026-04-24T05:15:00+00:00,48.1500,17.3900,160",
        ]
    )

    result = parse_import_payload("csv", payload, source_name="sample.csv")

    assert result["format"] == "csv"
    assert len(result["points"]) == 2
    assert result["warnings"] == []
    first_point = result["points"][0]
    assert first_point["timestamp_utc"] == datetime(2026, 4, 24, 5, 0, tzinfo=UTC).isoformat()


def test_parse_csv_rejects_naive_timestamp() -> None:
    payload = _csv_payload(["2026-04-24T05:00:00,48.1429,17.3776,130"])

    with pytest.raises(ImportValidationError, match="timezone"):
        parse_import_payload("csv", payload, source_name="naive.csv")


def test_parse_csv_drops_invalid_points_with_warnings() -> None:
    payload = _csv_payload(
        [
            "2026-04-24T05:00:00Z,48.1429,17.3776,130",
            "2026-04-24T05:15:00Z,not-a-lat,17.3900,160",
            "2026-04-24T05:30:00+00:00,48.1800,17.4100,220",
        ]
    )

    result = parse_import_payload("csv", payload, source_name="mixed.csv")

    assert len(result["points"]) == 2
    assert len(result["warnings"]) == 1
    warning = result["warnings"][0]
    assert warning["row"] == 3
    assert warning["code"] == "invalid_point"


def test_parse_gpx_supports_track_points() -> None:
    payload = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="pytest" xmlns="http://www.topografix.com/GPX/1/1">
  <trk>
    <name>Test Track</name>
    <trkseg>
      <trkpt lat="48.1429" lon="17.3776">
        <ele>130</ele>
        <time>2026-04-24T05:00:00Z</time>
      </trkpt>
      <trkpt lat="48.1500" lon="17.3900">
        <ele>160</ele>
        <time>2026-04-24T05:15:00+00:00</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>
"""
    result = parse_import_payload("gpx", payload, source_name="track.gpx")

    assert result["format"] == "gpx"
    assert len(result["points"]) == 2
    assert result["warnings"] == []
