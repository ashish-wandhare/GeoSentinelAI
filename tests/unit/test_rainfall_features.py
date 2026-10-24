
import pandas as pd
import pytest

from src.features.rainfall_features import build_features


def make_observations(rainfall_values):
    timestamps = pd.date_range(
        "2025-06-01T00:00:00Z",
        periods=len(rainfall_values),
        freq="h",
    )

    return pd.DataFrame(
        {
            "location_id": ["test-location"] * len(timestamps),
            "observed_at": timestamps,
            "latitude": [17.385] * len(timestamps),
            "longitude": [78.4867] * len(timestamps),
            "precipitation_mm": rainfall_values,
            "source_id": ["unit-test"] * len(timestamps),
            "data_origin": ["synthetic"] * len(timestamps),
        }
    )


def test_rolling_rainfall_totals():
    observations = make_observations([1.0] * 30)
    features = build_features(observations)

    assert pd.isna(features.loc[0, "rainfall_rolling_3h_mm"])
    assert features.loc[2, "rainfall_rolling_3h_mm"] == pytest.approx(3.0)
    assert features.loc[5, "rainfall_rolling_6h_mm"] == pytest.approx(6.0)
    assert features.loc[23, "rainfall_rolling_24h_mm"] == pytest.approx(24.0)


def test_missing_hour_is_not_filled_with_zero():
    observations = make_observations([1.0, 2.0, 3.0, 4.0])
    observations = observations.drop(index=2).reset_index(drop=True)

    features = build_features(observations)

    # The absent 02:00 hour is explicitly represented as missing.
    missing_row = features.loc[features["observed_at"].dt.hour == 2].iloc[0]
    assert not missing_row["observation_present"]
    assert pd.isna(missing_row["precipitation_mm"])

    # The 03:00 rolling total is unavailable because its 3-hour window
    # includes the missing 02:00 observation.
    row_03 = features.loc[features["observed_at"].dt.hour == 3].iloc[0]
    assert pd.isna(row_03["rainfall_rolling_3h_mm"])


def test_inconsistent_location_coordinates_are_rejected():
    observations = make_observations([1.0, 2.0, 3.0])
    observations.loc[1, "latitude"] = 18.0

    with pytest.raises(ValueError, match="inconsistent coordinates"):
        build_features(observations)
