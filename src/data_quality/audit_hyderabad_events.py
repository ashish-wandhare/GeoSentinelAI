
"""Audit Hyderabad flood-event candidates before ML label selection."""

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "hyderabad_events_for_review.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "hyderabad_events_audit.csv"
)


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    required = [
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
        column for column in required if column not in df.columns
    ]
    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # Parse dates without silently treating invalid dates as valid.
    start_dates = pd.to_datetime(
        df["Start Date"], dayfirst=True, errors="coerce"
    )
    end_dates = pd.to_datetime(
        df["End Date"], dayfirst=True, errors="coerce"
    )

    districts = df["Districts"].fillna("").astype(str).str.strip()
    normalized = districts.str.lower().str.replace(r"\s+", " ", regex=True)

    # A single listed district is more geographically specific,
    # but does not prove that the event was city-level waterlogging.
    df["district_count_listed"] = districts.apply(
        lambda value: (
            len([part for part in value.split(",") if part.strip()])
            if value
            else 0
        )
    )

    df["geographic_scope"] = "multiple_or_unclear_districts"
    df.loc[
        df["district_count_listed"] == 1, "geographic_scope"
    ] = "single_district_listed"
    df.loc[
        df["district_count_listed"] == 0, "geographic_scope"
    ] = "district_missing"

    df["start_date_parsed"] = start_dates
    df["end_date_parsed"] = end_dates
    df["start_date_valid"] = start_dates.notna()
    df["end_date_valid"] = end_dates.notna()
    df["date_order_valid"] = (
        start_dates.notna()
        & end_dates.notna()
        & (end_dates >= start_dates)
    )

    df["coordinates_available"] = False
    df["severity_available"] = (
        df["Severity"].notna()
        & df["Severity"].astype(str).str.strip().ne("")
    )

    df["ml_label_eligible"] = False
    df["audit_note"] = (
        "Manual verification required; not approved as a waterlogging label."
    )

    # Check whether the listed state explicitly names Telangana.
    state_text = df["State"].fillna("").astype(str).str.lower()
    df["telangana_named_in_state"] = state_text.str.contains(
        "telangana", regex=False
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)

    print("Hyderabad Flood-Event Data Quality Audit")
    print("=" * 45)
    print(f"Total records: {len(df)}")
    print("\nGeographic scope:")
    print(df["geographic_scope"].value_counts(dropna=False).to_string())

    print("\nData-quality checks:")
    print(f"Valid start dates: {df['start_date_valid'].sum()}")
    print(f"Valid end dates: {df['end_date_valid'].sum()}")
    print(f"Valid date order: {df['date_order_valid'].sum()}")
    print(f"Records with coordinates: {df['coordinates_available'].sum()}")
    print(f"Records with severity: {df['severity_available'].sum()}")
    print(
        "Records naming Telangana in State: "
        f"{df['telangana_named_in_state'].sum()}"
    )
    print(f"Approved ML labels: {df['ml_label_eligible'].sum()}")

    print(f"\nAudit file saved to:\n{OUTPUT_FILE}")
    print("\nNote: single-district records still require event-level verification.")


if __name__ == "__main__":
    main()
