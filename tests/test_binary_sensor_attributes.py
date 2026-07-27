"""Attribute size guardrails for binary_sensor.flynow_status."""

from __future__ import annotations

import json
from typing import Any

from custom_components.flynow.binary_sensor import (
    FlyNowStatusSensor,
    _active_conditions_by_site,
    _slim_sites_for_attributes,
)
from custom_components.flynow.const import SITE_IDS

RECORDER_ATTR_LIMIT_BYTES = 16_384


def _payload_size_bytes(payload: Any) -> int:
    return len(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def _condition_block() -> dict[str, Any]:
    return {
        "surface_wind_ms": {
            "value": 3.2,
            "threshold": 4.0,
            "ok": True,
            "blocking": True,
        },
        "altitude_wind_ms": {
            "value": 8.1,
            "threshold": 10.0,
            "ok": True,
            "blocking": True,
        },
        "precip_prob": {
            "value": 12.0,
            "threshold": 20.0,
            "ok": True,
            "blocking": True,
        },
        "visibility_km": {
            "value": 10.0,
            "threshold": 5.0,
            "ok": True,
            "blocking": True,
        },
        "fog_risk": {
            "value": "low",
            "threshold": "informational",
            "ok": True,
            "blocking": False,
            "trend": "stable",
            "min_visibility_km": 10.0,
            "max_relative_humidity_pct": 82.0,
            "min_temp_dew_spread_c": 2.5,
        },
    }


def _window(key: str, window_type: str) -> dict[str, Any]:
    return {
        "key": key,
        "type": window_type,
        "go": True,
        "day_start": "04:30",
        "day_end": "21:30",
        "sunrise": "05:00",
        "sunset": "21:00",
        "launch_start": "18:00",
        "launch_end": "18:30",
        "conditions": _condition_block(),
    }


def _build_sites(site_ids: tuple[str, ...] = SITE_IDS) -> dict[str, Any]:
    window_keys = (
        "today_evening",
        "tomorrow_evening",
        "day2_evening",
        "day3_evening",
        "tomorrow_morning",
        "day2_morning",
        "day3_morning",
    )
    labels = {
        "lzmada": "LZMADA — Malý Madaras",
        "katarinka": "Lúka pri Katarínke",
        "nitra-luka": "Lúka pri Nitre",
        "pezinok": "Pezinok",
        "dubova": "Dubová",
        "trnava-kopanka": "Trnava letisko Kopánka",
    }
    sites: dict[str, Any] = {}
    for site_id in site_ids:
        windows = {
            key: _window(key, "evening" if "evening" in key else "morning")
            for key in window_keys
        }
        sites[site_id] = {
            "site_id": site_id,
            "site_name": labels[site_id],
            "kraj_code": "TTSK",
            "elevation_m": 125,
            "windows": windows,
            "active_window": windows["today_evening"],
        }
    return sites


class _Coordinator:
    def __init__(self, data: dict[str, Any]):
        self.data = data
        self.hass = None


def _build_coordinator(sites: dict[str, Any], selected: str = "lzmada") -> _Coordinator:
    return _Coordinator(
        {
            "active_window": sites[selected]["active_window"],
            "windows": sites[selected]["windows"],
            "data_last_updated_utc": "2026-06-16T10:00:00+00:00",
            "notification_result": {
                "sent": False,
                "blocked": False,
                "reason": "notification_targets_not_configured",
                "errors": [],
            },
            "selected_site_id": selected,
            "sites_summary": {
                site_id: {
                    "site_name": site["site_name"],
                    "go": True,
                    "launch_start": "18:00",
                    "launch_end": "18:30",
                    "active_window": "evening",
                    "data_last_updated_utc": "2026-06-16T10:00:00+00:00",
                }
                for site_id, site in sites.items()
            },
            "sites": sites,
        }
    )


def test_slim_sites_keep_only_active_window_per_site() -> None:
    sites = _build_sites()
    slim = _slim_sites_for_attributes(sites)

    assert set(slim) == set(sites)
    for site in slim.values():
        assert len(site["windows"]) == 1
        assert "today_evening" in site["windows"]
        assert "conditions" not in site["windows"]["today_evening"]


def test_active_conditions_by_site_maps_all_sites() -> None:
    sites = _build_sites()
    conditions = _active_conditions_by_site(sites)

    assert set(conditions) == set(sites)
    assert "surface_wind_ms" in conditions["dubova"]


def test_extra_state_attributes_stay_below_recorder_limit_for_six_sites() -> None:
    sites = _build_sites()
    attrs = FlyNowStatusSensor(_build_coordinator(sites)).extra_state_attributes

    attrs_bytes = _payload_size_bytes(attrs)
    assert attrs_bytes <= RECORDER_ATTR_LIMIT_BYTES
    assert set(attrs["site_active_conditions"]) == set(SITE_IDS)
    assert json.dumps(attrs)
