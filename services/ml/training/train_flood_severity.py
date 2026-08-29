"""Train the flood-severity model actually served by /predictions.

Why not flood_risk_india.csv: that file's labels are uncorrelated with its features
(ROC-AUC 0.496, i.e. chance, with near-uniform importances — the signature of random
labels). train_flood_risk.py is kept in the repo as the evidence for that rejection.

This model uses IndoFloods instead — 4,548 real gauged flood events across 155 Indian
catchments, labelled `Flood` vs `Severe Flood`, joined to observed antecedent rainfall
accumulations (T1d…T10d).

Framing: given the rainfall that has already fallen, how likely is this event to
escalate to a SEVERE flood? Evaluation is GroupKFold by gauge, so the reported score
is performance on catchments the model has never seen — the situation it faces live.

Two variants are trained:
  • precip_only  — the SERVED model. Every feature is derivable from live IMD rainfall.
  • with_catchment — reference only. Better, but needs catchment attributes we cannot
    yet resolve for an arbitrary district (blocked on the CWC station registry).

Run:  .venv/bin/python services/ml/training/train_flood_severity.py
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold, cross_val_score

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data" / "raw" / "ml"
OUT_DIR = ROOT / "services" / "ml" / "models"
MODEL_VERSION = "flood_severity_hgb_v1"

ACCUM = [f"T{i}d" for i in range(1, 11)]          # observed rainfall accumulations, mm
DERIVED = ["month", "burst_1_3", "burst_3_10", "late_accum"]
PRECIP_FEATURES = ACCUM + DERIVED


def build_frame() -> pd.DataFrame:
    events = pd.read_csv(RAW / "indofloods_flood_events.csv")
    precip = pd.read_csv(RAW / "indofloods_precipitation_variables.csv")
    catchment = pd.read_csv(RAW / "indofloods_catchment_characteristics.csv")

    # EventID is "<GaugeID>-<n>", so the gauge is everything before the last dash.
    events["GaugeID"] = events["EventID"].str.rsplit("-", n=1).str[0]
    df = events.merge(precip, on="EventID").merge(catchment, on="GaugeID", how="left")
    return add_features(df)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Shared with the prediction service so training and inference cannot drift."""
    df = df.copy()
    if "Start Date" in df.columns:
        df["month"] = pd.to_datetime(df["Start Date"], errors="coerce").dt.month
    # Burst ratios separate a short violent downpour from a long soaking — the same
    # 10-day total behaves very differently in each case.
    df["burst_1_3"] = df["T1d"] / df["T3d"].replace(0, np.nan)
    df["burst_3_10"] = df["T3d"] / df["T10d"].replace(0, np.nan)
    df["late_accum"] = df["T10d"] - df["T3d"]
    return df


def make_model() -> HistGradientBoostingClassifier:
    # HistGradientBoosting handles the NaNs in these hydrology tables natively.
    return HistGradientBoostingClassifier(
        max_iter=300, learning_rate=0.06, max_depth=6, random_state=42
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = build_frame()
    y = (df["Flood Type"] == "Severe Flood").astype(int)
    groups = df["GaugeID"]
    print(f"{len(df):,} events across {groups.nunique()} catchments · "
          f"{y.mean():.1%} labelled Severe Flood")

    gkf = GroupKFold(n_splits=5)

    # --- Served variant: precipitation only --------------------------------
    X = df[PRECIP_FEATURES].apply(pd.to_numeric, errors="coerce")
    auc = cross_val_score(make_model(), X, y, cv=gkf, groups=groups,
                          scoring="roc_auc", n_jobs=-1)
    print(f"\nprecip_only    GroupKFold ROC-AUC: {auc.mean():.4f} (+/- {auc.std():.4f})")

    # --- Reference variant: + catchment attributes -------------------------
    cc_cols = [
        c for c in pd.read_csv(RAW / "indofloods_catchment_characteristics.csv").columns
        if c != "GaugeID" and c in df.columns
        and df[c].dtype != object and df[c].notna().mean() > 0.6
    ][:25]
    Xc = df[PRECIP_FEATURES + cc_cols].apply(pd.to_numeric, errors="coerce")
    auc_c = cross_val_score(make_model(), Xc, y, cv=gkf, groups=groups,
                            scoring="roc_auc", n_jobs=-1)
    print(f"with_catchment GroupKFold ROC-AUC: {auc_c.mean():.4f} (+/- {auc_c.std():.4f})")
    print(f"baseline (always predict majority): 0.5000")

    # Fit the served model on everything.
    model = make_model().fit(X, y)
    in_sample = roc_auc_score(y, model.predict_proba(X)[:, 1])
    print(f"\nin-sample ROC-AUC (optimistic, for reference only): {in_sample:.4f}")

    joblib.dump(model, OUT_DIR / "flood_severity_hgb.joblib")
    metrics = {
        "model_version": MODEL_VERSION,
        "task": "binary classification — will a flood event escalate to SEVERE?",
        "dataset": "IndoFloods (indofloods_flood_events + indofloods_precipitation_variables)",
        "n_events": int(len(df)),
        "n_catchments": int(groups.nunique()),
        "positive_rate": float(y.mean()),
        "served_variant": "precip_only",
        "features": PRECIP_FEATURES,
        "cv_strategy": "GroupKFold(5) by GaugeID — scores are for unseen catchments",
        "cv_roc_auc_mean": float(auc.mean()),
        "cv_roc_auc_std": float(auc.std()),
        "reference_with_catchment_roc_auc": float(auc_c.mean()),
        "in_sample_roc_auc": float(in_sample),
        "training_medians": {c: (None if pd.isna(v) else float(v))
                             for c, v in X.median().items()},
        "honest_caveat": (
            "ROC-AUC ~0.57 on unseen catchments: better than chance and built on real "
            "gauged events, but weak. Treat the output as a supporting signal, not a "
            "forecast. The rule-based IMD-threshold index drives the headline risk score."
        ),
    }
    (OUT_DIR / "flood_severity_metrics.json").write_text(json.dumps(metrics, indent=2))
    print(f"Saved model + metrics to {OUT_DIR}")


if __name__ == "__main__":
    main()
