"""
pipeline/correlator.py — Event Correlation Engine.

The heart of FloodGuard. When a TriggerResult arrives:

  1. Search for an existing flood_event within 50km radius + 24h time window.
  2. If found  → attach evidence, update confidence, update risk, update status.
  3. If not    → create a new flood_event at potential status.
  4. Persist everything, then trigger AI summarizer (non-blocking).

Status lifecycle:
  potential  → confidence < 0.30
  developing → 0.30 ≤ confidence < 0.55
  high_risk  → 0.55 ≤ confidence < 0.75
  active     → confidence ≥ 0.75
  resolved   → set manually (future: auto-resolve if no evidence for 72h)
"""
import math
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, select

from app.core.database import get_db
from app.core.logger import get_logger
from app.models.events import EventEvidence, FloodEvent
from app.pipeline.trigger import TriggerResult

log = get_logger(__name__)

# Correlation window
RADIUS_KM = 50.0
TIME_WINDOW_HOURS = 24

# Confidence → status thresholds
STATUS_THRESHOLDS = [
    (0.75, "active"),
    (0.55, "high_risk"),
    (0.30, "developing"),
    (0.00, "potential"),
]


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in km between two (lat, lng) points."""
    R = 6371.0
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    Δφ = math.radians(lat2 - lat1)
    Δλ = math.radians(lng2 - lng1)
    a = math.sin(Δφ / 2) ** 2 + math.cos(φ1) * math.cos(φ2) * math.sin(Δλ / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _status_for(confidence: float) -> str:
    for threshold, status in STATUS_THRESHOLDS:
        if confidence >= threshold:
            return status
    return "potential"


class EventCorrelator:

    async def process(self, trigger: TriggerResult) -> FloodEvent:
        """
        Main entry point. Find or create a FloodEvent for this trigger,
        attach evidence, update scores, and return the event.
        """
        async with get_db() as db:
            event = await self._find_nearby_event(db, trigger)

            if event:
                log.info(
                    f"Correlator: attaching evidence to existing event "
                    f"{event.event_id[:8]}… ({event.district})"
                )
                await self._attach_evidence(db, event, trigger)
            else:
                log.info(
                    f"Correlator: creating new flood event at "
                    f"{trigger.district or 'unknown'}, {trigger.state or ''}"
                )
                event = await self._create_event(db, trigger)

            # Update scores and status
            self._update_scores(event, trigger)
            event.last_updated = datetime.now(timezone.utc)

        # Async summarize (non-blocking — fire and forget)
        self._schedule_summary(event.event_id)

        return event

    # ── Private helpers ────────────────────────────────────────────────

    async def _find_nearby_event(
        self, db, trigger: TriggerResult
    ) -> FloodEvent | None:
        """Return the closest active/developing event within radius + time window."""
        since = datetime.now(timezone.utc) - timedelta(hours=TIME_WINDOW_HOURS)

        result = await db.execute(
            select(FloodEvent).where(
                and_(
                    FloodEvent.status.not_in(["resolved", "archived"]),
                    FloodEvent.last_updated >= since,
                )
            )
        )
        candidates = result.scalars().all()

        if not candidates:
            return None

        # Filter by radius (Haversine). Location match by district if coords missing.
        best = None
        best_dist = float("inf")

        for evt in candidates:
            # Try coordinate-based matching first
            if trigger.lat and trigger.lng and evt.lat and evt.lng:
                dist = _haversine_km(trigger.lat, trigger.lng, evt.lat, evt.lng)
                if dist <= RADIUS_KM and dist < best_dist:
                    best, best_dist = evt, dist
            # Fall back to district name match
            elif (
                trigger.district
                and evt.district
                and trigger.district.lower() == evt.district.lower()
            ):
                return evt  # Exact district match is always preferred

        return best

    async def _create_event(self, db, trigger: TriggerResult) -> FloodEvent:
        event = FloodEvent(
            district=trigger.district,
            state=trigger.state,
            lat=trigger.lat,
            lng=trigger.lng,
            status="potential",
            confidence_score=trigger.contribution_score,
            risk_score=trigger.contribution_score * 0.8,
            source_count=1,
            evidence_count=1,
        )
        db.add(event)
        await db.flush()  # Get event_id without committing

        evidence = EventEvidence(
            event_id=event.event_id,
            source=trigger.source,
            observation_id=trigger.observation_id,
            observation_table=trigger.observation_table,
            trigger_reason=trigger.reason,
            contribution_score=trigger.contribution_score,
        )
        db.add(evidence)
        return event

    async def _attach_evidence(
        self, db, event: FloodEvent, trigger: TriggerResult
    ) -> None:
        evidence = EventEvidence(
            event_id=event.event_id,
            source=trigger.source,
            observation_id=trigger.observation_id,
            observation_table=trigger.observation_table,
            trigger_reason=trigger.reason,
            contribution_score=trigger.contribution_score,
        )
        db.add(evidence)
        event.evidence_count = (event.evidence_count or 0) + 1

        # Count unique source types
        result = await db.execute(
            select(EventEvidence.source)
            .where(EventEvidence.event_id == event.event_id)
            .distinct()
        )
        unique_sources = {row[0] for row in result.all()}
        unique_sources.add(trigger.source)
        event.source_count = len(unique_sources)

    def _update_scores(self, event: FloodEvent, trigger: TriggerResult) -> None:
        """
        Update confidence and risk using an exponential moving average approach.
        Multiple sources push confidence up faster.
        """
        old_conf = event.confidence_score or 0.0
        n = event.evidence_count or 1

        # Weighted average: new evidence has diminishing weight as evidence accumulates
        weight = max(0.05, 1.0 / n)
        new_conf = old_conf * (1 - weight) + trigger.contribution_score * weight

        # Multi-source bonus: each unique source adds 8% confidence
        source_bonus = (event.source_count - 1) * 0.08
        new_conf = min(new_conf + source_bonus, 1.0)

        event.confidence_score = round(new_conf, 4)
        event.risk_score = round(new_conf * 0.9, 4)  # Risk slightly below confidence
        event.status = _status_for(new_conf)

        log.debug(
            f"Event {event.event_id[:8]}… → conf={event.confidence_score:.3f} "
            f"status={event.status}"
        )

    def _schedule_summary(self, event_id: str) -> None:
        """Non-blocking: trigger AI summarizer in background (best-effort)."""
        import asyncio

        async def _run():
            try:
                from app.ai.summarizer import AISummarizer
                await AISummarizer().summarize(event_id)
            except Exception as exc:
                log.debug(f"AI summary skipped for {event_id[:8]}…: {exc}")

        try:
            loop = asyncio.get_event_loop()
            loop.create_task(_run())
        except RuntimeError:
            pass  # No running loop (e.g. during unit tests)
