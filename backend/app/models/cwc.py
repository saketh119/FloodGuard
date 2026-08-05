"""
models/cwc.py — CWC Station metadata and time-series measurements.

Design mirrors the real CWC API which separates station metadata
(rarely changes) from observations (frequent time-series).
"""
from datetime import datetime
from typing import List

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CwcStation(Base):
    """
    Metadata for a CWC river gauging station — synced once, updated rarely.
    Primary key is the CWC station_code string (e.g. "GD-212").
    """
    __tablename__ = "cwc_station"

    station_code: Mapped[str] = mapped_column(String(30), primary_key=True)
    station_name: Mapped[str] = mapped_column(String(150))
    river: Mapped[str | None] = mapped_column(String(100), nullable=True)
    basin: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    state: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Flood reference levels (metres above datum)
    frl: Mapped[float | None] = mapped_column(Float, nullable=True)    # Full Reservoir Level
    mwl: Mapped[float | None] = mapped_column(Float, nullable=True)    # Maximum Water Level
    warning_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    danger_level: Mapped[float | None] = mapped_column(Float, nullable=True)

    raw_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_synced: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationship to measurements
    measurements: Mapped[List["CwcMeasurement"]] = relationship(
        back_populates="station", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<CwcStation {self.station_code} — {self.station_name}>"


class CwcMeasurement(Base):
    """
    Time-series water level / discharge observation for a CWC station.
    Immutable once written.
    """
    __tablename__ = "cwc_measurement"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_code: Mapped[str] = mapped_column(
        String(30), ForeignKey("cwc_station.station_code", ondelete="CASCADE"), index=True
    )
    measurement_time: Mapped[datetime] = mapped_column(DateTime, index=True)

    water_level: Mapped[float | None] = mapped_column(Float, nullable=True)   # metres
    discharge: Mapped[float | None] = mapped_column(Float, nullable=True)     # cumecs

    # Derived status based on station thresholds
    status: Mapped[str] = mapped_column(
        String(15), default="safe"
    )  # safe | warning | danger | severe

    raw_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Back-reference
    station: Mapped["CwcStation"] = relationship(back_populates="measurements")

    def __repr__(self) -> str:
        return f"<CwcMeasurement {self.station_code} @ {self.measurement_time} — {self.status}>"
