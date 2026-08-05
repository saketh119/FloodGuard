"""
models/imd.py — IMD Observation table.

Stores every raw observation fetched from the IMD API (mock or live).
One row per (station/district, fetch_time). Observations are immutable.
"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ImdObservation(Base):
    __tablename__ = "imd_observation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Station / district identity
    station_code: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    station_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    district_id: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    district_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    state: Mapped[str | None] = mapped_column(String(80), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Observation time (rounded to nearest fetch window)
    obs_time: Mapped[datetime] = mapped_column(DateTime, index=True)

    # Current weather metrics
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_speed: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_direction: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mslp: Mapped[float | None] = mapped_column(Float, nullable=True)
    rain_24h: Mapped[float | None] = mapped_column(Float, nullable=True)
    weather_code: Mapped[str | None] = mapped_column(String(5), nullable=True)

    # Nowcast (next 3h district warning)
    nowcast_color: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1=Green…4=Red
    nowcast_msg: Mapped[str | None] = mapped_column(Text, nullable=True)
    nowcast_valid_upto: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # 5-day warning color codes (1–4 per day)
    warning_day1_color: Mapped[int | None] = mapped_column(Integer, nullable=True)
    warning_day2_color: Mapped[int | None] = mapped_column(Integer, nullable=True)
    warning_day3_color: Mapped[int | None] = mapped_column(Integer, nullable=True)
    warning_day4_color: Mapped[int | None] = mapped_column(Integer, nullable=True)
    warning_day5_color: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Trigger flag (set by TriggerDetector)
    triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    trigger_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Raw API response stored for auditability
    raw_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    ingested_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"<ImdObservation id={self.id} district={self.district_name} color={self.nowcast_color}>"
