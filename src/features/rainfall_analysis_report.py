
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


INPUT_FILE = Path(
    "data/processed/hyderabad_rainfall_features_june_2025.jsonl"
)
OUTPUT_FILE = Path(
    "data/processed/hyderabad_rainfall_analysis_june_2025.json"
)


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    df = pd.read_json(INPUT_FILE, lines=True)

    if df.empty:
        raise ValueError("Rainfall feature dataset is empty.")

    required_columns = [
        "observed_at",
        "precipitation_mm",
        "rainfall_rolling_3h_mm",
        "rainfall_rolling_6h_mm",
        "rainfall_rolling_24h_mm",
        "data_origin",
    ]

    missing = set(required_columns) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df["observed_at"] = pd.to_datetime(df["observed_at"], utc=True)
    df = df.sort_values("observed_at").copy()

    rainfall = pd.to_numeric(df["precipitation_mm"], errors="raise")

    if rainfall.isna().any() or (rainfall < 0).any():
        raise ValueError("Hourly rainfall contains missing or negative values.")

    if not rainfall.map(lambda value: float(value) < float("inf")).all():
        raise ValueError("Hourly rainfall contains non-finite values.")

    df["date"] = df["observed_at"].dt.strftime("%Y-%m-%d")

    daily_totals = (
        df.groupby("date")["precipitation_mm"]
        .sum()
        .sort_values(ascending=False)
    )

    thresholds = {}
    for threshold in (1, 2, 5):
        thresholds[f"at_least_{threshold}_mm"] = int(
            (rainfall >= threshold).sum()
        )

    rolling_columns = [
        "rainfall_rolling_3h_mm",
        "rainfall_rolling_6h_mm",
        "rainfall_rolling_24h_mm",
    ]

    report = {
        "project": "GeoSentinel AI",
        "report_type": "historical_rainfall_exploratory_analysis",
        "period": {
            "start_utc": df["observed_at"].min().isoformat(),
            "end_utc": df["observed_at"].max().isoformat(),
            "unique_timestamps": int(df["observed_at"].nunique()),
            "locations": int(df["location_id"].nunique()),
        },
        "data_quality": {
            "rows": int(len(df)),
            "missing_hourly_rainfall": int(rainfall.isna().sum()),
            "duplicate_location_timestamps": int(
                df.duplicated(["location_id", "observed_at"]).sum()
            ),
            "data_origins": {
                str(key): int(value)
                for key, value in df["data_origin"].value_counts().items()
            },
        },
        "rainfall_statistics": {
            "total_mm": round(float(rainfall.sum()), 2),
            "maximum_hourly_mm": round(float(rainfall.max()), 2),
            "hours_with_rainfall": int((rainfall > 0).sum()),
            "hours_at_or_above_thresholds": thresholds,
            "maximum_rolling_accumulation_mm": {
                column: round(float(df[column].max()), 2)
                for column in rolling_columns
            },
        },
        "top_10_wettest_days_mm": [
            {
                "date": str(date),
                "rainfall_mm": round(float(total), 2),
            }
            for date, total in daily_totals.head(10).items()
        ],
        "limitations": [
            "This dataset represents one Hyderabad reference location.",
            "The analysis covers June 2025 only.",
            "Rainfall measurements do not establish that waterlogging occurred.",
            "No supervised waterlogging prediction accuracy is claimed.",
            "Mapped flooding locations are not timestamped incident labels.",
        ],
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, allow_nan=False)

    print(f"Report saved: {OUTPUT_FILE.resolve()}")
    print(f"Observations analyzed: {len(df)}")
    print(f"Monthly rainfall: {report['rainfall_statistics']['total_mm']} mm")
    print(f"Wettest day: {report['top_10_wettest_days_mm'][0]}")
    print("Data quality: checked")
    print("Waterlogging prediction accuracy: not evaluated")


if __name__ == "__main__":
    main()
