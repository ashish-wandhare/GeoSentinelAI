from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "hyderabad_rainfall_features_june_august_2025.jsonl"
)

OUTPUT_DIR = PROJECT_ROOT / "artifacts" / "rainfall_anomaly_baseline"
PREDICTIONS_PATH = OUTPUT_DIR / "rainfall_anomaly_results.csv"
MODEL_PATH = OUTPUT_DIR / "isolation_forest.joblib"

FEATURE_COLUMNS = [
    "precipitation_mm",
    "rainfall_rolling_3h_mm",
    "rainfall_rolling_6h_mm",
    "rainfall_rolling_24h_mm",
]


def run_baseline() -> pd.DataFrame:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input dataset not found: {INPUT_PATH}")

    df = pd.read_json(INPUT_PATH, lines=True)

    required_columns = ["observed_at", *FEATURE_COLUMNS]
    missing_columns = [
        column for column in required_columns if column not in df.columns
    ]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    df["observed_at"] = pd.to_datetime(df["observed_at"], utc=True)

    # Do not impute incomplete rolling windows.
    valid_mask = df[FEATURE_COLUMNS].notna().all(axis=1)
    valid = df.loc[valid_mask].copy()

    if len(valid) < 2:
        raise ValueError("Not enough complete rows to fit Isolation Forest.")

    X = valid[FEATURE_COLUMNS]

    model = IsolationForest(
        n_estimators=100,
        contamination=0.05,
        random_state=42,
    )
    model.fit(X)

    # sklearn: -1 indicates an anomaly; +1 indicates an inlier.
    valid["anomaly_flag"] = model.predict(X) == -1

    # Lower decision scores indicate observations more unusual
    # relative to this fitted dataset.
    valid["anomaly_score"] = model.decision_function(X)

    valid["interpretation"] = valid["anomaly_flag"].map(
        {
            True: "unusual_rainfall_pattern",
            False: "typical_rainfall_pattern",
        }
    )
    valid["waterlogging_confirmed"] = False

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    valid.to_csv(PREDICTIONS_PATH, index=False)
    joblib.dump(
        {
            "model": model,
            "feature_columns": FEATURE_COLUMNS,
            "purpose": "rainfall anomaly detection; not a waterlogging predictor",
        },
        MODEL_PATH,
    )

    anomaly_count = int(valid["anomaly_flag"].sum())

    print("=" * 65)
    print("GEOSENTINEL AI - RAINFALL ANOMALY BASELINE")
    print("=" * 65)
    print(f"Input rows: {len(df)}")
    print(f"Rows excluded for incomplete features: {len(df) - len(valid)}")
    print(f"Rows analysed: {len(valid)}")
    print(f"Anomalies detected: {anomaly_count}")
    print(f"Observed anomaly fraction: {anomaly_count / len(valid):.2%}")
    print(f"Predictions saved: {PREDICTIONS_PATH}")
    print(f"Model saved: {MODEL_PATH}")
    print("Warning: anomalies are not confirmed waterlogging events.")

    print("\nMost unusual rainfall observations:")
    print(
        valid.sort_values("anomaly_score")
        [["observed_at", *FEATURE_COLUMNS, "anomaly_score"]]
        .head(10)
        .to_string(index=False)
    )

    return valid


if __name__ == "__main__":
    run_baseline()
