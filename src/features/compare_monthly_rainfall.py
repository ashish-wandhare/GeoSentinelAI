
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


FILES = {
    "June 2025": Path(
        "data/processed/hyderabad_rainfall_features_june_2025.jsonl"
    ),
    "July 2025": Path(
        "data/processed/hyderabad_rainfall_features_july_2025.jsonl"
    ),
    "August 2025": Path(
        "data/processed/hyderabad_rainfall_features_august_2025.jsonl"
    ),
}

OUTPUT_DIR = Path("artifacts/rainfall_analysis/three_month_comparison")


def main() -> None:
    monthly_stats = []

    for month, path in FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"Missing feature file: {path}")

        df = pd.read_json(path, lines=True)
        df["observed_at"] = pd.to_datetime(
            df["observed_at"], utc=True
        )

        if df["precipitation_mm"].isna().any():
            raise ValueError(f"Missing rainfall values in {month}")

        monthly_stats.append(
            {
                "month": month,
                "observations": len(df),
                "total_rainfall_mm": df["precipitation_mm"].sum(),
                "wet_hours": (df["precipitation_mm"] > 0).sum(),
                "maximum_hourly_mm": df["precipitation_mm"].max(),
                "maximum_rolling_24h_mm": (
                    df["rainfall_rolling_24h_mm"].max()
                ),
            }
        )

    summary = pd.DataFrame(monthly_stats).round(2)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    summary.to_csv(
        OUTPUT_DIR / "monthly_rainfall_comparison.csv",
        index=False,
    )

    print("MONTHLY RAINFALL COMPARISON")
    print(summary.to_string(index=False))

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(summary["month"], summary["total_rainfall_mm"])
    ax.set_title("Monthly Rainfall - Hyderabad Reference Location")
    ax.set_xlabel("Month")
    ax.set_ylabel("Total rainfall (mm)")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "monthly_rainfall_comparison.png", dpi=150)
    plt.close(fig)

    print(f"\nComparison files saved to: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
