"""Train the flood-risk classifier used by the /predictions endpoint.

Data: data/raw/ml/flood_risk_india.csv — 10,000 labelled rows with the target
`Flood Occurred`. Alongside the model we persist the training medians and category
modes, because live IMD data supplies only a few of these features and the prediction
service must impute the rest from something principled rather than zeros.

Run:  .venv/bin/python services/ml/training/train_flood_risk.py
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix, roc_auc_score,
)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data" / "raw" / "ml" / "flood_risk_india.csv"
OUT_DIR = ROOT / "services" / "ml" / "models"
MODEL_VERSION = "flood_risk_rf_v1"

TARGET = "Flood Occurred"
NUMERIC = [
    "Rainfall (mm)", "Temperature (°C)", "Humidity (%)", "River Discharge (m³/s)",
    "Water Level (m)", "Elevation (m)", "Population Density", "Infrastructure",
    "Historical Floods",
]
CATEGORICAL = ["Land Cover", "Soil Type"]
# Latitude/Longitude are deliberately excluded: the model must generalise to districts
# the training set never saw, and raw coordinates invite memorising locations.


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(DATA)
    print(f"Loaded {len(df):,} rows, {df[TARGET].mean():.1%} positive class")

    X = df[NUMERIC + CATEGORICAL]
    y = df[TARGET].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = Pipeline([
        ("prep", ColumnTransformer([
            ("num", "passthrough", NUMERIC),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
        ])),
        ("clf", RandomForestClassifier(
            n_estimators=300, max_depth=14, min_samples_leaf=5,
            class_weight="balanced", random_state=42, n_jobs=-1,
        )),
    ])

    pipeline.fit(X_train, y_train)

    proba = pipeline.predict_proba(X_test)[:, 1]
    preds = (proba >= 0.5).astype(int)
    accuracy = accuracy_score(y_test, preds)
    auc = roc_auc_score(y_test, proba)
    cv_auc = cross_val_score(pipeline, X, y, cv=5, scoring="roc_auc", n_jobs=-1)

    print(f"\nHoldout accuracy : {accuracy:.4f}")
    print(f"Holdout ROC-AUC  : {auc:.4f}")
    print(f"5-fold CV ROC-AUC: {cv_auc.mean():.4f} (+/- {cv_auc.std():.4f})")
    print("\n" + classification_report(y_test, preds, digits=3))
    print("Confusion matrix:\n", confusion_matrix(y_test, preds))

    # Feature importances, mapped back through the one-hot expansion.
    feature_names = list(NUMERIC) + list(
        pipeline.named_steps["prep"].named_transformers_["cat"].get_feature_names_out(CATEGORICAL)
    )
    importances = sorted(
        zip(feature_names, pipeline.named_steps["clf"].feature_importances_),
        key=lambda kv: kv[1], reverse=True,
    )
    print("\nTop features:")
    for name, imp in importances[:10]:
        print(f"  {name:<28} {imp:.4f}")

    # Defaults for live inference, where CWC discharge/water-level are unavailable.
    defaults = {c: float(np.round(df[c].median(), 4)) for c in NUMERIC}
    defaults.update({c: str(df[c].mode().iloc[0]) for c in CATEGORICAL})

    joblib.dump(pipeline, OUT_DIR / "flood_risk_rf.joblib")
    metrics = {
        "model_version": MODEL_VERSION,
        "n_rows": int(len(df)),
        "positive_rate": float(df[TARGET].mean()),
        "holdout_accuracy": float(accuracy),
        "holdout_roc_auc": float(auc),
        "cv_roc_auc_mean": float(cv_auc.mean()),
        "cv_roc_auc_std": float(cv_auc.std()),
        "numeric_features": NUMERIC,
        "categorical_features": CATEGORICAL,
        "inference_defaults": defaults,
        "top_features": [{"feature": n, "importance": float(i)} for n, i in importances[:10]],
    }
    (OUT_DIR / "flood_risk_metrics.json").write_text(json.dumps(metrics, indent=2))
    print(f"\nSaved model + metrics to {OUT_DIR}")

    if auc < 0.60:
        print(
            "\nWARNING: ROC-AUC is near chance. This dataset carries little signal for the\n"
            "         target, so treat the probability as a demo-grade score, not a forecast.\n"
            "         Fixing this needs the IndoFloods event/precipitation tables joined on\n"
            "         GaugeID, which is a real modelling task and not a 2-hour job."
        )


if __name__ == "__main__":
    main()
