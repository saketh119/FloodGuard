from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import PredictionResult
from app.schemas import PredictionOut
from app.services.prediction_service import (
    ModelUnavailable, metrics, model_status, predict_open_events,
)

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/model")
def get_model_info():
    """Model provenance and its honest cross-validated score."""
    return {**model_status(), "full_metrics": metrics()}


@router.post("/run", response_model=list[PredictionOut])
def run_predictions(db: Session = Depends(get_db)):
    """Re-score every open event against the current rainfall picture."""
    try:
        return predict_open_events(db)
    except ModelUnavailable as exc:
        raise HTTPException(503, str(exc))


@router.get("")
def list_predictions(
    db: Session = Depends(get_db),
    district: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """Stored scoring history — this is what a prediction-trend chart reads."""
    stmt = select(PredictionResult).order_by(PredictionResult.created_at.desc())
    if district:
        stmt = stmt.where(PredictionResult.district.ilike(f"%{district}%"))
    rows = db.scalars(stmt.limit(limit)).all()
    return {
        "model": model_status(),
        "results": [
            {
                "id": r.id, "event_id": r.event_id, "district": r.district,
                "model_version": r.model_version, "probability": r.probability,
                "risk_band": r.risk_band, "created_at": r.created_at,
                "features": r.features, "imputed_features": r.imputed_features,
            }
            for r in rows
        ],
    }
