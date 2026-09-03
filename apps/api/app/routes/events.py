from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import EventEvidence, FloodEvent, ImdObservation
from app.schemas import EventDetailOut, EventOut, EvidenceOut
from app.services.summary_service import summarise_event

router = APIRouter(prefix="/events", tags=["events"])


def _with_counts(db: Session, events: list[FloodEvent]) -> list[EventOut]:
    if not events:
        return []
    counts = dict(
        db.execute(
            select(EventEvidence.event_id, func.count())
            .where(EventEvidence.event_id.in_([e.id for e in events]))
            .group_by(EventEvidence.event_id)
        ).all()
    )
    out = []
    for event in events:
        item = EventOut.model_validate(event)
        item.evidence_count = counts.get(event.id, 0)
        out.append(item)
    return out


@router.get("", response_model=list[EventOut])
def list_events(
    db: Session = Depends(get_db),
    district: str | None = Query(None, description="Filter by district name"),
    state: str | None = Query(None),
    status: str | None = Query(None, description="potential|developing|high_risk|active|resolved"),
    severity: str | None = Query(None, description="low|moderate|high|severe"),
    min_risk: float | None = Query(None, ge=0, le=100),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Search flood events. This is the endpoint the dashboard's flood pages read."""
    stmt = select(FloodEvent)
    if district:
        stmt = stmt.where(FloodEvent.district.ilike(f"%{district}%"))
    if state:
        stmt = stmt.where(FloodEvent.state.ilike(f"%{state}%"))
    if status:
        stmt = stmt.where(FloodEvent.status == status)
    if severity:
        stmt = stmt.where(FloodEvent.severity == severity)
    if min_risk is not None:
        stmt = stmt.where(FloodEvent.risk_score >= min_risk)

    stmt = stmt.order_by(FloodEvent.risk_score.desc(), FloodEvent.last_seen.desc())
    events = db.scalars(stmt.limit(limit).offset(offset)).all()
    return _with_counts(db, list(events))


@router.get("/{event_id}", response_model=EventDetailOut)
def get_event(event_id: int, db: Session = Depends(get_db)):
    """One event plus its full evidence trail — why the platform believes this is real."""
    event = db.get(FloodEvent, event_id)
    if not event:
        raise HTTPException(404, "Event not found")

    rows = db.execute(
        select(EventEvidence, ImdObservation)
        .join(ImdObservation, EventEvidence.observation_id == ImdObservation.id)
        .where(EventEvidence.event_id == event.id)
        .order_by(EventEvidence.added_at.desc())
    ).all()

    evidence = []
    for ev, obs in rows:
        item = EvidenceOut.model_validate(ev)
        item.observation_type = obs.observation_type
        item.observed_at = obs.observed_at
        evidence.append(item)

    detail = EventDetailOut.model_validate(event)
    detail.evidence = evidence
    detail.evidence_count = len(evidence)
    return detail


@router.post("/{event_id}/summary")
async def regenerate_summary(event_id: int, force: bool = True, db: Session = Depends(get_db)):
    """Ask Gemini to rewrite this event's narrative from its current evidence."""
    event = db.get(FloodEvent, event_id)
    if not event:
        raise HTTPException(404, "Event not found")
    return await summarise_event(db, event, force=force)
