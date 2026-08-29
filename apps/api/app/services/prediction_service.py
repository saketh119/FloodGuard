"""Prediction service — scores open flood events with the IndoFloods severity model.

The model wants observed rainfall accumulations over 1–10 days. IMD gives us daily,
weekly and cumulative district totals, so we anchor on those three and interpolate
between them. That interpolation is an approximation and every response says so:
`feature_provenance` marks each feature as observed, interpolated or imputed.
"""
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logger import get_logger
from app.flood.engine.correlation import compute_risk_score
from app.models import FloodEvent, ImdObservation, PredictionResult, utcnow

log = get_logger("floodguard.prediction")

ACCUM = [f"T{i}d" for i in range(1, 11)]
DERIVED = ["month", "burst_1_3", "burst_3_10", "late_accum"]
FEATURES = ACCUM + DERIVED


class ModelUnavailable(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _model():
    if not Path(settings.MODEL_PATH).exists():
        raise ModelUnavailable(
            f"No model at {settings.MODEL_PATH}. Run: "
            ".venv/bin/python services/ml/training/train_flood_severity.py"
        )
    return joblib.load(settings.MODEL_PATH)


@lru_cache(maxsize=1)
def metrics() -> dict[str, Any]:
    path = Path(settings.MODEL_METRICS_PATH)
    return json.loads(path.read_text()) if path.exists() else {}


def model_status() -> dict[str, Any]:
    m = metrics()
    try:
        _model()
        loaded = True
    except ModelUnavailable:
        loaded = False
    return {
        "loaded": loaded,
        "model_version": m.get("model_version"),
        "dataset": m.get("dataset"),
        "cv_roc_auc": m.get("cv_roc_auc_mean"),
        "cv_strategy": m.get("cv_strategy"),
        "caveat": m.get("honest_caveat"),
    }


def _rainfall_profile(db: Session, district: str) -> tuple[dict[str, float], dict[str, str]]:
    """Build T1d…T10d for a district from its most recent IMD rainfall observation."""
    obs = db.scalars(
        select(ImdObservation)
        .where(ImdObservation.district == district, ImdObservation.observation_type == "rainfall")
        .order_by(ImdObservation.observed_at.desc(), ImdObservation.id.desc())
    ).first()

    defaults = metrics().get("training_medians", {})
    provenance: dict[str, str] = {}

    if obs is None or obs.rainfall_mm is None:
        # No live rainfall for this district — fall back to training medians and say so.
        profile = {c: float(defaults.get(c) or 0.0) for c in ACCUM}
        provenance = {c: "imputed (training median — no live IMD rainfall)" for c in ACCUM}
        return profile, provenance

    raw = obs.raw_json or {}

    def _num(key: str) -> float | None:
        try:
            return float(raw.get(key))
        except (TypeError, ValueError):
            return None

    daily = obs.rainfall_mm or 0.0
    weekly = _num("Weekly Actual")
    cumulative = _num("Cumulative Actual")

    # Anchors: day 1 observed, day 7 from the weekly total, day 10 from the cumulative.
    if weekly is None or weekly < daily:
        weekly = daily * 3.0
        provenance["T7d"] = "estimated (no weekly total reported)"
    else:
        provenance["T7d"] = "observed (IMD weekly actual)"

    if cumulative is None or cumulative < weekly:
        cumulative = weekly * 1.25
        provenance["T10d"] = "estimated (no cumulative total reported)"
    else:
        provenance["T10d"] = "observed (IMD cumulative actual)"

    provenance["T1d"] = "observed (IMD daily actual)"

    # Accumulations must be monotonically non-decreasing; interpolate between anchors.
    profile = {"T1d": daily, "T7d": weekly, "T10d": cumulative}
    for day in (2, 3, 4, 5, 6):
        frac = (day - 1) / 6
        profile[f"T{day}d"] = daily + (weekly - daily) * frac
        provenance[f"T{day}d"] = "interpolated (between daily and weekly totals)"
    for day in (8, 9):
        frac = (day - 7) / 3
        profile[f"T{day}d"] = weekly + (cumulative - weekly) * frac
        provenance[f"T{day}d"] = "interpolated (between weekly and cumulative totals)"

    return {c: round(float(profile[c]), 3) for c in ACCUM}, provenance


def _derive(profile: dict[str, float], month: int) -> dict[str, float]:
    """Same derivation as ml/training/train_flood_severity.py — kept in lockstep."""
    frame = pd.DataFrame([{**profile, "Start Date": None}])
    frame["month"] = month
    frame["burst_1_3"] = frame["T1d"] / frame["T3d"].replace(0, np.nan)
    frame["burst_3_10"] = frame["T3d"] / frame["T10d"].replace(0, np.nan)
    frame["late_accum"] = frame["T10d"] - frame["T3d"]
    return {c: (None if pd.isna(frame.iloc[0][c]) else float(frame.iloc[0][c])) for c in DERIVED}


def _risk_band(p: float) -> str:
    if p >= 0.70:
        return "severe"
    if p >= 0.50:
        return "high"
    if p >= 0.30:
        return "moderate"
    return "low"


def predict_event(db: Session, event: FloodEvent) -> dict[str, Any]:
    """Score one event and persist the result so trends can be charted."""
    model = _model()

    profile, provenance = _rainfall_profile(db, event.district)
    derived = _derive(profile, event.last_seen.month)
    features = {**profile, **derived}

    X = pd.DataFrame([[features[c] for c in FEATURES]], columns=FEATURES)
    probability = float(model.predict_proba(X)[0, 1])

    # The ML output refines the rule-based score; it never replaces it.
    event.prediction_probability = round(probability, 4)
    event.risk_score = compute_risk_score(event.confidence_score, event.severity, probability)
    event.updated_at = utcnow()

    imputed = {k: v for k, v in provenance.items() if not v.startswith("observed")}
    record = PredictionResult(
        event_id=event.id, district=event.district,
        model_version=metrics().get("model_version", "unknown"),
        probability=round(probability, 4), risk_band=_risk_band(probability),
        features=features, imputed_features=imputed,
    )
    db.add(record)

    return {
        "event_id": event.id, "event_uid": event.event_uid, "district": event.district,
        "severe_escalation_probability": round(probability, 4),
        "risk_band": _risk_band(probability),
        "risk_score": event.risk_score,
        "confidence_score": event.confidence_score,
        "model_version": metrics().get("model_version"),
        "model_cv_roc_auc": metrics().get("cv_roc_auc_mean"),
        "features": features,
        "feature_provenance": provenance,
        "caveat": metrics().get("honest_caveat"),
    }


def predict_open_events(db: Session) -> list[dict[str, Any]]:
    events = db.scalars(
        select(FloodEvent).where(FloodEvent.status != "resolved")
        .order_by(FloodEvent.last_seen.desc())
    ).all()

    results = []
    for event in events:
        try:
            results.append(predict_event(db, event))
        except ModelUnavailable:
            raise
        except Exception as exc:
            log.warning("scoring failed for event %s: %s", event.event_uid, exc)
    db.commit()
    return results
