import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "models"
    / "rainfall_anomaly_baseline.py"
)

SPEC = importlib.util.spec_from_file_location(
    "rainfall_anomaly_baseline", MODULE_PATH
)
baseline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(baseline)


def sample_dataset():
    return pd.DataFrame(
        {
            "observed_at": pd.date_range(
                "2025-06-01", periods=40, freq="h", tz="UTC"
            ),
            "precipitation_mm": [0.0] * 39 + [6.7],
            "rainfall_rolling_3h_mm": [0.0] * 39 + [11.1],
            "rainfall_rolling_6h_mm": [0.0] * 39 + [11.3],
            "rainfall_rolling_24h_mm": [0.0] * 39 + [11.6],
        }
    )


def test_required_feature_columns_are_defined():
    assert baseline.FEATURE_COLUMNS == [
        "precipitation_mm",
        "rainfall_rolling_3h_mm",
        "rainfall_rolling_6h_mm",
        "rainfall_rolling_24h_mm",
    ]


def test_missing_required_column_is_reported(tmp_path, monkeypatch):
    input_path = tmp_path / "input.jsonl"
    df = sample_dataset().drop(columns=["rainfall_rolling_24h_mm"])
    df.to_json(input_path, orient="records", lines=True)

    monkeypatch.setattr(baseline, "INPUT_PATH", input_path)

    with pytest.raises(ValueError, match="Missing required columns"):
        baseline.run_baseline()


def test_incomplete_rows_are_excluded_and_outputs_are_saved(
    tmp_path, monkeypatch
):
    input_path = tmp_path / "input.jsonl"
    output_dir = tmp_path / "artifacts"
    df = sample_dataset()
    df.loc[0, "rainfall_rolling_24h_mm"] = np.nan
    df.to_json(input_path, orient="records", lines=True)

    monkeypatch.setattr(baseline, "INPUT_PATH", input_path)
    monkeypatch.setattr(baseline, "OUTPUT_DIR", output_dir)
    monkeypatch.setattr(
        baseline, "PREDICTIONS_PATH", output_dir / "results.csv"
    )
    monkeypatch.setattr(
        baseline, "MODEL_PATH", output_dir / "model.joblib"
    )

    results = baseline.run_baseline()

    assert len(results) == len(df) - 1
    assert results[baseline.FEATURE_COLUMNS].notna().all().all()
    assert results["anomaly_flag"].isin([True, False]).all()
    assert np.isfinite(results["anomaly_score"]).all()
    assert not results["waterlogging_confirmed"].any()
    assert set(results["interpretation"].unique()).issubset(
        {"unusual_rainfall_pattern", "typical_rainfall_pattern"}
    )
    assert (output_dir / "results.csv").exists()
    assert (output_dir / "model.joblib").exists()


def test_insufficient_complete_rows_raise_error(tmp_path, monkeypatch):
    input_path = tmp_path / "input.jsonl"
    df = sample_dataset().iloc[:1].copy()
    df["rainfall_rolling_24h_mm"] = np.nan
    df.to_json(input_path, orient="records", lines=True)

    monkeypatch.setattr(baseline, "INPUT_PATH", input_path)

    with pytest.raises(ValueError, match="Not enough complete rows"):
        baseline.run_baseline()
