"""Open-Meteo client for FlyNow."""

from __future__ import annotations

from typing import Any

import aiohttp

BASE_URL = "https://api.open-meteo.com/v1/forecast"

HOURLY_FIELDS = [
    "wind_speed_10m",
    "wind_speed_975hPa",
    "wind_speed_925hPa",
    "precipitation_probability",
    "visibility",
    "cloud_cover",
    "relative_humidity_2m",
    "temperature_2m",
    "dew_point_2m",
    # Open-Meteo does not support `ceiling` in hourly requests.
    # `cloud_base` provides cloud layer height in meters and is a usable proxy.
    "cloud_base",
]


class OpenMeteoError(RuntimeError):
    """Raised when Open-Meteo data cannot be retrieved or parsed."""


async def fetch_forecast(
    session: aiohttp.ClientSession, latitude: float, longitude: float
) -> dict[str, Any]:
    """Fetch and normalize weather payload for downstream processing."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": "Europe/Bratislava",
        "forecast_days": 7,
        "wind_speed_unit": "ms",
        "hourly": ",".join(HOURLY_FIELDS),
        "daily": "sunrise,sunset",
    }
    try:
        async with session.get(BASE_URL, params=params, timeout=20) as response:
            if response.status != 200:
                error_body = await response.text()
                raise OpenMeteoError(
                    f"Open-Meteo returned HTTP {response.status}: {error_body}"
                )
            payload = await response.json()
    except aiohttp.ClientError as err:
        raise OpenMeteoError(f"Open-Meteo request failed: {err}") from err

    try:
        hourly = payload["hourly"]
        daily = payload["daily"]
        return {"hourly": hourly, "daily": daily}
    except KeyError as err:
        raise OpenMeteoError(f"Open-Meteo payload missing key: {err}") from err
