
"""Prepare a manual verification queue for Hyderabad flood-event candidates."""

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "hyderabad_events_audit.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "hyderabad_manual_verification_queue.csv"
)


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Audit file not found: {INPUT_FILE}\n"
            "Run audit_hyderabad_events.py first."
        )

    df = pd.read_csv(INPUT_FILE)

    required_columns = [
        "UEI",
        "Start Date",
        "End Date",
        "Main Cause",
        "Districts",
        "State",
        "Event Source",
        "geographic_scope",
    ]

    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise ValueError(f"Required columns missing: {missing}")

    # Only prioritize records listing one district.
    districts = df["Districts"].fillna("").astype(str).str.strip()

# Only include records whose district field is exactly Hyderabad.
# Exclude broad descriptions such as "Hyderabad & Parts of Telangana".
    exact_hyderabad = districts.str.fullmatch(
    r"Hyderabad\s*,?",
    case=False,
    na=False,
)

    queue = df.loc[
    df["geographic_scope"].eq("single_district_listed")
    & exact_hyderabad,
    required_columns,
    ].copy()

    # These fields must be completed through independent verification.
    queue["verification_status"] = "pending"
    queue["verified_location"] = ""
    queue["evidence_url"] = ""
    queue["waterlogging_relevance"] = "not_assessed"
    queue["verified_event_date"] = ""
    queue["reviewer_notes"] = ""
    queue["approved_for_ml"] = False

    queue["review_guidance"] = (
        "Verify event date, Hyderabad geographic scope, "
        "and evidence of urban waterlogging before approval."
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    queue.to_csv(OUTPUT_FILE, index=False)

    print("Hyderabad Manual Verification Queue")
    print("=" * 42)
    print(f"Audit records: {len(df)}")
    print(f"Records queued for review: {len(queue)}")
    print(f"Pending verification: {queue['verification_status'].eq('pending').sum()}")
    print(f"Approved for ML: {queue['approved_for_ml'].sum()}")
    print(f"\nOutput saved to:\n{OUTPUT_FILE}")

    if not queue.empty:
        print("\nReview queue preview:")
        print(
            queue[
                ["UEI", "Start Date", "Main Cause", "Districts", "State"]
            ].to_string(index=False)
        )

    print(
        "\nReminder: a single listed district is not proof of "
        "street-level waterlogging."
    )


if __name__ == "__main__":
    main()
