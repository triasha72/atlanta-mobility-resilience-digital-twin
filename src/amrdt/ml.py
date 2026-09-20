"""Leakage-aware feature preparation for event-labeled road-edge studies."""

from __future__ import annotations

import math

import networkx as nx
import pandas as pd

from amrdt.hazards import _edge_geometry


def edge_learning_frame(
    graph: nx.MultiDiGraph,
    *,
    label: str = "observed_closed",
    block_degrees: float = 0.02,
) -> pd.DataFrame:
    """Return road-edge features and a coarse spatial group for held-out evaluation.

    Labels must originate from an event-specific official closure source.  This
    function only prepares them; it never creates synthetic closure labels.
    """
    if block_degrees <= 0:
        raise ValueError("block_degrees must be positive")
    rows: list[dict[str, object]] = []
    for u, v, key, data in graph.edges(keys=True, data=True):
        geometry = _edge_geometry(graph, u, v, data)
        point = geometry.centroid
        longitude, latitude = float(point.x), float(point.y)
        try:
            target = int(str(data[label]).lower() in {"true", "1"})
        except KeyError as exc:
            raise ValueError(f"graph edges must include {label!r}") from exc
        rows.append(
            {
                "edge_u": str(u),
                "edge_v": str(v),
                "edge_key": str(key),
                "length_m": float(data.get("length", geometry.length)),
                "travel_time_s": float(data.get("travel_time", 0.0)),
                "speed_kph": float(data.get("speed_kph", 0.0)),
                "flood_exposed": int(
                    str(data.get("flood_exposed", "")).lower() in {"true", "1"}
                ),
                "midpoint_lon": longitude,
                "midpoint_lat": latitude,
                "spatial_block": (
                    f"{math.floor(longitude / block_degrees)}:"
                    f"{math.floor(latitude / block_degrees)}"
                ),
                "observed_closed": target,
            }
        )
    return pd.DataFrame(rows)
