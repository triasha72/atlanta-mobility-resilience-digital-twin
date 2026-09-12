import pandas as pd

from scripts.create_proxy_calibration_sample import exclude_prior_tract_destination_pairs
from scripts.create_transit_holdout_sample import build_holdout
from scripts.create_transit_validation_sample import build_sample
from scripts.record_manual_validation import parse_planner_outcomes
from scripts.score_transit_validation import passes_publication_gate, score_completed_checks


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
    assert sample["planner_url"].str.contains("itsmarta.com/ride/planner").all()
    assert sample["planner_url"].str.contains("date=2026-09-07").all()
    assert sample["planner_url"].str.contains("results=true").all()


def test_score_completed_checks_uses_only_numeric_reviews() -> None:
    result = score_completed_checks(
        pd.DataFrame({"travel_time_minutes": [20.0, 50.0, 60.0], "planner_minutes": [25.0, 70.0, None]})
    )
    assert result.loc[0, "completed_planner_cases"] == 2
    assert result.loc[0, "comparable_numeric_cases"] == 2
    assert result.loc[0, "mean_absolute_difference_minutes"] == 12.5
    assert result.loc[0, "share_within_15_minutes"] == 0.5


def test_holdout_excludes_reviewed_pairs() -> None:
    od = pd.DataFrame({"origin_id": ["o1"] * 6, "destination_id": list("abcdef"),
                       "travel_time_minutes": [20, 40, 70, 100, None, 25]})
    origins = pd.DataFrame({"geoid": ["o1"], "lat": [33.75], "lon": [-84.39]})
    destinations = pd.DataFrame({"id": list("abcdef"), "label": list("abcdef"),
                                 "category": ["clinic"] * 6, "lat": [33.75] * 6,
                                 "lon": [-84.39] * 6})
    reviewed = pd.DataFrame({"origin_id": ["o1"], "destination_id": ["a"]})
    holdout = build_holdout(od, origins, destinations, reviewed, service_date="20260914",
                            departure="08:00", sample_per_band=1, seed=7)
    assert "a" not in set(holdout["destination_id"])
    assert set(holdout["validation_split"]) == {"holdout"}


def test_holdout_skips_an_empty_band_without_substituting_cases() -> None:
    od = pd.DataFrame({"origin_id": ["o1"] * 4, "destination_id": list("abcd"),
                       "travel_time_minutes": [20, 40, 70, 100]})
    origins = pd.DataFrame({"geoid": ["o1"], "lat": [33.75], "lon": [-84.39]})
    destinations = pd.DataFrame({"id": list("abcd"), "label": list("abcd"),
                                 "category": ["clinic"] * 4, "lat": [33.75] * 4,
                                 "lon": [-84.39] * 4})
    holdout = build_holdout(od, origins, destinations, pd.DataFrame(columns=["origin_id", "destination_id"]),
                            service_date="20260914", departure="08:00", sample_per_band=1, seed=7)
    assert len(holdout) == 4
    assert "no_scheduled_arrival" not in set(holdout["model_time_band"])


def test_publication_gate_requires_no_false_no_arrivals() -> None:
    assert passes_publication_gate(pd.DataFrame([{
        "model_no_arrival_with_planner_route": 0,
        "median_absolute_difference_minutes": 9.0,
        "share_within_15_minutes": 0.8,
    }]))
    assert not passes_publication_gate(pd.DataFrame([{
        "model_no_arrival_with_planner_route": 1,
        "median_absolute_difference_minutes": 2.0,
        "share_within_15_minutes": 1.0,
    }]))


def test_proxy_calibration_excludes_prior_tract_pair_for_every_proxy() -> None:
    od = pd.DataFrame({"origin_id": ["o1::north", "o1::south", "o2::north"],
                       "destination_id": ["d", "d", "d"], "travel_time_minutes": [20, 21, 22]})
    prior = pd.DataFrame({"origin_id": ["o1"], "destination_id": ["d"]})
    remaining = exclude_prior_tract_destination_pairs(od, prior)
    assert remaining.origin_id.tolist() == ["o2::north"]


def test_manual_outcomes_support_numeric_routes_and_no_route() -> None:
    minutes, no_route = parse_planner_outcomes("17.5,no_route,29", expected_count=3)
    assert minutes == [17.5, None, 29.0]
    assert no_route == [False, True, False]
