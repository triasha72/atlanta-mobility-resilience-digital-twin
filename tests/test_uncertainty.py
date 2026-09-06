import pandas as pd

from amrdt.uncertainty import population_weighted_accessibility_intervals


def test_population_uncertainty_is_reproducible_and_ordered():
    origins = pd.DataFrame({
        "geoid": ["1", "2"], "population": [100, 200], "population_moe": [10, 20]
    })
    accessibility = pd.DataFrame({
        "origin_id": ["1", "2"], "accessible_opportunities": [2.0, 8.0]
    })
    first = population_weighted_accessibility_intervals(
        {"baseline": accessibility}, origins, draws=200, seed=7
    )
    second = population_weighted_accessibility_intervals(
        {"baseline": accessibility}, origins, draws=200, seed=7
    )
    pd.testing.assert_frame_equal(first, second)
    row = first.iloc[0]
    assert row["population_weighted_accessibility_p05"] <= row[
        "population_weighted_accessibility_mean"
    ] <= row["population_weighted_accessibility_p95"]
