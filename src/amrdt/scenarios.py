"""Network-disruption scenario generation."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import networkx as nx
import numpy as np


@dataclass(frozen=True)
class ScenarioResult:
    """A disrupted graph plus metadata about removed edges."""

    name: str
    graph: nx.MultiDiGraph
    removed_edges: list[tuple[int, int, int]]


def _edge_pairs_ranked_by_betweenness(
    graph: nx.MultiDiGraph, *, sample_nodes: int | None = None, seed: int | None = None
) -> list[tuple[int, int]]:
    """Rank undirected node pairs by edge betweenness using travel time weights."""
    simple = nx.Graph()
    for u, v, _key, data in graph.edges(keys=True, data=True):
        weight = float(data.get("travel_time", data.get("length", 1.0)))
        if simple.has_edge(u, v):
            simple[u][v]["weight"] = min(simple[u][v]["weight"], weight)
        else:
            simple.add_edge(u, v, weight=weight)

    if sample_nodes is not None and sample_nodes < 1:
        raise ValueError("betweenness_sample_nodes must be positive")
    scores = nx.edge_betweenness_centrality(
        simple, weight="weight", normalized=True, k=sample_nodes, seed=seed
    )
    return [edge for edge, _score in sorted(scores.items(), key=lambda item: item[1], reverse=True)]


def _edges_for_pairs(
    graph: nx.MultiDiGraph, pairs: Iterable[tuple[int, int]]
) -> list[tuple[int, int, int]]:
    """Expand undirected node pairs into concrete directed MultiDiGraph edge tuples."""
    selected: list[tuple[int, int, int]] = []
    pair_set = {frozenset(pair) for pair in pairs}
    for u, v, key in graph.edges(keys=True):
        if frozenset((u, v)) in pair_set:
            selected.append((u, v, key))
    return selected


def apply_scenario(
    graph: nx.MultiDiGraph,
    scenario: dict,
    random_seed: int = 42,
) -> ScenarioResult:
    """Return a graph representing a baseline, random, or high-centrality closure scenario."""
    scenario_type = scenario["type"]
    name = scenario["name"]
    disrupted = graph.copy()

    if scenario_type == "baseline":
        return ScenarioResult(name=name, graph=disrupted, removed_edges=[])

    n_edges = int(scenario.get("n_edges", 1))
    if n_edges <= 0:
        raise ValueError("n_edges must be positive for a disruption scenario.")

    if scenario_type == "random_edges":
        rng = np.random.default_rng(random_seed)
        available = list(disrupted.edges(keys=True))
        n_edges = min(n_edges, len(available))
        indices = rng.choice(len(available), size=n_edges, replace=False)
        removed = [available[int(index)] for index in indices]

    elif scenario_type == "high_betweenness_edges":
        sample_nodes = scenario.get("betweenness_sample_nodes")
        ranked_pairs = _edge_pairs_ranked_by_betweenness(
            disrupted,
            sample_nodes=int(sample_nodes) if sample_nodes is not None else None,
            seed=random_seed,
        )
        selected_pairs = ranked_pairs[:n_edges]
        removed = _edges_for_pairs(disrupted, selected_pairs)

    elif scenario_type == "flood_exposed_edges":
        removed = [
            (u, v, key)
            for u, v, key, data in disrupted.edges(keys=True, data=True)
            if str(data.get("flood_exposed", "")).lower() in {"true", "1"}
        ]
        if not removed:
            raise ValueError("flood_exposed_edges requires a graph with exposed edges")

    else:
        raise ValueError(f"Unsupported scenario type: {scenario_type}")

    disrupted.remove_edges_from(removed)
    return ScenarioResult(name=name, graph=disrupted, removed_edges=removed)
