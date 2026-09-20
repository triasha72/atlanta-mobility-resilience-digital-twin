"""Create a GNN/baseline-ready road-edge table from official event labels."""

from __future__ import annotations

import argparse
from pathlib import Path

from amrdt.ml import edge_learning_frame
from amrdt.network import _require_osmnx


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", type=Path, required=True, help="GraphML with official observed_closed labels.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--block-degrees", type=float, default=0.02)
    args = parser.parse_args()
    graph = _require_osmnx().load_graphml(args.graph)
    table = edge_learning_frame(graph, block_degrees=args.block_degrees)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.output, index=False)
    print(f"wrote {len(table)} event-labeled edges across {table.spatial_block.nunique()} spatial blocks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
