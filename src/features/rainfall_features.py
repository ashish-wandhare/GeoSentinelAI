
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import settings
from src.data_quality.schemas import WeatherObservation


INPUT_FILE = settings.data_dir / "raw" / "hyderabad_weather.jsonl"
OUTPUT_FILE = settings.data_dir / "processed" / "hyderabad_rainfall_features.jsonl"

ROLLING_WINDOWS = (3, 6, 24)


def load_observations(input_path: Path) -> pd.DataFrame:
    """Load and validate the saved weather observations."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    records = []

    with input_path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                raw = json.loads(line)
                observation = WeatherObservation.model_validate(raw)
                records.append(observation.model_dump(mode="json"))
            except Exception as exc:
                raise ValueError(
                    f"Invalid observation at line {line_number}: {exc}"
                ) from exc

    if not records:
        raise ValueError("No weather observations found.")

    df = pd.DataFrame(records)
    df["observed_at"] = pd.to_datetime(df["observed_at"], utc=True)

    if df.duplicated(["location_id", "observed_at"]).any():
        raise ValueError("Duplicate timestamps found for a location.")

    # These features assume hourly observations.
    if (
        (df["observed_at"].dt.minute != 0).any()
        or (df["observed_at"].dt.second != 0).any()
        or (df["observed_at"].dt.microsecond != 0).any()
    ):
        raise ValueError("Expected observations aligned to whole hours.")

    return df.sort_values(["location_id", "observed_at"]).reset_index(drop=True)


def build_features(observations: pd.DataFrame) -> pd.DataFrame:
    """Create hourly rainfall and time-based features without filling gaps."""
    if observations.empty:
        raise ValueError("Cannot build features from an empty dataset.")

    result_frames = []

    for location_id, group in observations.groupby("location_id", sort=True):
        group = group.sort_values("observed_at").copy()

        # A location ID must consistently identify one reference point.
        if group["latitude"].nunique() != 1 or group["longitude"].nunique() != 1:
            raise ValueError(
                f"Location {location_id!r} has inconsistent coordinates."
            )

        start = group["observed_at"].min()
        end = group["observed_at"].max()
        full_index = pd.date_range(start=start, end=end, freq="h")

        indexed = group.set_index("observed_at")
        hourly = indexed.reindex(full_index)
        hourly.index.name = "observed_at"

        # Reindexing inserts NaN for absent hours; missing rainfall is not zero.
        hourly["location_id"] = location_id
        hourly["latitude"] = group["latitude"].iloc[0]
        hourly["longitude"] = group["longitude"].iloc[0]
        hourly["source_id"] = group["source_id"].iloc[0]
        hourly["data_origin"] = group["data_origin"].iloc[0]

        rainfall = pd.to_numeric(
            hourly["precipitation_mm"], errors="raise"
        ).astype(float)

        if (rainfall.dropna() < 0).any():
            raise ValueError("Rainfall cannot be negative.")

        if not np.isfinite(rainfall.dropna()).all():
            raise ValueError("Rainfall contains non-finite values.")

        hourly["observation_present"] = hourly.index.isin(
            indexed.index
        )
        hourly["precipitation_mm"] = rainfall

        # Each window includes the current hour and requires every hour
        # in the window to have a valid precipitation value.
        for window in ROLLING_WINDOWS:
            hourly[f"rainfall_rolling_{window}h_mm"] = (
                rainfall.rolling(window=window, min_periods=window).sum()
            )

        hourly["hour_of_day"] = hourly.index.hour
        hourly["day_of_week"] = hourly.index.day_of_week
        hourly["month"] = hourly.index.month
        hourly["is_weekend"] = hourly.index.day_of_week >= 5
        result_frames.append(hourly.reset_index())

    result = pd.concat(result_frames, ignore_index=True)
    return result.sort_values(
        ["location_id", "observed_at"]
    ).reset_index(drop=True)


def save_features(features: pd.DataFrame, output_path: Path) -> None:
    """Save features as JSONL; unavailable rolling values become JSON null."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    export = features.copy()
    export["observed_at"] = pd.to_datetime(
        export["observed_at"], utc=True
    ).map(lambda value: value.isoformat().replace("+00:00", "Z"))

    export = export.astype(object).where(pd.notna(export), None)

    with output_path.open("w", encoding="utf-8") as file:
        for record in export.to_dict(orient="records"):
            file.write(json.dumps(record, allow_nan=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build hourly rainfall features for GeoSentinel AI."
    )
    parser.add_argument("--input", type=Path, default=INPUT_FILE)
    parser.add_argument("--output", type=Path, default=OUTPUT_FILE)
    args = parser.parse_args()

    observations = load_observations(args.input)
    features = build_features(observations)
    save_features(features, args.output)

    print(f"Input observations: {len(observations)}")
    print(f"Feature rows: {len(features)}")
    print(f"Locations: {features['location_id'].nunique()}")
    print(f"Output: {args.output.resolve()}")
    print("\nMissing feature values:")
    print(
        features[
            [
                "precipitation_mm",
                "rainfall_rolling_3h_mm",
                "rainfall_rolling_6h_mm",
                "rainfall_rolling_24h_mm",
            ]
        ].isna().sum().to_string()
    )


if __name__ == "__main__":
    main()
