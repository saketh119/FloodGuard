"""Place lookup via OpenWeather's geocoding API.

This is what lifts the platform off its hardcoded district list. The built-in registry
exists because IMD reports on a fixed set of districts; OpenWeather works at any
coordinate, so anywhere a user can name can be followed for live conditions.
"""
from typing import Any

import httpx

from app.core.config import settings
from app.core.logger import get_logger

log = get_logger("floodguard.geocoding")

GEO_URL = "https://api.openweathermap.org/geo/1.0/direct"
REVERSE_URL = "https://api.openweathermap.org/geo/1.0/reverse"


class GeocodingUnavailable(RuntimeError):
    pass


async def search(query: str, limit: int = 5, country: str | None = "IN") -> list[dict[str, Any]]:
    """Find candidate places for a free-text query."""
    if not settings.openweather_enabled:
        raise GeocodingUnavailable("OPENWEATHER_API_KEY is not set — place search is unavailable")

    q = query.strip()
    if not q:
        return []

    async with httpx.AsyncClient(timeout=settings.OPENWEATHER_TIMEOUT_S) as client:
        try:
            res = await client.get(GEO_URL, params={
                # Scoping to a country keeps "Hyderabad" from returning Pakistan first.
                "q": f"{q},{country}" if country else q,
                "limit": limit,
                "appid": settings.OPENWEATHER_API_KEY,
            })
        except httpx.RequestError as exc:
            raise GeocodingUnavailable(f"Could not reach the geocoding service: {exc}") from exc

    if res.status_code == 401:
        raise GeocodingUnavailable("OpenWeather rejected the API key")
    if res.status_code != 200:
        raise GeocodingUnavailable(f"Geocoding returned HTTP {res.status_code}")

    out: list[dict[str, Any]] = []
    seen: set[tuple] = set()
    for row in res.json():
        # The API returns duplicates for large cities; one entry per name+state is enough.
        key = (row.get("name"), row.get("state"))
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "name": row.get("name"),
            "state": row.get("state"),
            "country": row.get("country"),
            "latitude": row.get("lat"),
            "longitude": row.get("lon"),
            "label": ", ".join(x for x in (row.get("name"), row.get("state")) if x),
        })
    return out


async def reverse(latitude: float, longitude: float, limit: int = 1) -> list[dict[str, Any]]:
    """Name the place at a coordinate.

    This is what makes "use my location" mean the user's actual position. Snapping a
    GPS fix to the nearest already-followed location instead would report Kerala to
    someone standing in Telangana — technically the closest known point, and wrong.
    """
    if not settings.openweather_enabled:
        raise GeocodingUnavailable("OPENWEATHER_API_KEY is not set — place lookup is unavailable")

    async with httpx.AsyncClient(timeout=settings.OPENWEATHER_TIMEOUT_S) as client:
        try:
            res = await client.get(REVERSE_URL, params={
                "lat": latitude, "lon": longitude, "limit": limit,
                "appid": settings.OPENWEATHER_API_KEY,
            })
        except httpx.RequestError as exc:
            raise GeocodingUnavailable(f"Could not reach the geocoding service: {exc}") from exc

    if res.status_code == 401:
        raise GeocodingUnavailable("OpenWeather rejected the API key")
    if res.status_code != 200:
        raise GeocodingUnavailable(f"Reverse geocoding returned HTTP {res.status_code}")

    return [
        {
            "name": row.get("name"),
            "state": row.get("state"),
            "country": row.get("country"),
            # Return the queried coordinates, not the place centroid: weather should be
            # fetched for where the user actually is.
            "latitude": latitude,
            "longitude": longitude,
            "label": ", ".join(x for x in (row.get("name"), row.get("state")) if x),
        }
        for row in res.json()
    ]
