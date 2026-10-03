from app.services.weather import get_forecast_data


def test_get_forecast_data_maps_seven_days(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "daily": {
                    "time": [
                        "2026-10-04",
                        "2026-10-05",
                        "2026-10-06",
                        "2026-10-07",
                        "2026-10-08",
                        "2026-10-09",
                        "2026-10-10",
                    ],
                    "temperature_2m_min": [
                        5.0,
                        6.0,
                        7.0,
                        8.0,
                        9.0,
                        10.0,
                        11.0,
                    ],
                    "temperature_2m_max": [
                        15.0,
                        16.0,
                        17.0,
                        18.0,
                        19.0,
                        20.0,
                        21.0,
                    ],
                    "weather_code": [
                        1,
                        2,
                        3,
                        45,
                        61,
                        80,
                        95,
                    ],
                    "precipitation_probability_max": [
                        10,
                        20,
                        30,
                        40,
                        50,
                        60,
                        70,
                    ],
                }
            }

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "app.services.weather.httpx.get",
        fake_get,
    )

    result = get_forecast_data(
        46.85,
        9.53,
    )

    assert len(result["daily"]) == 7

    assert result["daily"][0] == {
        "date": "2026-10-04",
        "temperature_min_celsius": 5.0,
        "temperature_max_celsius": 15.0,
        "weather_code": 1,
        "precipitation_probability_percent": 10,
    }
