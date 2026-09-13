import pandas as pd

from amrdt.demand import resilience_conclusion


def test_resilience_conclusion_reports_weighted_access_loss() -> None:
    demand = pd.DataFrame({"origin_id": ["a", "b"], "destination_id": ["x", "x"], "synthetic_trip_count": [3, 1]})
    baseline = pd.DataFrame({"origin_id": ["a", "b"], "destination_id": ["x", "x"], "travel_time_seconds": [60, 120], "reachable": [True, True]})
    scenario = pd.DataFrame({"origin_id": ["a", "b"], "destination_id": ["x", "x"], "travel_time_seconds": [120, None], "reachable": [True, False]})
    result = resilience_conclusion(demand, baseline, scenario).iloc[0]
    assert result["baseline_reachable_trip_share"] == 1
    assert result["scenario_reachable_trip_share"] == 0.75
    assert result["reachable_trip_share_change_pp"] == -25
