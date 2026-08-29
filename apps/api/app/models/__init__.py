"""Database models.

Design rule from the architecture docs: observations are IMMUTABLE and raw JSON is
never discarded. Flood events are DERIVED and evolve as evidence accumulates.
"""
from datetime import datetime, timezone

from sqlalchemy import (
    JSON, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ImdObservation(Base):
    """One immutable reading pulled from an IMD endpoint.

    `dedupe_hash` is a content hash of the meaningful fields — re-polling the same
    unchanged reading every 60s must not create duplicate rows.
    """
    __tablename__ = "imd_observation"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(32), default="IMD")
    observation_type: Mapped[str] = mapped_column(String(32), index=True)  # nowcast|warning|rainfall|current_wx|aws|qpf

    district_id: Mapped[str | None] = mapped_column(String(16), index=True)
    district: Mapped[str | None] = mapped_column(String(96), index=True)
    state: Mapped[str | None] = mapped_column(String(96), index=True)
    station_code: Mapped[str | None] = mapped_column(String(32), index=True)
    station_name: Mapped[str | None] = mapped_column(String(96))
    basin: Mapped[str | None] = mapped_column(String(96))
    sub_basin: Mapped[str | None] = mapped_column(String(96))

    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)

    observed_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    color_code: Mapped[int | None] = mapped_column(Integer)      # IMD 1=Green 2=Yellow 3=Orange 4=Red
    rainfall_mm: Mapped[float | None] = mapped_column(Float)
    temperature_c: Mapped[float | None] = mapped_column(Float)
    humidity_pct: Mapped[float | None] = mapped_column(Float)
    wind_speed_kmph: Mapped[float | None] = mapped_column(Float)
    pressure_hpa: Mapped[float | None] = mapped_column(Float)
    message: Mapped[str | None] = mapped_column(Text)

    raw_json: Mapped[dict] = mapped_column(JSON)
    dedupe_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    __table_args__ = (
        Index("ix_obs_district_time", "district", "observed_at"),
    )


class Station(Base):
    """Station / district metadata, kept separate from observations per the SADD."""
    __tablename__ = "station"

    id: Mapped[int] = mapped_column(primary_key=True)
    station_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    station_name: Mapped[str] = mapped_column(String(96))
    district_id: Mapped[str | None] = mapped_column(String(16))
    district: Mapped[str | None] = mapped_column(String(96))
    state: Mapped[str | None] = mapped_column(String(96))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(32), default="IMD")
    raw_metadata: Mapped[dict | None] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class TrackedLocation(Base):
    """A location a user asked for that is not in the built-in IMD registry.

    The static registry only covers districts the IMD source reports. OpenWeather
    works anywhere, so any place a user searches becomes trackable — it is stored
    here and the collector picks it up on the next cycle.
    """
    __tablename__ = "tracked_location"

    id: Mapped[int] = mapped_column(primary_key=True)
    district: Mapped[str] = mapped_column(String(96), unique=True, index=True)
    state: Mapped[str | None] = mapped_column(String(96))
    country: Mapped[str] = mapped_column(String(8), default="IN")
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    basin: Mapped[str | None] = mapped_column(String(96))
    added_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_viewed: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class FloodEvent(Base):
    """A derived, evolving flood situation — not a single API response."""
    __tablename__ = "flood_event"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_uid: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    district: Mapped[str] = mapped_column(String(96), index=True)
    state: Mapped[str | None] = mapped_column(String(96))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)

    category: Mapped[str] = mapped_column(String(48), default="heavy_rainfall")
    status: Mapped[str] = mapped_column(String(24), default="potential", index=True)  # potential|developing|high_risk|active|resolved
    severity: Mapped[str] = mapped_column(String(24), default="moderate")             # low|moderate|high|severe

    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)   # 0-1, evidence agreement
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)         # 0-100, blended
    prediction_probability: Mapped[float | None] = mapped_column(Float)   # 0-1, from the ML model

    ai_summary: Mapped[str | None] = mapped_column(Text)
    summary_generated_at: Mapped[datetime | None] = mapped_column(DateTime)

    first_seen: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    evidence: Mapped[list["EventEvidence"]] = relationship(
        back_populates="event", cascade="all, delete-orphan", order_by="EventEvidence.added_at.desc()"
    )


class EventEvidence(Base):
    """Link table: which observation caused which event to move, and why."""
    __tablename__ = "event_evidence"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("flood_event.id", ondelete="CASCADE"), index=True)
    observation_id: Mapped[int] = mapped_column(ForeignKey("imd_observation.id"), index=True)
    source: Mapped[str] = mapped_column(String(32))
    trigger_reason: Mapped[str] = mapped_column(Text)
    contribution_score: Mapped[float] = mapped_column(Float, default=0.0)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    event: Mapped[FloodEvent] = relationship(back_populates="evidence")

    __table_args__ = (
        # The same observation must never be attached to the same event twice.
        UniqueConstraint("event_id", "observation_id", name="uq_evidence_event_obs"),
    )


class PredictionResult(Base):
    """Every scoring run is kept so prediction trends can be charted."""
    __tablename__ = "prediction_result"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int | None] = mapped_column(ForeignKey("flood_event.id"), index=True)
    district: Mapped[str] = mapped_column(String(96), index=True)
    model_version: Mapped[str] = mapped_column(String(48))
    probability: Mapped[float] = mapped_column(Float)
    risk_band: Mapped[str] = mapped_column(String(24))
    features: Mapped[dict] = mapped_column(JSON)
    imputed_features: Mapped[dict | None] = mapped_column(JSON)  # honesty: what we had to guess
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


__all__ = [
    "ImdObservation", "Station", "TrackedLocation", "FloodEvent", "EventEvidence",
    "PredictionResult", "utcnow",
]
