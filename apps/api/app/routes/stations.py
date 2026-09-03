from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Station
from app.schemas import StationOut

router = APIRouter(prefix="/stations", tags=["stations"])


@router.get("", response_model=list[StationOut])
def list_stations(db: Session = Depends(get_db), state: str | None = Query(None)):
    """Station/district registry with coordinates — the map layer's source."""
    stmt = select(Station).order_by(Station.state, Station.station_name)
    if state:
        stmt = stmt.where(Station.state.ilike(f"%{state}%"))
    return list(db.scalars(stmt).all())
