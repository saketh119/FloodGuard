from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.weather import WeatherObservation

router = APIRouter()

@router.get("/")
async def get_weather(
    district: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(WeatherObservation)
    if district:
        query = query.where(WeatherObservation.district == district)
    elif lat and lng:
        query = query.where(WeatherObservation.lat == lat).where(WeatherObservation.lng == lng)
        
    query = query.order_by(WeatherObservation.obs_time.desc()).limit(1)
    result = await db.execute(query)
    obs = result.scalars().first()
    
    if not obs:
        return {"status": "success", "data": None}
    return {"status": "success", "data": obs}
