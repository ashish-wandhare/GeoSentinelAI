
from src.data_quality.ml_readiness import build_readiness_report


def sample_rainfall():
    return {
        "record_count": 168,
        "malformed_json_records": 0,
        "location_count": 1,
        "missing_feature_values": {
            "rainfall_rolling_3h_mm": 2,
            "rainfall_rolling_6h_mm": 5,
            "rainfall_rolling_24h_mm": 23,
        },
        "earliest_timestamp": "2025-06-01T00:00:00Z",
        "latest_timestamp": "2025-06-07T23:00:00Z",
    }


def sample_flooding():
    return {
        "mapped_point_count": 23,
        "timestamped_points": 0,
        "severity_labeled_points": 0,
        "usable_as_supervised_target_labels": False,
        "reason": "Mapped locations are not timestamped incidents.",
    }


def sample_incident_report():
    return {
        "input_file": "data/synthetic/incident_test.jsonl",
        "total_records": 1,
        "data_origin_counts": {"synthetic": 1},
        "verification_status_counts": {"unverified": 1},
        "records_without_severity": 1,
    }


def test_readiness_allows_exploration_but_not_supervised_prediction():
    report = build_readiness_report(
        sample_rainfall(),
        sample_flooding(),
        sample_incident_report(),
    )

    assert report["readiness"]["rainfall_feature_exploration"] == "ready"
    assert report["readiness"]["geospatial_visualization"] == "ready"
    assert report["readiness"]["supervised_waterlogging_prediction"] == "not_ready"


def test_synthetic_incidents_are_not_treated_as_real_evidence():
    report = build_readiness_report(
        sample_rainfall(),
        sample_flooding(),
        sample_incident_report(),
    )

    assert report["synthetic_incident_records_are_not_real_evidence"] is True
    assert report["datasets"]["incident_quality_report"]["data_origin_counts"] == {
        "synthetic": 1
    }


def test_malformed_rainfall_data_blocks_feature_readiness():
    rainfall = sample_rainfall()
    rainfall["malformed_json_records"] = 2

    report = build_readiness_report(
        rainfall,
        sample_flooding(),
        sample_incident_report(),
    )

    assert report["readiness"]["rainfall_feature_exploration"] == "not_ready"


def test_empty_rainfall_data_blocks_feature_readiness():
    rainfall = sample_rainfall()
    rainfall["record_count"] = 0

    report = build_readiness_report(
        rainfall,
        sample_flooding(),
        sample_incident_report(),
    )

    assert report["readiness"]["rainfall_feature_exploration"] == "not_ready"


def test_supervised_prediction_requires_incident_labels_and_real_records():
    flooding = sample_flooding()
    flooding["timestamped_points"] = 10
    flooding["severity_labeled_points"] = 10

    incident_report = sample_incident_report()
    incident_report["data_origin_counts"] = {"real": 10}

    report = build_readiness_report(
        sample_rainfall(),
        flooding,
        incident_report,
    )

    assert report["readiness"]["supervised_waterlogging_prediction"] == "ready"
