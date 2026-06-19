"""Static diagnostic plots for scenario results."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd


def plot_scenario_summary(summary: pd.DataFrame, output_path: str | Path) -> None:
    """Save a two-panel scenario comparison plot."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    axes[0].bar(summary["scenario"], summary["weighted_accessible_opportunities"])
    axes[0].set_title("Weighted accessible opportunities")
    axes[0].set_ylabel("Opportunity weight")
    axes[0].tick_params(axis="x", rotation=20)

    axes[1].bar(summary["scenario"], summary["mean_reachable_travel_time_minutes"])
    axes[1].set_title("Mean reachable travel time")
    axes[1].set_ylabel("Minutes")
    axes[1].tick_params(axis="x", rotation=20)

    fig.tight_layout()
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_disrupted_edges(
    graph: nx.MultiDiGraph,
    removed_edges: list[tuple[int, int, int]],
    output_path: str | Path,
) -> None:
    """Save a simple network plot with removed-edge endpoints highlighted."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    pos = {node: (data["x"], data["y"]) for node, data in graph.nodes(data=True)}
    affected_nodes = {node for edge in removed_edges for node in edge[:2]}

    fig, ax = plt.subplots(figsize=(8, 8))
    nx.draw_networkx_edges(graph, pos=pos, ax=ax, width=0.3, alpha=0.25, arrows=False)
    if affected_nodes:
        nx.draw_networkx_nodes(graph, pos=pos, nodelist=list(affected_nodes), ax=ax, node_size=10)
    ax.set_axis_off()
    ax.set_title("Affected edge endpoints")
    fig.tight_layout()
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)
