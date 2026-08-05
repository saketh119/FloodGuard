from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.cwc import CwcStation

router = APIRouter()

@router.get("/")
async def list_stations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CwcStation))
    stations = result.scalars().all()
    return {"status": "success", "count": len(stations), "data": stations}

@router.get("/{station_code}")
async def get_station(station_code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CwcStation).where(CwcStation.station_code == station_code))
    station = result.scalars().first()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    return {"status": "success", "data": station}
