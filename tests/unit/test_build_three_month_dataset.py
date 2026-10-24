
import pandas as pd
import pytest
from src.features.build_three_month_dataset import main


def test_build_three_month_dataset(monkeypatch, tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    timestamps = pd.date_range(
        "2025-06-30 22:00:00",
        periods=4,
        freq="h",
        tz="UTC",
    )

    records = []
    for timestamp, rainfall in zip(timestamps, [0.2, 0.4, 0.6, 0.8]):
        records.append(
            {
                "location_id": "hyderabad_reference",
                "observed_at": timestamp.isoformat(),
                "latitude": 17.385,
                "longitude": 78.4867,
                "precipitation_mm": rainfall,
                "source_id": "test-source",
                "data_origin": "real",
            }
        )

    input_files = []
    for index, record in enumerate(records):
        path = raw_dir / f"hour_{index}.jsonl"
        pd.DataFrame([record]).to_json(
            path,
            orient="records",
            lines=True,
        )
        input_files.append(path)

    # Use two input files to verify feature calculation across a boundary.
    first_file = raw_dir / "first.jsonl"
    second_file = raw_dir / "second.jsonl"

    pd.DataFrame(records[:2]).to_json(
        first_file, orient="records", lines=True
    )
    pd.DataFrame(records[2:]).to_json(
        second_file, orient="records", lines=True
    )

    output_file = tmp_path / "combined_features.jsonl"

    monkeypatch.setattr(
        "src.features.build_three_month_dataset.INPUT_FILES",
        [first_file, second_file],
    )
    monkeypatch.setattr(
        "src.features.build_three_month_dataset.OUTPUT_FILE",
        output_file,
    )

    main()

    result = pd.read_json(output_file, lines=True)

    assert len(result) == 4
    assert result["precipitation_mm"].tolist() == pytest.approx(
    [0.2, 0.4, 0.6, 0.8]
    )
    assert result["rainfall_rolling_3h_mm"].iloc[2] == 1.2
    assert result["rainfall_rolling_3h_mm"].iloc[3] == 1.8
    assert result["data_origin"].eq("real").all()
