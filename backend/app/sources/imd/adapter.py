"""
sources/imd/adapter.py — IMD Source Adapter.

Fetches all IMD endpoints for a given location configuration and
normalizes the results into an ImdObservation ORM object.

The adapter is pure transformation — it does NOT write to the database.
The collector calls the adapter, then writes the result.
"""
import json
from datetime import datetime, timezone

import httpx

from app.core.config import settings
from app.core.logger import get_logger
from app.models.imd import ImdObservation

log = get_logger(__name__)

# ── Location config that the adapter understands ───────────────────────
# Mirrors the frontend LOCATIONS dict; backend keeps its own copy
BACKEND_LOCATIONS = [
    {
        "key": "hyderabad",
        "label": "Hyderabad",
        "state": "Telangana",
        "lat": 17.385, "lng": 78.4867,
        "stationId": "42182",
        "districtId": "164",
        "basinId": "100",
        "awsStateId": "18",
    },
    {
        "key": "vijayawada",
        "label": "Vijayawada",
        "state": "Andhra Pradesh",
        "lat": 16.5062, "lng": 80.648,
        "stationId": "43353",
        "districtId": "201",
        "basinId": "200",
        "awsStateId": "7",
    },
    {
        "key": "guntur",
        "label": "Guntur",
        "state": "Andhra Pradesh",
        "lat": 16.3067, "lng": 80.4365,
        "stationId": "42492",
        "districtId": "202",
        "basinId": "200",
        "awsStateId": "7",
    },
    {
        "key": "warangal",
        "label": "Warangal",
        "state": "Telangana",
        "lat": 17.9689, "lng": 79.5941,
        "stationId": "42182",
        "districtId": "164",
        "basinId": "100",
        "awsStateId": "18",
    },
]


class IMDAdapter:
    """
    Fetches and normalizes IMD API data for a single location.

    Usage:
        adapter = IMDAdapter()
        obs = await adapter.ingest(location_cfg)
        # obs is ImdObservation ready to be saved
    """

    def __init__(self):
        self._base = settings.imd_base_url.rstrip("/")

    async def ingest(self, loc: dict) -> ImdObservation | None:
        """
        Fetch all relevant IMD endpoints for `loc` and return a normalized
        ImdObservation. Returns None if the API is unreachable.
        """
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                wx, nc, rf, warn = await self._fetch_all(client, loc)
            except Exception as exc:
                log.warning(f"IMD fetch failed for {loc['label']}: {exc}")
                return None

        return self._normalize(loc, wx, nc, rf, warn)

    async def _fetch_all(self, client: httpx.AsyncClient, loc: dict):
        sid = loc["stationId"]
        did = loc["districtId"]

        async def get(path, params):
            r = await client.get(f"{self._base}{path}", params=params)
            r.raise_for_status()
            return r.json()

        wx   = await get("/api/v1/current_wx",       {"id": sid})
        nc   = await get("/api/v1/nowcast",           {"id": did})
        rf   = await get("/api/v1/districtrainfall",  {"id": did})
        warn = await get("/api/v1/districtwarning",   {"id": did})
        return wx, nc, rf, warn

    def _normalize(self, loc, wx, nc, rf, warn) -> ImdObservation:
        wx_row   = (wx.get("data")   or [{}])[0]
        nc_row   = (nc.get("data")   or [{}])[0]
        rf_row   = (rf.get("data")   or [{}])[0]
        warn_row = (warn.get("data") or [{}])[0]

        rain24h  = float(wx_row.get("Last 24 hrs Rainfall", 0) or 0)
        w_speed  = float(wx_row.get("Wind Speed", 0) or 0)
        temp     = float(wx_row.get("Temperature", 0) or 0)
        humidity = float(wx_row.get("Humidity", 0) or 0)
        mslp     = wx_row.get("M.S.L.P")

        nc_color = int(nc_row.get("color", 1))
        nc_msg   = nc_row.get("message", "")

        raw = {
            "wx": wx_row, "nc": nc_row,
            "rf": rf_row, "warn": warn_row,
        }

        # Trigger logic (colour 3=Orange, 4=Red; or heavy rain)
        triggered = nc_color >= 3 or rain24h > 64.5
        reason = []
        if nc_color >= 3:
            reason.append(f"nowcast_color={nc_color}")
        if rain24h > 64.5:
            reason.append(f"rain24h={rain24h:.1f}mm")

        return ImdObservation(
            station_code=loc["stationId"],
            station_name=wx_row.get("Station", loc["label"]),
            district_id=loc["districtId"],
            district_name=warn_row.get("District", loc["label"]),
            state=loc["state"],
            lat=loc["lat"],
            lng=loc["lng"],
            obs_time=datetime.now(timezone.utc),
            temperature=temp or None,
            humidity=humidity or None,
            wind_speed=w_speed or None,
            wind_direction=wx_row.get("Wind Direction"),
            mslp=float(mslp) if mslp else None,
            rain_24h=rain24h,
            weather_code=str(wx_row.get("Weather Code", "00")).zfill(2),
            nowcast_color=nc_color,
            nowcast_msg=nc_msg,
            nowcast_valid_upto=nc_row.get("Vupto"),
            warning_day1_color=warn_row.get("Day1_Color"),
            warning_day2_color=warn_row.get("Day2_Color"),
            warning_day3_color=warn_row.get("Day3_Color"),
            warning_day4_color=warn_row.get("Day4_Color"),
            warning_day5_color=warn_row.get("Day5_Color"),
            triggered=triggered,
            trigger_reason="; ".join(reason) if reason else None,
            raw_json=json.dumps(raw),
        )
