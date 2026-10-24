
import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from src.config import settings
from src.data_quality.schemas import WeatherObservation


REQUIRED_FIELDS = [
    "location_id",
    "observed_at",
    "latitude",
    "longitude",
    "precipitation_mm",
    "source_id",
    "data_origin",
]


def is_missing(value) -> bool:
    """Treat absent, null and blank-string values as missing."""

    return value is None or (
        isinstance(value, str) and not value.strip()
    )


def build_quality_report(input_path: Path) -> dict:
    """Validate a JSONL file and summarize data quality."""

    total_records = 0
    valid_records = 0
    invalid_records = 0
    malformed_json_lines = 0

    missing_counts = Counter()
    origin_counts = Counter()
    seen_keys = set()
    duplicate_count = 0
    rainfall_values = []
    errors = []

    with input_path.open("r", encoding="utf-8-sig") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            total_records += 1

            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                malformed_json_lines += 1
                invalid_records += 1
                errors.append({
                    "line": line_number,
                    "error": f"Invalid JSON: {exc.msg}",
                })
                continue

            if not isinstance(raw, dict):
                invalid_records += 1
                errors.append({
                    "line": line_number,
                    "error": "Each JSONL record must be an object.",
                })
                continue

            for field in REQUIRED_FIELDS:
                if field not in raw or is_missing(raw.get(field)):
                    missing_counts[field] += 1

            origin = raw.get("data_origin")
            if isinstance(origin, str):
                origin_counts[origin] += 1

            key = (
                raw.get("location_id"),
                raw.get("observed_at"),
                raw.get("source_id"),
            )

            if all(value is not None for value in key):
                if key in seen_keys:
                    duplicate_count += 1
                else:
                    seen_keys.add(key)

            try:
                observation = WeatherObservation.model_validate(raw)
            except ValidationError as exc:
                invalid_records += 1
                errors.append({
                    "line": line_number,
                    "error": exc.errors(
                        include_input=False,
                        include_context=False,
                        include_url=False,
                    ),
                })
                continue

            valid_records += 1
            rainfall_values.append(observation.precipitation_mm)

    rainfall_summary = None

    if rainfall_values:
        rainfall_summary = {
            "minimum_mm": min(rainfall_values),
            "maximum_mm": max(rainfall_values),
            "mean_mm": round(
                sum(rainfall_values) / len(rainfall_values), 3
            ),
        }

    return {
        "report_generated_at": datetime.now(timezone.utc).isoformat(),
        "input_file": str(input_path),
        "data_origin_counts": dict(origin_counts),
        "total_records": total_records,
        "valid_records": valid_records,
        "invalid_records": invalid_records,
        "malformed_json_lines": malformed_json_lines,
        "duplicate_count": duplicate_count,
        "missing_values_by_field": dict(missing_counts),
        "rainfall_summary": rainfall_summary,
        "validation_errors": errors[:50],
        "validation_errors_truncated": len(errors) > 50,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate GeoSentinel AI JSONL observations."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=settings.data_dir / "synthetic"
        / "weather_observations.jsonl",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=settings.data_dir / "synthetic"
        / "quality_report.json",
    )
    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Input file not found: {args.input}")

    report = build_quality_report(args.input)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2))
    print(f"\nQuality report saved to: {args.output.resolve()}")

    if report["invalid_records"] > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
