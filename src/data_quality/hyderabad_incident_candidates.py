
from pathlib import Path

import pandas as pd


INPUT_FILE = Path("data/raw/India_Flood_Inventory_v3.csv")
OUTPUT_FILE = Path(
    "data/processed/hyderabad_incident_candidates.csv"
)


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE, low_memory=False)

    required = [
        "UEI",
        "Start Date",
        "End Date",
        "Main Cause",
        "Districts",
        "State",
        "Latitude",
        "Longitude",
        "Severity",
        "Event Source",
    ]

    missing = set(required) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    district_text = df["Districts"].fillna("").astype(str)
    state_text = df["State"].fillna("").astype(str)

    # Match Hyderabad as a whole word to avoid unrelated substring matches.
    hyderabad_match = district_text.str.contains(
        r"\bhyderabad\b", case=False, regex=True
    )

    telangana_match = state_text.str.contains(
        r"\btelangana\b", case=False, regex=True
    )

    candidates = df.loc[
        hyderabad_match | telangana_match, required
    ].copy()

    candidates["candidate_reason"] = [
        (
            "Hyderabad mentioned in district field"
            if hyderabad
            else "Telangana mentioned in state field"
        )
        for hyderabad, telangana in zip(
            hyderabad_match.loc[candidates.index],
            telangana_match.loc[candidates.index],
        )
    ]

    candidates["review_status"] = "needs_manual_geographic_review"
    candidates["street_level_location_verified"] = False

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    candidates.to_csv(OUTPUT_FILE, index=False)

    print(f"Source records: {len(df)}")
    print(f"Candidate records exported: {len(candidates)}")
    print(
        "Candidates with coordinates:",
        int(candidates[["Latitude", "Longitude"]].notna().all(axis=1).sum()),
    )
    print(
        "Candidates with severity:",
        int(candidates["Severity"].notna().sum()),
    )
    print(f"Output: {OUTPUT_FILE.resolve()}")
    print("Status: candidates only; not verified incident labels")


if __name__ == "__main__":
    main()
