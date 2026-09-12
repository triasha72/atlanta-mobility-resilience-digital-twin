"""Spatial hazard annotations for disruption scenarios."""

from __future__ import annotations

from collections.abc import Iterable

import networkx as nx
from shapely.geometry import LineString
from shapely.geometry.base import BaseGeometry


def _edge_geometry(graph: nx.MultiDiGraph, u: object, v: object, data: dict) -> BaseGeometry:
    geometry = data.get("geometry")
    if isinstance(geometry, BaseGeometry):
        return geometry
    return LineString([(graph.nodes[u]["x"], graph.nodes[u]["y"]), (graph.nodes[v]["x"], graph.nodes[v]["y"])])


def annotate_exposed_edges(
    graph: nx.MultiDiGraph, hazard_geometries: Iterable[BaseGeometry], *, attribute: str = "flood_exposed"
) -> nx.MultiDiGraph:
    """Return a copy with a boolean edge attribute for any hazard intersection."""
    hazards = [geometry for geometry in hazard_geometries if not geometry.is_empty]
    if not hazards:
        raise ValueError("hazard input has no non-empty geometries")
    result = graph.copy()
    for u, v, key, data in result.edges(keys=True, data=True):
        geometry = _edge_geometry(result, u, v, data)
        data[attribute] = any(geometry.intersects(hazard) for hazard in hazards)
    return result
