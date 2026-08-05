"""
app/main.py — FloodGuard FastAPI application entry point.

Startup sequence:
  1. Create all DB tables (idempotent)
  2. Start APScheduler with IMD/CWC/Weather/RSS jobs
  3. Mount all API routers under /api/v1/

Run locally:
    cd backend
    uvicorn app.main:app --reload --port 8000
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import create_all_tables
from app.core.logger import get_logger

log = get_logger(__name__)


# ── Lifespan (startup / shutdown) ─────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("FloodGuard backend starting up …")

    # 1. Ensure all DB tables exist
    await create_all_tables()
    log.info("Database tables ready.")

    # 2. Start background scheduler
    try:
        from app.scheduler.scheduler import start_scheduler, stop_scheduler
        start_scheduler()
        log.info("APScheduler started.")
    except Exception as exc:
        log.warning(f"Scheduler failed to start (non-fatal): {exc}")

    yield  # ── App is running ──

    # Shutdown
    try:
        from app.scheduler.scheduler import stop_scheduler
        stop_scheduler()
    except Exception:
        pass
    log.info("FloodGuard backend shut down.")


# ── App factory ────────────────────────────────────────────────────────
app = FastAPI(
    title="FloodGuard API",
    description=(
        "AI-Powered Flood Intelligence Platform — ingests IMD, CWC, Weather "
        "and News data, correlates flood events, and serves them via REST."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow the Vite dev server and any localhost port
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────
from app.api.v1 import router as api_v1_router  # noqa: E402

app.include_router(api_v1_router, prefix="/api/v1")


# ── Health / root ──────────────────────────────────────────────────────
@app.get("/", tags=["Meta"])
async def root():
    return {
        "service": "FloodGuard API",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
    }


@app.get("/health", tags=["Meta"])
async def health():
    return {"status": "ok", "env": settings.app_env}
