"""Road-network acquisition, saving, and graph utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import networkx as nx


def _require_osmnx() -> Any:
    try:
        import osmnx as ox
    except ImportError as exc:
        raise ImportError(
            "OSMnx is required for road-network download. "
            "Install dependencies with `pip install -e .`."
        ) from exc
    return ox


def load_or_download_graph(
    place_name: str | None,
    network_type: str,
    graph_file: str | Path,
    *,
    center_point: tuple[float, float] | None = None,
    dist_meters: float | None = None,
) -> nx.MultiDiGraph:
    """Load a cached OSM graph or download, enrich, and save it.

    A fixed center point is preferred for the small downtown demo because
    neighborhood names can resolve inconsistently in OpenStreetMap geocoding.
    """
    ox = _require_osmnx()
    graph_path = Path(graph_file)
    graph_path.parent.mkdir(parents=True, exist_ok=True)

    if graph_path.exists():
        return ox.load_graphml(graph_path)

    if center_point is not None:
        if dist_meters is None:
            raise ValueError(
                "Set `dist_meters` when using `center_lat` and `center_lon` "
                "in the configuration."
            )

        graph = ox.graph_from_point(
            center_point,
            dist=float(dist_meters),
            dist_type="bbox",
            network_type=network_type,
            simplify=True,
        )

    elif place_name:
        graph = ox.graph_from_place(
            place_name,
            network_type=network_type,
            simplify=True,
        )

    else:
        raise ValueError(
            "Provide either `place_name` or both `center_lat` and `center_lon` "
            "in the study_area configuration."
        )

    graph = ox.add_edge_speeds(graph)
    graph = ox.add_edge_travel_times(graph)
    ox.save_graphml(graph, graph_path)
    return graph


def nearest_nodes(graph: nx.MultiDiGraph, points: list[dict[str, Any]]) -> dict[str, int]:
    """Snap configured longitude/latitude points to nearest road-network nodes."""
    ox = _require_osmnx()
    result: dict[str, int] = {}

    for point in points:
        result[str(point["id"])] = int(
            ox.distance.nearest_nodes(
                graph,
                X=point["lon"],
                Y=point["lat"],
            )
        )

    return result


def graph_summary(graph: nx.MultiDiGraph) -> dict[str, int]:
    """Return basic directed graph size statistics."""
    return {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
    }