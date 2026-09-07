from pathlib import Path

import pandas as pd

from scripts.summarize_transit_accessibility import summarize_runs


def test_summarize_runs_calculates_system_and_origin_access(tmp_path: Path) -> None:
    input_path = tmp_path / "run.csv"
    pd.DataFrame(
        {
            "origin_id": ["a", "a", "b", "b"],
            "destination_id": ["one", "two", "one", "two"],
            "departure_seconds": [8 * 3600] * 4,
            "travel_time_minutes": [20.0, 70.0, 50.0, None],
        }
    ).to_csv(input_path, index=False)

    summary, origins = summarize_runs([input_path], thresholds=[30, 60])

    assert summary[["departure", "time_limit_minutes", "reachable_pairs"]].to_dict("records") == [
        {"departure": "08:00", "time_limit_minutes": 30, "reachable_pairs": 1},
        {"departure": "08:00", "time_limit_minutes": 60, "reachable_pairs": 2},
    ]
    within_sixty = origins.loc[origins["time_limit_minutes"] == 60].set_index("origin_id")
    assert within_sixty.loc["a", "reachable_destinations"] == 1
    assert within_sixty.loc["b", "reachable_destination_share"] == 0.5
