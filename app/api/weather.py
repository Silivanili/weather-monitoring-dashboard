from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.weather import WeatherResponse
from app.services.weather import WeatherProviderError, get_weather_data
from app.services.weather_storage import (
    get_latest_weather_observation,
    is_weather_observation_fresh,
    save_weather_observation,
    weather_observation_to_response,
)

router = APIRouter(prefix="/api", tags=["weather"])


@router.get("/weather", response_model=WeatherResponse)
def get_weather(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    db: Session = Depends(get_db),
):
    latest_observation = get_latest_weather_observation(
        latitude,
        longitude,
        db,
    )

    if latest_observation is not None and is_weather_observation_fresh(latest_observation):
        return weather_observation_to_response(
            latest_observation,
            stale=False,
        )

    try:
        weather_data = get_weather_data(latitude, longitude)

        save_weather_observation(
            weather_data,
            db,
        )

        return weather_data

    except WeatherProviderError as exc:
        if latest_observation is not None:
            return weather_observation_to_response(
                latest_observation,
                stale=True,
            )

        raise HTTPException(
            status_code=502,
            detail="Weather provider unavailable",
        ) from exc
