
from pathlib import Path

import joblib
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = (
    PROJECT_ROOT
    / "artifacts"
    / "rainfall_anomaly_baseline"
    / "isolation_forest.joblib"
)

FEATURE_COLUMNS = [
    "precipitation_mm",
    "rainfall_rolling_3h_mm",
    "rainfall_rolling_6h_mm",
    "rainfall_rolling_24h_mm",
]


def load_model():
    """Load the previously trained rainfall anomaly model."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Trained model not found: {MODEL_PATH}. "
            "Run the rainfall anomaly baseline first."
        )

    artifact = joblib.load(MODEL_PATH)

    if not isinstance(artifact, dict) or "model" not in artifact:
        raise ValueError("Invalid model artifact: expected a model dictionary.")

    model = artifact["model"]
    saved_features = artifact.get("feature_columns")

    if saved_features != FEATURE_COLUMNS:
        raise ValueError(
            "Model feature columns do not match the inference feature columns."
        )

    return model


def score_rainfall_observations(observations: pd.DataFrame) -> pd.DataFrame:
    """Score new rainfall observations without fitting or retraining."""
    if not isinstance(observations, pd.DataFrame):
        raise TypeError("observations must be a pandas DataFrame.")

    if observations.empty:
        raise ValueError("observations must contain at least one row.")

    required_columns = ["observed_at", *FEATURE_COLUMNS]
    missing_columns = [
        column for column in required_columns if column not in observations.columns
    ]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    results = observations.copy()
    results["observed_at"] = pd.to_datetime(
        results["observed_at"], utc=True, errors="raise"
    )

    for column in FEATURE_COLUMNS:
        results[column] = pd.to_numeric(results[column], errors="raise")

    features = results[FEATURE_COLUMNS]

    if features.isna().any().any():
        raise ValueError("Rainfall features must not contain missing values.")

    if not features.map(lambda value: pd.notna(value) and abs(value) != float("inf")).all().all():
        raise ValueError("Rainfall features must contain finite numeric values.")

    model = load_model()
    results["anomaly_flag"] = model.predict(features) == -1
    results["anomaly_score"] = model.decision_function(features)
    results["interpretation"] = results["anomaly_flag"].map(
        {
            True: "unusual_rainfall_pattern",
            False: "typical_rainfall_pattern",
        }
    )
    results["waterlogging_confirmed"] = False

    return results
