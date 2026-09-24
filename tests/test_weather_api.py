from fastapi.testclient import TestClient

from app.main import app
from app.services.weather import WeatherProviderError

client = TestClient(app)


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
        return {
            "coordinates": {
                "latitude": latitude,
                "longitude": longitude,
            },
            "current": {
                "time": "2026-09-24T15:00:00+02:00",
                "temperature_celsius": 14.2,
                "apparent_temperature_celsius": 13.4,
                "relative_humidity_percent": 72,
                "precipitation_mm": 0.0,
                "weather_code": 2,
                "wind_speed_kmh": 5.3,
            },
            "meta": {
                "source": "open-meteo",
                "fetched_at": "2026-09-24T15:18:42+02:00",
                "cached": False,
                "stale": False,
            },
        }

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


def test_weather_returns_502_when_provider_fails(monkeypatch):
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
    assert response.json() == {"detail": "Weather provider unavailable"}
