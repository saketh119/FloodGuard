from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.cwc import CwcStation

router = APIRouter()

@router.get("/")
async def list_rivers(db: AsyncSession = Depends(get_db)):
    # Get stations with their latest measurements
    query = select(CwcStation).options(selectinload(CwcStation.measurements))
    result = await db.execute(query)
    stations = result.scalars().all()
    return {"status": "success", "count": len(stations), "data": stations}
