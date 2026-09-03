"""APScheduler wiring — the platform pulls on a timer rather than on user request."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logger import get_logger
from app.flood.pipeline import run_cycle

log = get_logger("floodguard.scheduler")
_scheduler: AsyncIOScheduler | None = None


async def _job() -> None:
    db = SessionLocal()
    try:
        await run_cycle(db)
    except Exception as exc:                     # a failed cycle must not kill the timer
        log.exception("scheduled cycle failed: %s", exc)
    finally:
        db.close()


def start() -> AsyncIOScheduler | None:
    global _scheduler
    if not settings.SCHEDULER_ENABLED:
        log.info("scheduler disabled via SCHEDULER_ENABLED=false")
        return None
    _scheduler = AsyncIOScheduler(timezone="UTC")
    _scheduler.add_job(
        _job, "interval", seconds=settings.COLLECT_INTERVAL_S,
        id="imd_collect", max_instances=1,
        # coalesce: if the app was busy and several fires are due, run one, not a burst.
        coalesce=True,
    )
    _scheduler.start()
    log.info("scheduler started — IMD collection every %ss", settings.COLLECT_INTERVAL_S)
    return _scheduler


def shutdown() -> None:
    if _scheduler:
        _scheduler.shutdown(wait=False)
