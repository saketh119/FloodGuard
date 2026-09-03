"""OpenWeather adapter — real observed conditions, per district.

This is the first genuinely live source in the platform. IMD is still mocked, so
everything derived from it reflects a scripted scenario; OpenWeather reports what is
actually happening at the coordinates right now.

Two shapes are handled:
  current  /data/2.5/weather   — observed conditions, including rain in the last 1h/3h
  forecast /data/2.5/forecast  — 40 three-hourly slots over five days

The forecast is condensed into a next-24h rainfall accumulation, because that is the
quantity IMD's rainfall thresholds are defined against and therefore the one the
trigger engine can reason about.
"""
import hashlib
from datetime import datetime, timezone
from typing import Any, Iterable

MS_TO_KMPH = 3.6


def _dedupe_hash(kind: str, district: str, stamp: str, payload: str) -> str:
    return hashlib.sha256(f"ow-{kind}|{district}|{stamp}|{payload}".encode()).hexdigest()


def _utc(ts: int | None) -> datetime:
    if not ts:
        return datetime.now(timezone.utc)
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def adapt_current(payload: dict, district: dict[str, Any]) -> dict[str, Any]:
    """One observed reading for a district."""
    main = payload.get("main") or {}
    wind = payload.get("wind") or {}
    weather = (payload.get("weather") or [{}])[0]
    rain = payload.get("rain") or {}

    # OpenWeather reports rain over the last 1h and/or 3h; take the longer window
    # when present so short dry gaps do not read as "no rain".
    rain_mm = rain.get("3h", rain.get("1h", 0.0)) or 0.0
    observed_at = _utc(payload.get("dt"))

    return {
        "source": "OpenWeather",
        "observation_type": "ow_current",
        "observed_at": observed_at.replace(tzinfo=None),
        "district": district["district"],
        "district_id": district.get("district_id"),
        "state": district.get("state"),
        "station_code": f"OW-{district.get('district_id')}",
        "station_name": payload.get("name") or district["district"],
        "basin": district.get("basin"),
        "sub_basin": None,
        "latitude": (payload.get("coord") or {}).get("lat", district.get("latitude")),
        "longitude": (payload.get("coord") or {}).get("lon", district.get("longitude")),
        "color_code": None,
        "rainfall_mm": float(rain_mm),
        "temperature_c": main.get("temp"),
        "humidity_pct": main.get("humidity"),
        "wind_speed_kmph": round((wind.get("speed") or 0) * MS_TO_KMPH, 1),
        "pressure_hpa": main.get("pressure"),
        "message": (
            f"{weather.get('description', 'unknown conditions').capitalize()} at "
            f"{district['district']} — {main.get('temp')}°C, {main.get('humidity')}% humidity, "
            f"{rain_mm} mm rain observed"
        ),
        "raw_json": payload,
        "dedupe_hash": _dedupe_hash(
            "current", district["district"], observed_at.isoformat(timespec="minutes"),
            f"{main.get('temp')}|{main.get('humidity')}|{rain_mm}|{weather.get('id')}",
        ),
    }


def summarise_forecast(payload: dict, district: dict[str, Any]) -> dict[str, Any]:
    """Condense 3-hourly slots into the accumulations the trigger engine uses."""
    slots: Iterable[dict] = payload.get("list") or []

    next_24h = 0.0
    next_72h = 0.0
    peak_slot = None
    daily: dict[str, float] = {}

    for i, slot in enumerate(slots):
        mm = (slot.get("rain") or {}).get("3h", 0.0) or 0.0
        if i < 8:                       # 8 × 3h = 24h
            next_24h += mm
        if i < 24:                      # 72h
            next_72h += mm
        if peak_slot is None or mm > (peak_slot.get("rain") or {}).get("3h", 0):
            peak_slot = slot
        day = (slot.get("dt_txt") or "")[:10]
        if day:
            daily[day] = round(daily.get(day, 0.0) + mm, 2)

    first = slots[0] if slots else {}
    observed_at = _utc(first.get("dt"))

    return {
        "source": "OpenWeather",
        "observation_type": "ow_forecast",
        "observed_at": observed_at.replace(tzinfo=None),
        "district": district["district"],
        "district_id": district.get("district_id"),
        "state": district.get("state"),
        "station_code": f"OW-{district.get('district_id')}",
        "station_name": (payload.get("city") or {}).get("name") or district["district"],
        "basin": district.get("basin"),
        "sub_basin": None,
        "latitude": district.get("latitude"),
        "longitude": district.get("longitude"),
        "color_code": None,
        # rainfall_mm on a forecast row means "expected over the next 24h"
        "rainfall_mm": round(next_24h, 2),
        "temperature_c": ((first.get("main") or {}).get("temp")),
        "humidity_pct": ((first.get("main") or {}).get("humidity")),
        "wind_speed_kmph": round(((first.get("wind") or {}).get("speed") or 0) * MS_TO_KMPH, 1),
        "pressure_hpa": ((first.get("main") or {}).get("pressure")),
        "message": (
            f"OpenWeather forecasts {round(next_24h, 1)} mm of rain over the next 24h "
            f"and {round(next_72h, 1)} mm over 72h at {district['district']}"
        ),
        "raw_json": {
            "next_24h_mm": round(next_24h, 2),
            "next_72h_mm": round(next_72h, 2),
            "daily_mm": daily,
            "peak_3h_mm": (peak_slot or {}).get("rain", {}).get("3h", 0.0),
            "peak_at": (peak_slot or {}).get("dt_txt"),
            "city": payload.get("city"),
            # Keep a trimmed slot list — the full 40-slot payload is mostly noise.
            "slots": [
                {
                    "at": s.get("dt_txt"),
                    "temp": (s.get("main") or {}).get("temp"),
                    "rain_3h": (s.get("rain") or {}).get("3h", 0.0),
                    "humidity": (s.get("main") or {}).get("humidity"),
                    "description": ((s.get("weather") or [{}])[0]).get("description"),
                    "icon": ((s.get("weather") or [{}])[0]).get("icon"),
                }
                for s in list(slots)[:16]
            ],
        },
        "dedupe_hash": _dedupe_hash(
            "forecast", district["district"], observed_at.isoformat(timespec="hours"),
            f"{round(next_24h, 2)}|{round(next_72h, 2)}",
        ),
    }
