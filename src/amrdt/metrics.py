"""Scenario comparison metrics."""

from __future__ import annotations

import pandas as pd


def scenario_summary(
    scenario_name: str,
    od_matrix: pd.DataFrame,
    accessibility: pd.DataFrame,
    removed_edge_count: int,
) -> dict[str, float | int | str]:
    """Summarize travel-time and accessibility performance for one scenario."""
    reachable = od_matrix[od_matrix["reachable"]].copy()
    return {
        "scenario": scenario_name,
        "removed_edges": removed_edge_count,
        "reachable_od_share": float(od_matrix["reachable"].mean()),
        "mean_reachable_travel_time_minutes": float(reachable["travel_time_seconds"].mean() / 60.0)
        if not reachable.empty
        else float("nan"),
        "mean_accessible_opportunities": float(accessibility["accessible_opportunities"].mean()),
        "weighted_accessible_opportunities": float(
            (accessibility["accessible_opportunities"] * accessibility["population_weight"]).sum()
            / accessibility["population_weight"].sum()
        ),
    }


def compare_with_baseline(summary: pd.DataFrame) -> pd.DataFrame:
    """Add change-from-baseline fields to a scenario-summary table."""
    baseline = summary.loc[summary["scenario"].eq("baseline")]
    if baseline.empty:
        return summary

    baseline_row = baseline.iloc[0]
    result = summary.copy()
    for column in (
        "reachable_od_share",
        "mean_reachable_travel_time_minutes",
        "mean_accessible_opportunities",
        "weighted_accessible_opportunities",
    ):
        result[f"delta_{column}"] = result[column] - baseline_row[column]
    return result
