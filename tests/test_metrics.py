import pandas as pd

from amrdt.metrics import compare_with_baseline, scenario_summary


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
