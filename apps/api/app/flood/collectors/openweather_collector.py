"""OpenWeather collector — one current reading and one forecast per district."""
import asyncio
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logger import get_logger
from app.flood.adapters.openweather_adapter import adapt_current, summarise_forecast
from app.flood.collectors.imd_collector import persist
from app.flood.geo import registry
from app.models import ImdObservation

log = get_logger("floodguard.collector.openweather")

# Free tier allows 60 calls/minute. Seven districts × 2 endpoints = 14 calls per
# cycle, so a 60s schedule sits comfortably inside the limit.
CONCURRENCY = 4


async def _fetch(client: httpx.AsyncClient, path: str, district: dict) -> dict | None:
    try:
        res = await client.get(path, params={
            "lat": district["latitude"],
            "lon": district["longitude"],
            "units": "metric",
            "appid": settings.OPENWEATHER_API_KEY,
        })
    except httpx.RequestError as exc:
        log.warning("OpenWeather %s unreachable for %s: %s", path, district["district"], exc)
        return None

    if res.status_code == 401:
        log.error("OpenWeather rejected the API key — check OPENWEATHER_API_KEY")
        return None
    if res.status_code == 429:
        log.warning("OpenWeather rate limit hit; skipping %s this cycle", district["district"])
        return None
    if res.status_code != 200:
        log.warning("OpenWeather %s → HTTP %s for %s", path, res.status_code, district["district"])
        return None

    return res.json()


async def collect(db: Session) -> dict[str, Any]:
    """Fetch live conditions for every district. Returns a report plus new rows."""
    report: dict[str, Any] = {
        "fetched": {"ow_current": 0, "ow_forecast": 0},
        "stored": {"ow_current": 0, "ow_forecast": 0},
        "new_observations": [],
    }

    if not settings.openweather_enabled:
        report["skipped"] = "OPENWEATHER_API_KEY not set"
        return report

    # registry() = built-in IMD districts + whatever users have chosen to follow.
    districts = [d for d in registry(db) if d.get("latitude") and d.get("longitude")]
    semaphore = asyncio.Semaphore(CONCURRENCY)

    async with httpx.AsyncClient(
        base_url=settings.OPENWEATHER_BASE_URL, timeout=settings.OPENWEATHER_TIMEOUT_S
    ) as client:

        async def one(district: dict) -> tuple[dict | None, dict | None]:
            async with semaphore:
                current, forecast = await asyncio.gather(
                    _fetch(client, "/weather", district),
                    _fetch(client, "/forecast", district),
                )
            return (
                adapt_current(current, district) if current else None,
                summarise_forecast(forecast, district) if forecast else None,
            )

        results = await asyncio.gather(*(one(d) for d in districts))

    adapted: list[dict] = []
    for current, forecast in results:
        if current:
            report["fetched"]["ow_current"] += 1
            adapted.append(current)
        if forecast:
            report["fetched"]["ow_forecast"] += 1
            adapted.append(forecast)

    stored: list[ImdObservation] = persist(db, adapted)
    for obs in stored:
        report["stored"][obs.observation_type] = report["stored"].get(obs.observation_type, 0) + 1
    report["new_observations"] = stored

    log.info("openweather: fetched=%s stored=%s", report["fetched"], report["stored"])
    return report
