"""
sources/weather/adapter.py — OpenWeatherMap (or mock) Adapter.

Fetches current weather for each registered location and normalizes
it into a WeatherObservation ORM object.
"""
import json
from datetime import datetime, timezone

import httpx

from app.core.config import settings
from app.core.logger import get_logger
from app.models.weather import WeatherObservation

log = get_logger(__name__)

# Locations to poll (lat/lng + district metadata)
WEATHER_LOCATIONS = [
    {"lat": 17.385,  "lng": 78.4867, "district": "Hyderabad",           "state": "Telangana"},
    {"lat": 26.1445, "lng": 91.7362, "district": "Kamrup Metropolitan", "state": "Assam"},
    {"lat": 9.9816,  "lng": 76.2999, "district": "Ernakulam",           "state": "Kerala"},
    {"lat": 16.5062, "lng": 80.648,  "district": "NTR",                 "state": "Andhra Pradesh"},
    {"lat": 25.5941, "lng": 85.1376, "district": "Patna",               "state": "Bihar"},
]


class WeatherAdapter:

    def __init__(self):
        self._api_key = settings.openweather_api_key
        # Use mock server if running; swap base_url in .env for production
        self._base = "http://localhost:8082"  # mock server
        # self._base = settings.openweather_base_url  # real OWM

    async def ingest_all(self) -> list[WeatherObservation]:
        """Fetch and normalize weather for all registered locations."""
        results = []
        async with httpx.AsyncClient(timeout=10) as client:
            for loc in WEATHER_LOCATIONS:
                obs = await self._ingest_one(client, loc)
                if obs:
                    results.append(obs)
        return results

    async def _ingest_one(
        self, client: httpx.AsyncClient, loc: dict
    ) -> WeatherObservation | None:
        try:
            r = await client.get(
                f"{self._base}/data/2.5/weather",
                params={"lat": loc["lat"], "lon": loc["lng"], "appid": self._api_key},
            )
            r.raise_for_status()
            data = r.json()
        except Exception as exc:
            log.warning(f"Weather fetch failed for {loc['district']}: {exc}")
            return None

        return self._normalize(loc, data)

    def _normalize(self, loc: dict, d: dict) -> WeatherObservation:
        main    = d.get("main", {})
        wind    = d.get("wind", {})
        rain    = d.get("rain", {})
        weather = (d.get("weather") or [{}])[0]
        clouds  = d.get("clouds", {})

        # Convert wind m/s → km/h
        wind_speed_kmh = round(float(wind.get("speed", 0)) * 3.6, 1)
        rain_1h = float(rain.get("1h", 0))

        triggered = rain_1h > 15.0 or wind_speed_kmh > 50.0
        reasons = []
        if rain_1h > 15.0:
            reasons.append(f"rainfall_1h={rain_1h:.1f}mm")
        if wind_speed_kmh > 50.0:
            reasons.append(f"wind={wind_speed_kmh:.1f}km/h")

        return WeatherObservation(
            lat=loc["lat"],
            lng=loc["lng"],
            district=loc.get("district") or d.get("name"),
            state=loc.get("state"),
            city_name=d.get("name"),
            obs_time=datetime.now(timezone.utc),
            temp=main.get("temp"),
            feels_like=main.get("feels_like"),
            temp_min=main.get("temp_min"),
            temp_max=main.get("temp_max"),
            humidity=main.get("humidity"),
            wind_speed=wind_speed_kmh,
            wind_deg=wind.get("deg"),
            pressure=main.get("pressure"),
            visibility=d.get("visibility"),
            clouds=clouds.get("all"),
            rainfall_1h=rain_1h,
            rainfall_3h=float(rain.get("3h", 0)),
            weather_id=weather.get("id"),
            weather_main=weather.get("main"),
            weather_desc=weather.get("description"),
            source="mock-owm" if "8082" in self._base else "openweathermap",
            triggered=triggered,
            trigger_reason="; ".join(reasons) if reasons else None,
            raw_json=json.dumps(d),
        )
