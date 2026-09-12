import pandas as pd

from amrdt.metrics import compare_with_baseline, scenario_summary, scenario_uncertainty_intervals


def test_scenario_summary_and_baseline_deltas() -> None:
    od = pd.DataFrame(
        {
            "origin_id": ["o1", "o1"],
            "destination_id": ["d1", "d2"],
            "travel_time_seconds": [60.0, None],
            "reachable": [True, False],
        }
    )
    access = pd.DataFrame(
        {
            "origin_id": ["o1"],
            "population_weight": [2.0],
            "accessible_opportunities": [1.0],
        }
    )
    baseline = scenario_summary("baseline", od, access, 0)
    disrupted = scenario_summary("closure", od, access, 2)
    summary = compare_with_baseline(pd.DataFrame([baseline, disrupted]))
    assert summary.loc[summary["scenario"].eq("baseline"), "delta_reachable_od_share"].iloc[0] == 0
    assert summary.loc[summary["scenario"].eq("closure"), "removed_edges"].iloc[0] == 2


def test_scenario_uncertainty_intervals_group_repeated_closures() -> None:
    summary = pd.DataFrame({
        "scenario_family": ["random", "random"],
        "reachable_od_share": [1.0, 0.8],
        "mean_reachable_travel_time_minutes": [10.0, 20.0],
        "mean_accessible_opportunities": [3.0, 1.0],
        "weighted_accessible_opportunities": [3.0, 1.0],
    })
    result = scenario_uncertainty_intervals(summary)
    assert result.loc[0, "simulations"] == 2
    assert result.loc[0, "reachable_od_share_mean"] == 0.9
    assert result.loc[0, "mean_reachable_travel_time_minutes_p05"] == 10.5
    assert result.loc[0, "mean_reachable_travel_time_minutes_p95"] == 19.5
