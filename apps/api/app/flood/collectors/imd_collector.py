"""IMD collector — fetch, adapt, dedupe-insert. Runs on the scheduler and on demand."""
import asyncio
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logger import get_logger
from app.flood.adapters.imd_adapter import ADAPTERS
from app.flood.geo import all_districts
from app.models import ImdObservation, Station

log = get_logger("floodguard.collector.imd")

# endpoint → observation type. Each is polled for every known district/station.
ENDPOINTS = [
    ("nowcast",    "/api/v1/nowcast"),
    ("warning",    "/api/v1/districtwarning"),
    ("rainfall",   "/api/v1/districtrainfall"),
    ("current_wx", "/api/v1/current_wx"),
    ("aws",        "/api/v1/aws_data"),
    ("qpf",        "/api/v1/basinqpf"),
    ("forecast",   "/api/v1/cityforecastloc"),
]


async def _get(client: httpx.AsyncClient, path: str) -> list[dict]:
    """Calls one endpoint with no id filter so we get every district/station at once."""
    try:
        res = await client.get(path)
        res.raise_for_status()
        body = res.json()
    except Exception as exc:  # network, non-2xx, bad JSON — a dead endpoint must not kill the run
        log.warning("IMD %s failed: %s", path, exc)
        return []

    data = body.get("data") if isinstance(body, dict) else body
    if data is None:
        return []
    return data if isinstance(data, list) else [data]


async def fetch_all() -> dict[str, list[dict]]:
    """Fan out across all IMD endpoints in one latency budget."""
    async with httpx.AsyncClient(base_url=settings.IMD_BASE_URL, timeout=settings.IMD_TIMEOUT_S) as client:
        results = await asyncio.gather(*(_get(client, path) for _, path in ENDPOINTS))
    return {obs_type: rows for (obs_type, _), rows in zip(ENDPOINTS, results)}


def seed_stations(db: Session) -> int:
    """Upsert district metadata so /stations has something to serve immediately."""
    added = 0
    for d in all_districts():
        code = f"IMD-D{d['district_id']}"
        existing = db.scalar(select(Station).where(Station.station_code == code))
        if existing:
            continue
        db.add(Station(
            station_code=code, station_name=d["district"], district_id=d["district_id"],
            district=d["district"], state=d["state"], latitude=d["latitude"],
            longitude=d["longitude"], source="IMD", raw_metadata=d,
        ))
        added += 1
    db.commit()
    return added


def persist(db: Session, adapted: list[dict]) -> list[ImdObservation]:
    """Insert only observations we have not already stored (content hash)."""
    if not adapted:
        return []

    hashes = [r["dedupe_hash"] for r in adapted]
    seen = set(db.scalars(select(ImdObservation.dedupe_hash).where(ImdObservation.dedupe_hash.in_(hashes))).all())

    fresh: list[ImdObservation] = []
    batch_hashes: set[str] = set()
    for rec in adapted:
        h = rec["dedupe_hash"]
        if h in seen or h in batch_hashes:   # guard against dupes inside one batch too
            continue
        batch_hashes.add(h)
        fresh.append(ImdObservation(**rec))

    if fresh:
        db.add_all(fresh)
        db.commit()
    return fresh


async def collect(db: Session) -> dict[str, Any]:
    """One full collection cycle. Returns a per-endpoint report."""
    payloads = await fetch_all()
    report: dict[str, Any] = {"fetched": {}, "stored": {}, "new_observations": []}

    for obs_type, rows in payloads.items():
        report["fetched"][obs_type] = len(rows)
        if not rows:
            report["stored"][obs_type] = 0
            continue
        adapted = ADAPTERS[obs_type](rows)
        stored = persist(db, adapted)
        report["stored"][obs_type] = len(stored)
        report["new_observations"].extend(stored)

    log.info("collected: fetched=%s stored=%s", report["fetched"], report["stored"])
    return report
