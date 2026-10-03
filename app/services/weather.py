from datetime import datetime, timedelta, timezone

import httpx

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


class WeatherProviderError(Exception):
    """Raised when the external weather provider cannot deliver data."""


def get_weather_data(latitude: float, longitude: float):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,"
            "apparent_temperature,"
            "relative_humidity_2m,"
            "precipitation,"
            "weather_code,"
            "wind_speed_10m"
        ),
        "timezone": "auto",
    }

    try:
        response = httpx.get(
            OPEN_METEO_URL,
            params=params,
            timeout=5.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise WeatherProviderError("Weather provider unavailable") from exc

    provider_data = response.json()
    current = provider_data["current"]
    utc_offset = timezone(timedelta(seconds=provider_data["utc_offset_seconds"]))

    current_time = datetime.fromisoformat(current["time"]).replace(tzinfo=utc_offset)

    return {
        "coordinates": {
            "latitude": latitude,
            "longitude": longitude,
        },
        "current": {
            "time": current_time,
            "temperature_celsius": current["temperature_2m"],
            "apparent_temperature_celsius": current["apparent_temperature"],
            "relative_humidity_percent": current["relative_humidity_2m"],
            "precipitation_mm": current["precipitation"],
            "weather_code": current["weather_code"],
            "wind_speed_kmh": current["wind_speed_10m"],
        },
        "meta": {
            "source": "open-meteo",
            "fetched_at": datetime.now(timezone.utc),
            "cached": False,
            "stale": False,
        },
    }


def get_forecast_data(latitude: float, longitude: float):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": (
            "temperature_2m_min,temperature_2m_max,weather_code,precipitation_probability_max"
        ),
        "forecast_days": 7,
        "timezone": "auto",
    }

    try:
        response = httpx.get(
            OPEN_METEO_URL,
            params=params,
            timeout=5.0,
        )
        response.raise_for_status()
        provider_data = response.json()
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        raise WeatherProviderError("Weather provider unavailable") from exc

    try:
        daily = provider_data["daily"]

        days = [
            {
                "date": daily["time"][index],
                "temperature_min_celsius": daily["temperature_2m_min"][index],
                "temperature_max_celsius": daily["temperature_2m_max"][index],
                "weather_code": daily["weather_code"][index],
                "precipitation_probability_percent": daily["precipitation_probability_max"][index],
            }
            for index in range(7)
        ]
    except (KeyError, IndexError, TypeError) as exc:
        raise WeatherProviderError("Invalid weather provider response") from exc

    return {
        "coordinates": {
            "latitude": latitude,
            "longitude": longitude,
        },
        "daily": days,
        "meta": {
            "source": "open-meteo",
            "fetched_at": datetime.now(timezone.utc),
        },
    }
