from custom_components.flynow.sensor import FlyNowStatusSensor


class _Coordinator:
    def __init__(self):
        self.data = {
            "active_window": {"go": True, "type": "evening", "launch_start": "18:00", "launch_end": "18:30"},
            "windows": {"today_evening": {"go": True, "launch_start": "18:00", "launch_end": "18:30", "conditions": {}}},
            "data_last_updated_utc": "2026-04-22T10:00:00+00:00",
            "notification_result": {"reason": "sent"},
            "decision_snapshot": {
                "observed_source": None,
                "weather_missing": False,
                "weather_missing_reason": None,
                "corrections": [],
            },
            "selected_site_id": "lzmada",
            "sites_summary": {
                "lzmada": {"go": True},
                "katarinka": {"go": False},
                "nitra-luka": {"go": True},
            },
        }


def test_sensor_projects_state():
    sensor = FlyNowStatusSensor(_Coordinator())
    assert sensor.is_on is True
    attrs = sensor.extra_state_attributes
    assert attrs["active_window"] == "evening"
    assert "today_evening_go" in attrs
    assert attrs["data_last_updated_utc"] == "2026-04-22T10:00:00+00:00"
    assert attrs["selected_site_id"] == "lzmada"
    assert set(attrs["sites_summary"]) == {"lzmada", "katarinka", "nitra-luka"}
    assert attrs["correlation_summary"]["weather_missing"] is False


def test_sensor_projects_legacy_keys_from_selected_site_payload() -> None:
    coordinator = _Coordinator()
    coordinator.data["active_window"] = None
    coordinator.data["windows"] = {}
    coordinator.data["selected_site_id"] = "katarinka"
    coordinator.data["sites"] = {
        "katarinka": {
            "active_window": {
                "go": False,
                "type": "tomorrow_morning",
                "launch_start": "05:30",
                "launch_end": "06:00",
            },
            "windows": {
                "tomorrow_morning": {
                    "go": False,
                    "launch_start": "05:30",
                    "launch_end": "06:00",
                    "conditions": {"surface_wind_ms": {"ok": False}},
                }
            },
        }
    }

    sensor = FlyNowStatusSensor(coordinator)
    assert sensor.is_on is False
    attrs = sensor.extra_state_attributes
    assert attrs["active_window"] == "tomorrow_morning"
    assert attrs["launch_start"] == "05:30"
    assert attrs["launch_end"] == "06:00"
    assert attrs["tomorrow_morning_go"] is False
