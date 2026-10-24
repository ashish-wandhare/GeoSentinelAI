
"""Check evidence-register IDs and dates against the review queue."""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "processed"

QUEUE_FILE = DATA_DIR / "hyderabad_manual_verification_queue.csv"
REGISTER_FILE = DATA_DIR / "hyderabad_event_evidence_register.csv"


def main() -> None:
    for path in (QUEUE_FILE, REGISTER_FILE):
        if not path.exists():
            raise FileNotFoundError(f"Required file not found: {path}")

    queue = pd.read_csv(QUEUE_FILE, dtype={"UEI": str})
    register = pd.read_csv(REGISTER_FILE, dtype={"UEI": str})

    required_queue = {"UEI", "Start Date"}
    required_register = {
        "UEI",
        "candidate_event_date",
        "source_url",
        "verification_status",
        "approved_for_ml",
    }

    if not required_queue.issubset(queue.columns):
        raise ValueError("Review queue is missing required columns.")

    if not required_register.issubset(register.columns):
        raise ValueError("Evidence register is missing required columns.")

    if register["UEI"].duplicated().any():
        raise ValueError("Duplicate UEI values found in evidence register.")

    queue_dates = queue[["UEI", "Start Date"]].copy()
    queue_dates["inventory_date"] = pd.to_datetime(
        queue_dates["Start Date"], dayfirst=True, errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    merged = register.merge(
        queue_dates[["UEI", "inventory_date"]],
        on="UEI",
        how="left",
        validate="one_to_one",
        indicator=True,
    )

    merged["candidate_event_date"] = pd.to_datetime(
        merged["candidate_event_date"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    merged["candidate_date_matches_inventory"] = (
        merged["candidate_event_date"] == merged["inventory_date"]
    )

    merged["source_url_present"] = (
        merged["source_url"].fillna("").str.startswith(("https://", "http://"))
    )

    merged["approved_for_ml"] = (
        merged["approved_for_ml"]
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(["true", "1", "yes"])
    )

    print("Evidence Register Consistency Check")
    print("=" * 40)
    print(f"Register entries: {len(merged)}")
    print(f"Candidate IDs found in queue: {(merged['_merge'] == 'both').sum()}")
    print(f"Valid-looking source URLs: {merged['source_url_present'].sum()}")
    print(
        "Candidate dates matching inventory dates: "
        f"{merged['candidate_date_matches_inventory'].sum()}"
    )
    print(f"Approved ML labels: {merged['approved_for_ml'].sum()}")

    print("\nRecord-level checks:")
    print(
        merged[
            [
                "UEI",
                "candidate_event_date",
                "inventory_date",
                "candidate_date_matches_inventory",
                "source_url_present",
                "verification_status",
            ]
        ].to_string(index=False)
    )

    print("\nNote: matching dates do not prove that an article verifies an event.")
    print("Review article dates, event dates, locations, and source contents manually.")


if __name__ == "__main__":
    main()
