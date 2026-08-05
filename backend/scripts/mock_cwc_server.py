"""
scripts/mock_cwc_server.py — Mock CWC (Central Water Commission) API Server.

Replicates the real CWC endpoints discovered via reverse engineering:
  GET /iam/api/layer-station/{stationCode}  → station metadata
  GET /iam/api/station-data/{stationCode}   → time-series water levels

Run with:
    python backend/scripts/mock_cwc_server.py
    # → http://localhost:8081

Six stations across major flood-prone river basins, two of which are
near / above danger level to trigger the detection pipeline.
"""
import uvicorn
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import random

app = FastAPI(title="CWC Mock API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Station Registry ───────────────────────────────────────────────────
STATIONS = {
    "GD-212": {
        "station_code": "GD-212",
        "station_name": "Brahmaputra at Guwahati",
        "river": "Brahmaputra",
        "basin": "Brahmaputra",
        "district": "Kamrup Metropolitan",
        "state": "Assam",
        "lat": 26.1445,
        "lng": 91.7362,
        "frl": 49.68,          # Full Reservoir Level (m)
        "mwl": 51.80,          # Maximum Water Level (m)
        "warning_level": 49.68,
        "danger_level": 51.00,
        "flood_scenario": True,   # Near danger → triggers pipeline
    },
    "KR-309": {
        "station_code": "KR-309",
        "station_name": "Krishna at Vijayawada",
        "river": "Krishna",
        "basin": "Krishna",
        "district": "NTR",
        "state": "Andhra Pradesh",
        "lat": 16.5062,
        "lng": 80.648,
        "frl": 98.45,
        "mwl": 102.10,
        "warning_level": 98.45,
        "danger_level": 100.60,
        "flood_scenario": False,
    },
    "GD-415": {
        "station_code": "GD-415",
        "station_name": "Godavari at Polavaram",
        "river": "Godavari",
        "basin": "Godavari",
        "district": "West Godavari",
        "state": "Andhra Pradesh",
        "lat": 17.2547,
        "lng": 81.6532,
        "frl": 44.90,
        "mwl": 47.20,
        "warning_level": 43.50,
        "danger_level": 45.72,
        "flood_scenario": True,   # Above danger
    },
    "PR-101": {
        "station_code": "PR-101",
        "station_name": "Periyar at Neeleswaram",
        "river": "Periyar",
        "basin": "Periyar",
        "district": "Ernakulam",
        "state": "Kerala",
        "lat": 9.9816,
        "lng": 76.2999,
        "frl": 8.40,
        "mwl": 10.20,
        "warning_level": 7.80,
        "danger_level": 9.10,
        "flood_scenario": False,
    },
    "GA-208": {
        "station_code": "GA-208",
        "station_name": "Ganga at Patna",
        "river": "Ganga",
        "basin": "Ganga",
        "district": "Patna",
        "state": "Bihar",
        "lat": 25.5941,
        "lng": 85.1376,
        "frl": 48.50,
        "mwl": 52.30,
        "warning_level": 48.00,
        "danger_level": 50.27,
        "flood_scenario": False,
    },
    "MH-317": {
        "station_code": "MH-317",
        "station_name": "Musi at Hyderabad",
        "river": "Musi",
        "basin": "Krishna",
        "district": "Hyderabad",
        "state": "Telangana",
        "lat": 17.385,
        "lng": 78.4867,
        "frl": 497.0,
        "mwl": 503.0,
        "warning_level": 497.0,
        "danger_level": 500.5,
        "flood_scenario": False,
    },
}


def _water_level(station: dict) -> float:
    """Generate realistic water level: above danger if flood_scenario=True."""
    if station["flood_scenario"]:
        # 50–110% above danger level
        pct = random.uniform(1.005, 1.10)
        return round(station["danger_level"] * pct, 2)
    else:
        # 70–95% of warning level
        pct = random.uniform(0.70, 0.95)
        return round(station["warning_level"] * pct, 2)


def _status(level: float, station: dict) -> str:
    if level >= station["danger_level"] * 1.05:
        return "severe"
    if level >= station["danger_level"]:
        return "danger"
    if level >= station["warning_level"]:
        return "warning"
    return "safe"


# ── Endpoints ──────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"service": "CWC Mock API", "stations": len(STATIONS)}


@app.get("/iam/api/layer-station/{station_code}")
def station_metadata(station_code: str):
    s = STATIONS.get(station_code)
    if not s:
        raise HTTPException(404, detail=f"Station {station_code!r} not found")
    return {
        "status": True,
        "data": {k: v for k, v in s.items() if k != "flood_scenario"},
    }


@app.get("/iam/api/station-data/{station_code}")
def station_data(station_code: str):
    s = STATIONS.get(station_code)
    if not s:
        raise HTTPException(404, detail=f"Station {station_code!r} not found")

    now = datetime.utcnow()
    records = []
    level = _water_level(s)

    for i in range(24):  # Last 24 hourly readings
        t = now - timedelta(hours=i)
        variation = random.uniform(-0.3, 0.3)
        lvl = round(level + variation, 2)
        records.append({
            "measurement_time": t.isoformat(),
            "water_level": lvl,
            "discharge": round(lvl * random.uniform(180, 220), 1),
            "status": _status(lvl, s),
        })

    return {
        "status": True,
        "station_code": station_code,
        "data": records,
    }


@app.get("/iam/api/stations")
def all_stations():
    """Return all station metadata (for batch sync)."""
    return {
        "status": True,
        "totalCount": len(STATIONS),
        "data": [{k: v for k, v in s.items() if k != "flood_scenario"} for s in STATIONS.values()],
    }


if __name__ == "__main__":
    print("Starting CWC Mock Server on http://localhost:8081 …")
    uvicorn.run("mock_cwc_server:app", host="0.0.0.0", port=8081, reload=True)
