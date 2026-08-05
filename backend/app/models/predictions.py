"""
models/predictions.py — Flood risk prediction results.

Prediction results are produced either:
  a) By the rule-based scorer (always runs)
  b) By an ML model (future enhancement)

They can be event-specific (linked to a flood_event) or
district-wide (standalone risk forecast).
"""
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PredictionResult(Base):
    __tablename__ = "prediction_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Optional link to a specific flood event
    event_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("flood_events.event_id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    # Location (duplicated from event for standalone predictions)
    district: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    state: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Prediction time horizon
    prediction_time: Mapped[datetime] = mapped_column(DateTime, index=True)  # When this was predicted
    valid_for_hours: Mapped[int] = mapped_column(Integer, default=24)        # Validity window

    # Scores (0.0 – 1.0)
    flood_probability: Mapped[float] = mapped_column(Float, default=0.0)
    severity_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Feature snapshot used for prediction (JSON)
    features_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    model_version: Mapped[str] = mapped_column(String(30), default="rule-based-v1")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Back-reference (avoids circular import — use string ref)
    event: Mapped["FloodEvent"] = relationship(back_populates="predictions")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return (
            f"<Prediction id={self.id} "
            f"{self.district} prob={self.flood_probability:.2f} sev={self.severity_score:.2f}>"
        )


# Resolve forward ref for FloodEvent.predictions
from app.models.events import FloodEvent  # noqa: F401, E402
