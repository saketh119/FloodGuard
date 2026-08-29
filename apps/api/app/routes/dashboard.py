"""Aggregate read model for the web dashboard.

One call returns everything a district view needs: the latest observation of each
type, the correlated events, and the most recent ML scoring. The web app makes a
single request per location instead of fanning out across six IMD endpoints, and it
never talks to IMD directly — the gateway owns that relationship.
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.flood.geo import district_for_station, is_builtin, resolve_any
from app.models import FloodEvent, ImdObservation, PredictionResult

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Observation types keyed by district name.
DISTRICT_TYPES = ("nowcast", "warning", "rainfall", "ow_current", "ow_forecast")
# Observation types keyed by station — resolved to a district via the station registry.
STATION_TYPES = ("current_wx", "aws", "forecast")

COLOR_NAMES = {1: "Green", 2: "Yellow", 3: "Orange", 4: "Red"}
ALERT_LABELS = {1: "Low", 2: "Moderate", 3: "High", 4: "Severe"}


def _latest_by_district(db: Session, district: str, obs_type: str) -> ImdObservation | None:
    return db.scalars(
        select(ImdObservation)
        .where(ImdObservation.district == district, ImdObservation.observation_type == obs_type)
        .order_by(ImdObservation.observed_at.desc(), ImdObservation.id.desc())
    ).first()


def _latest_by_station(db: Session, district: str, obs_type: str) -> ImdObservation | None:
    """Station observations carry no district, so filter in Python via the registry."""
    candidates = db.scalars(
        select(ImdObservation)
        .where(ImdObservation.observation_type == obs_type)
        .order_by(ImdObservation.observed_at.desc(), ImdObservation.id.desc())
        .limit(60)
    ).all()
    for obs in candidates:
        if obs.district == district:
            return obs
        hit = district_for_station(obs.station_code)
        if hit and hit["district"] == district:
            return obs
    return None


def _latest_qpf(db: Session, basin: str | None) -> list[dict[str, Any]]:
    if not basin:
        return []
    rows = db.scalars(
        select(ImdObservation)
        .where(ImdObservation.observation_type == "qpf", ImdObservation.basin == basin)
        .order_by(ImdObservation.observed_at.desc(), ImdObservation.id.desc())
        .limit(12)
    ).all()
    seen, out = set(), []
    for obs in rows:                       # one row per sub-basin, newest first
        if obs.sub_basin in seen:
            continue
        seen.add(obs.sub_basin)
        out.append({"sub_basin": obs.sub_basin, "day1_upper_mm": obs.rainfall_mm, **(obs.raw_json or {})})
    return out


def _serialise(obs: ImdObservation | None) -> dict[str, Any] | None:
    if obs is None:
        return None
    return {
        "id": obs.id,
        "observation_type": obs.observation_type,
        "observed_at": obs.observed_at,
        "district": obs.district,
        "station_name": obs.station_name,
        "color_code": obs.color_code,
        "color_name": COLOR_NAMES.get(obs.color_code or 0),
        "rainfall_mm": obs.rainfall_mm,
        "temperature_c": obs.temperature_c,
        "humidity_pct": obs.humidity_pct,
        "wind_speed_kmph": obs.wind_speed_kmph,
        "pressure_hpa": obs.pressure_hpa,
        "message": obs.message,
        "raw": obs.raw_json,
    }


@router.get("/{district}")
def district_dashboard(district: str, db: Session = Depends(get_db)):
    """Everything the web app needs for one district, in one round trip."""
    geo = resolve_any(db, district)
    if geo is None:
        raise HTTPException(
            404,
            f"'{district}' is not being followed. Search for it with "
            f"GET /districts/search?q={district} and add it with POST /districts/track.",
        )

    name = geo["district"]
    # IMD only reports on the built-in districts; a tracked place gets live weather
    # only, and the response says so rather than silently showing empty panels.
    imd_covered = is_builtin(name)
    observations = {t: _serialise(_latest_by_district(db, name, t)) for t in DISTRICT_TYPES}
    observations.update({t: _serialise(_latest_by_station(db, name, t)) for t in STATION_TYPES})
    if not imd_covered:
        # Do not present a tracked location's empty IMD slots as if data were pending.
        for t in ("nowcast", "warning", "rainfall", "current_wx", "aws", "forecast"):
            observations[t] = None

    events = db.scalars(
        select(FloodEvent)
        .where(FloodEvent.district == name)
        .order_by(FloodEvent.risk_score.desc(), FloodEvent.last_seen.desc())
    ).all()

    predictions = db.scalars(
        select(PredictionResult)
        .where(PredictionResult.district == name)
        .order_by(PredictionResult.created_at.desc())
        .limit(10)
    ).all()

    # Headline alert level: the strongest colour currently in force for this district.
    colors = [o["color_code"] for o in observations.values() if o and o.get("color_code")]
    alert_code = max(colors) if colors else 1

    active = [e for e in events if e.status != "resolved"]
    rainfall = observations.get("rainfall")

    # Live conditions come from OpenWeather when we have them — that is a real reading
    # at real coordinates, where every IMD figure is currently scripted by the mock.
    live = observations.get("ow_current")
    forecast_ow = observations.get("ow_forecast")

    return {
        "location": {
            "district": name, "state": geo["state"], "basin": geo.get("basin"),
            "latitude": geo.get("latitude"), "longitude": geo.get("longitude"),
            "coords": (
                f"{abs(geo['latitude']):.4f}° {'N' if geo['latitude'] >= 0 else 'S'}, "
                f"{abs(geo['longitude']):.4f}° {'E' if geo['longitude'] >= 0 else 'W'}"
                if geo.get("latitude") is not None else None
            ),
            "imd_covered": imd_covered,
            "tracked": geo.get("tracked", False),
        },
        "summary": {
            "alert_code": alert_code,
            "alert_color": COLOR_NAMES.get(alert_code, "Green"),
            "alert_label": ALERT_LABELS.get(alert_code, "Low"),
            "active_events": len(active),
            "rain_24h_mm": rainfall["rainfall_mm"] if rainfall else None,
            # Live block — present only when OpenWeather has reported.
            "live": {
                "temperature_c": live["temperature_c"],
                "humidity_pct": live["humidity_pct"],
                "wind_speed_kmph": live["wind_speed_kmph"],
                "pressure_hpa": live["pressure_hpa"],
                "rain_observed_mm": live["rainfall_mm"],
                "conditions": ((live["raw"].get("weather") or [{}])[0]).get("description"),
                "icon": ((live["raw"].get("weather") or [{}])[0]).get("icon"),
                "feels_like_c": (live["raw"].get("main") or {}).get("feels_like"),
                "observed_at": live["observed_at"],
                "station": live["station_name"],
            } if live else None,
            "forecast_24h_mm": forecast_ow["rainfall_mm"] if forecast_ow else None,
            "forecast_72h_mm": (forecast_ow["raw"] or {}).get("next_72h_mm") if forecast_ow else None,
            "max_risk_score": max((e.risk_score for e in active), default=0.0),
            "severe_probability": max(
                (e.prediction_probability for e in active if e.prediction_probability is not None),
                default=None,
            ),
        },
        "observations": observations,
        "qpf": _latest_qpf(db, geo.get("basin")),
        "events": [
            {
                "id": e.id, "event_uid": e.event_uid, "district": e.district, "state": e.state,
                "category": e.category, "status": e.status, "severity": e.severity,
                "confidence_score": e.confidence_score, "risk_score": e.risk_score,
                "prediction_probability": e.prediction_probability,
                "ai_summary": e.ai_summary, "first_seen": e.first_seen, "last_seen": e.last_seen,
            }
            for e in events
        ],
        "predictions": [
            {
                "id": p.id, "probability": p.probability, "risk_band": p.risk_band,
                "created_at": p.created_at, "model_version": p.model_version,
                "imputed_features": p.imputed_features,
            }
            for p in predictions
        ],
    }
