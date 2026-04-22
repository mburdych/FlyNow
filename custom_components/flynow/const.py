"""Constants for the FlyNow integration."""

from __future__ import annotations

DOMAIN = "flynow"
PLATFORMS = ["binary_sensor"]

CONF_SITE_NAME = "site_name"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_FLIGHT_DURATION_MIN = "flight_duration_min"
CONF_PREP_TIME_MIN = "prep_time_min"
CONF_UPDATE_INTERVAL_MIN = "update_interval_min"
CONF_MAX_SURFACE_WIND_MS = "max_surface_wind_ms"
CONF_MAX_ALTITUDE_WIND_MS = "max_altitude_wind_ms"
CONF_MIN_CEILING_M = "min_ceiling_m"
CONF_MAX_PRECIP_PROB_PCT = "max_precip_prob_pct"
CONF_MIN_VISIBILITY_KM = "min_visibility_km"
CONF_CREW_NOTIFIER = "crew_notifier"
CONF_PILOT_NOTIFIER = "pilot_notifier"
CONF_WHATSAPP_NOTIFIER = "whatsapp_notifier"
CONF_CALENDAR_ENTITY = "calendar_entity"

DEFAULT_SITE_NAME = "Maly Madaras"
DEFAULT_LATITUDE = 48.142866
DEFAULT_LONGITUDE = 17.377625
DEFAULT_FLIGHT_DURATION_MIN = 90
DEFAULT_PREP_TIME_MIN = 30
DEFAULT_UPDATE_INTERVAL_MIN = 60
DEFAULT_MAX_SURFACE_WIND_MS = 4.0
DEFAULT_MAX_ALTITUDE_WIND_MS = 10.0
DEFAULT_MIN_CEILING_M = 500
DEFAULT_MAX_PRECIP_PROB_PCT = 20
DEFAULT_MIN_VISIBILITY_KM = 5.0
DEFAULT_CREW_NOTIFIER = "notify.crew_phone"
DEFAULT_PILOT_NOTIFIER = "notify.pilot_phone"
DEFAULT_WHATSAPP_NOTIFIER = "notify.whatsapp_group"
DEFAULT_CALENDAR_ENTITY = "calendar.flynow"

MIN_FLIGHT_DURATION_MIN = 60
MAX_FLIGHT_DURATION_MIN = 90
MIN_PREP_TIME_MIN = 10
MAX_PREP_TIME_MIN = 60
MIN_UPDATE_INTERVAL_MIN = 30
MAX_UPDATE_INTERVAL_MIN = 60

MIN_SURFACE_WIND_MS = 0.0
MAX_SURFACE_WIND_MS = 20.0
MIN_ALTITUDE_WIND_MS = 0.0
MAX_ALTITUDE_WIND_MS = 30.0
MIN_CEILING_M = 100
MAX_CEILING_M = 5000
MIN_PRECIP_PROB_PCT = 0
MAX_PRECIP_PROB_PCT = 100
MIN_VISIBILITY_KM = 0.0
MAX_VISIBILITY_KM = 30.0

SLOVAK_DAY_NAMES = {
    0: "Pondelok",
    1: "Utorok",
    2: "Streda",
    3: "Stvrtok",
    4: "Piatok",
    5: "Sobota",
    6: "Nedela",
}

WINDOW_KEYS = (
    "today_evening",
    "tomorrow_evening",
    "day2_evening",
    "day3_evening",
    "tomorrow_morning",
    "day2_morning",
    "day3_morning",
)

COORDINATOR_DATA = "coordinator_data"

NOTIF_DEDUP_COOLDOWN_SEC = 3600
NOTIF_WINDOW_ID_SEP = "@"
NOTIF_WINDOW_ID_FORMAT = "{window_key}@{launch_start}"
