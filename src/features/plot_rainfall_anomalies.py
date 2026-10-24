
"""Visualize rainfall anomalies detected by GeoSentinel AI."""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_RESULTS_FILE = (
    PROJECT_ROOT
    / "artifacts"
    / "rainfall_anomaly_baseline"
    / "rainfall_anomaly_results.csv"
)

DEFAULT_OUTPUT_DIR = (
    PROJECT_ROOT
    / "artifacts"
    / "rainfall_anomaly_baseline"
    / "plots"
)


REQUIRED_COLUMNS = [
    "observed_at",
    "precipitation_mm",
    "rainfall_rolling_3h_mm",
    "rainfall_rolling_6h_mm",
    "rainfall_rolling_24h_mm",
    "anomaly_flag",
    "anomaly_score",
]


def load_results(input_file: Path) -> pd.DataFrame:
    """Load and validate anomaly results."""

    if not input_file.exists():
        raise FileNotFoundError(
            f"Anomaly results file not found: {input_file}"
        )

    df = pd.read_csv(input_file)

    if df.empty:
        raise ValueError("The anomaly results dataset is empty.")

    missing_columns = sorted(set(REQUIRED_COLUMNS) - set(df.columns))
    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    df["observed_at"] = pd.to_datetime(
        df["observed_at"],
        errors="coerce",
        utc=True,
    )

    if df["observed_at"].isna().any():
        raise ValueError("Invalid timestamps found in observed_at.")

    numeric_columns = [
        "precipitation_mm",
        "rainfall_rolling_3h_mm",
        "rainfall_rolling_6h_mm",
        "rainfall_rolling_24h_mm",
        "anomaly_score",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

        if df[column].isna().any():
            raise ValueError(
                f"Missing or invalid numeric values in {column}."
            )

    def parse_flag(value):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)) and value in (0, 1):
            return bool(value)
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "1"}:
                return True
            if normalized in {"false", "0"}:
                return False
        raise ValueError(f"Invalid anomaly flag: {value!r}")

    df["anomaly_flag"] = df["anomaly_flag"].map(parse_flag)
    df = df.sort_values("observed_at").reset_index(drop=True)

    return df


def plot_rainfall_anomalies(
    df: pd.DataFrame,
    output_dir: Path,
) -> None:
    """Generate rainfall anomaly charts."""

    output_dir.mkdir(parents=True, exist_ok=True)

    anomalies = df.loc[df["anomaly_flag"]]

    # Chart 1: Hourly rainfall with detected anomalies.
    fig, ax = plt.subplots(figsize=(14, 6))

    ax.plot(
        df["observed_at"],
        df["precipitation_mm"],
        label="Hourly rainfall",
        linewidth=0.8,
    )

    ax.scatter(
        anomalies["observed_at"],
        anomalies["precipitation_mm"],
        label="Detected anomaly",
        marker="x",
        s=35,
    )

    ax.set_title(
        "Rainfall Anomaly Detection — Hyderabad Reference Location"
    )
    ax.set_xlabel("Observation time (UTC)")
    ax.set_ylabel("Hourly rainfall (mm)")
    ax.legend()
    ax.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(
        output_dir / "rainfall_anomalies_timeseries.png",
        dpi=150,
    )
    plt.close(fig)

    # Chart 2: Rolling rainfall with anomaly observations highlighted.
    fig, ax = plt.subplots(figsize=(14, 6))

    rolling_columns = {
        "rainfall_rolling_3h_mm": "Rolling 3-hour rainfall",
        "rainfall_rolling_6h_mm": "Rolling 6-hour rainfall",
        "rainfall_rolling_24h_mm": "Rolling 24-hour rainfall",
    }

    for column, label in rolling_columns.items():
        ax.plot(df["observed_at"], df[column], label=label)

    ax.scatter(
        anomalies["observed_at"],
        anomalies["rainfall_rolling_24h_mm"],
        label="Detected anomaly",
        marker="x",
        s=30,
    )

    ax.set_title("Rolling Rainfall Trends and Detected Anomalies")
    ax.set_xlabel("Observation time (UTC)")
    ax.set_ylabel("Accumulated rainfall (mm)")
    ax.legend()
    ax.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(
        output_dir / "rolling_rainfall_anomalies.png",
        dpi=150,
    )
    plt.close(fig)

    # Chart 3: Monthly anomaly counts.
    monthly = df.assign(
        month=df["observed_at"].dt.strftime("%Y-%m")
    ).groupby("month", sort=True).agg(
        observations=("anomaly_flag", "size"),
        anomalies=("anomaly_flag", "sum"),
    )

    monthly["anomalies"] = monthly["anomalies"].astype(int)

    fig, ax = plt.subplots(figsize=(9, 5))

    monthly["anomalies"].plot(
        kind="bar",
        ax=ax,
    )

    ax.set_title("Monthly Rainfall Anomaly Counts")
    ax.set_xlabel("Month")
    ax.set_ylabel("Detected anomalies")
    ax.tick_params(axis="x", rotation=0)
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(
        output_dir / "monthly_anomaly_counts.png",
        dpi=150,
    )
    plt.close(fig)

    # Save the monthly counts used in the chart.
    monthly.reset_index().to_csv(
        output_dir / "monthly_anomaly_counts.csv",
        index=False,
    )

    print("GeoSentinel AI Rainfall Anomaly Visualizations")
    print("===============================================")
    print(f"Observations: {len(df)}")
    print(f"Detected anomalies: {len(anomalies)}")
    print(f"Output directory: {output_dir.resolve()}")
    print("Generated files:")
    print("- rainfall_anomalies_timeseries.png")
    print("- rolling_rainfall_anomalies.png")
    print("- monthly_anomaly_counts.png")
    print("- monthly_anomaly_counts.csv")


def main() -> None:
    """Run the visualization pipeline."""

    parser = argparse.ArgumentParser(
        description="Plot GeoSentinel AI rainfall anomalies."
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_RESULTS_FILE,
        help="Path to the rainfall anomaly results CSV.",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where visualizations will be saved.",
    )

    args = parser.parse_args()

    df = load_results(args.input)
    plot_rainfall_anomalies(df, args.output_dir)


if __name__ == "__main__":
    main()
