
import pytest
from pydantic import ValidationError

from src.data_quality.schemas import WeatherObservation


@pytest.fixture
def valid_observation():
    return {
        "location_id": "hyd-cell-001",
        "observed_at": "2026-10-23T10:00:00+05:30",
        "latitude": 17.385,
        "longitude": 78.4867,
        "precipitation_mm": 12.5,
        "source_id": "test-weather-source",
        "data_origin": "real",
    }


def test_valid_weather_observation(valid_observation):
    observation = WeatherObservation(**valid_observation)

    assert observation.location_id == "hyd-cell-001"
    assert observation.precipitation_mm == 12.5
    assert observation.data_origin == "real"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("latitude", 95),
        ("longitude", 190),
        ("precipitation_mm", -1),
        ("precipitation_mm", float("nan")),
        ("precipitation_mm", float("inf")),
        ("data_origin", "unknown"),
        ("unexpected_field", "not-allowed"),
    ],
)
def test_invalid_values_are_rejected(
    valid_observation, field, value
):
    valid_observation[field] = value

    with pytest.raises(ValidationError):
        WeatherObservation(**valid_observation)


def test_missing_required_field_is_rejected(valid_observation):
    del valid_observation["source_id"]

    with pytest.raises(ValidationError):
        WeatherObservation(**valid_observation)


def test_naive_timestamp_is_rejected(valid_observation):
    valid_observation["observed_at"] = "2026-10-23T10:00:00"

    with pytest.raises(ValidationError):
        WeatherObservation(**valid_observation)


def test_blank_source_id_is_rejected(valid_observation):
    valid_observation["source_id"] = "   "

    with pytest.raises(ValidationError):
        WeatherObservation(**valid_observation)


def test_synthetic_origin_is_preserved(valid_observation):
    valid_observation["data_origin"] = "synthetic"

    observation = WeatherObservation(**valid_observation)

    assert observation.data_origin == "synthetic"
