"""Annotate an OSM road GraphML with intersections from a flood-hazard GeoJSON."""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd

from amrdt.hazards import annotate_exposed_edges
from amrdt.network import _require_osmnx


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", type=Path, required=True, help="Input OSMnx GraphML.")
    parser.add_argument("--hazards", type=Path, required=True, help="Flood-hazard GeoJSON or GeoPackage.")
    parser.add_argument("--output", type=Path, required=True, help="Annotated GraphML output path.")
    args = parser.parse_args()

    ox = _require_osmnx()
    graph = ox.load_graphml(args.graph)
    hazards = gpd.read_file(args.hazards)
    graph_crs = graph.graph.get("crs", "EPSG:4326")
    if hazards.crs is None:
        raise ValueError("hazard data must declare a coordinate reference system")
    hazards = hazards.to_crs(graph_crs)
    annotated = annotate_exposed_edges(graph, hazards.geometry)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    ox.save_graphml(annotated, args.output)
    exposed = sum(data["flood_exposed"] for _, _, data in annotated.edges(data=True))
    print(f"wrote {args.output} with {exposed} flood-exposed directed edges")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
