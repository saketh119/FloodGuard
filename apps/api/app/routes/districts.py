"""Location registry and place search.

The built-in registry covers the districts IMD reports on. Anything a user searches
for is geocoded and tracked, and the collector then follows it for live conditions —
so the platform is not limited to the handful of districts the mock source knows.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.flood.geo import registry
from app.models import TrackedLocation, utcnow
from app.services.geocoding import GeocodingUnavailable, reverse, search

router = APIRouter(prefix="/districts", tags=["reference"])


def _coords(lat: float | None, lon: float | None) -> str | None:
    if lat is None or lon is None:
        return None
    return (f"{abs(lat):.4f}\u00b0 {'N' if lat >= 0 else 'S'}, "
            f"{abs(lon):.4f}\u00b0 {'E' if lon >= 0 else 'W'}")


@router.get("")
def list_districts(db: Session = Depends(get_db)):
    """Everything currently followed — built-in districts plus tracked locations."""
    return [
        {
            "id": d["district_id"],
            "district": d["district"],
            "state": d["state"],
            "label": ", ".join(x for x in (d["district"], d.get("state")) if x),
            "latitude": d.get("latitude"),
            "longitude": d.get("longitude"),
            "basin": d.get("basin"),
            "coords": _coords(d.get("latitude"), d.get("longitude")),
            # imd=False means live weather only: IMD warnings and district rainfall
            # are not available for this location.
            "imd": d.get("imd", True),
            "tracked": d.get("tracked", False),
        }
        for d in registry(db)
    ]


@router.get("/search")
async def search_places(
    q: str = Query(min_length=2, max_length=80, description="Place name"),
    country: str | None = Query("IN", description="ISO country code, or empty for worldwide"),
):
    """Find places to follow. Results are candidates — POST /districts/track to add one."""
    try:
        return await search(q, country=country or None)
    except GeocodingUnavailable as exc:
        raise HTTPException(503, str(exc))


@router.get("/reverse")
async def reverse_lookup(
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
):
    """Name the place at a coordinate — backs the browser's "use my location"."""
    try:
        results = await reverse(lat, lon)
    except GeocodingUnavailable as exc:
        raise HTTPException(503, str(exc))
    if not results:
        raise HTTPException(404, "No named place found at those coordinates")
    return results[0]


@router.post("/track")
def track_place(
    district: str = Query(min_length=1, max_length=96),
    latitude: float = Query(ge=-90, le=90),
    longitude: float = Query(ge=-180, le=180),
    state: str | None = Query(None),
    country: str = Query("IN"),
    db: Session = Depends(get_db),
):
    """Follow a location. The next collection cycle picks it up automatically."""
    name = " ".join(district.strip().split())

    existing = db.scalar(select(TrackedLocation).where(TrackedLocation.district == name))
    if existing:
        existing.last_viewed = utcnow().replace(tzinfo=None)
        db.commit()
        return {"district": existing.district, "already_tracked": True}

    if any(d["district"].lower() == name.lower() for d in registry(db)):
        return {"district": name, "already_tracked": True, "builtin": True}

    row = TrackedLocation(
        district=name, state=state, country=country,
        latitude=latitude, longitude=longitude,
    )
    db.add(row)
    db.commit()
    return {"district": row.district, "already_tracked": False,
            "note": "Live weather only — IMD warnings are unavailable for this location."}


@router.delete("/track/{district}")
def untrack_place(district: str, db: Session = Depends(get_db)):
    row = db.scalar(select(TrackedLocation).where(TrackedLocation.district == district))
    if not row:
        raise HTTPException(404, f"'{district}' is not a tracked location")
    db.delete(row)
    db.commit()
    return {"district": district, "removed": True}
