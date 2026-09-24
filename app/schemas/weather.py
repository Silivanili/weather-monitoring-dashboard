from datetime import datetime

from pydantic import BaseModel


class Coordinates(BaseModel):
    latitude: float
    longitude: float


class CurrentWeather(BaseModel):
    time: datetime
    temperature_celsius: float
    apparent_temperature_celsius: float
    relative_humidity_percent: int
    precipitation_mm: float
    weather_code: int
    wind_speed_kmh: float


class WeatherMeta(BaseModel):
    source: str
    fetched_at: datetime
    cached: bool
    stale: bool


class WeatherResponse(BaseModel):
    coordinates: Coordinates
    current: CurrentWeather
    meta: WeatherMeta
