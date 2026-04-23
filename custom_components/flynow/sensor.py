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
        active = (self.coordinator.data or {}).get("active_window")
        return bool(active and active.get("go"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        attrs: dict[str, Any] = {
            "active_window": "none",
            "launch_start": None,
            "launch_end": None,
            "data_last_updated_utc": data.get("data_last_updated_utc"),
            "notification_result": data.get("notification_result", {}),
            "selected_site_id": data.get("selected_site_id"),
            "sites_summary": data.get("sites_summary", {}),
        }
        active = data.get("active_window")
        if active:
            attrs["active_window"] = active.get("type", "none")
            attrs["launch_start"] = active.get("launch_start")
            attrs["launch_end"] = active.get("launch_end")
        for key, item in data.get("windows", {}).items():
            attrs[f"{key}_go"] = item.get("go")
            attrs[f"{key}_launch_start"] = item.get("launch_start")
            attrs[f"{key}_launch_end"] = item.get("launch_end")
            attrs[f"{key}_conditions"] = item.get("conditions", {})
        return attrs
