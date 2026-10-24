
"""Run saved-model inference on complete live hourly rainfall features."""

import pandas as pd

from src.models.rainfall_anomaly_inference import (
    FEATURE_COLUMNS,
    score_rainfall_observations,
)


def build_live_rainfall_features(live_data: dict) -> pd.DataFrame:
    """Build rolling rainfall features from complete hourly observations."""
    hourly = live_data.get("hourly", {})
    times = hourly.get("time")
    rainfall = hourly.get("precipitation")

    if not isinstance(times, list) or not isinstance(rainfall, list):
        raise ValueError("Live hourly rainfall data is missing.")

    if not times or len(times) != len(rainfall):
        raise ValueError("Hourly timestamps and rainfall values are invalid.")

    df = pd.DataFrame({
        "observed_at": pd.to_datetime(times, utc=True, errors="raise"),
        "precipitation_mm": pd.to_numeric(
            pd.Series(rainfall), errors="raise"
        ),
    })

    if df["precipitation_mm"].isna().any():
        raise ValueError("Hourly rainfall contains missing values.")

    if (df["precipitation_mm"] < 0).any():
        raise ValueError("Rainfall cannot be negative.")

    if not df["observed_at"].is_monotonic_increasing:
        df = df.sort_values("observed_at").reset_index(drop=True)

    if df["observed_at"].duplicated().any():
        raise ValueError("Duplicate hourly timestamps are not allowed.")

    intervals = df["observed_at"].diff().dropna()
    if not intervals.eq(pd.Timedelta(hours=1)).all():
        raise ValueError("Hourly rainfall data contains gaps.")

    for window in (3, 6, 24):
        df[f"rainfall_rolling_{window}h_mm"] = (
            df["precipitation_mm"].rolling(
                window=window,
                min_periods=window,
            ).sum()
        )

    latest = df.iloc[[-1]].copy()

    if latest[FEATURE_COLUMNS].isna().any().any():
        raise ValueError("Latest observation has incomplete rolling features.")

    return latest[["observed_at", *FEATURE_COLUMNS]]


def classify_rainfall_risk(rolling_3h_mm: float) -> dict:
    """Classify rainfall intensity using illustrative prototype thresholds."""
    if pd.isna(rolling_3h_mm) or rolling_3h_mm < 0:
        raise ValueError("Rolling rainfall must be a valid non-negative value.")

    if rolling_3h_mm >= 30:
        level = "VERY HIGH"
        message = "Strong rainfall warning. Monitor local conditions."
    elif rolling_3h_mm >= 15:
        level = "HIGH"
        message = "Elevated rainfall warning. Monitor local conditions."
    elif rolling_3h_mm >= 5:
        level = "MODERATE"
        message = "Increased rainfall monitoring recommended."
    else:
        level = "LOW"
        message = "No rainfall threshold triggered."

    return {
        "rainfall_risk_level": level,
        "rainfall_warning": message,
        "risk_basis": "rolling_3h_rainfall_mm",
        "thresholds_validated": False,
        "waterlogging_confirmed": False,
    }


def infer_live_rainfall(live_data: dict) -> dict:
    """Score the latest rainfall observation and classify rainfall intensity."""
    features = build_live_rainfall_features(live_data)
    result = score_rainfall_observations(features).iloc[0]

    rolling_3h_mm = float(result["rainfall_rolling_3h_mm"])
    risk = classify_rainfall_risk(rolling_3h_mm)

    return {
        "observed_at_utc": result["observed_at"].isoformat(),
        "precipitation_mm": round(float(result["precipitation_mm"]), 1),
        "rainfall_rolling_3h_mm": round(rolling_3h_mm, 1),
        "rainfall_rolling_6h_mm": round(
            float(result["rainfall_rolling_6h_mm"]), 1
        ),
        "rainfall_rolling_24h_mm": round(
            float(result["rainfall_rolling_24h_mm"]), 1
        ),
        "unusual_rainfall_pattern": bool(result["anomaly_flag"]),
        "anomaly_score": round(float(result["anomaly_score"]), 4),
        "interpretation": str(result["interpretation"]),
        "waterlogging_confirmed": False,
        "data_status": "live_hourly_rainfall_model_inference",
        **risk,
    }
