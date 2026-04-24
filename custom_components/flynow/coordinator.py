"""DataUpdateCoordinator implementation for FlyNow."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import aiohttp

_LOGGER = logging.getLogger(__name__)

from .analyzer import analyze_window
from .const import (
    CONF_CALENDAR_ENTITY,
    CONF_CREW_NOTIFIER,
    CONF_FLIGHT_DURATION_MIN,
    CONF_MAX_ALTITUDE_WIND_MS,
    CONF_MAX_PRECIP_PROB_PCT,
    CONF_PILOT_NOTIFIER,
    CONF_MAX_SURFACE_WIND_MS,
    CONF_MIN_CEILING_M,
    CONF_MIN_VISIBILITY_KM,
    CONF_SITE_NAME,
    CONF_PREP_TIME_MIN,
    CONF_SELECTED_SITE_ID,
    CONF_UPDATE_INTERVAL_MIN,
    CONF_WHATSAPP_NOTIFIER,
    DEFAULT_SELECTED_SITE_ID,
    SITE_CATALOG,
    SITE_IDS,
)
from .notifications import dispatch_go_transition_notifications
from .open_meteo import OpenMeteoError, fetch_forecast
from .windows import build_windows

try:
    from astral import Observer
    from astral.sun import dawn, dusk
except ImportError:  # pragma: no cover
    Observer = None
    dawn = None
    dusk = None

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
        super().__init__(hass, logger=_LOGGER, name="flynow", update_interval=interval)
        self._config = config
        self._previous_windows: dict[str, dict[str, Any]] = {}
        self._notification_dedup: dict[str, datetime] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        now_local = datetime.now()
        now_utc = datetime.now(UTC)
        thresholds = {
            "max_surface_wind_ms": float(self._config[CONF_MAX_SURFACE_WIND_MS]),
            "max_altitude_wind_ms": float(self._config[CONF_MAX_ALTITUDE_WIND_MS]),
            "max_precip_prob_pct": float(self._config[CONF_MAX_PRECIP_PROB_PCT]),
            "min_ceiling_m": float(self._config[CONF_MIN_CEILING_M]),
            "min_visibility_km": float(self._config[CONF_MIN_VISIBILITY_KM]),
        }
        selected_site_id = str(
            self._config.get(CONF_SELECTED_SITE_ID, DEFAULT_SELECTED_SITE_ID)
        )
        if selected_site_id not in SITE_IDS:
            selected_site_id = DEFAULT_SELECTED_SITE_ID

        sites: dict[str, Any] = {}
        try:
            async with aiohttp.ClientSession() as session:
                for site in SITE_CATALOG:
                    payload = await fetch_forecast(
                        session, float(site["lat"]), float(site["lon"])
                    )
                    sunrise = [
                        datetime.fromisoformat(v) for v in payload["daily"]["sunrise"][:4]
                    ]
                    sunset = [
                        datetime.fromisoformat(v) for v in payload["daily"]["sunset"][:4]
                    ]
                    day_start, day_end = self._easa_day_boundaries(
                        latitude=float(site["lat"]),
                        longitude=float(site["lon"]),
                        sunrise_by_day=sunrise,
                        sunset_by_day=sunset,
                    )
                    windows = build_windows(
                        now_local=now_local,
                        day_start_by_day=day_start,
                        day_end_by_day=day_end,
                        sunrise_by_day=sunrise,
                        sunset_by_day=sunset,
                        flight_duration_min=int(self._config[CONF_FLIGHT_DURATION_MIN]),
                        prep_time_min=int(self._config[CONF_PREP_TIME_MIN]),
                    )
                    result_windows: dict[str, Any] = {}
                    for window in windows:
                        result_windows[window["key"]] = {
                            **window,
                            **analyze_window(payload["hourly"], thresholds),
                        }
                    site_id = str(site["id"])
                    sites[site_id] = {
                        "site_id": site_id,
                        "site_name": str(site["name"]),
                        "kraj_code": str(site["kraj_code"]),
                        "elevation_m": int(site["elevation_m"]),
                        "windows": result_windows,
                        "active_window": next(iter(result_windows.values()), None),
                    }
        except OpenMeteoError as err:
            raise UpdateFailed(str(err)) from err

        selected_site = sites.get(selected_site_id) or sites.get(DEFAULT_SELECTED_SITE_ID) or {}
        result_windows = dict(selected_site.get("windows", {}))
        active = selected_site.get("active_window")
        sites_summary = {
            site_id: {
                "site_name": site_data.get("site_name"),
                "go": bool((site_data.get("active_window") or {}).get("go")),
                "launch_start": (site_data.get("active_window") or {}).get("launch_start"),
                "launch_end": (site_data.get("active_window") or {}).get("launch_end"),
                "active_window": (site_data.get("active_window") or {}).get("type", "none"),
                "data_last_updated_utc": now_utc.isoformat(),
            }
            for site_id, site_data in sites.items()
        }
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
            "selected_site_id": selected_site_id,
            "sites": sites,
            "sites_summary": sites_summary,
        }

    def _easa_day_boundaries(
        self,
        latitude: float,
        longitude: float,
        sunrise_by_day: list[datetime],
        sunset_by_day: list[datetime],
    ) -> tuple[list[datetime], list[datetime]]:
        """Compute EASA day boundaries: morning/evening civil twilight."""
        if not Observer or not dawn or not dusk:
            _LOGGER.warning("Astral unavailable, falling back to sunrise/sunset day boundaries")
            return sunrise_by_day, sunset_by_day

        observer = Observer(latitude=latitude, longitude=longitude)
        tz = ZoneInfo("Europe/Bratislava")
        starts: list[datetime] = []
        ends: list[datetime] = []
        for sunrise_dt in sunrise_by_day:
            day = sunrise_dt.date()
            start = dawn(observer, date=day, tzinfo=tz, depression=6).replace(tzinfo=None)
            end = dusk(observer, date=day, tzinfo=tz, depression=6).replace(tzinfo=None)
            starts.append(start)
            ends.append(end)
        return starts, ends
