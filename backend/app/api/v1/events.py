import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.events import FloodEvent

router = APIRouter()

@router.get("/")
async def list_events(
    district: Optional[str] = None,
    state: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(FloodEvent)
    if district:
        query = query.where(FloodEvent.district == district)
    if state:
        query = query.where(FloodEvent.state == state)
    if status:
        query = query.where(FloodEvent.status == status)
        
    query = query.order_by(FloodEvent.last_updated.desc())
    result = await db.execute(query)
    events = result.scalars().all()
    
    return {"status": "success", "count": len(events), "data": events}

@router.get("/active")
async def active_events(db: AsyncSession = Depends(get_db)):
    query = select(FloodEvent).where(FloodEvent.status.in_(["active", "high_risk"]))
    query = query.order_by(FloodEvent.last_updated.desc())
    result = await db.execute(query)
    events = result.scalars().all()
    return {"status": "success", "count": len(events), "data": events}

@router.get("/{event_id}")
async def get_event(event_id: str, db: AsyncSession = Depends(get_db)):
    query = select(FloodEvent).options(selectinload(FloodEvent.evidence)).where(FloodEvent.event_id == event_id)
    result = await db.execute(query)
    event = result.scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"status": "success", "data": event}
