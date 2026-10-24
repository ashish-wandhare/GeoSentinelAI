
"""Build a review-ready evidence register for Hyderabad flood candidates.

Sources are research leads only. No event is automatically verified
or approved for ML training.
"""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "processed"

QUEUE_FILE = DATA_DIR / "hyderabad_manual_verification_queue.csv"
OUTPUT_FILE = DATA_DIR / "hyderabad_event_evidence_register.csv"


EVIDENCE = [
    {
        "UEI": "UEI-IMD-FL-2021-0286",
        "candidate_event_date": "2021-10-08",
        "source_title": (
            "Heavy rain lashes Hyderabad inundating several areas"
        ),
        "source_url": (
            "https://indianexpress.com/article/cities/hyderabad/"
            "shops-restaurants-inundated-traffic-at-standstill-as-"
            "heavy-rains-lash-hyderabad-7562081/"
        ),
        "evidence_assessment": "date_aligned_candidate",
        "verification_status": "pending_manual_review",
        "notes": "Confirm actual event date, locations, and event type.",
    },
    {
        "UEI": "UEI-IMD-FL-2022-0840",
        "candidate_event_date": "2022-06-16",
        "source_title": (
            "Flooding and waterlogging in Hyderabad spotlight "
            "misplaced priorities in urban development"
        ),
        "source_url": (
            "https://indianexpress.com/article/cities/hyderabad/"
            "hyderabad-flooding-waterlogging-spotlight-misplaced-"
            "priorities-urban-development-7973890/"
        ),
        "evidence_assessment": "date_aligned_candidate",
        "verification_status": "pending_manual_review",
        "notes": "Confirm that the article supports this specific event.",
    },
    {
        "UEI": "UEI-IMD-FL-2022-0931",
        "candidate_event_date": "2022-09-01",
        "source_title": (
            "Water-logging in multiple parts of Hyderabad, "
            "IMD predicts heavy rains till Sep 10"
        ),
        "source_url": (
            "https://www.indiatoday.in/cities/hyderabad/story/"
            "water-logging-multiple-parts-hyderabad-imd-predicts-"
            "heavy-rains-september-videos-1997104-2022-09-06"
        ),
        "evidence_assessment": "nearby_period_only",
        "verification_status": "not_verified_for_candidate_date",
        "notes": (
            "The report concerns a nearby date. It does not establish "
            "that waterlogging occurred on September 1."
        ),
    },
    {
        "UEI": "UEI-IMD-FL-2022-0929",
        "candidate_event_date": "2022-09-27",
        "source_title": (
            "Hyderabad: Sudden downpour wreaks havoc, "
            "traffic goes haywire"
        ),
        "source_url": (
            "https://indianexpress.com/article/cities/hyderabad/"
            "hyderabad-sudden-downpour-wreaks-havoc-traffic-goes-haywire-8175091/"
        ),
        "evidence_assessment": "date_requires_confirmation",
        "verification_status": "pending_manual_review",
        "notes": (
            "Check the actual event date against the article's "
            "publication date and inventory record."
        ),
    },
]


def main() -> None:
    if not QUEUE_FILE.exists():
        raise FileNotFoundError(
            f"Verification queue not found: {QUEUE_FILE}"
        )

    queue = pd.read_csv(QUEUE_FILE, dtype={"UEI": str})

    if "UEI" not in queue.columns:
        raise ValueError("Verification queue must contain a UEI column.")

    evidence_df = pd.DataFrame(EVIDENCE)

    if evidence_df["UEI"].duplicated().any():
        raise ValueError("Duplicate UEI values found in evidence entries.")

    queue_ids = set(queue["UEI"].dropna().astype(str))
    unknown_ids = sorted(set(evidence_df["UEI"]) - queue_ids)

    if unknown_ids:
        raise ValueError(
            f"Evidence IDs not found in verification queue: {unknown_ids}"
        )

    # Manual review fields: intentionally blank or pending by default.
    evidence_df["source_confirms_event"] = "pending"
    evidence_df["actual_event_date"] = ""
    evidence_df["geographic_match"] = "not_reviewed"
    evidence_df["event_type"] = "not_reviewed"
    evidence_df["evidence_quality"] = "not_reviewed"
    evidence_df["reviewer_notes"] = ""
    evidence_df["final_decision"] = "needs_more_evidence"
    evidence_df["approved_for_ml"] = False

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    evidence_df.to_csv(OUTPUT_FILE, index=False)

    print("Hyderabad Event Evidence Register")
    print("=" * 38)
    print(f"Evidence entries: {len(evidence_df)}")
    print(
        "Unique candidate IDs: "
        f"{evidence_df['UEI'].nunique()}"
    )
    print(
        "Source URLs present: "
        f"{evidence_df['source_url'].fillna('').str.startswith('https://').sum()}"
    )
    print(
        "Pending source confirmation: "
        f"{evidence_df['source_confirms_event'].eq('pending').sum()}"
    )
    print(
        "Awaiting final decision: "
        f"{evidence_df['final_decision'].eq('needs_more_evidence').sum()}"
    )
    print(f"Approved ML labels: {evidence_df['approved_for_ml'].sum()}")
    print(f"\nSaved to:\n{OUTPUT_FILE}")
    print(
        "\nReview each source manually. Do not approve a label solely "
        "because a candidate date matches an inventory date."
    )


if __name__ == "__main__":
    main()
