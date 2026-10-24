
import runpy
from pathlib import Path

import pandas as pd


def test_rainfall_visualization_generates_both_charts(tmp_path, monkeypatch):
    import src.features.plot_rainfall_features as plotting

    input_file = tmp_path / "rainfall.jsonl"
    output_dir = tmp_path / "charts"

    sample = pd.DataFrame(
        {
            "observed_at": [
                "2025-06-01T00:00:00Z",
                "2025-06-01T01:00:00Z",
                "2025-06-01T02:00:00Z",
            ],
            "precipitation_mm": [0.0, 0.2, 0.1],
            "rainfall_rolling_3h_mm": [None, None, 0.3],
            "rainfall_rolling_6h_mm": [None, None, None],
            "rainfall_rolling_24h_mm": [None, None, None],
        }
    )
    sample.to_json(input_file, orient="records", lines=True)

    monkeypatch.setattr(plotting, "INPUT_FILE", input_file)
    monkeypatch.setattr(plotting, "OUTPUT_DIR", output_dir)

    plotting.main()

    assert (output_dir / "hourly_precipitation.png").is_file()
    assert (output_dir / "rolling_rainfall_features.png").is_file()
    assert (output_dir / "hourly_precipitation.png").stat().st_size > 0
    assert (output_dir / "rolling_rainfall_features.png").stat().st_size > 0
