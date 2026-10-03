from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db.database import SessionLocal
from app.db.models import WeatherObservation
from app.main import app
from app.services.weather import WeatherProviderError
from app.services.weather_storage import save_weather_observation

client = TestClient(app)


def clear_weather_observations():
    with SessionLocal() as db:
        db.execute(delete(WeatherObservation))
        db.commit()


@pytest.fixture(autouse=True)
def clean_database():
    clear_weather_observations()
    yield
    clear_weather_observations()


def make_weather_data(
    latitude: float = 46.85,
    longitude: float = 9.53,
    temperature: float = 14.2,
    fetched_at: datetime | None = None,
):
    if fetched_at is None:
        fetched_at = datetime.now(timezone.utc)

    return {
        "coordinates": {
            "latitude": latitude,
            "longitude": longitude,
        },
        "current": {
            "time": datetime.now(timezone.utc),
            "temperature_celsius": temperature,
            "apparent_temperature_celsius": 13.4,
            "relative_humidity_percent": 72,
            "precipitation_mm": 0.0,
            "weather_code": 2,
            "wind_speed_kmh": 5.3,
        },
        "meta": {
            "source": "open-meteo",
            "fetched_at": fetched_at,
            "cached": False,
            "stale": False,
        },
    }


def test_weather_requires_coordinates():
    response = client.get("/api/weather")

    assert response.status_code == 422


def test_weather_rejects_invalid_latitude():
    response = client.get(
        "/api/weather",
        params={
            "latitude": 100,
            "longitude": 9.53,
        },
    )

    assert response.status_code == 422


def test_weather_rejects_invalid_longitude():
    response = client.get(
        "/api/weather",
        params={
            "latitude": 46.85,
            "longitude": 200,
        },
    )

    assert response.status_code == 422


def test_weather_returns_weather_data(monkeypatch):
    def fake_get_weather(latitude: float, longitude: float):
        return make_weather_data(
            latitude=latitude,
            longitude=longitude,
        )

    monkeypatch.setattr(
        "app.api.weather.get_weather_data",
        fake_get_weather,
    )

    response = client.get(
        "/api/weather",
        params={
            "latitude": 46.85,
            "longitude": 9.53,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["coordinates"] == {
        "latitude": 46.85,
        "longitude": 9.53,
    }

    assert data["current"]["temperature_celsius"] == 14.2
    assert data["meta"]["source"] == "open-meteo"
    assert data["meta"]["cached"] is False
    assert data["meta"]["stale"] is False


def test_weather_uses_fresh_cache(monkeypatch):
    with SessionLocal() as db:
        save_weather_observation(
            make_weather_data(
                temperature=8.5,
                fetched_at=datetime.now(timezone.utc),
            ),
            db,
        )

    def provider_must_not_be_called(latitude: float, longitude: float):
        raise AssertionError("Provider should not be called for fresh cache")

    monkeypatch.setattr(
        "app.api.weather.get_weather_data",
        provider_must_not_be_called,
    )

    response = client.get(
        "/api/weather",
        params={
            "latitude": 46.85,
            "longitude": 9.53,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["current"]["temperature_celsius"] == 8.5
    assert data["meta"]["cached"] is True
    assert data["meta"]["stale"] is False


def test_weather_returns_stale_cache_when_provider_fails(monkeypatch):
    with SessionLocal() as db:
        save_weather_observation(
            make_weather_data(
                temperature=7.0,
                fetched_at=datetime.now(timezone.utc) - timedelta(minutes=30),
            ),
            db,
        )

    def fake_get_weather(latitude: float, longitude: float):
        raise WeatherProviderError

    monkeypatch.setattr(
        "app.api.weather.get_weather_data",
        fake_get_weather,
    )

    response = client.get(
        "/api/weather",
        params={
            "latitude": 46.85,
            "longitude": 9.53,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["current"]["temperature_celsius"] == 7.0
    assert data["meta"]["cached"] is True
    assert data["meta"]["stale"] is True


def test_weather_returns_502_when_provider_fails_without_cache(
    monkeypatch,
):
    def fake_get_weather(latitude: float, longitude: float):
        raise WeatherProviderError

    monkeypatch.setattr(
        "app.api.weather.get_weather_data",
        fake_get_weather,
    )

    response = client.get(
        "/api/weather",
        params={
            "latitude": 46.85,
            "longitude": 9.53,
        },
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Weather provider unavailable",
    }
