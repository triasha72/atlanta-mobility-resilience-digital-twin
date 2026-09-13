"""Benchmark CPU shortest-path routing and report CUDA/cuGraph availability."""

from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import time
from pathlib import Path

from amrdt.accessibility import compute_od_matrix
from amrdt.config import load_config
from amrdt.network import load_or_download_graph, nearest_nodes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = load_config(args.config)
    study = config["study_area"]
    graph = load_or_download_graph(
        study.get("place_name"), study.get("network_type", "drive"), config["paths"]["graph_file"],
        center_point=(float(study["center_lat"]), float(study["center_lon"])) if "center_lat" in study else None,
        dist_meters=study.get("dist_meters"),
    )
    start = time.perf_counter()
    od = compute_od_matrix(graph, nearest_nodes(graph, config["origins"]), nearest_nodes(graph, config["destinations"]))
    payload = {
        "schema_version": "1.0", "platform": platform.platform(), "nodes": graph.number_of_nodes(), "edges": graph.number_of_edges(),
        "od_pairs": len(od), "cpu_routing_seconds": time.perf_counter() - start,
        "cugraph_available": importlib.util.find_spec("cugraph") is not None,
        "cuda_runtime_available": importlib.util.find_spec("cudf") is not None,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
