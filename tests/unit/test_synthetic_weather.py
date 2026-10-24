
import json

from src.ingestion.synthetic_weather import (
    generate_dataset,
    save_jsonl,
)
from src.data_quality.report import build_quality_report


def test_generator_is_reproducible():
    first = generate_dataset(records=20, seed=42)
    second = generate_dataset(records=20, seed=42)

    assert first == second


def test_generator_marks_all_records_synthetic():
    observations = generate_dataset(records=20, seed=42)

    assert len(observations) == 20
    assert all(
        row["data_origin"] == "synthetic"
        for row in observations
    )


def test_generator_rejects_zero_records():
    import pytest

    with pytest.raises(ValueError):
        generate_dataset(records=0)


def test_generated_jsonl_passes_quality_report(tmp_path):
    observations = generate_dataset(records=20, seed=42)
    input_path = tmp_path / "weather.jsonl"
    save_jsonl(observations, input_path)

    report = build_quality_report(input_path)

    assert report["total_records"] == 20
    assert report["valid_records"] == 20
    assert report["invalid_records"] == 0
    assert report["duplicate_count"] == 0
    assert report["data_origin_counts"] == {"synthetic": 20}


def test_quality_report_detects_invalid_records(tmp_path):
    input_path = tmp_path / "bad_weather.jsonl"

    valid_record = generate_dataset(records=1, seed=42)[0]
    invalid_record = {
        **valid_record,
        "precipitation_mm": -10,
    }

    with input_path.open("w", encoding="utf-8") as file:
        file.write(json.dumps(valid_record) + "\n")
        file.write(json.dumps(invalid_record) + "\n")
        file.write("{invalid-json}\n")

    report = build_quality_report(input_path)

    assert report["total_records"] == 3
    assert report["valid_records"] == 1
    assert report["invalid_records"] == 2
    assert report["malformed_json_lines"] == 1
