
import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "features"
    / "rainfall_anomaly_report.py"
)

SPEC = importlib.util.spec_from_file_location(
    "rainfall_anomaly_report", MODULE_PATH
)
report_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(report_module)


def sample_results():
    return pd.DataFrame(
        {
            "observed_at": [
                "2025-06-01T00:00:00Z",
                "2025-06-01T01:00:00Z",
                "2025-07-01T00:00:00Z",
                "2025-08-01T00:00:00Z",
            ],
            "precipitation_mm": [0.0, 1.0, 3.0, 5.0],
            "rainfall_rolling_3h_mm": [0.0, 1.0, 4.0, 8.0],
            "rainfall_rolling_6h_mm": [0.0, 1.0, 6.0, 12.0],
            "rainfall_rolling_24h_mm": [0.0, 1.0, 10.0, 25.0],
            "anomaly_flag": [False, True, True, True],
            "anomaly_score": [0.1, -0.01, -0.05, -0.1],
            "interpretation": [
                "typical_rainfall_pattern",
                "unusual_rainfall_pattern",
                "unusual_rainfall_pattern",
                "unusual_rainfall_pattern",
            ],
            "waterlogging_confirmed": [False, False, False, False],
        }
    )


def configure_paths(tmp_path, monkeypatch, df):
    input_file = tmp_path / "results.csv"
    output_dir = tmp_path / "output"

    df.to_csv(input_file, index=False)

    monkeypatch.setattr(report_module, "INPUT_FILE", input_file)
    monkeypatch.setattr(report_module, "OUTPUT_DIR", output_dir)
    monkeypatch.setattr(
        report_module, "SUMMARY_FILE", output_dir / "report.json"
    )
    monkeypatch.setattr(
        report_module, "MONTHLY_FILE", output_dir / "monthly.csv"
    )
    monkeypatch.setattr(
        report_module, "TOP_ANOMALIES_FILE", output_dir / "top.csv"
    )

    return output_dir


def test_report_creates_artifacts_and_monthly_counts(
    tmp_path, monkeypatch
):
    output_dir = configure_paths(
        tmp_path, monkeypatch, sample_results()
    )

    report_module.main()

    report = json.loads(
        (output_dir / "report.json").read_text(encoding="utf-8")
    )
    monthly = pd.read_csv(output_dir / "monthly.csv")
    top = pd.read_csv(output_dir / "top.csv")

    assert report["dataset"]["rows_analyzed"] == 4
    assert report["dataset"]["anomaly_count"] == 3
    assert report["dataset"]["confirmed_waterlogging_labels"] == 0

    assert len(monthly) == 3
    assert monthly.set_index("month").loc["2025-06", "anomalies"] == 1
    assert len(top) == 3
    assert (output_dir / "report.json").exists()


def test_invalid_anomaly_flags_are_rejected(tmp_path, monkeypatch):
    df = sample_results()

    # Convert to object dtype before assigning an invalid string.
    # This lets the report validator handle the invalid value.
    df["anomaly_flag"] = df["anomaly_flag"].astype(object)
    df.loc[0, "anomaly_flag"] = "maybe"

    configure_paths(tmp_path, monkeypatch, df)

    with pytest.raises(
        ValueError,
        match="Anomaly flags contain invalid values",
    ):
        report_module.main()


def test_true_waterlogging_confirmation_is_rejected(
    tmp_path, monkeypatch
):
    df = sample_results()
    df.loc[1, "waterlogging_confirmed"] = True

    configure_paths(tmp_path, monkeypatch, df)

    with pytest.raises(
        ValueError,
        match="Unexpected waterlogging confirmation",
    ):
        report_module.main()
