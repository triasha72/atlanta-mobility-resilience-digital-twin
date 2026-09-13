"""Calibrate FEMA flood-edge exposure against observed road-closure geometry."""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import pandas as pd

from amrdt.hazards import annotate_exposed_edges
from amrdt.network import _require_osmnx


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", type=Path, required=True, help="GraphML already annotated with flood_exposed.")
    parser.add_argument("--closures", type=Path, required=True, help="CRS-declared observed closure GeoJSON/GeoPackage.")
    parser.add_argument("--output-graph", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    args = parser.parse_args()
    ox = _require_osmnx()
    graph = ox.load_graphml(args.graph)
    closures = gpd.read_file(args.closures)
    if closures.crs is None:
        raise ValueError("observed closure data must declare a coordinate reference system")
    annotated = annotate_exposed_edges(
        graph, closures.to_crs(graph.graph.get("crs", "EPSG:4326")).geometry, attribute="observed_closed"
    )
    rows = pd.DataFrame([
        {"flood_exposed": str(data.get("flood_exposed", "")).lower() in {"true", "1"},
         "observed_closed": bool(data.get("observed_closed", False))}
        for _, _, data in annotated.edges(data=True)
    ])
    tp = int((rows.flood_exposed & rows.observed_closed).sum())
    fp = int((rows.flood_exposed & ~rows.observed_closed).sum())
    fn = int((~rows.flood_exposed & rows.observed_closed).sum())
    summary = pd.DataFrame([{
        "edges": len(rows), "true_positive_edges": tp, "false_positive_edges": fp, "false_negative_edges": fn,
        "precision": tp / (tp + fp) if tp + fp else float("nan"),
        "recall": tp / (tp + fn) if tp + fn else float("nan"),
    }])
    args.output_graph.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    ox.save_graphml(annotated, args.output_graph)
    summary.to_csv(args.summary_output, index=False)
    print(summary.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
