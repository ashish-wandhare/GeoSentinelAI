
"""Generate a monthly report for rainfall anomaly detection results."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.models.rainfall_anomaly_baseline import FEATURE_COLUMNS


PROJECT_ROOT = Path(__file__).resolve().parents[2]

OUTPUT_DIR = PROJECT_ROOT / "artifacts" / "rainfall_anomaly_baseline"
INPUT_FILE = OUTPUT_DIR / "rainfall_anomaly_results.csv"
SUMMARY_FILE = OUTPUT_DIR / "rainfall_anomaly_report.json"
MONTHLY_FILE = OUTPUT_DIR / "monthly_anomaly_summary.csv"
TOP_ANOMALIES_FILE = OUTPUT_DIR / "top_rainfall_anomalies.csv"


REQUIRED_COLUMNS = [
    "observed_at",
    *FEATURE_COLUMNS,
    "anomaly_score",
    "anomaly_flag",
    "interpretation",
    "waterlogging_confirmed",
]


def load_results(input_file=None):
    """Load and validate rainfall anomaly results."""

    if input_file is None:
        input_file = INPUT_FILE

    input_file = Path(input_file)

    if not input_file.exists():
        raise FileNotFoundError(
            f"Anomaly results file not found: {input_file}. "
            "Run the rainfall anomaly baseline first."
        )

    df = pd.read_csv(input_file)

    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in df.columns
    ]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    if df.empty:
        raise ValueError("Anomaly results file contains no observations.")

    df["observed_at"] = pd.to_datetime(
        df["observed_at"],
        errors="coerce",
        utc=True,
    )

    if df["observed_at"].isna().any():
        raise ValueError(
            "The observed_at column contains invalid timestamps."
        )

    for column in [*FEATURE_COLUMNS, "anomaly_score"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

        if df[column].isna().any():
            raise ValueError(
                f"The {column} column contains missing or non-numeric values."
            )

        if not np.isfinite(df[column].to_numpy(dtype=float)).all():
            raise ValueError(
                f"The {column} column contains non-finite values."
            )

    # Validate anomaly flags before converting them to Boolean values.
    def is_valid_flag(value):
        if isinstance(value, (bool, np.bool_)):
            return True

        if isinstance(value, (int, np.integer, float, np.floating)):
            return value in (0, 1)

        if isinstance(value, str):
            return value.strip().lower() in {
                "true", "false", "1", "0"
            }

        return False

    if not df["anomaly_flag"].map(is_valid_flag).all():
        raise ValueError("Anomaly flags contain invalid values")

    df["anomaly_flag"] = df["anomaly_flag"].map(
        lambda value: (
            value.strip().lower() in {"true", "1"}
            if isinstance(value, str)
            else bool(value)
        )
    )

    # Waterlogging must not be claimed as confirmed without verified labels.
    def is_valid_confirmation(value):
        if isinstance(value, (bool, np.bool_)):
            return True

        if isinstance(value, (int, np.integer, float, np.floating)):
            return value in (0, 1)

        if isinstance(value, str):
            return value.strip().lower() in {
                "true", "false", "1", "0"
            }

        return False

    if not df["waterlogging_confirmed"].map(
        is_valid_confirmation
    ).all():
        raise ValueError(
            "Unexpected waterlogging confirmation: invalid label values."
        )

    confirmed = df["waterlogging_confirmed"].map(
        lambda value: (
            value.strip().lower() in {"true", "1"}
            if isinstance(value, str)
            else bool(value)
        )
    )

    if confirmed.any():
        raise ValueError(
            "Unexpected waterlogging confirmation: this baseline "
            "does not accept confirmed waterlogging labels."
        )

    df["waterlogging_confirmed"] = False
    df["month"] = df["observed_at"].dt.strftime("%Y-%m")

    return df


def build_monthly_summary(df):
    """Summarize rainfall observations and anomalies by month."""

    monthly = (
        df.groupby("month", sort=True)
        .agg(
            observations=("observed_at", "size"),
            anomalies=("anomaly_flag", "sum"),
            mean_hourly_rainfall_mm=("precipitation_mm", "mean"),
            max_hourly_rainfall_mm=("precipitation_mm", "max"),
            max_rolling_24h_rainfall_mm=(
                "rainfall_rolling_24h_mm",
                "max",
            ),
        )
        .reset_index()
    )

    monthly["anomalies"] = monthly["anomalies"].astype(int)
    monthly["anomaly_rate_pct"] = (
        monthly["anomalies"] / monthly["observations"] * 100
    )

    return monthly


def generate_report():
    """Generate the JSON report and monthly/top-anomaly CSV files."""

    # Resolve paths at runtime so pytest monkeypatch overrides are respected.
    input_file = Path(INPUT_FILE)
    output_dir = Path(OUTPUT_DIR)
    report_file = Path(SUMMARY_FILE)
    monthly_file = Path(MONTHLY_FILE)
    top_file = Path(TOP_ANOMALIES_FILE)

    df = load_results(input_file)
    monthly = build_monthly_summary(df)

    rows_analyzed = int(len(df))
    anomaly_count = int(df["anomaly_flag"].sum())
    confirmed_labels = int(df["waterlogging_confirmed"].sum())

    top = (
        df.loc[df["anomaly_flag"]]
        .sort_values("anomaly_score", ascending=True)
        .head(20)
    )

    top_columns = [
        "observed_at",
        *FEATURE_COLUMNS,
        "anomaly_score",
        "interpretation",
    ]

    # Create the output directory before writing any files.
    output_dir.mkdir(parents=True, exist_ok=True)

    monthly.to_csv(monthly_file, index=False)
    top[top_columns].to_csv(top_file, index=False)

    report = {
        "project": "GeoSentinel AI",
        "report_type": "rainfall_anomaly_baseline",
        "dataset": {
            "rows_analyzed": rows_analyzed,
            "anomaly_count": anomaly_count,
            "confirmed_waterlogging_labels": confirmed_labels,
        },
        "observations_analyzed": rows_analyzed,
        "anomalies_detected": anomaly_count,
        "anomaly_rate_pct": round(
            anomaly_count / rows_analyzed * 100, 2
        ),
        "feature_columns": FEATURE_COLUMNS,
        "model_interpretation": (
            "Detected observations represent unusual rainfall patterns. "
            "They are not confirmed waterlogging or flood events."
        ),
        "anomaly_threshold_note": (
            "The Isolation Forest contamination parameter controls the "
            "expected proportion of anomalies. It is not a flood "
            "incidence rate or a validated waterlogging threshold."
        ),
        "waterlogging_confirmed": False,
        "monthly_summary": monthly.to_dict(orient="records"),
        "artifacts": {
            "monthly_summary_csv": str(monthly_file),
            "top_anomalies_csv": str(top_file),
        },
    }

    with report_file.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, default=str)

    print("Rainfall Anomaly Report")
    print("=======================")
    print(f"Observations analyzed: {rows_analyzed}")
    print(f"Anomalies detected: {anomaly_count}")
    print(
        f"Anomaly rate: {anomaly_count / rows_analyzed * 100:.2f}%"
    )
    print("\nMonthly summary:")
    print(monthly.to_string(index=False))
    print("\nReport artifacts:")
    print(f"- {report_file}")
    print(f"- {monthly_file}")
    print(f"- {top_file}")

    return report


def main():
    """Run the rainfall anomaly report."""

    generate_report()


if __name__ == "__main__":
    main()
