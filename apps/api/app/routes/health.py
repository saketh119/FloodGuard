from fastapi import APIRouter
from sqlalchemy import func, select

from app.core.config import settings
from app.core.database import SessionLocal
from app.models import FloodEvent, ImdObservation
from app.services import llm, rag_service
from app.services.prediction_service import model_status

router = APIRouter(tags=["system"])


@router.get("/health")
def health():
    """Single call that tells you which half of the platform is currently degraded."""
    db = SessionLocal()
    try:
        observations = db.scalar(select(func.count()).select_from(ImdObservation)) or 0
        events = db.scalar(select(func.count()).select_from(FloodEvent)) or 0
    finally:
        db.close()

    return {
        "status": "ok",
        "database": {"url": settings.DATABASE_URL, "observations": observations, "events": events},
        "sources": {
            "imd": {"url": settings.IMD_BASE_URL, "live": False,
                    "note": "mock server — real IMD needs government credentials"},
            "openweather": {"configured": settings.openweather_enabled, "live": True,
                            "note": "real observed conditions + 5-day forecast"},
        },
        "scheduler": {"enabled": settings.SCHEDULER_ENABLED, "interval_s": settings.COLLECT_INTERVAL_S},
        "model": model_status(),
        "rag": rag_service.index_status(),
        "llm": llm.status(),
    }
