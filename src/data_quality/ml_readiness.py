
import json
from pathlib import Path

RAINFALL_FILE = Path(
    "data/processed/hyderabad_rainfall_features_june_august_2025.jsonl"
)
FLOODING_POINTS_FILE = Path("data/processed/hyderabad_flooding_points.geojson")
INCIDENT_REPORT_FILE = Path("data/processed/incident_test_quality.json")
OUTPUT_FILE = Path("data/processed/ml_readiness_report.json")


def count_jsonl_records(path: Path) -> dict:
    """Count JSONL records and missing rainfall feature values."""
    total = 0
    malformed = 0
    missing_values = {
        "rainfall_rolling_3h_mm": 0,
        "rainfall_rolling_6h_mm": 0,
        "rainfall_rolling_24h_mm": 0,
    }
    timestamps = []
    locations = set()

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                malformed += 1
                continue

            total += 1
            timestamps.append(record.get("observed_at"))
            locations.add(record.get("location_id"))

            for key in missing_values:
                if record.get(key) is None:
                    missing_values[key] += 1

    valid_timestamps = sorted(t for t in timestamps if t)

    return {
        "record_count": total,
        "malformed_json_records": malformed,
        "location_count": len(locations),
        "missing_feature_values": missing_values,
        "earliest_timestamp": valid_timestamps[0] if valid_timestamps else None,
        "latest_timestamp": valid_timestamps[-1] if valid_timestamps else None,
    }


def count_flooding_points(path: Path) -> dict:
    """Summarize mapped flooding points without treating them as labels."""
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError("Flooding points must be a GeoJSON FeatureCollection.")

    features = data.get("features", [])
    points = [
        feature
        for feature in features
        if feature.get("geometry", {}).get("type") == "Point"
    ]

    timestamped = sum(
        bool(feature.get("properties", {}).get("occurred_at"))
        for feature in points
    )
    severity_labeled = sum(
        feature.get("properties", {}).get("severity") is not None
        for feature in points
    )

    return {
        "mapped_point_count": len(points),
        "timestamped_points": timestamped,
        "severity_labeled_points": severity_labeled,
        "usable_as_supervised_target_labels": False,
        "reason": (
            "The inspected source contains mapped locations, not "
            "timestamped, independently verified incident events."
        ),
    }


def build_readiness_report(
    rainfall: dict,
    flooding: dict,
    incident_report: dict,
) -> dict:
    """Assess whether current datasets support supervised flood prediction."""
    synthetic_records = incident_report.get("data_origin_counts", {}).get(
        "synthetic", 0
    )
    real_incident_records = incident_report.get("data_origin_counts", {}).get(
        "real", 0
    )

    rainfall_is_usable_for_feature_exploration = (
        rainfall["record_count"] > 0
        and rainfall["malformed_json_records"] == 0
    )

    supervised_prediction_ready = (
        flooding["timestamped_points"] > 0
        and flooding["severity_labeled_points"] > 0
        and real_incident_records > 0
    )

    return {
        "assessment_type": "ml_data_readiness",
        "datasets": {
            "historical_rainfall": rainfall,
            "mapped_flooding_locations": flooding,
            "incident_quality_report": {
                "input_file": incident_report.get("input_file"),
                "total_records": incident_report.get("total_records", 0),
                "data_origin_counts": incident_report.get(
                    "data_origin_counts", {}
                ),
                "verification_status_counts": incident_report.get(
                    "verification_status_counts", {}
                ),
                "records_without_severity": incident_report.get(
                    "records_without_severity", 0
                ),
            },
        },
        "readiness": {
            "rainfall_feature_exploration": (
                "ready"
                if rainfall_is_usable_for_feature_exploration
                else "not_ready"
            ),
            "geospatial_visualization": (
                "ready" if flooding["mapped_point_count"] > 0 else "not_ready"
            ),
            "supervised_waterlogging_prediction": (
                "ready" if supervised_prediction_ready else "not_ready"
            ),
        },
        "missing_requirements": [
            "Time-stamped, verified waterlogging incident events.",
            "A defensible target label and matching time/location for each sample.",
            "Representative rainfall observations across multiple locations and events.",
            "Confirmed negative examples; absence of a report is not proof of no flooding.",
            "A time-aware validation plan to prevent data leakage.",
        ],
        "recommendation": (
            "Continue data validation and feature exploration. Do not train or "
            "claim a validated supervised waterlogging prediction model until "
            "suitable incident labels and evaluation data are available."
        ),
        "synthetic_incident_records_are_not_real_evidence": synthetic_records > 0,
    }


def main() -> None:
    rainfall = count_jsonl_records(RAINFALL_FILE)
    flooding = count_flooding_points(FLOODING_POINTS_FILE)

    with INCIDENT_REPORT_FILE.open("r", encoding="utf-8") as file:
        incident_report = json.load(file)

    report = build_readiness_report(rainfall, flooding, incident_report)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    print("ML data-readiness assessment generated.")
    print(f"Rainfall records: {rainfall['record_count']}")
    print(f"Mapped flooding points: {flooding['mapped_point_count']}")
    print(
        "Supervised waterlogging prediction: "
        f"{report['readiness']['supervised_waterlogging_prediction']}"
    )
    print(f"Report saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
