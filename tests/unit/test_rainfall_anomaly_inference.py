
import numpy as np
import pandas as pd
import pytest

from src.models import rainfall_anomaly_inference as inference


def sample_observations():
    return pd.DataFrame(
        {
            "observed_at": [
                "2025-09-01T10:00:00Z",
                "2025-09-01T11:00:00Z",
            ],
            "precipitation_mm": [0.0, 6.7],
            "rainfall_rolling_3h_mm": [0.0, 11.1],
            "rainfall_rolling_6h_mm": [0.0, 11.3],
            "rainfall_rolling_24h_mm": [0.0, 11.6],
        }
    )


def test_load_saved_model():
    model = inference.load_model()

    assert hasattr(model, "predict")
    assert hasattr(model, "decision_function")
    assert callable(model.predict)
    assert callable(model.decision_function)


def test_scores_observations_without_retraining(monkeypatch):
    class FakeModel:
        def predict(self, features):
            return np.array([1, -1])

        def decision_function(self, features):
            return np.array([0.2, -0.15])

    monkeypatch.setattr(inference, "load_model", lambda: FakeModel())

    results = inference.score_rainfall_observations(sample_observations())

    assert results["anomaly_flag"].tolist() == [False, True]
    assert results["interpretation"].tolist() == [
        "typical_rainfall_pattern",
        "unusual_rainfall_pattern",
    ]
    assert results["anomaly_score"].tolist() == [0.2, -0.15]
    assert not results["waterlogging_confirmed"].any()
    assert len(results) == 2


def test_missing_feature_column_is_rejected(monkeypatch):
    monkeypatch.setattr(
        inference,
        "load_model",
        lambda: pytest.fail("Model should not load for invalid input"),
    )

    observations = sample_observations().drop(
        columns=["rainfall_rolling_24h_mm"]
    )

    with pytest.raises(ValueError, match="Missing required columns"):
        inference.score_rainfall_observations(observations)


def test_missing_feature_value_is_rejected(monkeypatch):
    monkeypatch.setattr(
        inference,
        "load_model",
        lambda: pytest.fail("Model should not load for invalid input"),
    )

    observations = sample_observations()
    observations.loc[0, "rainfall_rolling_3h_mm"] = np.nan

    with pytest.raises(ValueError, match="missing values"):
        inference.score_rainfall_observations(observations)


def test_infinite_feature_value_is_rejected(monkeypatch):
    monkeypatch.setattr(
        inference,
        "load_model",
        lambda: pytest.fail("Model should not load for invalid input"),
    )

    observations = sample_observations()
    observations.loc[0, "precipitation_mm"] = np.inf

    with pytest.raises(ValueError, match="finite numeric values"):
        inference.score_rainfall_observations(observations)


def test_empty_input_is_rejected():
    with pytest.raises(ValueError, match="at least one row"):
        inference.score_rainfall_observations(
            pd.DataFrame(
                columns=["observed_at", *inference.FEATURE_COLUMNS]
            )
        )
