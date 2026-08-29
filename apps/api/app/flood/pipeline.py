"""One end-to-end pipeline pass: collect → trigger+correlate → predict → summarise."""
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logger import get_logger
from app.flood.collectors.imd_collector import collect, seed_stations
from app.flood.collectors import openweather_collector
from app.flood.engine.correlation import correlate, resolve_stale
from app.models import FloodEvent
from app.services.prediction_service import ModelUnavailable, predict_open_events
from app.routes.stream import publish
from app.services.summary_service import summarise_event

log = get_logger("floodguard.pipeline")


async def run_cycle(db: Session, summarise: bool = True) -> dict[str, Any]:
    seed_stations(db)

    collection = await collect(db)
    weather = await openweather_collector.collect(db)

    # Both sources feed one correlation pass, so a live OpenWeather reading and an
    # IMD warning for the same district land on the same event as separate evidence.
    new_observations = collection["new_observations"] + weather["new_observations"]
    correlation = correlate(db, new_observations)
    resolved = resolve_stale(db)

    report: dict[str, Any] = {
        "fetched": {**collection["fetched"], **weather["fetched"]},
        "stored": {**collection["stored"], **weather["stored"]},
        "triggered": correlation["triggered"],
        "events_created": correlation["events_created"],
        "evidence_attached": correlation["evidence_attached"],
        "events_resolved": resolved,
    }

    try:
        predictions = predict_open_events(db)
        report["events_scored"] = len(predictions)
    except ModelUnavailable as exc:
        report["events_scored"] = 0
        report["prediction_error"] = str(exc)

    if summarise and correlation["event_ids"]:
        # Only events that gained evidence this cycle need a fresh narrative.
        events = db.scalars(
            select(FloodEvent).where(FloodEvent.id.in_(correlation["event_ids"]))
        ).all()
        generated = 0
        for event in events:
            result = await summarise_event(db, event, force=True)
            generated += int(result.get("generated", False))
        report["summaries_generated"] = generated

    log.info("cycle complete: %s", report)

    # Tell connected dashboards immediately rather than making them wait for a poll.
    publish("cycle", {
        "stored": report["stored"],
        "events_created": report["events_created"],
        "evidence_attached": report["evidence_attached"],
        "events_scored": report.get("events_scored", 0),
    })
    return report
