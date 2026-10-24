
"""Evaluate a saved rainfall anomaly model on a later time period."""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "hyderabad_rainfall_features_june_august_2025.jsonl"
)
MODEL_PATH = (
    PROJECT_ROOT
    / "artifacts"
    / "rainfall_anomaly_baseline"
    / "isolation_forest.joblib"
)
OUTPUT_DIR = PROJECT_ROOT / "artifacts" / "rainfall_chronological_evaluation"
RESULTS_PATH = OUTPUT_DIR / "evaluation_results.csv"
REPORT_PATH = OUTPUT_DIR / "evaluation_report.json"

MIN_TRAINING_ROWS = 24


def evaluate() -> dict:
    """Score a later chronological period without fitting the model."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Saved model not found: {MODEL_PATH}. "
            "Run the rainfall anomaly baseline first."
        )

    df = pd.read_json(DATA_PATH, lines=True)

    required = [
        "observed_at",
        "precipitation_mm",
        "rainfall_rolling_3h_mm",
        "rainfall_rolling_6h_mm",
        "rainfall_rolling_24h_mm",
    ]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df["observed_at"] = pd.to_datetime(
        df["observed_at"], utc=True, errors="coerce"
    )
    if df["observed_at"].isna().any():
        raise ValueError("Dataset contains invalid timestamps.")

    df = df.sort_values("observed_at").reset_index(drop=True)

    if df["observed_at"].duplicated().any():
        raise ValueError("Dataset contains duplicate timestamps.")

    artifact = joblib.load(MODEL_PATH)
    if not isinstance(artifact, dict) or "model" not in artifact:
        raise ValueError("Invalid saved model artifact.")

    model = artifact["model"]
    feature_columns = artifact.get("feature_columns", [])

    if not feature_columns or any(c not in required for c in feature_columns):
        raise ValueError("Saved model feature metadata is invalid.")

    complete = df[feature_columns].notna().all(axis=1)
    df = df.loc[complete].copy().reset_index(drop=True)

    if len(df) < MIN_TRAINING_ROWS + 1:
        raise ValueError("Not enough complete observations for evaluation.")

    # Chronological split: earlier observations are the reference period.
    split_index = int(len(df) * 0.70)
    if split_index < MIN_TRAINING_ROWS or split_index >= len(df):
        raise ValueError("Unable to create a valid chronological split.")

    df["period"] = np.where(
        np.arange(len(df)) < split_index,
        "earlier_reference",
        "later_evaluation",
    )

    # Score both periods with the already-saved model. No fit() call.
    features = df[feature_columns]
    if not np.isfinite(features.to_numpy(dtype=float)).all():
        raise ValueError("Rainfall features contain non-finite values.")

    predictions = model.predict(features)
    scores = model.decision_function(features)

    df["anomaly_flag"] = predictions == -1
    df["anomaly_score"] = scores
    df["interpretation"] = df["anomaly_flag"].map(
        {
            True: "unusual_rainfall_pattern",
            False: "typical_rainfall_pattern",
        }
    )
    df["waterlogging_confirmed"] = False

    summary = []
    for period, group in df.groupby("period", sort=False):
        summary.append(
            {
                "period": period,
                "observations": int(len(group)),
                "anomalies": int(group["anomaly_flag"].sum()),
                "anomaly_rate_pct": round(
                    float(group["anomaly_flag"].mean() * 100), 2
                ),
                "mean_anomaly_score": round(
                    float(group["anomaly_score"].mean()), 6
                ),
                "start_utc": group["observed_at"].min().isoformat(),
                "end_utc": group["observed_at"].max().isoformat(),
            }
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(RESULTS_PATH, index=False)

    report = {
        "project": "GeoSentinel AI",
        "evaluation_type": "chronological_unsupervised_anomaly_analysis",
        "model_retrained_during_evaluation": False,
        "dataset_rows_scored": int(len(df)),
        "split_method": "first 70% earlier reference; final 30% later evaluation",
        "feature_columns": feature_columns,
        "period_summary": summary,
        "limitations": [
            "Both periods are scored using the saved model trained on the full historical dataset.",
            "This is a chronological score comparison, not a leakage-free prospective evaluation.",
            "No verified waterlogging labels are available to measure waterlogging prediction accuracy.",
            "Anomalies indicate unusual rainfall patterns, not confirmed flooding.",
        ],
        "waterlogging_prediction_accuracy_evaluated": False,
        "results_csv": str(RESULTS_PATH),
    }

    with REPORT_PATH.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    print("GeoSentinel AI - Chronological Anomaly Analysis")
    print("==============================================")
    for item in summary:
        print(
            f"{item['period']}: {item['observations']} observations, "
            f"{item['anomalies']} anomalies "
            f"({item['anomaly_rate_pct']:.2f}%)"
        )
    print(f"Results: {RESULTS_PATH}")
    print(f"Report:  {REPORT_PATH}")
    print("Note: this does not measure waterlogging prediction accuracy.")

    return report


if __name__ == "__main__":
    evaluate()
