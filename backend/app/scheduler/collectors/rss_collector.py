"""
scheduler/collectors/rss_collector.py
"""
from app.core.database import get_db
from app.core.logger import get_logger
from app.sources.rss.adapter import RSSAdapter
from app.pipeline.trigger import TriggerDetector
from app.pipeline.correlator import EventCorrelator
from sqlalchemy import select
from app.models.news import NewsObservation

log = get_logger(__name__)

async def run_rss_collection():
    log.info("Starting RSS collection cycle...")
    adapter = RSSAdapter()
    trigger_detector = TriggerDetector()
    correlator = EventCorrelator()

    articles = await adapter.ingest_all()

    for obs in articles:
        async with get_db() as db:
            # Check for duplicates using URL
            if obs.url:
                existing = await db.execute(select(NewsObservation).where(NewsObservation.url == obs.url))
                if existing.scalars().first():
                    continue

            db.add(obs)
            await db.flush()
            trigger = trigger_detector.check(obs)
            
        if trigger:
            await correlator.process(trigger)

    log.info("Finished RSS collection cycle.")
