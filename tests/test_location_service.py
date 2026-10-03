from app.services.location import search_locations


def test_search_locations_maps_provider_response(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "results": [
                    {
                        "id": 2661169,
                        "name": "Chur",
                        "latitude": 46.8499,
                        "longitude": 9.5329,
                        "country": "Schweiz",
                        "timezone": "Europe/Zurich",
                    }
                ]
            }

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "app.services.location.httpx.get",
        fake_get,
    )

    result = search_locations("Chur")

    assert result == [
        {
            "name": "Chur",
            "country": "Schweiz",
            "latitude": 46.8499,
            "longitude": 9.5329,
        }
    ]


def test_search_locations_returns_empty_list_without_results(
    monkeypatch,
):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {}

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "app.services.location.httpx.get",
        fake_get,
    )

    assert search_locations("xyznonexistent") == []
