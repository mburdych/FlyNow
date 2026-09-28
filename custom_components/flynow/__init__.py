"""FlyNow integration setup."""

from __future__ import annotations

from typing import Any

from .const import (
    CONF_FLIGHT_DURATION_MIN,
    CONFIG_VERSION,
    COORDINATOR_DATA,
    DEFAULT_FLIGHT_DURATION_MIN,
    DOMAIN,
    MAX_FLIGHT_DURATION_MIN,
    MIN_FLIGHT_DURATION_MIN,
    PLATFORMS,
)
from .coordinator import FlyNowCoordinator
from .flight_log import async_register_services


async def async_migrate_entry(hass: Any, entry: Any) -> bool:
    if entry.version >= CONFIG_VERSION:
        return True
    new_data = {k: v for k, v in entry.data.items() if k != "min_ceiling_m"}
    hass.config_entries.async_update_entry(entry, data=new_data, version=CONFIG_VERSION)
    return True


async def async_setup_entry(hass: Any, entry: Any) -> bool:
    hass.data.setdefault(DOMAIN, {})
    data = dict(entry.data)
    raw_duration = int(data.get(CONF_FLIGHT_DURATION_MIN, DEFAULT_FLIGHT_DURATION_MIN))
    flight_duration_min = min(MAX_FLIGHT_DURATION_MIN, max(MIN_FLIGHT_DURATION_MIN, raw_duration))
    if flight_duration_min != raw_duration:
        data[CONF_FLIGHT_DURATION_MIN] = flight_duration_min
        hass.config_entries.async_update_entry(entry, data=data)
    coordinator = FlyNowCoordinator(hass, data)
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = {COORDINATOR_DATA: coordinator}
    await async_register_services(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: Any, entry: Any) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return ok
