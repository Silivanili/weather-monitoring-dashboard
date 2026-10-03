from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class WeatherObservation(Base):
    __tablename__ = "weather_observations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True,
    )

    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True,
    )

    weather_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    temperature_celsius: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    apparent_temperature_celsius: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    relative_humidity_percent: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    precipitation_mm: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    weather_code: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    wind_speed_kmh: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
