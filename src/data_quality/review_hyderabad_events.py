
"""Prepare Hyderabad-mentioned flood inventory candidates for manual review."""

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "hyderabad_incident_candidates.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "hyderabad_events_for_review.csv"
)


def main() -> None:
    """Export inventory candidates that explicitly mention Hyderabad."""

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Candidate file not found: {INPUT_FILE}\n"
            "Run hyderabad_incident_candidates.py first."
        )

    df = pd.read_csv(INPUT_FILE)

    required_columns = [
        "UEI",
        "Start Date",
        "End Date",
        "Main Cause",
        "Districts",
        "State",
        "Severity",
        "Event Source",
    ]

    missing_columns = [
        column for column in required_columns if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Required columns missing from candidate file: {missing_columns}"
        )

    # Match Hyderabad in the district field, ignoring case and missing values.
    mask = df["Districts"].astype("string").str.contains(
        r"\bHyderabad\b",
        case=False,
        na=False,
        regex=True,
    )

    review = df.loc[mask, required_columns].copy()

    # Add explicit review fields; do not imply these events are verified.
    review["street_level_location_verified"] = False
    review["review_status"] = "needs_manual_geographic_review"

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    review.to_csv(OUTPUT_FILE, index=False)

    print("Hyderabad Event Review Export")
    print("-" * 40)
    print(f"Input candidate records: {len(df)}")
    print(f"Records mentioning Hyderabad in Districts: {len(review)}")
    print(f"Output: {OUTPUT_FILE}")
    print()
    print("Important:")
    print("- These records are candidates, not verified city waterlogging events.")
    print("- Check dates, locations, causes, and sources manually.")
    print("- Do not use them as confirmed ML labels without validation.")


if __name__ == "__main__":
    main()
