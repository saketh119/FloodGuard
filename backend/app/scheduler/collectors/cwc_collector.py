"""
scheduler/collectors/cwc_collector.py
"""
from app.core.logger import get_logger
from app.sources.cwc.adapter import CWCAdapter
from app.pipeline.trigger import TriggerDetector
from app.pipeline.correlator import EventCorrelator

log = get_logger(__name__)

async def run_cwc_collection():
    log.info("Starting CWC collection cycle...")
    adapter = CWCAdapter()
    trigger_detector = TriggerDetector()
    correlator = EventCorrelator()

    # Sync stations occasionally (every cycle here for simplicity, could be less frequent)
    await adapter.sync_stations()

    # Ingest measurements
    measurements = await adapter.ingest_measurements()
    
    for obs in measurements:
        trigger = trigger_detector.check(obs)
        if trigger:
            await correlator.process(trigger)

    log.info("Finished CWC collection cycle.")
