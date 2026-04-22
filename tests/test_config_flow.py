from custom_components.flynow import const
from custom_components.flynow.config_flow import FlyNowConfigFlow


def test_manifest_and_constants_contract():
    assert const.DOMAIN == "flynow"
    assert const.CONF_SITE_NAME in (
        "site_name",
    )
    assert const.MIN_UPDATE_INTERVAL_MIN == 30
    assert const.MAX_UPDATE_INTERVAL_MIN == 60


def test_no_contact_fields_in_phase_one_constants():
    keys = [k for k in dir(const) if k.startswith("CONF_")]
    assert "CONF_PHONE" not in keys
    assert "CONF_WHATSAPP" not in keys


def test_notification_constants_exist_for_phase_two():
    assert const.CONF_CREW_NOTIFIER == "crew_notifier"
    assert const.CONF_PILOT_NOTIFIER == "pilot_notifier"
    assert const.CONF_WHATSAPP_NOTIFIER == "whatsapp_notifier"
    assert const.CONF_CALENDAR_ENTITY == "calendar_entity"
    assert const.NOTIF_DEDUP_COOLDOWN_SEC == 3600
    assert const.NOTIF_WINDOW_ID_FORMAT == "{window_key}@{launch_start}"


def test_notification_step_rejects_blank_notifier_targets():
    flow = FlyNowConfigFlow()
    flow._data = {const.CONF_SITE_NAME: "Test Site"}

    result = __import__("asyncio").run(
        flow.async_step_notifications(
            {
                const.CONF_CREW_NOTIFIER: "",
                const.CONF_PILOT_NOTIFIER: "notify.pilot",
                const.CONF_WHATSAPP_NOTIFIER: "notify.whatsapp",
                const.CONF_CALENDAR_ENTITY: "calendar.flynow",
            }
        )
    )

    assert result["type"] == "form"
    assert result["errors"][const.CONF_CREW_NOTIFIER] == "required"
