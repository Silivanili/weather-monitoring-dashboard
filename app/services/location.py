import httpx

OPEN_METEO_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"


class LocationProviderError(Exception):
    """Raised when the external geocoding provider cannot deliver data."""


def search_locations(query: str) -> list[dict]:
    params = {
        "name": query,
        "count": 5,
        "language": "de",
        "format": "json",
    }

    try:
        response = httpx.get(
            OPEN_METEO_GEOCODING_URL,
            params=params,
            timeout=5.0,
        )
        response.raise_for_status()
        provider_data = response.json()

    except (httpx.HTTPError, ValueError) as exc:
        raise LocationProviderError("Location provider unavailable") from exc

    results = provider_data.get("results", [])

    locations = []

    for result in results:
        if not all(
            key in result
            for key in (
                "name",
                "country",
                "latitude",
                "longitude",
            )
        ):
            continue

        locations.append(
            {
                "name": result["name"],
                "country": result["country"],
                "latitude": result["latitude"],
                "longitude": result["longitude"],
            }
        )

    return locations
