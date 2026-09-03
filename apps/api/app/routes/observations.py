from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import ImdObservation
from app.schemas import ObservationOut

router = APIRouter(prefix="/observations", tags=["observations"])


@router.get("", response_model=list[ObservationOut])
def list_observations(
    db: Session = Depends(get_db),
    observation_type: str | None = Query(None, description="nowcast|warning|rainfall|current_wx|aws|qpf"),
    district: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
):
    """The immutable raw feed. Useful for auditing why an event exists."""
    stmt = select(ImdObservation).order_by(ImdObservation.observed_at.desc(), ImdObservation.id.desc())
    if observation_type:
        stmt = stmt.where(ImdObservation.observation_type == observation_type)
    if district:
        stmt = stmt.where(ImdObservation.district.ilike(f"%{district}%"))
    return list(db.scalars(stmt.limit(limit)).all())
