"""Event correlation — the heart of the platform.

Turns isolated triggered observations into a small number of evolving flood events:
an observation that matches an open event in the same district within the correlation
window is attached as EVIDENCE and raises that event's confidence; otherwise a new
event is opened. Observations are never modified.
"""
from datetime import timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logger import get_logger
from app.flood.engine.triggers import SEVERITY_ORDER, Trigger, evaluate, max_severity
from app.flood.geo import district_for_station, districts_in_basin, resolve_district
from app.models import EventEvidence, FloodEvent, ImdObservation, utcnow

log = get_logger("floodguard.engine.correlation")

OPEN_STATUSES = ("potential", "developing", "high_risk", "active")
SEVERITY_WEIGHT = {"low": 0.25, "moderate": 0.5, "high": 0.75, "severe": 1.0}
STALE_AFTER_HOURS = 24


def _targets(obs: ImdObservation) -> list[dict[str, Any]]:
    """Which district(s) does this observation speak about?

    District endpoints name one directly; station readings resolve through the station
    registry; a basin QPF applies to every district in that basin.
    """
    if obs.district:
        # OpenWeather rows carry their own state and coordinates, including for
        # user-tracked places the built-in registry has never heard of. Trust them.
        if obs.state and obs.latitude is not None and obs.longitude is not None:
            return [{
                "district": obs.district, "district_id": obs.district_id,
                "state": obs.state, "latitude": obs.latitude,
                "longitude": obs.longitude, "basin": obs.basin,
            }]
        return [resolve_district(name=obs.district, district_id=obs.district_id)]
    if obs.station_code:
        hit = district_for_station(obs.station_code)
        return [hit] if hit else []
    if obs.basin:
        return districts_in_basin(obs.basin)
    return []


def _status_for(confidence: float, severity: str) -> str:
    if confidence >= 0.75 and severity in ("high", "severe"):
        return "active"
    if confidence >= 0.60:
        return "high_risk"
    if confidence >= 0.35:
        return "developing"
    return "potential"


def compute_risk_score(confidence: float, severity: str, ml_probability: float | None) -> float:
    """0-100. Evidence agreement and observed severity always count; the ML model
    contributes only once it has actually scored the event."""
    sev = SEVERITY_WEIGHT.get(severity, 0.5)
    if ml_probability is None:
        score = 100 * (0.55 * confidence + 0.45 * sev)
    else:
        score = 100 * (0.40 * confidence + 0.35 * sev + 0.25 * ml_probability)
    return round(min(score, 100.0), 1)


def _find_open_event(db: Session, district: str, observed_at) -> FloodEvent | None:
    """Same district, still open, and last touched inside the correlation window."""
    window_start = observed_at - timedelta(hours=settings.CORRELATION_WINDOW_HOURS)
    return db.scalars(
        select(FloodEvent)
        .where(
            FloodEvent.district == district,
            FloodEvent.status.in_(OPEN_STATUSES),
            FloodEvent.last_seen >= window_start,
        )
        .order_by(FloodEvent.last_seen.desc())
    ).first()


def _attach(db: Session, event: FloodEvent, obs: ImdObservation, trigger: Trigger) -> bool:
    """Attach evidence and raise confidence. Returns False if already attached."""
    dupe = db.scalar(
        select(EventEvidence).where(
            EventEvidence.event_id == event.id, EventEvidence.observation_id == obs.id
        )
    )
    if dupe:
        return False

    # Diminishing returns per evidence type. One basin forecast split across four
    # sub-basins is ONE signal, not four — without this, repeating the same kind of
    # observation would inflate confidence far beyond what the evidence supports.
    same_type = db.scalar(
        select(func.count())
        .select_from(EventEvidence)
        .join(ImdObservation, EventEvidence.observation_id == ImdObservation.id)
        .where(
            EventEvidence.event_id == event.id,
            ImdObservation.observation_type == obs.observation_type,
        )
    ) or 0
    contribution = round(trigger.contribution * (0.5 ** same_type), 4)

    db.add(EventEvidence(
        event_id=event.id, observation_id=obs.id, source=obs.source,
        trigger_reason=trigger.reason, contribution_score=contribution,
    ))
    # The session runs with autoflush off, so flush here — otherwise the count above
    # would not see evidence added earlier in this same batch and every contribution
    # would be treated as the first of its type.
    db.flush()

    # Confidence grows with corroborating evidence but never reaches certainty.
    event.confidence_score = round(min(event.confidence_score + contribution, 0.98), 3)
    event.severity = max_severity(event.severity, trigger.severity)
    event.last_seen = max(event.last_seen, obs.observed_at)
    event.status = _status_for(event.confidence_score, event.severity)
    event.risk_score = compute_risk_score(
        event.confidence_score, event.severity, event.prediction_probability
    )
    event.updated_at = utcnow()
    return True


def _open_event(db: Session, geo: dict, obs: ImdObservation, trigger: Trigger) -> FloodEvent:
    district = geo.get("district") or "Unknown"
    uid = f"FE-{district.replace(' ', '')[:12].upper()}-{obs.observed_at.strftime('%Y%m%d')}-{obs.id}"
    confidence = round(min(trigger.contribution + 0.10, 0.98), 3)
    event = FloodEvent(
        event_uid=uid, district=district, state=geo.get("state"),
        latitude=geo.get("latitude"), longitude=geo.get("longitude"),
        category=trigger.category, severity=trigger.severity,
        confidence_score=confidence, status=_status_for(confidence, trigger.severity),
        risk_score=compute_risk_score(confidence, trigger.severity, None),
        first_seen=obs.observed_at, last_seen=obs.observed_at,
    )
    db.add(event)
    db.flush()   # need event.id before attaching evidence
    return event


def correlate(db: Session, observations: list[ImdObservation]) -> dict[str, Any]:
    """Run trigger detection + correlation over a batch of new observations."""
    report = {"evaluated": len(observations), "triggered": 0,
              "events_created": 0, "evidence_attached": 0, "event_ids": []}

    for obs in observations:
        trigger = evaluate(obs)
        if not trigger.fired:
            continue
        report["triggered"] += 1

        for geo in _targets(obs):
            district = geo.get("district")
            if not district:
                continue

            event = _find_open_event(db, district, obs.observed_at)
            if event is None:
                event = _open_event(db, geo, obs, trigger)
                report["events_created"] += 1

            if _attach(db, event, obs, trigger):
                report["evidence_attached"] += 1
            if event.id not in report["event_ids"]:
                report["event_ids"].append(event.id)

    db.commit()
    log.info("correlation: %s", {k: v for k, v in report.items() if k != "event_ids"})
    return report


def resolve_stale(db: Session) -> int:
    """Close events that have had no new evidence for a day — the lifecycle end state."""
    cutoff = utcnow().replace(tzinfo=None) - timedelta(hours=STALE_AFTER_HOURS)
    stale = db.scalars(
        select(FloodEvent).where(FloodEvent.status.in_(OPEN_STATUSES), FloodEvent.last_seen < cutoff)
    ).all()
    for event in stale:
        event.status = "resolved"
        event.updated_at = utcnow()
    if stale:
        db.commit()
    return len(stale)
