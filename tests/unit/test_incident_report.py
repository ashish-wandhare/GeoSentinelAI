
import json
from datetime import datetime, timezone

from src.data_quality.incident_report import analyze_incidents


def incident_record(incident_id="incident-001", origin="real"):
    return {
        "incident_id": incident_id,
        "location_id": "hyd-area-001",
        "occurred_at": datetime(
            2025, 6, 1, 10, 0, tzinfo=timezone.utc
        ).isoformat(),
        "reported_at": datetime(
            2025, 6, 1, 10, 30, tzinfo=timezone.utc
        ).isoformat(),
        "latitude": 17.385,
        "longitude": 78.4867,
        "source_id": "test-source",
        "verification_status": "unverified",
        "severity": None,
        "data_origin": origin,
    }


def write_jsonl(path, lines):
    path.write_text(
        "".join(line + "\n" for line in lines),
        encoding="utf-8",
    )


def test_report_counts_valid_records_and_origins(tmp_path):
    source = tmp_path / "incidents.jsonl"
    write_jsonl(
        source,
        [
            json.dumps(incident_record("incident-001", "real")),
            json.dumps(incident_record("incident-002", "synthetic")),
        ],
    )

    report = analyze_incidents(source)

    assert report["total_records"] == 2
    assert report["valid_records"] == 2
    assert report["invalid_records"] == 0
    assert report["data_origin_counts"] == {
        "real": 1,
        "synthetic": 1,
    }


def test_report_flags_duplicate_ids_without_dropping_records(tmp_path):
    source = tmp_path / "incidents.jsonl"
    record = incident_record("duplicate-id")
    write_jsonl(source, [json.dumps(record), json.dumps(record)])

    report = analyze_incidents(source)

    assert report["valid_records"] == 2
    assert report["duplicate_incident_ids"] == ["duplicate-id"]
    assert report["duplicate_records_beyond_first"] == 1


def test_report_detects_malformed_json(tmp_path):
    source = tmp_path / "incidents.jsonl"
    write_jsonl(source, ["{not valid json"])

    report = analyze_incidents(source)

    assert report["malformed_json_records"] == 1
    assert report["invalid_records"] == 1


def test_report_detects_schema_invalid_records(tmp_path):
    source = tmp_path / "incidents.jsonl"
    record = incident_record()
    record["latitude"] = 120
    write_jsonl(source, [json.dumps(record)])

    report = analyze_incidents(source)

    assert report["valid_records"] == 0
    assert report["invalid_records"] == 1


def test_report_counts_unverified_and_missing_severity(tmp_path):
    source = tmp_path / "incidents.jsonl"
    write_jsonl(source, [json.dumps(incident_record())])

    report = analyze_incidents(source)

    assert report["verification_status_counts"] == {"unverified": 1}
    assert report["records_without_severity"] == 1
    assert report["severity_counts"] == {"not_specified": 1}


def test_report_summarizes_geography_and_time(tmp_path):
    source = tmp_path / "incidents.jsonl"
    write_jsonl(source, [json.dumps(incident_record())])

    report = analyze_incidents(source)

    coverage = report["geographic_coverage"]
    assert coverage["latitude_min"] == 17.385
    assert coverage["latitude_max"] == 17.385
    assert coverage["longitude_min"] == 78.4867
    assert report["occurrence_time_coverage"]["earliest"].startswith(
        "2025-06-01T10:00:00"
    )


def test_report_handles_empty_file(tmp_path):
    source = tmp_path / "empty.jsonl"
    source.write_text("", encoding="utf-8")

    report = analyze_incidents(source)

    assert report["total_records"] == 0
    assert report["valid_records"] == 0
    assert report["geographic_coverage"]["latitude_min"] is None
