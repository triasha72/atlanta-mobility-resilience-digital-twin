"""Cached pedestrian-network helpers for transit access and egress legs."""

from __future__ import annotations

from pathlib import Path

import networkx as nx
import numpy as np
from scipy.spatial import cKDTree

from amrdt.gtfs import haversine_meters
from amrdt.transit import Stop


def load_walk_graph(path: str | Path, *, walking_speed_kph: float = 4.8) -> nx.MultiDiGraph:
    """Load a GraphML walk graph and attach deterministic edge travel seconds."""
    if walking_speed_kph <= 0:
        raise ValueError("walking_speed_kph must be positive")
    graph = nx.read_graphml(path, force_multigraph=True)
    for _, _, _, data in graph.edges(keys=True, data=True):
        length = float(data.get("length", 0))
        if length < 0:
            raise ValueError("walk graph edge length must be nonnegative")
        data["walk_seconds"] = length / (walking_speed_kph * 1000 / 3600)
    return graph


def _node_index(graph: nx.MultiDiGraph) -> tuple[cKDTree, list[str], np.ndarray]:
    """Build and cache a local-coordinate nearest-node index."""
    cache_key = "_amrdt_node_index"
    cached = graph.graph.get(cache_key)
    if cached is not None:
        return cached
    node_ids = []
    coordinates = []
    for node, data in graph.nodes(data=True):
        if "x" in data and "y" in data:
            node_ids.append(str(node))
            coordinates.append((float(data["y"]), float(data["x"])))
    if not coordinates:
        raise ValueError("walk graph nodes must include x and y coordinates")
    raw = np.array(coordinates)
    longitude_scale = float(np.cos(np.radians(raw[:, 0].mean())))
    indexed = raw.copy()
    indexed[:, 1] *= longitude_scale
    result = (cKDTree(indexed), node_ids, raw)
    graph.graph[cache_key] = result
    return result


def nearest_node_with_distance(
    graph: nx.MultiDiGraph, *, lat: float, lon: float
) -> tuple[str, float]:
    """Return the nearest graph node and its straight-line snap distance."""
    tree, node_ids, raw = _node_index(graph)
    longitude_scale = float(np.cos(np.radians(raw[:, 0].mean())))
    _, index = tree.query((lat, lon * longitude_scale))
    node_lat, node_lon = raw[int(index)]
    return node_ids[int(index)], haversine_meters(lat, lon, node_lat, node_lon)


def nearest_node(graph: nx.MultiDiGraph, *, lat: float, lon: float) -> str:
    """Return the nearest graph node using coordinates stored in GraphML."""
    return nearest_node_with_distance(graph, lat=lat, lon=lon)[0]


def _stop_snaps(
    graph: nx.MultiDiGraph, stops: dict[str, Stop]
) -> dict[str, tuple[str, float]]:
    """Cache stop-to-walk-network snaps on the graph for repeated OD runs."""
    cache_key = "_amrdt_stop_snaps"
    cached = graph.graph.get(cache_key)
    if cached is not None and set(cached) == set(stops):
        return cached
    snapped = {
        stop_id: nearest_node_with_distance(graph, lat=stop.lat, lon=stop.lon)
        for stop_id, stop in stops.items()
    }
    graph.graph[cache_key] = snapped
    return snapped


def walk_seconds_to_stops(
    graph: nx.MultiDiGraph, *, lat: float, lon: float, stops: dict[str, Stop],
    max_walk_meters: float, walking_speed_kph: float = 4.8,
) -> dict[str, float]:
    """Route from a point to nearby GTFS stops on a cached pedestrian network."""
    if max_walk_meters <= 0:
        raise ValueError("max_walk_meters must be positive")
    source, source_snap_meters = nearest_node_with_distance(graph, lat=lat, lon=lon)
    meters_per_second = walking_speed_kph * 1000 / 3600
    cutoff = max_walk_meters / meters_per_second
    source_snap_seconds = source_snap_meters / meters_per_second
    lengths = nx.single_source_dijkstra_path_length(
        graph, source, cutoff=max(0.0, cutoff - source_snap_seconds), weight="walk_seconds"
    )
    result = {}
    for stop_id, (node, stop_snap_meters) in _stop_snaps(graph, stops).items():
        seconds = source_snap_seconds + lengths.get(node, float("inf")) + (
            stop_snap_meters / meters_per_second
        )
        if seconds <= cutoff:
            result[stop_id] = seconds
    return result


def walk_seconds_from_stops_to_point(
    graph: nx.MultiDiGraph, *, stops: dict[str, Stop], lat: float, lon: float,
    max_walk_meters: float, walking_speed_kph: float = 4.8,
) -> dict[str, float]:
    """Route from GTFS stops to a point while respecting one-way walk edges."""
    reversed_graph = graph.reverse(copy=False)
    reverse_times = walk_seconds_to_stops(
        reversed_graph, lat=lat, lon=lon, stops=stops, max_walk_meters=max_walk_meters,
        walking_speed_kph=walking_speed_kph,
    )
    return reverse_times


def walk_seconds_to_points(
    graph: nx.MultiDiGraph, *, lat: float, lon: float,
    points: dict[str, tuple[float, float]], max_walk_meters: float,
    walking_speed_kph: float = 4.8,
) -> dict[str, float]:
    """Return pedestrian-network times from one point to nearby named points."""
    if max_walk_meters <= 0:
        raise ValueError("max_walk_meters must be positive")
    source, source_snap_meters = nearest_node_with_distance(graph, lat=lat, lon=lon)
    meters_per_second = walking_speed_kph * 1000 / 3600
    cutoff = max_walk_meters / meters_per_second
    source_snap_seconds = source_snap_meters / meters_per_second
    lengths = nx.single_source_dijkstra_path_length(
        graph, source, cutoff=max(0.0, cutoff - source_snap_seconds), weight="walk_seconds"
    )
    result = {}
    for point_id, (point_lat, point_lon) in points.items():
        if haversine_meters(lat, lon, point_lat, point_lon) > max_walk_meters:
            continue
        node, point_snap_meters = nearest_node_with_distance(
            graph, lat=point_lat, lon=point_lon
        )
        seconds = source_snap_seconds + lengths.get(node, float("inf")) + (
            point_snap_meters / meters_per_second
        )
        if seconds <= cutoff:
            result[point_id] = seconds
    return result
