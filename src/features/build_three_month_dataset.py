
from pathlib import Path

import pandas as pd

from src.features.rainfall_features import (
    build_features,
    load_observations,
    save_features,
)


INPUT_FILES = [
    Path("data/raw/hyderabad_weather_june_2025.jsonl"),
    Path("data/raw/hyderabad_weather_july_2025.jsonl"),
    Path("data/raw/hyderabad_weather_august_2025.jsonl"),
]

OUTPUT_FILE = Path(
    "data/processed/hyderabad_rainfall_features_june_august_2025.jsonl"
)


def main() -> None:
    monthly_frames = []

    for input_file in INPUT_FILES:
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")

        observations = load_observations(input_file)
        monthly_frames.append(observations)

        print(f"Loaded {len(observations)} observations: {input_file.name}")

    combined = pd.concat(monthly_frames, ignore_index=True)
    combined = combined.sort_values(
        ["location_id", "observed_at"]
    ).reset_index(drop=True)

    if combined.duplicated(["location_id", "observed_at"]).any():
        raise ValueError("Duplicate timestamps found across monthly files.")

    # Recalculate rolling windows over the continuous timeline.
    # This allows rolling features to use preceding-month observations.
    features = build_features(combined)

    save_features(features, OUTPUT_FILE)

    print("\nCOMBINED DATASET")
    print(f"Input observations: {len(combined)}")
    print(f"Feature rows: {len(features)}")
    print(f"Locations: {features['location_id'].nunique()}")
    print(f"Start: {features['observed_at'].min()}")
    print(f"End: {features['observed_at'].max()}")
    print(f"Output: {OUTPUT_FILE.resolve()}")
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
