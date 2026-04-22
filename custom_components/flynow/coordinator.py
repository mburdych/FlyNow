"""DataUpdateCoordinator implementation for FlyNow."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import aiohttp

from .analyzer import analyze_window
from .const import (
    CONF_CALENDAR_ENTITY,
    CONF_CREW_NOTIFIER,
    CONF_FLIGHT_DURATION_MIN,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_MAX_ALTITUDE_WIND_MS,
    CONF_MAX_PRECIP_PROB_PCT,
    CONF_PILOT_NOTIFIER,
    CONF_MAX_SURFACE_WIND_MS,
    CONF_MIN_CEILING_M,
    CONF_MIN_VISIBILITY_KM,
    CONF_SITE_NAME,
    CONF_PREP_TIME_MIN,
    CONF_UPDATE_INTERVAL_MIN,
    CONF_WHATSAPP_NOTIFIER,
)
from .notifications import dispatch_go_transition_notifications
from .open_meteo import OpenMeteoError, fetch_forecast
from .windows import build_windows

try:
    from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
except ImportError:  # pragma: no cover
    class UpdateFailed(Exception):
        pass

    class DataUpdateCoordinator:
        def __init__(self, hass, logger, name, update_interval):
            self.hass = hass
            self.data = None
            self.update_interval = update_interval

        async def async_config_entry_first_refresh(self):
            self.data = await self._async_update_data()

        async def async_request_refresh(self):
            self.data = await self._async_update_data()


class FlyNowCoordinator(DataUpdateCoordinator):
    """Fetches forecast data and projects all window decisions."""

    def __init__(self, hass: Any, config: dict[str, Any]):
        interval = timedelta(minutes=int(config[CONF_UPDATE_INTERVAL_MIN]))
        super().__init__(hass, logger=None, name="flynow", update_interval=interval)
        self._config = config
        self._previous_windows: dict[str, dict[str, Any]] = {}
        self._notification_dedup: dict[str, datetime] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            async with aiohttp.ClientSession() as session:
                payload = await fetch_forecast(
                    session, self._config[CONF_LATITUDE], self._config[CONF_LONGITUDE]
                )
        except OpenMeteoError as err:
            raise UpdateFailed(str(err)) from err

        now_local = datetime.now()
        now_utc = datetime.now(UTC)
        sunrise = [datetime.fromisoformat(v) for v in payload["daily"]["sunrise"][:4]]
        sunset = [datetime.fromisoformat(v) for v in payload["daily"]["sunset"][:4]]
        windows = build_windows(
            now_local=now_local,
            sunrise_by_day=sunrise,
            sunset_by_day=sunset,
            flight_duration_min=int(self._config[CONF_FLIGHT_DURATION_MIN]),
            prep_time_min=int(self._config[CONF_PREP_TIME_MIN]),
        )
        thresholds = {
            "max_surface_wind_ms": float(self._config[CONF_MAX_SURFACE_WIND_MS]),
            "max_altitude_wind_ms": float(self._config[CONF_MAX_ALTITUDE_WIND_MS]),
            "max_precip_prob_pct": float(self._config[CONF_MAX_PRECIP_PROB_PCT]),
            "min_ceiling_m": float(self._config[CONF_MIN_CEILING_M]),
            "min_visibility_km": float(self._config[CONF_MIN_VISIBILITY_KM]),
        }
        result_windows: dict[str, Any] = {}
        for window in windows:
            result_windows[window["key"]] = {
                **window,
                **analyze_window(payload["hourly"], thresholds),
            }
        active = next(iter(result_windows.values()), None)
        notification_result = {
            "sent": False,
            "blocked": False,
            "reason": "notification_targets_not_configured",
            "errors": [],
        }
        notification_fields = (
            CONF_CREW_NOTIFIER,
            CONF_PILOT_NOTIFIER,
            CONF_WHATSAPP_NOTIFIER,
            CONF_CALENDAR_ENTITY,
        )
        if all(self._config.get(field) for field in notification_fields):
            notification_result = await dispatch_go_transition_notifications(
                hass=self.hass,
                config=self._config,
                previous_windows=self._previous_windows,
                current_windows=result_windows,
                dedup_store=self._notification_dedup,
                now_utc=now_utc,
            )
        self._previous_windows = result_windows
        return {
            "active_window": active,
            "windows": result_windows,
            "data_last_updated_utc": now_utc.isoformat(),
            "notification_result": notification_result,
            "site_name": str(self._config.get(CONF_SITE_NAME, "FlyNow")),
        }
