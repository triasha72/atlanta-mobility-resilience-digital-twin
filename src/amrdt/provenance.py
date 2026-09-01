"""Text-only provenance records for public-network simulation runs."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256_file(path: str | Path) -> str:
    value = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def write_run_manifest(
    config: dict[str, Any], graph_file: str | Path, output_dir: str | Path
) -> Path:
    """Bind a run to its OSM graph cache, config, and tabular outputs."""
    graph_path = Path(graph_file)
    destination = Path(output_dir)
    csv_files = sorted(destination.glob("*.csv"))
    canonical_config = json.dumps(config, sort_keys=True, separators=(",", ":"))
    payload = {
        "schema_version": "1.0",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "network_source": "OpenStreetMap via OSMnx",
        "network_license": "ODbL-1.0",
        "graph": {"path": str(graph_path), "sha256": sha256_file(graph_path)},
        "config_sha256": hashlib.sha256(canonical_config.encode()).hexdigest(),
        "outputs": [{"path": item.name, "sha256": sha256_file(item)} for item in csv_files],
        "interpretation": "free-flow shortest-path simulation; not observed traffic",
    }
    manifest = destination / "run_manifest.json"
    manifest.write_text(json.dumps(payload, indent=2) + "\n")
    return manifest
