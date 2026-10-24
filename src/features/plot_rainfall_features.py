
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

INPUT_FILE = Path("data/processed/hyderabad_rainfall_features.jsonl")
OUTPUT_DIR = Path("artifacts/rainfall_analysis")


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(
        description="Plot GeoSentinel AI rainfall features."
    )
    parser.add_argument("--input", type=Path, default=INPUT_FILE)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)

    # Use normal command-line arguments when run as a script.
    # Use an empty argument list when called directly by tests.
    args = parser.parse_args(
        argv if argv is not None else []
    )

    if not args.input.exists():
        raise FileNotFoundError(f"Input file not found: {args.input}")

    df = pd.read_json(args.input, lines=True)

    if df.empty:
        raise ValueError("The input feature dataset is empty.")

    required_columns = [
        "observed_at",
        "precipitation_mm",
        "rainfall_rolling_3h_mm",
        "rainfall_rolling_6h_mm",
        "rainfall_rolling_24h_mm",
    ]
    missing_columns = set(required_columns) - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    df["observed_at"] = pd.to_datetime(
        df["observed_at"], utc=True
    )
    df = df.sort_values("observed_at")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Chart 1: Hourly precipitation
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(
        df["observed_at"],
        df["precipitation_mm"],
        width=0.03,
    )
    ax.set_title(
        "Hourly Precipitation - Hyderabad Reference Location"
    )
    ax.set_xlabel("Observation time (UTC)")
    ax.set_ylabel("Precipitation (mm)")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(
        args.output_dir / "hourly_precipitation.png",
        dpi=150,
    )
    plt.close(fig)

    # Chart 2: Rolling rainfall features
    fig, ax = plt.subplots(figsize=(12, 5))

    columns = {
        "rainfall_rolling_3h_mm": "Rolling 3-hour rainfall",
        "rainfall_rolling_6h_mm": "Rolling 6-hour rainfall",
        "rainfall_rolling_24h_mm": "Rolling 24-hour rainfall",
    }

    for column, label in columns.items():
        ax.plot(df["observed_at"], df[column], label=label)

    ax.set_title(
        "Rolling Rainfall Features - Hyderabad Reference Location"
    )
    ax.set_xlabel("Observation time (UTC)")
    ax.set_ylabel("Accumulated rainfall (mm)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(
        args.output_dir / "rolling_rainfall_features.png",
        dpi=150,
    )
    plt.close(fig)

    print(f"Input: {args.input.resolve()}")
    print(f"Observations plotted: {len(df)}")
    print(f"Charts saved to: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
