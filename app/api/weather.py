from fastapi import APIRouter, HTTPException, Query

from app.schemas.weather import WeatherResponse
from app.services.weather import WeatherProviderError, get_weather_data

router = APIRouter(prefix="/api", tags=["weather"])


@router.get("/weather", response_model=WeatherResponse)
def get_weather(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    try:
        return get_weather_data(latitude, longitude)

    except WeatherProviderError as exc:
        raise HTTPException(
            status_code=502,
            detail="Weather provider unavailable",
        ) from exc
