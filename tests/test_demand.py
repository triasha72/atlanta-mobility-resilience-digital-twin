import pandas as pd

from amrdt.demand import margin_utility, synthetic_gravity_demand


def test_synthetic_demand_is_reproducible_and_preserves_aggregate_margins() -> None:
    origins = pd.DataFrame({"id": ["o1", "o2"], "population": [3, 1]})
    destinations = pd.DataFrame({"id": ["d1", "d2"], "opportunity_weight": [1, 3]})
    first = synthetic_gravity_demand(origins, destinations, trips=100_000, seed=4)
    second = synthetic_gravity_demand(origins, destinations, trips=100_000, seed=4)
    assert first.equals(second)
    utility = margin_utility(first, origins, destinations)
    assert utility.loc[0, "origin_margin_total_variation"] < 0.01
    assert utility.loc[0, "destination_margin_total_variation"] < 0.01
