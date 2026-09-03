"""District registry — the enrichment step of the pipeline.

IMD's nowcast and warning endpoints return a district NAME only. Trigger detection
and event correlation need a state and coordinates, so we resolve them here.
Today this is a static registry covering the districts the mock server serves; the
production path is a geocoding service behind the same two functions.
"""
from typing import Any

_DISTRICTS: list[dict[str, Any]] = [
    {"district_id": "164", "district": "Kamrup Metropolitan", "state": "Assam",
     "latitude": 26.1445, "longitude": 91.7362, "basin": "Brahmaputra"},
    {"district_id": "165", "district": "Dibrugarh", "state": "Assam",
     "latitude": 27.4728, "longitude": 94.9120, "basin": "Brahmaputra"},
    {"district_id": "573", "district": "Ernakulam", "state": "Kerala",
     "latitude": 9.9816, "longitude": 76.2999, "basin": "Periyar"},
    {"district_id": "574", "district": "Wayanad", "state": "Kerala",
     "latitude": 11.6854, "longitude": 76.1320, "basin": "Periyar"},
    {"district_id": "201", "district": "Patna", "state": "Bihar",
     "latitude": 25.5941, "longitude": 85.1376, "basin": "Ganga"},
    {"district_id": "202", "district": "Muzaffarpur", "state": "Bihar",
     "latitude": 26.1197, "longitude": 85.3910, "basin": "Ganga"},
    {"district_id": "999", "district": "New Delhi", "state": "Delhi",
     "latitude": 28.6139, "longitude": 77.2090, "basin": "Yamuna"},
]

_BY_ID = {d["district_id"]: d for d in _DISTRICTS}
_BY_NAME = {d["district"].lower(): d for d in _DISTRICTS}


def normalize_district(name: str | None) -> str | None:
    """Standardise district spelling so correlation matches across sources."""
    if not name:
        return None
    cleaned = " ".join(name.strip().split())
    known = _BY_NAME.get(cleaned.lower())
    return known["district"] if known else cleaned


def resolve_district(name: str | None = None, district_id: str | None = None) -> dict[str, Any]:
    """Returns state/lat/lng/basin for a district, or empty strings when unknown."""
    if district_id and district_id in _BY_ID:
        return dict(_BY_ID[district_id])
    if name:
        hit = _BY_NAME.get(" ".join(name.strip().split()).lower())
        if hit:
            return dict(hit)
    return {"district_id": district_id, "district": normalize_district(name),
            "state": None, "latitude": None, "longitude": None, "basin": None}


def all_districts() -> list[dict[str, Any]]:
    """The built-in registry — districts the IMD source actually reports on."""
    return [dict(d) for d in _DISTRICTS]


def is_builtin(name: str | None) -> bool:
    return bool(name) and " ".join(name.strip().split()).lower() in _BY_NAME


def tracked_districts(db) -> list[dict[str, Any]]:
    """Locations users added. OpenWeather covers these; IMD does not."""
    from sqlalchemy import select

    from app.models import TrackedLocation

    return [
        {
            "district_id": f"OW{row.id}", "district": row.district, "state": row.state,
            "latitude": row.latitude, "longitude": row.longitude, "basin": row.basin,
            "country": row.country, "tracked": True,
        }
        for row in db.scalars(select(TrackedLocation).order_by(TrackedLocation.district)).all()
    ]


def registry(db) -> list[dict[str, Any]]:
    """Everything the platform currently follows, built-in first.

    Built-in entries win on a name clash — they carry the IMD ids that the district
    endpoints need, which a geocoded entry cannot supply.
    """
    merged = all_districts()
    for d in merged:
        d["tracked"] = False
        d["imd"] = True
    seen = {d["district"].lower() for d in merged}
    for d in tracked_districts(db):
        if d["district"].lower() not in seen:
            d["imd"] = False
            merged.append(d)
    return merged


def resolve_any(db, name: str | None) -> dict[str, Any] | None:
    """Resolve a district by name across both the built-in and tracked sets."""
    if not name:
        return None
    target = " ".join(name.strip().split()).lower()
    for d in registry(db):
        if d["district"].lower() == target:
            return d
    return None


# Station code → district id (IMD publishes stations and districts as separate registries).
_STATION_DISTRICT = {
    "42182": "164",   # Guwahati        → Kamrup Metropolitan
    "43353": "573",   # Kochi           → Ernakulam
    "42492": "201",   # Patna Airport   → Patna
    "GHT": "164", "KCH": "573", "NDL": "999",
}


def district_for_station(station_code: str | None) -> dict[str, Any] | None:
    if not station_code:
        return None
    did = _STATION_DISTRICT.get(str(station_code))
    return dict(_BY_ID[did]) if did and did in _BY_ID else None


def districts_in_basin(basin: str | None) -> list[dict[str, Any]]:
    """A basin-wide forecast applies to every district that basin drains."""
    if not basin:
        return []
    return [dict(d) for d in _DISTRICTS if (d.get("basin") or "").lower() == basin.lower()]
