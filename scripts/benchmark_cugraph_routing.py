"""Benchmark equivalent all-origin shortest-path routing with cuGraph."""

from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path

from amrdt.config import load_config
from amrdt.gpu import coalesced_edge_table
from amrdt.network import load_or_download_graph, nearest_nodes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        import cudf
        import cugraph
    except ImportError as exc:
        raise SystemExit(
            "cuGraph is required. In Colab, run the RAPIDS install cell and reconnect the runtime."
        ) from exc

    config = load_config(args.config)
    study = config["study_area"]
    graph = load_or_download_graph(
        study.get("place_name"),
        study.get("network_type", "drive"),
        config["paths"]["graph_file"],
        center_point=(float(study["center_lat"]), float(study["center_lon"]))
        if "center_lat" in study
        else None,
        dist_meters=study.get("dist_meters"),
    )
    origin_nodes = nearest_nodes(graph, config["origins"])
    destination_nodes = nearest_nodes(graph, config["destinations"])
    edge_table = coalesced_edge_table(graph)

    setup_start = time.perf_counter()
    gpu_edges = cudf.from_pandas(edge_table)
    gpu_graph = cugraph.Graph(directed=True)
    # OSM node identifiers are sparse, large integers. cuGraph must compact
    # them to [0, V) rather than allocating arrays indexed by their raw value.
    # cuGraph's public shortest-path API accepts and returns external IDs.
    gpu_graph.from_cudf_edgelist(
        gpu_edges,
        source="source",
        destination="target",
        edge_attr="weight",
        renumber=True,
    )
    graph_setup_seconds = time.perf_counter() - setup_start

    routing_start = time.perf_counter()
    reachable_pairs = 0
    for source in origin_nodes.values():
        # Edge weights are bound when the graph is constructed.  Recent
        # cuGraph releases do not accept a NetworkX-style ``weight`` keyword.
        distances = cugraph.sssp(gpu_graph, source=int(source))
        requested = distances[distances["vertex"].isin(list(destination_nodes.values()))]
        reachable_pairs += int((requested["distance"] != float("inf")).sum())
    routing_seconds = time.perf_counter() - routing_start

    payload = {
        "schema_version": "1.0",
        "platform": platform.platform(),
        "cugraph_version": getattr(cugraph, "__version__", "unknown"),
        "nodes": graph.number_of_nodes(),
        "input_edges": graph.number_of_edges(),
        "coalesced_edges": len(edge_table),
        "vertex_ids_renumbered": bool(gpu_graph.is_renumbered()),
        "origins": len(origin_nodes),
        "destinations": len(destination_nodes),
        "od_pairs": len(origin_nodes) * len(destination_nodes),
        "reachable_od_pairs": reachable_pairs,
        "gpu_graph_setup_seconds": graph_setup_seconds,
        "gpu_routing_seconds": routing_seconds,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
