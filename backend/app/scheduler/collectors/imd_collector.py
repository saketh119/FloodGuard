"""
scheduler/collectors/imd_collector.py
"""
import asyncio
from app.core.database import get_db
from app.core.logger import get_logger
from app.sources.imd.adapter import IMDAdapter, BACKEND_LOCATIONS
from app.pipeline.trigger import TriggerDetector
from app.pipeline.correlator import EventCorrelator

log = get_logger(__name__)

async def run_imd_collection():
    log.info("Starting IMD collection cycle...")
    adapter = IMDAdapter()
    trigger_detector = TriggerDetector()
    correlator = EventCorrelator()

    for loc in BACKEND_LOCATIONS:
        obs = await adapter.ingest(loc)
        if not obs:
            continue
            
        # Persist observation
        async with get_db() as db:
            db.add(obs)
            await db.flush() # flush to get obs.id
            
            # Check for triggers
            trigger = trigger_detector.check(obs)
            
        # If triggered, correlate and update events
        if trigger:
            await correlator.process(trigger)
            
    log.info("Finished IMD collection cycle.")
