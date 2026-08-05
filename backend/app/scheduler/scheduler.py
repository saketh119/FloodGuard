"""
scheduler/scheduler.py — APScheduler configuration.
Starts background tasks to run the collectors at defined intervals.
"""
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.core.logger import get_logger

# Collectors
from app.scheduler.collectors.imd_collector import run_imd_collection
from app.scheduler.collectors.cwc_collector import run_cwc_collection
from app.scheduler.collectors.weather_collector import run_weather_collection
from app.scheduler.collectors.rss_collector import run_rss_collection

log = get_logger(__name__)

_scheduler = AsyncIOScheduler()


def start_scheduler():
    """Starts the scheduler with all collection jobs."""
    if _scheduler.running:
        log.warning("Scheduler is already running.")
        return

    # Add jobs
    _scheduler.add_job(
        run_imd_collection,
        "interval",
        seconds=settings.imd_poll_seconds,
        id="imd_collection_job",
        replace_existing=True,
    )
    _scheduler.add_job(
        run_cwc_collection,
        "interval",
        seconds=settings.imd_poll_seconds * 2, # E.g., every 10 min
        id="cwc_collection_job",
        replace_existing=True,
    )
    _scheduler.add_job(
        run_weather_collection,
        "interval",
        seconds=settings.weather_poll_seconds,
        id="weather_collection_job",
        replace_existing=True,
    )
    _scheduler.add_job(
        run_rss_collection,
        "interval",
        seconds=settings.news_poll_seconds,
        id="rss_collection_job",
        replace_existing=True,
    )

    _scheduler.start()
    log.info("APScheduler started with all collection jobs.")
    
    # Optional: trigger initial run immediately in the background
    asyncio.create_task(run_imd_collection())
    asyncio.create_task(run_cwc_collection())
    asyncio.create_task(run_weather_collection())
    asyncio.create_task(run_rss_collection())


def stop_scheduler():
    """Stops the scheduler."""
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        log.info("APScheduler stopped.")
