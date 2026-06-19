"""Configuration loading and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_config(path: str | Path) -> dict[str, Any]:
    """Load a YAML configuration file and create output directories."""
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    required = {"study_area", "routing", "scenarios", "origins", "destinations", "paths"}
    missing = required.difference(config)
    if missing:
        raise ValueError(f"Config missing required sections: {sorted(missing)}")

    for directory_key in ("output_dir", "figure_dir"):
        Path(config["paths"][directory_key]).mkdir(parents=True, exist_ok=True)
    Path(config["paths"]["graph_file"]).parent.mkdir(parents=True, exist_ok=True)
    return config
