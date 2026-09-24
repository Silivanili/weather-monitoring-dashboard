from datetime import datetime

import httpx
import pytest

from app.services.weather import WeatherProviderError, get_weather_data


def test_get_weather_data_maps_provider_response(monkeypatch):
    provider_response = {
        "latitude": 46.85,
        "longitude": 9.53,
        "utc_offset_seconds": 7200,
        "current": {
            "time": "2026-09-24T15:00",
            "temperature_2m": 14.2,
            "apparent_temperature": 13.4,
            "relative_humidity_2m": 72,
            "precipitation": 0.0,
            "weather_code": 2,
            "wind_speed_10m": 5.3,
        },
    }

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return provider_response

    def fake_get(url, params, timeout):
        assert url == "https://api.open-meteo.com/v1/forecast"

        assert params["latitude"] == 46.85
        assert params["longitude"] == 9.53
        assert params["timezone"] == "auto"

        return FakeResponse()

    monkeypatch.setattr(httpx, "get", fake_get)

    result = get_weather_data(
        latitude=46.85,
        longitude=9.53,
    )

    assert result["coordinates"] == {
        "latitude": 46.85,
        "longitude": 9.53,
    }

    assert result["current"]["temperature_celsius"] == 14.2
    assert result["current"]["apparent_temperature_celsius"] == 13.4
    assert result["current"]["relative_humidity_percent"] == 72
    assert result["current"]["precipitation_mm"] == 0.0
    assert result["current"]["weather_code"] == 2
    assert result["current"]["wind_speed_kmh"] == 5.3

    assert result["current"]["time"].utcoffset().total_seconds() == 7200

    assert result["meta"]["source"] == "open-meteo"
    assert isinstance(result["meta"]["fetched_at"], datetime)
    assert result["meta"]["fetched_at"].tzinfo is not None
    assert result["meta"]["cached"] is False
    assert result["meta"]["stale"] is False


def test_get_weather_data_raises_provider_error_on_http_failure(monkeypatch):
    def fake_get(url, params, timeout):
        raise httpx.RequestError("Provider unavailable")

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(WeatherProviderError):
        get_weather_data(
            latitude=46.85,
            longitude=9.53,
        )
