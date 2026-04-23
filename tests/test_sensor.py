from custom_components.flynow.sensor import FlyNowStatusSensor


class _Coordinator:
    def __init__(self):
        self.data = {
            "active_window": {"go": True, "type": "evening", "launch_start": "18:00", "launch_end": "18:30"},
            "windows": {"today_evening": {"go": True, "launch_start": "18:00", "launch_end": "18:30", "conditions": {}}},
            "data_last_updated_utc": "2026-04-22T10:00:00+00:00",
            "notification_result": {"reason": "sent"},
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
