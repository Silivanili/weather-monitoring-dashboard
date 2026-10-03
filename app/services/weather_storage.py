from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import WeatherObservation

CACHE_TTL = timedelta(minutes=10)


def _to_utc_datetime(value: datetime | str) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value)

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def save_weather_observation(
    weather_data: dict,
    db: Session,
) -> WeatherObservation:
    observation = WeatherObservation(
        latitude=weather_data["coordinates"]["latitude"],
        longitude=weather_data["coordinates"]["longitude"],
        weather_time=_to_utc_datetime(
            weather_data["current"]["time"],
        ),
        temperature_celsius=weather_data["current"]["temperature_celsius"],
        apparent_temperature_celsius=weather_data["current"]["apparent_temperature_celsius"],
        relative_humidity_percent=weather_data["current"]["relative_humidity_percent"],
        precipitation_mm=weather_data["current"]["precipitation_mm"],
        weather_code=weather_data["current"]["weather_code"],
        wind_speed_kmh=weather_data["current"]["wind_speed_kmh"],
        source=weather_data["meta"]["source"],
        fetched_at=_to_utc_datetime(
            weather_data["meta"]["fetched_at"],
        ),
    )

    db.add(observation)
    db.commit()
    db.refresh(observation)

    return observation


def get_latest_weather_observation(
    latitude: float,
    longitude: float,
    db: Session,
) -> WeatherObservation | None:
    statement = (
        select(WeatherObservation)
        .where(
            WeatherObservation.latitude == latitude,
            WeatherObservation.longitude == longitude,
        )
        .order_by(WeatherObservation.fetched_at.desc())
        .limit(1)
    )

    return db.execute(statement).scalar_one_or_none()


def is_weather_observation_fresh(
    observation: WeatherObservation,
    now: datetime | None = None,
) -> bool:
    if now is None:
        now = datetime.now(timezone.utc)

    fetched_at = _to_utc_datetime(observation.fetched_at)
    now = _to_utc_datetime(now)

    age = now - fetched_at

    return timedelta(0) <= age <= CACHE_TTL


def weather_observation_to_response(
    observation: WeatherObservation,
    *,
    stale: bool,
) -> dict:
    return {
        "coordinates": {
            "latitude": observation.latitude,
            "longitude": observation.longitude,
        },
        "current": {
            "time": _to_utc_datetime(observation.weather_time),
            "temperature_celsius": observation.temperature_celsius,
            "apparent_temperature_celsius": (observation.apparent_temperature_celsius),
            "relative_humidity_percent": observation.relative_humidity_percent,
            "precipitation_mm": observation.precipitation_mm,
            "weather_code": observation.weather_code,
            "wind_speed_kmh": observation.wind_speed_kmh,
        },
        "meta": {
            "source": observation.source,
            "fetched_at": _to_utc_datetime(observation.fetched_at),
            "cached": True,
            "stale": stale,
        },
    }
