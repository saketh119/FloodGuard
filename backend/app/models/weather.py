"""
models/weather.py — Weather observation from OpenWeatherMap (or mock).
"""
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WeatherObservation(Base):
    __tablename__ = "weather_observation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Location
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    state: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    city_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    obs_time: Mapped[datetime] = mapped_column(DateTime, index=True)

    # Meteorological values
    temp: Mapped[float | None] = mapped_column(Float, nullable=True)           # °C
    feels_like: Mapped[float | None] = mapped_column(Float, nullable=True)     # °C
    temp_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    temp_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity: Mapped[int | None] = mapped_column(Integer, nullable=True)       # %
    wind_speed: Mapped[float | None] = mapped_column(Float, nullable=True)     # km/h
    wind_deg: Mapped[int | None] = mapped_column(Integer, nullable=True)       # degrees
    pressure: Mapped[int | None] = mapped_column(Integer, nullable=True)       # hPa
    visibility: Mapped[int | None] = mapped_column(Integer, nullable=True)     # metres
    clouds: Mapped[int | None] = mapped_column(Integer, nullable=True)         # %
    rainfall_1h: Mapped[float | None] = mapped_column(Float, nullable=True)    # mm
    rainfall_3h: Mapped[float | None] = mapped_column(Float, nullable=True)    # mm
    weather_id: Mapped[int | None] = mapped_column(Integer, nullable=True)     # OWM code
    weather_main: Mapped[str | None] = mapped_column(String(50), nullable=True)
    weather_desc: Mapped[str | None] = mapped_column(String(100), nullable=True)

    source: Mapped[str] = mapped_column(String(30), default="openweathermap")

    # Trigger flag
    triggered: Mapped[bool] = mapped_column(Integer, default=0)
    trigger_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)

    raw_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"<WeatherObs id={self.id} {self.district} rain={self.rainfall_1h}mm>"
