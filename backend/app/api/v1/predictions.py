from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.predictions import PredictionResult

router = APIRouter()

@router.get("/")
async def list_predictions(
    district: Optional[str] = None,
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(PredictionResult)
    if district:
        query = query.where(PredictionResult.district == district)
    if state:
        query = query.where(PredictionResult.state == state)
        
    query = query.order_by(PredictionResult.prediction_time.desc())
    result = await db.execute(query)
    preds = result.scalars().all()
    
    return {"status": "success", "count": len(preds), "data": preds}
