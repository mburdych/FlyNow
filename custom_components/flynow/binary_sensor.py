"""FlyNow binary sensor projection."""

from __future__ import annotations

from typing import Any

from .const import COORDINATOR_DATA

try:
    from homeassistant.components.binary_sensor import BinarySensorEntity
    from homeassistant.helpers.update_coordinator import CoordinatorEntity
except ImportError:  # pragma: no cover
    class BinarySensorEntity:  # type: ignore[no-redef]
        pass

    class CoordinatorEntity:  # type: ignore[no-redef]
        def __init__(self, coordinator):
            self.coordinator = coordinator


async def async_setup_entry(hass: Any, entry: Any, async_add_entities: Any) -> None:
    coordinator = hass.data["flynow"][entry.entry_id][COORDINATOR_DATA]
    async_add_entities([FlyNowStatusSensor(coordinator)])


class FlyNowStatusSensor(CoordinatorEntity, BinarySensorEntity):
    """Single authoritative GO/NO-GO sensor."""

    _attr_name = "FlyNow Status"
    _attr_unique_id = "flynow_status"

    @property
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        active = data.get("active_window")
        if not active:
            selected_site_id = data.get("selected_site_id")
            selected_site = (data.get("sites") or {}).get(selected_site_id, {})
            active = selected_site.get("active_window")
        return bool(active and active.get("go"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        selected_site_id = data.get("selected_site_id")
        selected_site = (data.get("sites") or {}).get(selected_site_id, {})
        active = data.get("active_window") or selected_site.get("active_window")
        windows = data.get("windows") or selected_site.get("windows") or {}
        raw_sites = data.get("sites") or {}
        attrs: dict[str, Any] = {
            "active_window": "none",
            "launch_start": None,
            "launch_end": None,
            "data_last_updated_utc": data.get("data_last_updated_utc"),
            "notification_result": data.get("notification_result", {}),
            "selected_site_id": selected_site_id,
            "sites_summary": data.get("sites_summary", {}),
            "sites": _slim_sites_for_attributes(raw_sites),
            "site_active_conditions": _active_conditions_by_site(raw_sites),
        }
        if active:
            attrs["active_window"] = active.get("type", "none")
            attrs["launch_start"] = active.get("launch_start")
            attrs["launch_end"] = active.get("launch_end")
        for key, item in windows.items():
            attrs[f"{key}_go"] = item.get("go")
            attrs[f"{key}_launch_start"] = item.get("launch_start")
            attrs[f"{key}_launch_end"] = item.get("launch_end")
            attrs[f"{key}_conditions"] = item.get("conditions", {})
        return attrs


def _slim_window_for_attributes(window: dict[str, Any] | None) -> dict[str, Any] | None:
    if not window:
        return None
    return {
        "key": window.get("key"),
        "type": window.get("type"),
        "go": window.get("go"),
        "day_start": window.get("day_start"),
        "day_end": window.get("day_end"),
        "sunrise": window.get("sunrise"),
        "sunset": window.get("sunset"),
        "launch_start": window.get("launch_start"),
        "launch_end": window.get("launch_end"),
    }


def _slim_site_for_attributes(site: dict[str, Any]) -> dict[str, Any]:
    active = site.get("active_window") or {}
    active_key = active.get("key")
    windows = site.get("windows") or {}
    slim_active = _slim_window_for_attributes(active)
    slim_windows: dict[str, Any] = {}
    if active_key and active_key in windows:
        slim_windows[active_key] = _slim_window_for_attributes(windows[active_key])
    elif slim_active:
        window_key = active_key or str(active.get("type") or "active")
        slim_windows[window_key] = slim_active
    return {
        "site_id": site.get("site_id"),
        "site_name": site.get("site_name"),
        "active_window": slim_active,
        "windows": slim_windows,
    }


def _slim_sites_for_attributes(sites: dict[str, Any]) -> dict[str, Any]:
    return {site_id: _slim_site_for_attributes(site) for site_id, site in sites.items()}


def _active_conditions_by_site(sites: dict[str, Any]) -> dict[str, Any]:
    """Per-site active-window conditions without duplicating full window payloads."""
    conditions_by_site: dict[str, Any] = {}
    for site_id, site in sites.items():
        active = site.get("active_window") or {}
        active_key = active.get("key")
        windows = site.get("windows") or {}
        window = windows.get(active_key, active) if active_key else active
        if isinstance(window, dict):
            conditions = window.get("conditions")
            if conditions:
                conditions_by_site[site_id] = conditions
    return conditions_by_site
