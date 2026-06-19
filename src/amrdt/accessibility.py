"""OD routing and opportunity accessibility calculations."""

from __future__ import annotations

from typing import Any

import networkx as nx
import pandas as pd


def compute_od_matrix(
    graph: nx.MultiDiGraph,
    origin_nodes: dict[str, int],
    destination_nodes: dict[str, int],
    weight: str = "travel_time",
) -> pd.DataFrame:
    """Compute a long-form all-pairs OD travel-time matrix in seconds."""
    records: list[dict[str, Any]] = []
    for origin_id, source in origin_nodes.items():
        lengths = nx.single_source_dijkstra_path_length(graph, source, weight=weight)
        for destination_id, target in destination_nodes.items():
            travel_time = lengths.get(target)
            records.append(
                {
                    "origin_id": origin_id,
                    "destination_id": destination_id,
                    "travel_time_seconds": travel_time,
                    "reachable": travel_time is not None,
                }
            )
    return pd.DataFrame.from_records(records)


def summarize_accessibility(
    od_matrix: pd.DataFrame,
    origins: list[dict[str, Any]],
    destinations: list[dict[str, Any]],
    threshold_minutes: float,
) -> pd.DataFrame:
    """Calculate destination opportunities reachable from each origin within a time threshold."""
    origin_weights = {str(row["id"]): float(row.get("population_weight", 1.0)) for row in origins}
    destination_weights = {
        str(row["id"]): float(row.get("opportunity_weight", 1.0)) for row in destinations
    }

    frame = od_matrix.copy()
    frame["travel_time_minutes"] = frame["travel_time_seconds"] / 60.0
    frame["opportunity_weight"] = frame["destination_id"].map(destination_weights)
    reachable = frame[frame["travel_time_minutes"].le(threshold_minutes)].copy()

    access = (
        reachable.groupby("origin_id", as_index=False)["opportunity_weight"]
        .sum()
        .rename(columns={"opportunity_weight": "accessible_opportunities"})
    )
    all_origins = pd.DataFrame({"origin_id": list(origin_weights), "population_weight": list(origin_weights.values())})
    access = all_origins.merge(access, on="origin_id", how="left")
    access["accessible_opportunities"] = access["accessible_opportunities"].fillna(0.0)
    return access
