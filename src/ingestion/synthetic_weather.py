
import argparse
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.config import settings


def generate_observation(
    rng: random.Random,
    location_number: int,
    observed_at: datetime,
) -> dict:
    """Generate one simulated Hyderabad-area weather observation."""

    # Approximate Hyderabad-area coordinates for testing only.
    latitude = round(17.20 + rng.random() * 0.35, 6)
    longitude = round(78.25 + rng.random() * 0.40, 6)

    # Simulated rainfall distribution; not a real weather model.
    chance = rng.random()

    if chance < 0.80:
        rainfall = 0.0
    elif chance < 0.95:
        rainfall = rng.uniform(0.1, 8.0)
    else:
        rainfall = rng.uniform(8.1, 35.0)

    return {
        "location_id": f"hyd-test-{location_number:03d}",
        "observed_at": observed_at.isoformat(),
        "latitude": latitude,
        "longitude": longitude,
        "precipitation_mm": round(rainfall, 2),
        "source_id": "synthetic-generator-v1",
        "data_origin": "synthetic",
    }


def generate_dataset(
    records: int = 100,
    seed: int = 42,
) -> list[dict]:
    """Generate a reproducible collection of test observations."""

    if records < 1:
        raise ValueError("records must be at least 1")

    rng = random.Random(seed)
    # Fixed reference time makes the complete test dataset reproducible.
    # These timestamps are synthetic fixtures, not live observations.
    now = datetime(2026, 10, 23, 0, 0, tzinfo=timezone.utc)

    observations = []

    for index in range(records):
        location_number = (index % 10) + 1
        hour_offset = index // 10

        observed_at = now - timedelta(hours=hour_offset)

        observation = generate_observation(
            rng=rng,
            location_number=location_number,
            observed_at=observed_at,
        )
        observations.append(observation)

    return observations


def save_jsonl(observations: list[dict], output_path: Path) -> None:
    """Write one JSON observation per line."""

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        for observation in observations:
            file.write(
                json.dumps(observation, allow_nan=False) + "\n"
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic GeoSentinel AI weather data."
    )
    parser.add_argument("--records", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output",
        type=Path,
        default=settings.data_dir / "synthetic"
        / "weather_observations.jsonl",
    )
    args = parser.parse_args()

    observations = generate_dataset(
        records=args.records,
        seed=args.seed,
    )
    save_jsonl(observations, args.output)

    print(f"Generated records: {len(observations)}")
    print("Data origin: synthetic")
    print(f"Output file: {args.output.resolve()}")


if __name__ == "__main__":
    main()
