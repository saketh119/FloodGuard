"""FloodGuard API gateway."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.core.logger import get_logger
from app.flood import scheduler
from app.flood.collectors.imd_collector import seed_stations
from app.routes import (
    chat, dashboard, districts, events, health, ingest, observations, predictions,
    stations, stream,
)

log = get_logger("floodguard.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seeded = seed_stations(db)
        log.info("database ready (%s stations seeded)", seeded)
    finally:
        db.close()

    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="FloodGuard API",
    description=(
        "AI-powered flood intelligence. Ingests IMD observations, detects triggers, "
        "correlates them into evolving flood events, scores severity with an ML model "
        "trained on IndoFloods, and answers preparedness questions from NDMA/IMD guidelines."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (health.router, events.router, stations.router, districts.router,
               dashboard.router, observations.router, predictions.router,
               chat.router, ingest.router, stream.router):
    app.include_router(router)


@app.get("/", tags=["system"])
def root():
    return {
        "service": "FloodGuard API",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": ["/health", "/events", "/stations", "/districts", "/dashboard/{district}",
                      "/observations", "/predictions", "/chat", "/ingest/run"],
    }
