import pandas as pd
import pytest
import yaml

from amrdt.config import load_config


def _base_config():
    return {
        "study_area": {}, "routing": {}, "scenarios": [],
        "paths": {"output_dir": "out", "figure_dir": "fig", "graph_file": "graph/file"},
    }


def test_load_config_materializes_external_point_tables(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    pd.DataFrame([{"id": "o1", "lat": 1, "lon": 2, "population_weight": 1}]).to_csv(
        tmp_path / "origins.csv", index=False
    )
    pd.DataFrame([{"id": "d1", "lat": 3, "lon": 4, "opportunity_weight": 1}]).to_csv(
        tmp_path / "destinations.csv", index=False
    )
    config = {**_base_config(), "origins_file": "origins.csv", "destinations_file": "destinations.csv"}
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(config))
    loaded = load_config(path)
    assert loaded["origins"][0]["id"] == "o1"
    assert loaded["destinations"][0]["id"] == "d1"


def test_load_config_rejects_inline_and_file_points(tmp_path):
    config = {
        **_base_config(), "origins": [{"id": "o1", "lat": 1, "lon": 2}],
        "origins_file": "origins.csv", "destinations": [{"id": "d1", "lat": 3, "lon": 4}],
    }
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(config))
    with pytest.raises(ValueError, match="either origins or origins_file"):
        load_config(path)
