
import argparse
import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx

from src.config import settings
from src.data_quality.schemas import WeatherObservation


API_URL = "https://archive-api.open-meteo.com/v1/archive"

# Approximate Hyderabad weather reference point, not a street-level sensor.
HYDERABAD_LATITUDE = 17.385
HYDERABAD_LONGITUDE = 78.4867

SOURCE_ID = "open-meteo-historical-archive"
LOCATION_ID = "hyd-weather-reference"


def fetch_weather(start_date: date, end_date: date) -> dict:
    """Fetch hourly historical precipitation for Hyderabad."""
    if end_date < start_date:
        raise ValueError("end_date must not precede start_date")

    params = {
        "latitude": HYDERABAD_LATITUDE,
        "longitude": HYDERABAD_LONGITUDE,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "hourly": "precipitation",
        "timezone": "GMT",
        "precipitation_unit": "mm",
    }

    with httpx.Client(timeout=60.0) as client:
        response = client.get(API_URL, params=params)
        response.raise_for_status()
        payload = response.json()

    if not isinstance(payload, dict):
        raise ValueError("API response must be a JSON object")

    if payload.get("error"):
        raise RuntimeError(
            f"Open-Meteo API error: {payload.get('reason')}"
        )

    hourly = payload.get("hourly")
    if not isinstance(hourly, dict):
        raise ValueError("API response has no hourly data")

    times = hourly.get("time")
    rainfall = hourly.get("precipitation")

    if not isinstance(times, list) or not isinstance(rainfall, list):
        raise ValueError("Missing hourly time or precipitation arrays")

    if len(times) != len(rainfall):
        raise ValueError("Hourly time and precipitation arrays differ in length")

    if not times:
        raise ValueError("API returned no hourly timestamps")

    if payload.get("latitude") is None or payload.get("longitude") is None:
        raise ValueError("API response is missing coordinates")

    return payload


def parse_timestamp(value: str) -> datetime:
    """Parse a timestamp and normalize it to UTC."""
    timestamp = datetime.fromisoformat(value)

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    return timestamp.astimezone(timezone.utc)


def normalize_observations(payload: dict) -> list[dict]:
    """Validate and normalize records with available precipitation values."""
    hourly = payload["hourly"]
    observations = []

    for timestamp, precipitation in zip(
        hourly["time"],
        hourly["precipitation"],
    ):
        if precipitation is None:
            # Missing is not the same as zero rainfall.
            continue

        if isinstance(precipitation, bool):
            raise ValueError("Boolean precipitation value is invalid")

        observed_at = parse_timestamp(timestamp)

        record = {
            "location_id": LOCATION_ID,
            "observed_at": observed_at.isoformat(),
            "latitude": payload["latitude"],
            "longitude": payload["longitude"],
            "precipitation_mm": precipitation,
            "source_id": SOURCE_ID,
            "data_origin": "real",
        }

        validated = WeatherObservation.model_validate(record)
        observations.append(validated.model_dump(mode="json"))

    return observations


def save_jsonl(records: list[dict], output_path: Path) -> None:
    """Save observations as JSON Lines."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(
                json.dumps(record, allow_nan=False) + "\n"
            )


def build_audit(
    payload: dict,
    start_date: date,
    end_date: date,
    records: list[dict],
) -> dict:
    """Summarize expected, returned, missing, and saved hourly data."""
    hourly = payload["hourly"]
    timestamps = hourly["time"]
    rainfall = hourly["precipitation"]

    expected_hours = (
        (end_date - start_date).days + 1
    ) * 24

    returned_timestamps = [
        parse_timestamp(value) for value in timestamps
    ]

    expected_timestamps = {
        datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
        + timedelta(hours=hour)
        for hour in range(expected_hours)
    }

    returned_set = set(returned_timestamps)
    missing_timestamps = sorted(expected_timestamps - returned_set)

    null_precipitation_timestamps = [
        parse_timestamp(timestamp).isoformat()
        for timestamp, value in zip(timestamps, rainfall)
        if value is None
    ]

    return {
        "dataset_name": "Hyderabad Historical Hourly Precipitation",
        "provider": "Open-Meteo",
        "endpoint": API_URL,
        "product": "Historical weather reanalysis",
        "source_id": SOURCE_ID,
        "data_origin": "real",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "requested_start_date": start_date.isoformat(),
        "requested_end_date": end_date.isoformat(),
        "timezone_requested": "GMT",
        "precipitation_unit": "mm",
        "latitude": payload["latitude"],
        "longitude": payload["longitude"],
        "location_id": LOCATION_ID,
        "expected_hourly_records": expected_hours,
        "returned_hourly_timestamps": len(timestamps),
        "unique_returned_timestamps": len(returned_set),
        "duplicate_timestamps": len(timestamps) - len(returned_set),
        "missing_expected_timestamps": len(missing_timestamps),
        "missing_expected_timestamp_examples": [
            value.isoformat() for value in missing_timestamps[:20]
        ],
        "missing_precipitation_hours": len(null_precipitation_timestamps),
        "missing_precipitation_timestamp_examples": (
            null_precipitation_timestamps[:20]
        ),
        "valid_observations_saved": len(records),
        "spatial_scope": "Single weather reference point",
        "limitations": [
            "Reanalysis values are not necessarily direct station observations.",
            "Weather grid resolution is not street-level.",
            "This dataset contains no waterlogging event labels.",
            "A single reference point cannot establish district-level rainfall.",
            "Missing precipitation is not treated as zero rainfall.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download historical Hyderabad weather data."
    )
    parser.add_argument(
        "--start",
        type=date.fromisoformat,
        required=True,
        help="Start date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--end",
        type=date.fromisoformat,
        required=True,
        help="End date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=settings.data_dir / "raw" / "hyderabad_weather.jsonl",
    )

    args = parser.parse_args()

    if args.end < args.start:
        parser.error("--end must not precede --start")

    print("Fetching Open-Meteo historical weather...")
    payload = fetch_weather(args.start, args.end)
    records = normalize_observations(payload)

    save_jsonl(records, args.output)

    manifest_path = args.output.with_name(
        f"{args.output.stem}_manifest.json"
    )
    manifest = build_audit(
        payload,
        args.start,
        args.end,
        records,
    )

    manifest["downloaded_file"] = str(args.output)
    manifest["manifest_file"] = str(manifest_path)

    file_hash = hashlib.sha256()
    with args.output.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            file_hash.update(chunk)

    manifest["sha256"] = file_hash.hexdigest()

    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Expected hourly records: {manifest['expected_hourly_records']}")
    print(
        "Returned hourly timestamps: "
        f"{manifest['returned_hourly_timestamps']}"
    )
    print(
        "Missing precipitation hours: "
        f"{manifest['missing_precipitation_hours']}"
    )
    print(
        "Missing expected timestamps: "
        f"{manifest['missing_expected_timestamps']}"
    )
    print(f"Valid observations saved: {len(records)}")
    print(f"Data origin: {manifest['data_origin']}")
    print(f"Output: {args.output.resolve()}")
    print(f"Manifest: {manifest_path.resolve()}")

    if not records:
        print("WARNING: No valid precipitation observations were saved.")


if __name__ == "__main__":
    main()
