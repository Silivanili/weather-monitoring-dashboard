from fastapi.testclient import TestClient

from app.main import app
from app.services.location import LocationProviderError

client = TestClient(app)


def test_location_search_requires_query():
    response = client.get("/api/locations/search")

    assert response.status_code == 422


def test_location_search_rejects_too_short_query():
    response = client.get(
        "/api/locations/search",
        params={"q": "C"},
    )

    assert response.status_code == 422


def test_location_search_returns_results(monkeypatch):
    def fake_search_locations(query: str):
        assert query == "Chur"

        return [
            {
                "name": "Chur",
                "country": "Schweiz",
                "latitude": 46.8499,
                "longitude": 9.5329,
            }
        ]

    monkeypatch.setattr(
        "app.api.locations.search_locations",
        fake_search_locations,
    )

    response = client.get(
        "/api/locations/search",
        params={"q": "Chur"},
    )

    assert response.status_code == 200

    assert response.json() == [
        {
            "name": "Chur",
            "country": "Schweiz",
            "latitude": 46.8499,
            "longitude": 9.5329,
        }
    ]


def test_location_search_returns_502_when_provider_fails(
    monkeypatch,
):
    def fake_search_locations(query: str):
        raise LocationProviderError

    monkeypatch.setattr(
        "app.api.locations.search_locations",
        fake_search_locations,
    )

    response = client.get(
        "/api/locations/search",
        params={"q": "Chur"},
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Location provider unavailable",
    }
