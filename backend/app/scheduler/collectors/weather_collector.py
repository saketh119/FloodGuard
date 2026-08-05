"""
scheduler/collectors/weather_collector.py
"""
from app.core.database import get_db
from app.core.logger import get_logger
from app.sources.weather.adapter import WeatherAdapter
from app.pipeline.trigger import TriggerDetector
from app.pipeline.correlator import EventCorrelator

log = get_logger(__name__)

async def run_weather_collection():
    log.info("Starting Weather collection cycle...")
    adapter = WeatherAdapter()
    trigger_detector = TriggerDetector()
    correlator = EventCorrelator()

    observations = await adapter.ingest_all()

    for obs in observations:
        async with get_db() as db:
            db.add(obs)
            await db.flush()
            trigger = trigger_detector.check(obs)
            
        if trigger:
            await correlator.process(trigger)

    log.info("Finished Weather collection cycle.")
