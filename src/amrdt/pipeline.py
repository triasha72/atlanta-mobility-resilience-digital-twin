"""End-to-end Version 1 pipeline."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from amrdt.accessibility import compute_od_matrix, summarize_accessibility
from amrdt.metrics import compare_with_baseline, scenario_summary
from amrdt.network import graph_summary, load_or_download_graph, nearest_nodes
from amrdt.scenarios import apply_scenario
from amrdt.visualization import plot_disrupted_edges, plot_scenario_summary


def run_pipeline(config: dict) -> pd.DataFrame:
    """Run baseline and disruption scenarios and write reproducible outputs."""

    study_area = config["study_area"]

    center_point = None
    if "center_lat" in study_area and "center_lon" in study_area:
        center_point = (
            float(study_area["center_lat"]),
            float(study_area["center_lon"]),
        )

    graph = load_or_download_graph(
        place_name=study_area.get("place_name"),
        network_type=study_area.get("network_type", "drive"),
        graph_file=config["paths"]["graph_file"],
        center_point=center_point,
        dist_meters=study_area.get("dist_meters"),
    )

    if not config["origins"] or not config["destinations"]:
        raise ValueError(
            "Origins and destinations are empty. "
            "Add valid lon/lat points to the YAML config before running."
        )

    origin_nodes = nearest_nodes(graph, config["origins"])
    destination_nodes = nearest_nodes(graph, config["destinations"])

    output_dir = Path(config["paths"]["output_dir"])
    figure_dir = Path(config["paths"]["figure_dir"])

    output_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)

    threshold = float(config["routing"]["max_travel_time_minutes"])
    random_seed = int(config.get("project", {}).get("random_seed", 42))

    all_summaries: list[dict] = []

    for position, scenario in enumerate(config["scenarios"]):
        result = apply_scenario(
            graph,
            scenario,
            random_seed=random_seed + position,
        )

        od_matrix = compute_od_matrix(
            result.graph,
            origin_nodes=origin_nodes,
            destination_nodes=destination_nodes,
            weight=config["routing"].get("weight", "travel_time"),
        )

        access = summarize_accessibility(
            od_matrix,
            origins=config["origins"],
            destinations=config["destinations"],
            threshold_minutes=threshold,
        )

        od_matrix.to_csv(
            output_dir / f"od_{result.name}.csv",
            index=False,
        )

        access.to_csv(
            output_dir / f"accessibility_{result.name}.csv",
            index=False,
        )

        plot_disrupted_edges(
            graph,
            result.removed_edges,
            figure_dir / f"{result.name}_affected_nodes.png",
        )

        all_summaries.append(
            scenario_summary(
                scenario_name=result.name,
                od_matrix=od_matrix,
                accessibility=access,
                removed_edge_count=len(result.removed_edges),
            )
        )

    summary = compare_with_baseline(pd.DataFrame(all_summaries))

    network_stats = graph_summary(graph)
    summary["network_nodes"] = network_stats["nodes"]
    summary["network_edges"] = network_stats["edges"]

    summary.to_csv(
        output_dir / "scenario_summary.csv",
        index=False,
    )

    plot_scenario_summary(
        summary,
        figure_dir / "scenario_summary.png",
    )

    return summary
