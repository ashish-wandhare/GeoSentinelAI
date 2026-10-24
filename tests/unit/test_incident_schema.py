
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.data_quality.incident_schema import WaterloggingIncident


def valid_incident():
    return {
        "incident_id": "incident-test-001",
        "location_id": "hyd-area-001",
        "occurred_at": datetime(
            2025, 6, 1, 10, 0, tzinfo=timezone.utc
        ),
        "reported_at": datetime(
            2025, 6, 1, 10, 30, tzinfo=timezone.utc
        ),
        "latitude": 17.385,
        "longitude": 78.4867,
        "source_id": "unit-test-source",
        "verification_status": "verified",
        "severity": "moderate",
        "data_origin": "real",
    }


def test_valid_incident_is_accepted():
    incident = WaterloggingIncident.model_validate(valid_incident())

    assert incident.incident_id == "incident-test-001"
    assert incident.verification_status == "verified"
    assert incident.data_origin == "real"


def test_synthetic_origin_is_preserved():
    record = valid_incident()
    record["data_origin"] = "synthetic"
    record["verification_status"] = "unverified"

    incident = WaterloggingIncident.model_validate(record)

    assert incident.data_origin == "synthetic"
    assert incident.verification_status == "unverified"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("latitude", 95),
        ("longitude", 190),
        ("severity", "extreme"),
        ("verification_status", "confirmed"),
        ("data_origin", "unknown"),
    ],
)
def test_invalid_values_are_rejected(field, value):
    record = valid_incident()
    record[field] = value

    with pytest.raises(ValidationError):
        WaterloggingIncident.model_validate(record)


def test_naive_occurrence_timestamp_is_rejected():
    record = valid_incident()
    record["occurred_at"] = datetime(2025, 6, 1, 10, 0)

    with pytest.raises(ValidationError, match="timezone"):
        WaterloggingIncident.model_validate(record)


def test_blank_source_is_rejected():
    record = valid_incident()
    record["source_id"] = "   "

    with pytest.raises(ValidationError, match="Identifier"):
        WaterloggingIncident.model_validate(record)


def test_unknown_fields_are_rejected():
    record = valid_incident()
    record["invented_field"] = "unexpected"

    with pytest.raises(ValidationError):
        WaterloggingIncident.model_validate(record)


def test_optional_severity_and_source_reference():
    record = valid_incident()
    record["severity"] = None
    record["source_reference"] = None

    incident = WaterloggingIncident.model_validate(record)

    assert incident.severity is None
    assert incident.source_reference is None
