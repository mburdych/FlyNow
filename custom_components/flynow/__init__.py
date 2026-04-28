"""FlyNow integration setup."""

from __future__ import annotations

from typing import Any

from .const import CONFIG_VERSION, COORDINATOR_DATA, DOMAIN, PLATFORMS
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
    coordinator = FlyNowCoordinator(hass, entry.data)
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
