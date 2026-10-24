"""SQLite alert lifecycle and duplicate suppression for GeoSentinel AI."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config import settings

DB_PATH = Path(settings.data_dir) / "geosentinel_alerts.db"
VALID_STATUSES = {"ACTIVE", "ACKNOWLEDGED", "RESOLVED"}
ALERT_RISK_LEVELS = {"HIGH", "VERY HIGH"}


def initialize_database() -> None:
    """Create the alert table without modifying evaluation history."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH, timeout=10) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at_utc TEXT NOT NULL,
                updated_at_utc TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                risk_level TEXT NOT NULL,
                rule_key TEXT NOT NULL,
                reason TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'ACTIVE',
                anomaly_score REAL,
                rainfall_3h_mm REAL,
                rainfall_6h_mm REAL,
                rainfall_24h_mm REAL,
                data_status TEXT NOT NULL,
                waterlogging_confirmed INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_alerts_created_at
            ON alerts(created_at_utc)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_alerts_dedupe
            ON alerts(latitude, longitude, rule_key, status)
            """
        )


def evaluate_alert(result: dict[str, Any]) -> dict[str, Any]:
    """Create a rule-based alert when risk/anomaly criteria are met.

    Rules are prototype operational rules, not validated flood thresholds.
    An active or acknowledged alert with the same rounded coordinates and
    rule key suppresses duplicate alerts until it is resolved.
    """
    initialize_database()
    risk = str(result.get("rainfall_risk_level", "UNAVAILABLE")).upper()
    unusual = bool(result.get("unusual_rainfall_pattern", False))
    location = result.get("location") or {}
    lat = _coordinate(location.get("latitude"), -90, 90, "latitude")
    lon = _coordinate(location.get("longitude"), -180, 180, "longitude")

    triggers: list[tuple[str, str]] = []
    if risk in ALERT_RISK_LEVELS:
        triggers.append((f"RISK_{risk.replace(' ', '_')}", f"Prototype rainfall risk level is {risk}."))
    if unusual:
        triggers.append(("UNUSUAL_RAINFALL_PATTERN", "Isolation Forest flagged an unusual rainfall pattern."))

    if not triggers:
        return {
            "status": "NO_ALERT",
            "message": "No prototype alert rule was triggered by this evaluation.",
            "risk_level": risk,
            "unusual_rainfall_pattern": unusual,
            "alerts": [],
            "waterlogging_confirmed": False,
        }

    now = datetime.now(timezone.utc).isoformat()
    results = []
    with sqlite3.connect(DB_PATH, timeout=10) as connection:
        connection.row_factory = sqlite3.Row
        for rule_key, reason in triggers:
            existing = connection.execute(
                """
                SELECT * FROM alerts
                WHERE latitude IS ? AND longitude IS ?
                  AND rule_key = ? AND status IN ('ACTIVE', 'ACKNOWLEDGED')
                ORDER BY id DESC LIMIT 1
                """,
                (lat, lon, rule_key),
            ).fetchone()
            # Coordinate equality is made tolerant by comparing rounded values below
            # when exact stored values do not match.
            if existing is None and lat is not None and lon is not None:
                candidates = connection.execute(
                    """
                    SELECT * FROM alerts
                    WHERE rule_key = ? AND status IN ('ACTIVE', 'ACKNOWLEDGED')
                      AND latitude IS NOT NULL AND longitude IS NOT NULL
                    ORDER BY id DESC LIMIT 500
                    """,
                    (rule_key,),
                ).fetchall()
                existing = next(
                    (row for row in candidates
                     if round(float(row["latitude"]), 3) == round(lat, 3)
                     and round(float(row["longitude"]), 3) == round(lon, 3)),
                    None,
                )
            if existing is not None:
                results.append({
                    "id": existing["id"],
                    "status": existing["status"],
                    "rule_key": rule_key,
                    "message": "Duplicate suppressed; a matching alert is already active.",
                    "created_at_utc": existing["created_at_utc"],
                })
                continue

            cursor = connection.execute(
                """
                INSERT INTO alerts (
                    created_at_utc, updated_at_utc, latitude, longitude,
                    risk_level, rule_key, reason, status, anomaly_score,
                    rainfall_3h_mm, rainfall_6h_mm, rainfall_24h_mm,
                    data_status, waterlogging_confirmed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?, ?, ?, ?, 0)
                """,
                (
                    now, now, lat, lon, risk, rule_key, reason,
                    _optional_float(result.get("anomaly_score")),
                    _optional_float(result.get("rainfall_rolling_3h_mm")),
                    _optional_float(result.get("rainfall_rolling_6h_mm")),
                    _optional_float(result.get("rainfall_rolling_24h_mm")),
                    str(result.get("data_status", "unknown")),
                ),
            )
            results.append({
                "id": cursor.lastrowid,
                "status": "ACTIVE",
                "rule_key": rule_key,
                "reason": reason,
                "created_at_utc": now,
            })

    created = any(item.get("status") == "ACTIVE" and "reason" in item for item in results)
    return {
        "status": "ALERT_CREATED" if created else "DUPLICATE_SUPPRESSED",
        "risk_level": risk,
        "alerts": results,
        "waterlogging_confirmed": False,
        "message": "Prototype alert rules are illustrative and do not confirm flooding.",
    }


def get_alerts(limit: int = 100, status: str | None = None) -> list[dict[str, Any]]:
    """Return alert records newest first, optionally filtered by status."""
    if not 1 <= limit <= 1000:
        raise ValueError("Limit must be between 1 and 1000.")
    if status is not None:
        status = status.upper()
        if status not in VALID_STATUSES:
            raise ValueError(f"Status must be one of {sorted(VALID_STATUSES)}.")
    initialize_database()
    with sqlite3.connect(DB_PATH, timeout=10) as connection:
        connection.row_factory = sqlite3.Row
        if status:
            rows = connection.execute(
                "SELECT * FROM alerts WHERE status = ? ORDER BY id DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT * FROM alerts ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
    records = []
    for row in rows:
        item = dict(row)
        item["waterlogging_confirmed"] = False
        records.append(item)
    return records


def update_alert_status(alert_id: int, status: str) -> dict[str, Any]:
    """Change an alert status; RESOLVED alerts no longer suppress future alerts."""
    status = status.upper()
    if status not in {"ACKNOWLEDGED", "RESOLVED"}:
        raise ValueError("Status must be ACKNOWLEDGED or RESOLVED.")
    initialize_database()
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(DB_PATH, timeout=10) as connection:
        cursor = connection.execute(
            "UPDATE alerts SET status = ?, updated_at_utc = ? WHERE id = ?",
            (status, now, alert_id),
        )
        if cursor.rowcount == 0:
            raise ValueError(f"Alert ID {alert_id} was not found.")
    return {
        "id": alert_id,
        "status": status,
        "updated_at_utc": now,
        "waterlogging_confirmed": False,
    }


def _coordinate(value: Any, minimum: float, maximum: float, name: str) -> float | None:
    if value is None:
        return None
    number = float(value)
    if not minimum <= number <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}.")
    return number


def _optional_float(value: Any) -> float | None:
    return None if value is None else float(value)
