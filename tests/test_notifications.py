from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from custom_components.flynow.notifications import dispatch_go_transition_notifications


class _Services:
    def __init__(self, fail_notify_target: str | None = None) -> None:
        self.calls: list[tuple[str, str, dict]] = []
        self._fail_notify_target = fail_notify_target

    async def async_call(
        self, domain: str, service: str, service_data: dict, blocking: bool = True
    ) -> None:
        self.calls.append((domain, service, service_data))
        if (
            self._fail_notify_target
            and domain == "notify"
            and service_data.get("entity_id") == self._fail_notify_target
        ):
            raise RuntimeError("simulated channel failure")


class _Hass:
    def __init__(self, fail_notify_target: str | None = None) -> None:
        self.services = _Services(fail_notify_target=fail_notify_target)


def _window(go: bool, launch_start: str = "2026-04-22T18:30:00") -> dict:
    return {
        "go": go,
        "launch_start": launch_start,
        "launch_end": "2026-04-22T20:00:00",
        "conditions": {"surface_wind_ms": {"value": 3.2, "threshold": 4.0, "pass": True}},
    }


@pytest.mark.asyncio
async def test_first_go_transition_sends_all_channels() -> None:
    hass = _Hass()
    dedup_store: dict[str, datetime] = {}
    config = {
        "crew_notifier": "notify.crew_phone",
        "pilot_notifier": "notify.pilot_phone",
        "whatsapp_notifier": "notify.whatsapp_group",
        "calendar_entity": "calendar.flynow",
        "site_name": "Test Site",
    }

    result = await dispatch_go_transition_notifications(
        hass=hass,
        config=config,
        previous_windows={"tomorrow_morning": _window(False)},
        current_windows={"tomorrow_morning": _window(True)},
        dedup_store=dedup_store,
        now_utc=datetime(2026, 4, 22, 16, 0, tzinfo=UTC),
    )

    assert result["sent"] is True
    assert len(hass.services.calls) == 4
    assert len(dedup_store) == 1


@pytest.mark.asyncio
async def test_duplicate_transition_blocked_within_cooldown() -> None:
    hass = _Hass()
    now_utc = datetime(2026, 4, 22, 16, 0, tzinfo=UTC)
    dedup_store = {"tomorrow_morning@2026-04-22T18:30:00": now_utc}
    config = {
        "crew_notifier": "notify.crew_phone",
        "pilot_notifier": "notify.pilot_phone",
        "whatsapp_notifier": "notify.whatsapp_group",
        "calendar_entity": "calendar.flynow",
        "site_name": "Test Site",
    }

    result = await dispatch_go_transition_notifications(
        hass=hass,
        config=config,
        previous_windows={"tomorrow_morning": _window(False)},
        current_windows={"tomorrow_morning": _window(True)},
        dedup_store=dedup_store,
        now_utc=now_utc + timedelta(minutes=30),
    )

    assert result["sent"] is False
    assert result["blocked"] is True
    assert hass.services.calls == []


@pytest.mark.asyncio
async def test_duplicate_transition_allowed_after_cooldown() -> None:
    hass = _Hass()
    now_utc = datetime(2026, 4, 22, 16, 0, tzinfo=UTC)
    dedup_store = {"tomorrow_morning@2026-04-22T18:30:00": now_utc}
    config = {
        "crew_notifier": "notify.crew_phone",
        "pilot_notifier": "notify.pilot_phone",
        "whatsapp_notifier": "notify.whatsapp_group",
        "calendar_entity": "calendar.flynow",
        "site_name": "Test Site",
    }

    result = await dispatch_go_transition_notifications(
        hass=hass,
        config=config,
        previous_windows={"tomorrow_morning": _window(False)},
        current_windows={"tomorrow_morning": _window(True)},
        dedup_store=dedup_store,
        now_utc=now_utc + timedelta(hours=2),
    )

    assert result["sent"] is True
    assert len(hass.services.calls) == 4


@pytest.mark.asyncio
async def test_single_channel_failure_does_not_block_others() -> None:
    hass = _Hass(fail_notify_target="notify.pilot_phone")
    dedup_store: dict[str, datetime] = {}
    config = {
        "crew_notifier": "notify.crew_phone",
        "pilot_notifier": "notify.pilot_phone",
        "whatsapp_notifier": "notify.whatsapp_group",
        "calendar_entity": "calendar.flynow",
        "site_name": "Test Site",
    }

    result = await dispatch_go_transition_notifications(
        hass=hass,
        config=config,
        previous_windows={"tomorrow_morning": _window(False)},
        current_windows={"tomorrow_morning": _window(True)},
        dedup_store=dedup_store,
        now_utc=datetime(2026, 4, 22, 16, 0, tzinfo=UTC),
    )

    assert result["sent"] is True
    assert any("pilot_notifier" in item for item in result["errors"])
    assert len(hass.services.calls) == 4
