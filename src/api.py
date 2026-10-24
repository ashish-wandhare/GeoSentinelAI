"""GeoSentinel AI API for rainfall monitoring, GPS inference, and warning history."""

import json
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Body

from src.ingestion.open_meteo_live import (
    fetch_live_weather,
    fetch_weather_for_coordinates,
)
from src.models.live_rainfall_inference import infer_live_rainfall
from src.storage.warning_history import get_history, record_evaluation
from src.storage.alert_manager import evaluate_alert, get_alerts, update_alert_status

PROJECT_ROOT = Path(__file__).resolve().parents[1]

ANOMALY_RESULTS = (
    PROJECT_ROOT
    / "artifacts"
    / "rainfall_anomaly_baseline"
    / "rainfall_anomaly_results.csv"
)
HOTSPOTS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "hyderabad_flooding_hotspots.geojson"
)

app = FastAPI(
    title="GeoSentinel AI",
    description=(
        "Geospatial rainfall monitoring, location-specific weather, "
        "ML anomaly inference, and evaluation history. Rainfall anomalies "
        "are not confirmed waterlogging events."
    ),
    version="0.4.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    """Check API availability."""
    return {"status": "ok", "service": "GeoSentinel AI"}


@app.get("/api/v1/weather/live")
def live_weather() -> dict[str, Any]:
    """Return current weather for the configured Hyderabad reference point."""
    try:
        return fetch_live_weather()
    except (OSError, ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to fetch live weather: {exc}",
        ) from exc


@app.get("/api/v1/weather/location")
def location_weather(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
) -> dict[str, Any]:
    """Return weather for coordinates supplied with user permission."""
    try:
        return fetch_weather_for_coordinates(latitude, longitude)
    except (OSError, ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to fetch location weather: {exc}",
        ) from exc


@app.get("/api/v1/rainfall/location-inference")
def location_rainfall_inference(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
) -> dict[str, Any]:
    """Run rainfall anomaly inference for user-provided coordinates."""
    try:
        live_data = fetch_weather_for_coordinates(latitude, longitude)
        result = infer_live_rainfall(live_data)
        result["location"] = live_data["location"]
        result["data_status"] = "location_specific_live_rainfall_inference"
        return result
    except (OSError, ValueError, RuntimeError, TypeError, KeyError) as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to run location-specific rainfall inference: {exc}",
        ) from exc


@app.get("/api/v1/rainfall/live-inference")
def live_rainfall_inference() -> dict[str, Any]:
    """Run the existing rainfall model for the configured reference location."""
    try:
        live_data = fetch_live_weather()
        return infer_live_rainfall(live_data)
    except (OSError, ValueError, RuntimeError, TypeError, KeyError) as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to run live rainfall inference: {exc}",
        ) from exc


@app.post("/api/v1/warnings/record", status_code=201)
def create_warning_record(
    result: dict[str, Any] = Body(
        ...,
        description="Rainfall evaluation result returned by GeoSentinel AI inference.",
    ),
) -> dict[str, Any]:
    """Explicitly save one rainfall evaluation to local SQLite history."""
    try:
        saved = record_evaluation(result)
        return {
            "status": "recorded",
            "message": "Rainfall evaluation saved to warning history.",
            "record": saved,
        }
    except (OSError, ValueError, TypeError, KeyError, RuntimeError) as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to record rainfall evaluation: {exc}",
        ) from exc


@app.get("/api/v1/warnings/history")
def warning_history(
    limit: int = Query(100, ge=1, le=1000),
) -> dict[str, Any]:
    """Return the newest saved rainfall evaluation records."""
    try:
        records = get_history(limit=limit)
        return {
            "count": len(records),
            "limit": limit,
            "data_status": "saved_rainfall_evaluation_history",
            "waterlogging_confirmed": False,
            "records": records,
        }
    except (OSError, ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to retrieve warning history: {exc}",
        ) from exc


@app.post("/api/v1/alerts/evaluate")
def evaluate_rainfall_alert(
    result: dict[str, Any] = Body(
        ...,
        description="Rainfall inference result returned by GeoSentinel AI.",
    ),
) -> dict[str, Any]:
    """Evaluate an inference result against prototype alert rules."""
    try:
        return evaluate_alert(result)
    except (OSError, ValueError, TypeError, KeyError, RuntimeError) as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to evaluate rainfall alert: {exc}",
        ) from exc


@app.get("/api/v1/alerts/history")
def alert_history(
    limit: int = Query(100, ge=1, le=1000),
    status: str | None = Query(None, description="Optional status: ACTIVE, ACKNOWLEDGED, RESOLVED"),
) -> dict[str, Any]:
    """Return alert records, newest first."""
    try:
        records = get_alerts(limit=limit, status=status)
        return {
            "count": len(records),
            "limit": limit,
            "data_status": "prototype_alert_history",
            "waterlogging_confirmed": False,
            "records": records,
        }
    except (OSError, ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to retrieve alert history: {exc}",
        ) from exc


@app.patch("/api/v1/alerts/{alert_id}/status")
def change_alert_status(
    alert_id: int,
    payload: dict[str, Any] = Body(..., example={"status": "ACKNOWLEDGED"}),
) -> dict[str, Any]:
    """Update an alert to ACKNOWLEDGED or RESOLVED."""
    try:
        return update_alert_status(alert_id, str(payload.get("status", "")))
    except (OSError, ValueError, TypeError, RuntimeError) as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to update alert status: {exc}",
        ) from exc


@app.get("/api/v1/rainfall/latest")
def latest_rainfall() -> dict[str, Any]:
    """Return the latest observation in saved historical model results."""
    if not ANOMALY_RESULTS.exists():
        raise HTTPException(
            status_code=503,
            detail="Rainfall anomaly results are not available.",
        )

    try:
        df = pd.read_csv(ANOMALY_RESULTS)
        required = [
            "observed_at",
            "precipitation_mm",
            "rainfall_rolling_3h_mm",
            "rainfall_rolling_6h_mm",
            "rainfall_rolling_24h_mm",
            "anomaly_flag",
            "anomaly_score",
            "interpretation",
        ]
        missing = [column for column in required if column not in df.columns]
        if df.empty or missing:
            raise ValueError(
                f"Results are empty or missing required columns: {missing}"
            )

        df["observed_at"] = pd.to_datetime(
            df["observed_at"], utc=True, errors="raise"
        )
        record = df.sort_values("observed_at").iloc[-1]
        return {
            "observed_at_utc": record["observed_at"].isoformat(),
            "precipitation_mm": round(float(record["precipitation_mm"]), 1),
            "rainfall_rolling_3h_mm": round(
                float(record["rainfall_rolling_3h_mm"]), 1
            ),
            "rainfall_rolling_6h_mm": round(
                float(record["rainfall_rolling_6h_mm"]), 1
            ),
            "rainfall_rolling_24h_mm": round(
                float(record["rainfall_rolling_24h_mm"]), 1
            ),
            "unusual_rainfall_pattern": bool(record["anomaly_flag"]),
            "anomaly_score": round(float(record["anomaly_score"]), 4),
            "interpretation": str(record["interpretation"]),
            "waterlogging_confirmed": False,
            "data_status": "historical",
        }
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to read valid rainfall results: {exc}",
        ) from exc


@app.get("/api/v1/geospatial/hotspots")
def mapped_hotspots() -> dict[str, Any]:
    """Return historical mapped-location polygons, not flood predictions."""
    if not HOTSPOTS_FILE.exists():
        raise HTTPException(
            status_code=503,
            detail="Mapped hotspot data is not available.",
        )

    try:
        with HOTSPOTS_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if data.get("type") != "FeatureCollection":
            raise ValueError("Expected a GeoJSON FeatureCollection.")
        return {
            "data_status": "historical_mapped_locations",
            "is_flooding_prediction": False,
            "independently_verified": False,
            "geojson": data,
        }
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to read valid hotspot data: {exc}",
        ) from exc
