import pandas as pd

from scripts.create_transit_validation_sample import build_sample
from scripts.score_transit_validation import score_completed_checks


def test_build_sample_is_stratified_and_repeatable() -> None:
    od = pd.DataFrame(
        {
            "origin_id": ["o1"] * 5,
            "destination_id": ["d1", "d2", "d3", "d4", "d5"],
            "travel_time_minutes": [20.0, 40.0, 70.0, 100.0, None],
        }
    )
    origins = pd.DataFrame({"geoid": ["o1"], "lat": [33.75], "lon": [-84.39]})
    destinations = pd.DataFrame(
        {
            "id": ["d1", "d2", "d3", "d4", "d5"],
            "label": ["one", "two", "three", "four", "five"],
            "category": ["clinic"] * 5,
            "lat": [33.75] * 5,
            "lon": [-84.39] * 5,
        }
    )
    sample = build_sample(
        od, origins, destinations, service_date="20260907", departure="08:00",
        sample_per_band=1, seed=7,
    )
    assert len(sample) == 5
    assert set(sample["model_time_band"]) == {
        "00_30_minutes", "31_60_minutes", "61_90_minutes", "over_90_minutes",
        "no_scheduled_arrival",
    }
    assert sample["planner_url"].str.contains("date=2026-09-07").all()


def test_score_completed_checks_uses_only_numeric_reviews() -> None:
    result = score_completed_checks(
        pd.DataFrame({"travel_time_minutes": [20.0, 50.0, 60.0], "planner_minutes": [25.0, 70.0, None]})
    )
    assert result.loc[0, "completed_planner_cases"] == 2
    assert result.loc[0, "comparable_numeric_cases"] == 2
    assert result.loc[0, "mean_absolute_difference_minutes"] == 12.5
    assert result.loc[0, "share_within_15_minutes"] == 0.5
