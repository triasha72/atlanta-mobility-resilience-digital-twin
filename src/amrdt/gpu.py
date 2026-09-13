"""Small, optional helpers shared by GPU routing benchmarks."""

from __future__ import annotations

import math

import networkx as nx
import pandas as pd


def coalesced_edge_table(graph: nx.MultiDiGraph, weight: str = "travel_time") -> pd.DataFrame:
    """Return one minimum-weight directed edge per endpoint pair.

    NetworkX's Dijkstra implementation implicitly chooses the least-cost edge
    among parallel edges.  Collapsing them explicitly makes the cuGraph input
    semantically equivalent to the CPU graph.
    """
    rows: list[dict[str, float | int]] = []
    for source, target, data in graph.edges(data=True):
        value = float(data[weight])
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"{weight} must be finite and non-negative")
        rows.append({"source": int(source), "target": int(target), "weight": value})
    return pd.DataFrame(rows).groupby(["source", "target"], as_index=False)["weight"].min()
