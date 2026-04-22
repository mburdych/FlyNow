"""Config flow for FlyNow."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from .const import (
    CONF_CALENDAR_ENTITY,
    CONF_CREW_NOTIFIER,
    CONF_FLIGHT_DURATION_MIN,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_MAX_ALTITUDE_WIND_MS,
    CONF_MAX_PRECIP_PROB_PCT,
    CONF_MAX_SURFACE_WIND_MS,
    CONF_MIN_CEILING_M,
    CONF_MIN_VISIBILITY_KM,
    CONF_PILOT_NOTIFIER,
    CONF_PREP_TIME_MIN,
    CONF_SITE_NAME,
    CONF_UPDATE_INTERVAL_MIN,
    CONF_WHATSAPP_NOTIFIER,
    DEFAULT_CALENDAR_ENTITY,
    DEFAULT_CREW_NOTIFIER,
    DEFAULT_FLIGHT_DURATION_MIN,
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
    DEFAULT_MAX_ALTITUDE_WIND_MS,
    DEFAULT_MAX_PRECIP_PROB_PCT,
    DEFAULT_MAX_SURFACE_WIND_MS,
    DEFAULT_MIN_CEILING_M,
    DEFAULT_MIN_VISIBILITY_KM,
    DEFAULT_PILOT_NOTIFIER,
    DEFAULT_PREP_TIME_MIN,
    DEFAULT_SITE_NAME,
    DEFAULT_UPDATE_INTERVAL_MIN,
    DEFAULT_WHATSAPP_NOTIFIER,
    DOMAIN,
    MAX_ALTITUDE_WIND_MS,
    MAX_CEILING_M,
    MAX_FLIGHT_DURATION_MIN,
    MAX_PRECIP_PROB_PCT,
    MAX_PREP_TIME_MIN,
    MAX_SURFACE_WIND_MS,
    MAX_UPDATE_INTERVAL_MIN,
    MAX_VISIBILITY_KM,
    MIN_ALTITUDE_WIND_MS,
    MIN_CEILING_M,
    MIN_FLIGHT_DURATION_MIN,
    MIN_PRECIP_PROB_PCT,
    MIN_PREP_TIME_MIN,
    MIN_SURFACE_WIND_MS,
    MIN_UPDATE_INTERVAL_MIN,
    MIN_VISIBILITY_KM,
)

try:
    from homeassistant import config_entries
except ImportError:  # pragma: no cover
    class _Flow:
        def __init_subclass__(cls, **kwargs):
            return super().__init_subclass__()

        def async_show_form(self, **kwargs):
            return {"type": "form", **kwargs}

        def async_create_entry(self, **kwargs):
            return {"type": "create_entry", **kwargs}

        def _async_current_entries(self):
            return []

    class _ConfigEntries:
        ConfigFlow = _Flow

    config_entries = _ConfigEntries()


def _in_range(value: float, min_value: float, max_value: float) -> bool:
    return min_value <= value <= max_value


def _is_entity_in_domain(entity_id: str, domain: str) -> bool:
    return entity_id.startswith(f"{domain}.") and len(entity_id) > len(domain) + 1


class FlyNowConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """3-step one-site configuration flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors = {}
        if user_input:
            if not _in_range(user_input[CONF_LATITUDE], -90, 90):
                errors[CONF_LATITUDE] = "invalid_latitude"
            if not _in_range(user_input[CONF_LONGITUDE], -180, 180):
                errors[CONF_LONGITUDE] = "invalid_longitude"
            if not errors:
                self._data.update(user_input)
                return await self.async_step_flight_parameters()
        schema = vol.Schema(
            {
                vol.Required(CONF_SITE_NAME, default=DEFAULT_SITE_NAME): str,
                vol.Required(CONF_LATITUDE, default=DEFAULT_LATITUDE): float,
                vol.Required(CONF_LONGITUDE, default=DEFAULT_LONGITUDE): float,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_flight_parameters(self, user_input: dict[str, Any] | None = None):
        errors = {}
        if user_input:
            if not _in_range(
                user_input[CONF_FLIGHT_DURATION_MIN],
                MIN_FLIGHT_DURATION_MIN,
                MAX_FLIGHT_DURATION_MIN,
            ):
                errors[CONF_FLIGHT_DURATION_MIN] = "out_of_bounds"
            if not _in_range(
                user_input[CONF_PREP_TIME_MIN], MIN_PREP_TIME_MIN, MAX_PREP_TIME_MIN
            ):
                errors[CONF_PREP_TIME_MIN] = "out_of_bounds"
            if not _in_range(
                user_input[CONF_UPDATE_INTERVAL_MIN],
                MIN_UPDATE_INTERVAL_MIN,
                MAX_UPDATE_INTERVAL_MIN,
            ):
                errors[CONF_UPDATE_INTERVAL_MIN] = "out_of_bounds"
            if not errors:
                self._data.update(user_input)
                return await self.async_step_thresholds()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_FLIGHT_DURATION_MIN, default=DEFAULT_FLIGHT_DURATION_MIN
                ): int,
                vol.Required(CONF_PREP_TIME_MIN, default=DEFAULT_PREP_TIME_MIN): int,
                vol.Required(
                    CONF_UPDATE_INTERVAL_MIN, default=DEFAULT_UPDATE_INTERVAL_MIN
                ): int,
            }
        )
        return self.async_show_form(
            step_id="flight_parameters", data_schema=schema, errors=errors
        )

    async def async_step_thresholds(self, user_input: dict[str, Any] | None = None):
        errors = {}
        if user_input:
            checks = [
                (CONF_MAX_SURFACE_WIND_MS, MIN_SURFACE_WIND_MS, MAX_SURFACE_WIND_MS),
                (CONF_MAX_ALTITUDE_WIND_MS, MIN_ALTITUDE_WIND_MS, MAX_ALTITUDE_WIND_MS),
                (CONF_MIN_CEILING_M, MIN_CEILING_M, MAX_CEILING_M),
                (CONF_MAX_PRECIP_PROB_PCT, MIN_PRECIP_PROB_PCT, MAX_PRECIP_PROB_PCT),
                (CONF_MIN_VISIBILITY_KM, MIN_VISIBILITY_KM, MAX_VISIBILITY_KM),
            ]
            for key, min_value, max_value in checks:
                if not _in_range(user_input[key], min_value, max_value):
                    errors[key] = "out_of_bounds"

            if not errors:
                self._data.update(user_input)
                if len(self._async_current_entries()) > 0:
                    return self.async_show_form(
                        step_id="thresholds", errors={"base": "single_site_only"}
                    )
                return await self.async_step_notifications()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_MAX_SURFACE_WIND_MS, default=DEFAULT_MAX_SURFACE_WIND_MS
                ): float,
                vol.Required(
                    CONF_MAX_ALTITUDE_WIND_MS, default=DEFAULT_MAX_ALTITUDE_WIND_MS
                ): float,
                vol.Required(CONF_MIN_CEILING_M, default=DEFAULT_MIN_CEILING_M): int,
                vol.Required(
                    CONF_MAX_PRECIP_PROB_PCT, default=DEFAULT_MAX_PRECIP_PROB_PCT
                ): int,
                vol.Required(
                    CONF_MIN_VISIBILITY_KM, default=DEFAULT_MIN_VISIBILITY_KM
                ): float,
            }
        )
        return self.async_show_form(step_id="thresholds", data_schema=schema, errors=errors)

    async def async_step_notifications(self, user_input: dict[str, Any] | None = None):
        errors = {}
        required_fields = (
            CONF_CREW_NOTIFIER,
            CONF_PILOT_NOTIFIER,
            CONF_WHATSAPP_NOTIFIER,
            CONF_CALENDAR_ENTITY,
        )
        if user_input:
            for field in required_fields:
                value = str(user_input.get(field, "")).strip()
                if not value:
                    errors[field] = "required"
                else:
                    user_input[field] = value
            if not errors:
                notifier_fields = (
                    CONF_CREW_NOTIFIER,
                    CONF_PILOT_NOTIFIER,
                    CONF_WHATSAPP_NOTIFIER,
                )
                for field in notifier_fields:
                    if not _is_entity_in_domain(user_input[field], "notify"):
                        errors[field] = "invalid_entity_id"
                if not _is_entity_in_domain(user_input[CONF_CALENDAR_ENTITY], "calendar"):
                    errors[CONF_CALENDAR_ENTITY] = "invalid_entity_id"
            if not errors:
                self._data.update(user_input)
                return self.async_create_entry(title=self._data[CONF_SITE_NAME], data=self._data)

        schema = vol.Schema(
            {
                vol.Required(CONF_CREW_NOTIFIER, default=DEFAULT_CREW_NOTIFIER): str,
                vol.Required(CONF_PILOT_NOTIFIER, default=DEFAULT_PILOT_NOTIFIER): str,
                vol.Required(
                    CONF_WHATSAPP_NOTIFIER, default=DEFAULT_WHATSAPP_NOTIFIER
                ): str,
                vol.Required(CONF_CALENDAR_ENTITY, default=DEFAULT_CALENDAR_ENTITY): str,
            }
        )
        return self.async_show_form(
            step_id="notifications", data_schema=schema, errors=errors
        )
