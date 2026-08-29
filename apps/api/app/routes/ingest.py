from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.flood.pipeline import run_cycle
from app.schemas import IngestReport

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/run", response_model=IngestReport)
async def trigger_ingest(
    db: Session = Depends(get_db),
    summarise: bool = Query(True, description="Also regenerate AI summaries for touched events"),
):
    """Run one full pipeline pass now, instead of waiting for the scheduler."""
    return await run_cycle(db, summarise=summarise)
