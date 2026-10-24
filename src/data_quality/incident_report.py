
import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from src.config import settings
from src.data_quality.incident_schema import WaterloggingIncident


DEFAULT_INPUT = settings.data_dir / "raw" / "waterlogging_incidents.jsonl"
DEFAULT_OUTPUT = (
    settings.data_dir / "processed" / "waterlogging_incident_quality.json"
)


def analyze_incidents(input_path: Path) -> dict:
    """Validate incident JSONL records and summarize data quality."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    total_records = 0
    malformed_json = 0
    invalid_records = []
    valid_records = []

    with input_path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            total_records += 1

            try:
                raw_record = json.loads(line)
            except json.JSONDecodeError as exc:
                malformed_json += 1
                invalid_records.append({
                    "line": line_number,
                    "error": f"Malformed JSON: {exc.msg}",
                })
                continue

            try:
                incident = WaterloggingIncident.model_validate(raw_record)
                valid_records.append(incident)
            except Exception as exc:
                invalid_records.append({
                    "line": line_number,
                    "error": str(exc)[:500],
                })

    # Flag duplicate IDs without deleting or modifying any records.
    id_counts = Counter(record.incident_id for record in valid_records)
    duplicate_ids = sorted(
        incident_id
        for incident_id, count in id_counts.items()
        if count > 1
    )
    duplicate_records = sum(
        count - 1 for count in id_counts.values() if count > 1
    )

    status_counts = Counter(
        record.verification_status for record in valid_records
    )
    origin_counts = Counter(
        record.data_origin for record in valid_records
    )
    severity_counts = Counter(
        record.severity or "not_specified"
        for record in valid_records
    )

    latitudes = [record.latitude for record in valid_records]
    longitudes = [record.longitude for record in valid_records]
    occurrence_times = [record.occurred_at for record in valid_records]
    report_times = [record.reported_at for record in valid_records]

    def time_range(values):
        if not values:
            return {"earliest": None, "latest": None}

        return {
            "earliest": min(values).isoformat(),
            "latest": max(values).isoformat(),
        }

    return {
        "report_generated_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "input_file": str(input_path),
        "total_records": total_records,
        "valid_records": len(valid_records),
        "invalid_records": len(invalid_records),
        "malformed_json_records": malformed_json,
        "duplicate_incident_ids": duplicate_ids,
        "duplicate_records_beyond_first": duplicate_records,
        "verification_status_counts": dict(sorted(status_counts.items())),
        "data_origin_counts": dict(sorted(origin_counts.items())),
        "severity_counts": dict(sorted(severity_counts.items())),
        "records_without_severity": sum(
            record.severity is None for record in valid_records
        ),
        "geographic_coverage": {
            "latitude_min": min(latitudes) if latitudes else None,
            "latitude_max": max(latitudes) if latitudes else None,
            "longitude_min": min(longitudes) if longitudes else None,
            "longitude_max": max(longitudes) if longitudes else None,
        },
        "occurrence_time_coverage": time_range(occurrence_times),
        "report_time_coverage": time_range(report_times),
        "invalid_record_details": invalid_records,
        "limitations": [
            "Schema validation does not independently verify incidents.",
            "Unverified reports are not confirmed incidents.",
            "Duplicate IDs are flagged, not automatically removed.",
            "Missing incident reports must not be treated as confirmed negatives.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a waterlogging incident data-quality report."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    report = analyze_incidents(args.input)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Total records: {report['total_records']}")
    print(f"Valid records: {report['valid_records']}")
    print(f"Invalid records: {report['invalid_records']}")
    print(f"Malformed JSON: {report['malformed_json_records']}")
    print(
        "Duplicate IDs: "
        f"{len(report['duplicate_incident_ids'])}"
    )
    print(f"Report saved: {args.output.resolve()}")

    if report["invalid_records"] > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
