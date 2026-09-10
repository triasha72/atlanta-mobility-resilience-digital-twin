import pandas as pd

from scripts.create_tract_access_proxies import build_proxies


def test_build_proxies_emits_centroid_and_four_bounded_offsets() -> None:
    origins = pd.DataFrame({"geoid": ["1"], "lat": [33.75], "lon": [-84.39], "population_weight": [1.0]})
    gazetteer = pd.DataFrame({"GEOID": ["1"], "ALAND": [1_000_000]})
    result = build_proxies(origins, gazetteer, max_radius_m=200)
    assert set(result.proxy_label) == {"centroid", "north", "south", "east", "west"}
    assert len(result) == 5
    assert result.proxy_radius_m.eq(200).all()
    assert result.population_weight.sum() == 1.0
