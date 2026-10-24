
"""SQLite storage for GeoSentinel AI rainfall evaluation history."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config import settings

DB_PATH = Path(settings.data_dir) / "geosentinel_warning_history.db"

VALID_RISK_LEVELS = {"LOW", "MODERATE", "HIGH", "VERY HIGH", "UNAVAILABLE"}


def initialize_database() -> None:
    """Create the warning history table if it does not exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH, timeout=10) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS warning_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recorded_at_utc TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                risk_level TEXT NOT NULL,
                rainfall_3h_mm REAL,
                rainfall_6h_mm REAL,
                rainfall_24h_mm REAL,
                unusual_rainfall_pattern INTEGER NOT NULL,
                anomaly_score REAL,
                interpretation TEXT,
                waterlogging_confirmed INTEGER NOT NULL DEFAULT 0,
                data_status TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_warning_history_recorded_at
            ON warning_history(recorded_at_utc)
            """
        )


def record_evaluation(result: dict[str, Any]) -> dict[str, Any]:
    """Persist one rainfall evaluation and return its record identifier."""
    risk_level = str(result.get("rainfall_risk_level", "UNAVAILABLE")).upper()

    if risk_level not in VALID_RISK_LEVELS:
        raise ValueError(f"Unsupported rainfall risk level: {risk_level}")

    location = result.get("location") or {}
    latitude = location.get("latitude")
    longitude = location.get("longitude")

    if latitude is not None and not -90 <= float(latitude) <= 90:
        raise ValueError("Latitude must be between -90 and 90.")

    if longitude is not None and not -180 <= float(longitude) <= 180:
        raise ValueError("Longitude must be between -180 and 180.")

    recorded_at = datetime.now(timezone.utc).isoformat()

    initialize_database()

    with sqlite3.connect(DB_PATH, timeout=10) as connection:
        cursor = connection.execute(
            """
            INSERT INTO warning_history (
                recorded_at_utc,
                latitude,
                longitude,
                risk_level,
                rainfall_3h_mm,
                rainfall_6h_mm,
                rainfall_24h_mm,
                unusual_rainfall_pattern,
                anomaly_score,
                interpretation,
                waterlogging_confirmed,
                data_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                recorded_at,
                float(latitude) if latitude is not None else None,
                float(longitude) if longitude is not None else None,
                risk_level,
                _optional_float(result.get("rainfall_rolling_3h_mm")),
                _optional_float(result.get("rainfall_rolling_6h_mm")),
                _optional_float(result.get("rainfall_rolling_24h_mm")),
                int(bool(result.get("unusual_rainfall_pattern", False))),
                _optional_float(result.get("anomaly_score")),
                str(result.get("interpretation", "unavailable")),
                0,
                str(result.get("data_status", "unknown")),
            ),
        )
        record_id = cursor.lastrowid

    return {
        "id": record_id,
        "recorded_at_utc": recorded_at,
        "risk_level": risk_level,
        "waterlogging_confirmed": False,
    }


def get_history(limit: int = 100) -> list[dict[str, Any]]:
    """Return the newest evaluation records first."""
    if not 1 <= limit <= 1000:
        raise ValueError("Limit must be between 1 and 1000.")

    initialize_database()

    with sqlite3.connect(DB_PATH, timeout=10) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT *
            FROM warning_history
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    records = []
    for row in rows:
        record = dict(row)
        record["unusual_rainfall_pattern"] = bool(
            record["unusual_rainfall_pattern"]
        )
        record["waterlogging_confirmed"] = False
        records.append(record)

    return records


def _optional_float(value: Any) -> float | None:
    """Convert a value to float, preserving missing values."""
    if value is None:
        return None
    return float(value)
