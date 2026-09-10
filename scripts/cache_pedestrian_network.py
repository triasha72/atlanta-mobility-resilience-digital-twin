"""Cache an OpenStreetMap pedestrian GraphML network for transit walking legs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--center-lat", type=float, default=33.7580)
    parser.add_argument("--center-lon", type=float, default=-84.3880)
    parser.add_argument("--radius-meters", type=int, default=12000)
    parser.add_argument("--output", type=Path, default=Path("data/processed/atlanta_walk.graphml"))
    parser.add_argument("--receipt", type=Path, default=Path("artifacts/atlanta_walk_network_v1.json"))
    args = parser.parse_args()
    if args.radius_meters <= 0:
        raise ValueError("radius-meters must be positive")

    import osmnx as ox

    graph = ox.graph_from_point(
        (args.center_lat, args.center_lon), dist=args.radius_meters, network_type="walk", simplify=True
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    ox.save_graphml(graph, args.output)
    digest = hashlib.sha256(args.output.read_bytes()).hexdigest()
    receipt = {
        "dataset": "OpenStreetMap pedestrian network",
        "license": "Open Data Commons Open Database License (ODbL) 1.0",
        "attribution": "OpenStreetMap contributors",
        "network_type": "walk",
        "center": {"lat": args.center_lat, "lon": args.center_lon},
        "radius_meters": args.radius_meters,
        "graphml_sha256": digest,
        "nodes": len(graph.nodes),
        "edges": len(graph.edges),
        "limitations": [
            "Walkable OSM links do not establish sidewalk condition, safety, or ADA accessibility.",
            "The graph is a source snapshot and does not measure temporary closures.",
        ],
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
