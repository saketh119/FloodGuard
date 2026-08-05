"""
sources/cwc/adapter.py — CWC Source Adapter.

Two operations:
  sync_stations()        → Upsert all station metadata from CWC API
  ingest_measurements()  → Fetch latest water levels for all stations

Derives CwcMeasurement.status from danger_level / warning_level.
"""
import json
from datetime import datetime, timezone

import httpx
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.core.logger import get_logger
from app.models.cwc import CwcMeasurement, CwcStation

log = get_logger(__name__)

CWC_BASE = "http://localhost:8081"  # mock server; swap for real CWC base URL


class CWCAdapter:

    async def sync_stations(self) -> int:
        """
        Fetch all CWC station metadata and upsert into cwc_station.
        Returns number of stations synced.
        """
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                r = await client.get(f"{CWC_BASE}/iam/api/stations")
                r.raise_for_status()
                payload = r.json()
            except Exception as exc:
                log.warning(f"CWC station sync failed: {exc}")
                return 0

        stations_data = payload.get("data", [])
        count = 0

        async with get_db() as db:
            for s in stations_data:
                code = s.get("station_code")
                if not code:
                    continue

                existing = await db.get(CwcStation, code)
                if existing:
                    existing.station_name = s.get("station_name", existing.station_name)
                    existing.river = s.get("river", existing.river)
                    existing.basin = s.get("basin", existing.basin)
                    existing.district = s.get("district", existing.district)
                    existing.state = s.get("state", existing.state)
                    existing.lat = s.get("lat", existing.lat)
                    existing.lng = s.get("lng", existing.lng)
                    existing.frl = s.get("frl", existing.frl)
                    existing.mwl = s.get("mwl", existing.mwl)
                    existing.warning_level = s.get("warning_level", existing.warning_level)
                    existing.danger_level = s.get("danger_level", existing.danger_level)
                    existing.raw_metadata = json.dumps(s)
                else:
                    station = CwcStation(
                        station_code=code,
                        station_name=s.get("station_name", ""),
                        river=s.get("river"),
                        basin=s.get("basin"),
                        district=s.get("district"),
                        state=s.get("state"),
                        lat=s.get("lat"),
                        lng=s.get("lng"),
                        frl=s.get("frl"),
                        mwl=s.get("mwl"),
                        warning_level=s.get("warning_level"),
                        danger_level=s.get("danger_level"),
                        raw_metadata=json.dumps(s),
                    )
                    db.add(station)

                count += 1

        log.info(f"CWC: synced {count} stations")
        return count

    async def ingest_measurements(self) -> list[CwcMeasurement]:
        """
        Fetch the latest water level for every known station.
        Returns a list of CwcMeasurement objects (already saved to DB).
        """
        async with get_db() as db:
            result = await db.execute(select(CwcStation))
            stations = result.scalars().all()

        if not stations:
            log.warning("No CWC stations in DB — run sync_stations() first")
            return []

        measurements = []
        async with httpx.AsyncClient(timeout=15) as client:
            for station in stations:
                m = await self._fetch_measurement(client, station)
                if m:
                    measurements.append(m)

        # Persist all in one transaction
        if measurements:
            async with get_db() as db:
                db.add_all(measurements)

        log.info(f"CWC: ingested {len(measurements)} measurements")
        return measurements

    async def _fetch_measurement(
        self, client: httpx.AsyncClient, station: CwcStation
    ) -> CwcMeasurement | None:
        try:
            r = await client.get(f"{CWC_BASE}/iam/api/station-data/{station.station_code}")
            r.raise_for_status()
            payload = r.json()
        except Exception as exc:
            log.warning(f"CWC fetch failed for {station.station_code}: {exc}")
            return None

        records = payload.get("data", [])
        if not records:
            return None

        # Use the most recent record (index 0 = now)
        latest = records[0]
        level = latest.get("water_level")
        discharge = latest.get("discharge")
        status = self._derive_status(level, station)

        return CwcMeasurement(
            station_code=station.station_code,
            measurement_time=datetime.now(timezone.utc),
            water_level=level,
            discharge=discharge,
            status=status,
            raw_json=json.dumps(latest),
        )

    @staticmethod
    def _derive_status(level: float | None, station: CwcStation) -> str:
        if level is None:
            return "safe"
        danger = station.danger_level or 0
        warning = station.warning_level or 0
        if danger and level >= danger * 1.05:
            return "severe"
        if danger and level >= danger:
            return "danger"
        if warning and level >= warning:
            return "warning"
        return "safe"
