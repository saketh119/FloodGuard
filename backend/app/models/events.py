"""
models/events.py — Flood Events and Event Evidence tables.

flood_events:   One row per unique, evolving flood situation.
event_evidence: Every observation that contributed to an event.

Events are derived from observations — they are NOT immutable.
Their status, confidence_score, risk_score, and ai_summary all update
as new evidence arrives.
"""
import uuid
from datetime import datetime
from typing import List

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class FloodEvent(Base):
    """
    A unified flood event, aggregating evidence from multiple sources.

    Lifecycle: potential → developing → high_risk → active → resolved → archived
    """
    __tablename__ = "flood_events"

    event_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Location
    district: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    state: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Classification
    category: Mapped[str] = mapped_column(String(30), default="flood")
    # status: potential | developing | high_risk | active | resolved | archived
    status: Mapped[str] = mapped_column(String(20), default="potential", index=True)

    # Scoring (0.0 – 1.0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.1)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)

    # How many distinct sources contributed evidence
    source_count: Mapped[int] = mapped_column(Integer, default=1)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)

    # AI-generated summary (updated after each evidence attachment)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    first_seen: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_updated: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    evidence: Mapped[List["EventEvidence"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )
    predictions: Mapped[List["PredictionResult"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<FloodEvent {self.event_id[:8]}… "
            f"{self.district}/{self.state} status={self.status} conf={self.confidence_score:.2f}>"
        )


class EventEvidence(Base):
    """
    Links a raw observation to a flood event.
    One row per (event × observation) pair — immutable once written.
    """
    __tablename__ = "event_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("flood_events.event_id", ondelete="CASCADE"), index=True
    )

    # Source type and observation reference
    source: Mapped[str] = mapped_column(String(15))    # imd | cwc | weather | news
    observation_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    observation_table: Mapped[str | None] = mapped_column(String(50), nullable=True)

    trigger_reason: Mapped[str | None] = mapped_column(String(300), nullable=True)
    contribution_score: Mapped[float] = mapped_column(Float, default=0.1)

    added_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Back-reference
    event: Mapped["FloodEvent"] = relationship(back_populates="evidence")

    def __repr__(self) -> str:
        return f"<Evidence event={self.event_id[:8]}… source={self.source} obs={self.observation_id}>"


# Circular import resolution — import here so it resolves after class definitions
from app.models.predictions import PredictionResult  # noqa: E402, F401
