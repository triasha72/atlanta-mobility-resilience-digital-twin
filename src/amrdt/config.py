"""Configuration loading and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml


def _point_records(config: dict[str, Any], key: str, config_path: Path) -> list[dict[str, Any]]:
    inline = config.get(key)
    file_key = f"{key}_file"
    if inline and config.get(file_key):
        raise ValueError(f"Use either {key} or {file_key}, not both")
    if inline:
        return inline
    if not config.get(file_key):
        raise ValueError(f"Config requires non-empty {key} or {file_key}")
    source = Path(config[file_key])
    if not source.is_absolute():
        source = (config_path.parent / source).resolve()
    frame = pd.read_csv(source)
    if "id" not in frame.columns and "geoid" in frame.columns:
        frame = frame.rename(columns={"geoid": "id"})
    required = {"id", "lat", "lon"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"{file_key} missing columns: {sorted(missing)}")
    return frame.where(frame.notna(), None).to_dict(orient="records")


def load_config(path: str | Path) -> dict[str, Any]:
    """Load a YAML configuration file and create output directories."""
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    required = {"study_area", "routing", "scenarios", "paths"}
    missing = required.difference(config)
    if missing:
        raise ValueError(f"Config missing required sections: {sorted(missing)}")

    config["origins"] = _point_records(config, "origins", config_path)
    config["destinations"] = _point_records(config, "destinations", config_path)

    for directory_key in ("output_dir", "figure_dir"):
        Path(config["paths"][directory_key]).mkdir(parents=True, exist_ok=True)
    Path(config["paths"]["graph_file"]).parent.mkdir(parents=True, exist_ok=True)
    return config
