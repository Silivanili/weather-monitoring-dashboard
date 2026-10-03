from fastapi.testclient import TestClient

from app.main import app
from app.services.weather import WeatherProviderError

client = TestClient(app)


def make_forecast():
    return {
        "coordinates": {
            "latitude": 46.85,
            "longitude": 9.53,
        },
        "daily": [
            {
                "date": f"2026-10-{day:02d}",
                "temperature_min_celsius": 5.0,
                "temperature_max_celsius": 15.0,
                "weather_code": 2,
                "precipitation_probability_percent": 20,
            }
            for day in range(4, 11)
        ],
        "meta": {
            "source": "open-meteo",
            "fetched_at": "2026-10-03T21:00:00+00:00",
        },
    }


def test_forecast_requires_coordinates():
    response = client.get("/api/weather/forecast")

    assert response.status_code == 422


def test_forecast_rejects_invalid_coordinates():
    response = client.get(
        "/api/weather/forecast",
        params={
            "latitude": 100,
            "longitude": 9.53,
        },
    )

    assert response.status_code == 422


def test_forecast_returns_seven_days(monkeypatch):
    def fake_get_forecast(latitude: float, longitude: float):
        return make_forecast()

    monkeypatch.setattr(
        "app.api.weather.get_forecast_data",
        fake_get_forecast,
    )

    response = client.get(
        "/api/weather/forecast",
        params={
            "latitude": 46.85,
            "longitude": 9.53,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["daily"]) == 7
    assert data["coordinates"]["latitude"] == 46.85
    assert data["coordinates"]["longitude"] == 9.53
    assert data["daily"][0]["temperature_min_celsius"] == 5.0
    assert data["daily"][0]["temperature_max_celsius"] == 15.0
    assert data["daily"][0]["weather_code"] == 2
    assert data["daily"][0]["precipitation_probability_percent"] == 20
    assert data["meta"]["source"] == "open-meteo"


def test_forecast_returns_502_when_provider_fails(monkeypatch):
    def fake_get_forecast(latitude: float, longitude: float):
        raise WeatherProviderError

    monkeypatch.setattr(
        "app.api.weather.get_forecast_data",
        fake_get_forecast,
    )

    response = client.get(
        "/api/weather/forecast",
        params={
            "latitude": 46.85,
            "longitude": 9.53,
        },
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Weather provider unavailable",
    }
