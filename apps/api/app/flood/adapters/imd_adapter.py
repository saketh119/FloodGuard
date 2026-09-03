"""IMD adapter — turns six different IMD response shapes into one observation record.

Nothing downstream of this file knows what an IMD payload looks like. Adding CWC or
RSS means adding a sibling adapter that emits the same dict, not touching the engines.
"""
import hashlib
from datetime import datetime, timezone
from typing import Any, Iterable

from app.flood.geo import normalize_district, resolve_district


def _f(value: Any) -> float | None:
    """IMD mixes numbers and numeric strings ('+1.2', '142.5', '')."""
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace("+", "").strip())
    except (TypeError, ValueError):
        return None


def _parse_date(value: Any) -> datetime:
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(value[:10], fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    return datetime.now(timezone.utc)


def _qpf_upper_mm(band: Any) -> float | None:
    """Basin QPF arrives as a band string like '100-200' or '0-10'. Take the upper bound."""
    if not band or not isinstance(band, str):
        return None
    parts = band.replace(">", "").split("-")
    try:
        return float(parts[-1].strip())
    except ValueError:
        return None


def _dedupe_hash(obs_type: str, key: str, day: str, payload: str) -> str:
    """Content hash so a 60s re-poll of an unchanged reading is not stored twice.

    The observation DATE is part of the key (not the clock time) — the same reading
    on a new day is genuinely a new observation, an identical re-poll is not.
    """
    return hashlib.sha256(f"{obs_type}|{key}|{day}|{payload}".encode()).hexdigest()


def _base(obs_type: str, observed_at: datetime, raw: dict) -> dict[str, Any]:
    return {
        "source": "IMD",
        "observation_type": obs_type,
        "observed_at": observed_at.replace(tzinfo=None),
        "raw_json": raw,
        "district_id": None, "district": None, "state": None,
        "station_code": None, "station_name": None, "basin": None, "sub_basin": None,
        "latitude": None, "longitude": None, "color_code": None,
        "rainfall_mm": None, "temperature_c": None, "humidity_pct": None,
        "wind_speed_kmph": None, "pressure_hpa": None, "message": None,
    }


# ── Per-endpoint adapters ────────────────────────────────────────────────────

def adapt_nowcast(rows: Iterable[dict]) -> list[dict]:
    """GET /api/v1/nowcast — district nowcast, next 3 hours. `Station` holds the district."""
    out = []
    for row in rows:
        district = normalize_district(row.get("Station"))
        geo = resolve_district(name=district)
        observed_at = _parse_date(row.get("Date"))
        rec = _base("nowcast", observed_at, row)
        rec.update({
            "district": district, "district_id": geo.get("district_id"),
            "state": geo.get("state"), "latitude": geo.get("latitude"),
            "longitude": geo.get("longitude"), "basin": geo.get("basin"),
            "color_code": int(row["color"]) if row.get("color") is not None else None,
            "message": row.get("message"),
        })
        rec["dedupe_hash"] = _dedupe_hash(
            "nowcast", district or "?", observed_at.date().isoformat(),
            f"{rec['color_code']}|{rec['message']}",
        )
        out.append(rec)
    return out


def adapt_district_warning(rows: Iterable[dict]) -> list[dict]:
    """GET /api/v1/districtwarning — 5-day colour-coded warnings. Day 1 drives triggers."""
    out = []
    for row in rows:
        district = normalize_district(row.get("District"))
        geo = resolve_district(name=district, district_id=str(row.get("Obj_id") or "") or None)
        observed_at = _parse_date(row.get("Date"))
        day1_color = row.get("Day1_Color")
        rec = _base("warning", observed_at, row)
        rec.update({
            "district": district, "district_id": geo.get("district_id"),
            "state": geo.get("state"), "latitude": geo.get("latitude"),
            "longitude": geo.get("longitude"), "basin": geo.get("basin"),
            "color_code": int(day1_color) if day1_color is not None else None,
            "message": f"5-day warning codes: D1={row.get('Day_1')} D2={row.get('Day_2')} "
                       f"D3={row.get('Day_3')} D4={row.get('Day_4')} D5={row.get('Day_5')}",
        })
        rec["dedupe_hash"] = _dedupe_hash(
            "warning", district or "?", observed_at.date().isoformat(),
            "|".join(str(row.get(f"Day{i}_Color")) for i in range(1, 6)),
        )
        out.append(rec)
    return out


def adapt_district_rainfall(rows: Iterable[dict]) -> list[dict]:
    """GET /api/v1/districtrainfall — daily/weekly actuals vs normals."""
    out = []
    for row in rows:
        district = normalize_district(row.get("District"))
        geo = resolve_district(name=district, district_id=str(row.get("OBJ_ID") or "") or None)
        observed_at = _parse_date(row.get("Date"))
        daily = _f(row.get("Daily Actual"))
        rec = _base("rainfall", observed_at, row)
        rec.update({
            "district": district, "district_id": geo.get("district_id"),
            "state": geo.get("state"), "latitude": geo.get("latitude"),
            "longitude": geo.get("longitude"), "basin": geo.get("basin"),
            "rainfall_mm": daily,
            "message": f"Daily actual {daily} mm vs normal {_f(row.get('Daily Normal'))} mm "
                       f"({row.get('Daily Departure Per')}% departure, category {row.get('Daily Category')})",
        })
        rec["dedupe_hash"] = _dedupe_hash(
            "rainfall", district or "?", observed_at.date().isoformat(),
            f"{daily}|{_f(row.get('Weekly Actual'))}",
        )
        out.append(rec)
    return out


def adapt_current_weather(rows: Iterable[dict]) -> list[dict]:
    """GET /api/v1/current_wx — station-level current observation."""
    out = []
    for row in rows:
        station_code = str(row.get("Station Id") or "")
        observed_at = _parse_date(row.get("Date of Observation"))
        rec = _base("current_wx", observed_at, row)
        rec.update({
            "station_code": station_code or None,
            "station_name": row.get("Station"),
            "rainfall_mm": _f(row.get("Last 24 hrs Rainfall")),
            "temperature_c": _f(row.get("Temperature")),
            "humidity_pct": _f(row.get("Humidity")),
            "wind_speed_kmph": _f(row.get("Wind Speed")),
            "pressure_hpa": _f(row.get("M.S.L.P")),
            "message": f"Weather code {row.get('Weather Code')} at {row.get('Station')}",
        })
        rec["dedupe_hash"] = _dedupe_hash(
            "current_wx", station_code or "?", observed_at.date().isoformat(),
            f"{rec['rainfall_mm']}|{rec['temperature_c']}|{rec['humidity_pct']}|{rec['pressure_hpa']}",
        )
        out.append(rec)
    return out


def adapt_aws(rows: Iterable[dict]) -> list[dict]:
    """GET /api/v1/aws_data — automatic weather station telemetry, carries lat/lng + district."""
    out = []
    for row in rows:
        district = normalize_district(row.get("DISTRICT"))
        geo = resolve_district(name=district)
        observed_at = _parse_date(row.get("DATE"))
        rec = _base("aws", observed_at, row)
        rec.update({
            "district": district, "district_id": geo.get("district_id"),
            "state": row.get("STATE") or geo.get("state"),
            "station_code": str(row.get("CALL_SIGN") or "") or None,
            "station_name": row.get("STATION"),
            "latitude": _f(row.get("Latitude")) or geo.get("latitude"),
            "longitude": _f(row.get("Longitude")) or geo.get("longitude"),
            "basin": geo.get("basin"),
            "temperature_c": _f(row.get("CURR_TEMP")),
            "humidity_pct": _f(row.get("RH")),
            "wind_speed_kmph": _f(row.get("WIND_SPEED")),
            "pressure_hpa": _f(row.get("MSLP")),
            "message": f"AWS {row.get('CALL_SIGN')} weather code {row.get('WEATHER_CODE')}",
        })
        rec["dedupe_hash"] = _dedupe_hash(
            "aws", str(row.get("CALL_SIGN") or "?"), observed_at.date().isoformat(),
            f"{rec['temperature_c']}|{rec['humidity_pct']}|{rec['pressure_hpa']}|{rec['wind_speed_kmph']}",
        )
        out.append(rec)
    return out


def adapt_basin_qpf(rows: Iterable[dict]) -> list[dict]:
    """GET /api/v1/basinqpf — sub-basin rainfall forecast bands. Upper bound of Day1 is stored."""
    out = []
    for row in rows:
        observed_at = _parse_date(row.get("Date"))
        day1 = _qpf_upper_mm(row.get("Day1"))
        rec = _base("qpf", observed_at, row)
        rec.update({
            "basin": row.get("Basin"), "sub_basin": row.get("SubBasin"),
            "rainfall_mm": day1,
            "message": f"{row.get('Basin')}/{row.get('SubBasin')} QPF Day1 {row.get('Day1')} mm, "
                       f"Day2 {row.get('Day2')} mm, area avg precip {row.get('AAP')} mm",
        })
        rec["dedupe_hash"] = _dedupe_hash(
            "qpf", f"{row.get('Basin')}/{row.get('SubBasin')}", observed_at.date().isoformat(),
            f"{row.get('Day1')}|{row.get('Day2')}|{row.get('AAP')}",
        )
        out.append(rec)
    return out


def adapt_city_forecast(rows: Iterable[dict]) -> list[dict]:
    """GET /api/v1/cityforecastloc — 7-day station forecast.

    Stored but never triggered on: a forecast is not an observation of what happened,
    and basin QPF already covers the forward-looking trigger path. The dashboard reads
    the raw payload back for its 7-day strip.
    """
    out = []
    for row in rows:
        station_code = str(row.get("Station_Code") or "")
        observed_at = _parse_date(row.get("Date"))
        rec = _base("forecast", observed_at, row)
        rec.update({
            "station_code": station_code or None,
            "station_name": row.get("Station_Name"),
            "latitude": _f(row.get("Latitude")),
            "longitude": _f(row.get("Longitude")),
            "rainfall_mm": _f(row.get("Past_24_hrs_Rainfall")),
            "temperature_c": _f(row.get("Today_Max_temp")),
            "humidity_pct": _f(row.get("Relative_Humidity_at_0830")),
            "message": f"Today: {row.get('Todays_Forecast')}",
        })
        rec["dedupe_hash"] = _dedupe_hash(
            "forecast", station_code or "?", observed_at.date().isoformat(),
            "|".join(str(row.get(f"Day_{i}_Forecast")) for i in range(2, 8)) + f"|{row.get('Todays_Forecast')}",
        )
        out.append(rec)
    return out


ADAPTERS = {
    "nowcast": adapt_nowcast,
    "warning": adapt_district_warning,
    "rainfall": adapt_district_rainfall,
    "current_wx": adapt_current_weather,
    "aws": adapt_aws,
    "qpf": adapt_basin_qpf,
    "forecast": adapt_city_forecast,
}
