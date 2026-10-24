
from pathlib import Path

import pandas as pd


FILES = {
    "June": Path("data/processed/hyderabad_rainfall_features_june_2025.jsonl"),
    "July": Path("data/processed/hyderabad_rainfall_features_july_2025.jsonl"),
    "August": Path("data/processed/hyderabad_rainfall_features_august_2025.jsonl"),
}


def main() -> None:
    total_rows = 0

    print("MONTHLY RAINFALL VALIDATION")
    print("-" * 75)

    for month, path in FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"Missing dataset: {path}")

        df = pd.read_json(path, lines=True)
        df["observed_at"] = pd.to_datetime(df["observed_at"], utc=True)

        duplicates = int(
            df.duplicated(["location_id", "observed_at"]).sum()
        )
        missing_rainfall = int(df["precipitation_mm"].isna().sum())
        unique_timestamps = int(df["observed_at"].nunique())
        origins = sorted(df["data_origin"].dropna().unique().tolist())

        print(f"{month}:")
        print(f"  Rows: {len(df)}")
        print(f"  Unique timestamps: {unique_timestamps}")
        print(f"  Missing hourly rainfall: {missing_rainfall}")
        print(f"  Duplicate location/timestamps: {duplicates}")
        print(f"  Data origins: {origins}")

        if duplicates or missing_rainfall or len(df) != unique_timestamps:
            raise ValueError(f"{month} dataset failed validation.")

        if origins != ["real"]:
            raise ValueError(f"{month} has unexpected data origins.")

        total_rows += len(df)

    print("-" * 75)
    print(f"TOTAL ROWS: {total_rows}")
    print("VALIDATION: PASSED" if total_rows == 2208 else "CHECK TOTAL ROWS")


if __name__ == "__main__":
    main()
