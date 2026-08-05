"""
scripts/mock_weather_server.py — Mock OpenWeatherMap-compatible server.

Implements:
  GET /data/2.5/weather?lat=&lon=    → current weather
  GET /data/2.5/forecast?lat=&lon=   → 5-day/3-hour forecast (8 entries)

Run with:
    python backend/scripts/mock_weather_server.py
    # → http://localhost:8082

Assam / Kerala coordinates return heavy rain / storm conditions to
exercise the weather trigger rules.
"""
import uvicorn
from datetime import datetime, timedelta
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import math

app = FastAPI(title="Weather Mock API (OWM-compatible)", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _is_flood_zone(lat: float, lon: float) -> bool:
    """Rough bounding boxes for Assam (flood zone) and Kerala (rain zone)."""
    assam = (24.0 <= lat <= 28.5) and (88.0 <= lon <= 96.5)
    kerala = (8.0 <= lat <= 13.0) and (74.5 <= lon <= 78.0)
    return assam or kerala


def _current(lat: float, lon: float) -> dict:
    flood = _is_flood_zone(lat, lon)
    now = int(datetime.utcnow().timestamp())
    return {
        "coord": {"lat": lat, "lon": lon},
        "weather": [
            {
                "id": 502 if flood else 800,
                "main": "Rain" if flood else "Clear",
                "description": "heavy intensity rain" if flood else "clear sky",
                "icon": "10d" if flood else "01d",
            }
        ],
        "main": {
            "temp": 24.2 if flood else 32.8,
            "feels_like": 26.5 if flood else 37.2,
            "temp_min": 22.0 if flood else 29.5,
            "temp_max": 28.0 if flood else 35.2,
            "pressure": 996 if flood else 1010,
            "humidity": 96 if flood else 55,
        },
        "visibility": 2000 if flood else 10000,
        "wind": {
            "speed": 9.5 if flood else 2.1,   # m/s → ≈34 km/h flood, ≈8 km/h normal
            "deg": 230 if flood else 90,
        },
        "clouds": {"all": 95 if flood else 10},
        "rain": {"1h": 22.5 if flood else 0.0},
        "dt": now,
        "sys": {"country": "IN"},
        "name": "Guwahati" if flood else "Hyderabad",
        "cod": 200,
    }


def _forecast(lat: float, lon: float) -> dict:
    flood = _is_flood_zone(lat, lon)
    now = datetime.utcnow()
    items = []
    for i in range(8):  # 8 × 3h = 24h
        t = now + timedelta(hours=i * 3)
        rain_mm = (20 + i * 2) if flood else 0.0
        items.append({
            "dt": int(t.timestamp()),
            "dt_txt": t.strftime("%Y-%m-%d %H:%M:%S"),
            "main": {
                "temp": 24.0 if flood else 32.0,
                "humidity": 95 if flood else 55,
                "pressure": 996 if flood else 1010,
            },
            "weather": [{"id": 502 if flood else 800, "main": "Rain" if flood else "Clear",
                          "description": "heavy rain" if flood else "clear sky", "icon": "10d"}],
            "wind": {"speed": 9.0 if flood else 2.0, "deg": 230},
            "rain": {"3h": rain_mm},
            "clouds": {"all": 90 if flood else 10},
        })
    return {
        "cod": "200",
        "cnt": len(items),
        "list": items,
        "city": {"name": "Guwahati" if flood else "Hyderabad", "country": "IN",
                 "coord": {"lat": lat, "lon": lon}},
    }


@app.get("/")
def root():
    return {"service": "Weather Mock API", "compatible_with": "OpenWeatherMap 2.5"}


@app.get("/data/2.5/weather")
def current_weather(lat: float = Query(...), lon: float = Query(...)):
    return _current(lat, lon)


@app.get("/data/2.5/forecast")
def forecast(lat: float = Query(...), lon: float = Query(...)):
    return _forecast(lat, lon)


if __name__ == "__main__":
    print("Starting Weather Mock Server on http://localhost:8082 …")
    uvicorn.run("mock_weather_server:app", host="0.0.0.0", port=8082, reload=True)
