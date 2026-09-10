import pandas as pd

from scripts.materialize_proxy_origins import materialize
from scripts.summarize_proxy_access_sensitivity import summarize


def test_proxy_materialization_and_range_summary() -> None:
    proxies = materialize(pd.DataFrame({"tract_geoid": ["1", "1"], "proxy_label": ["centroid", "north"],
                                        "lat": [33.7, 33.71], "lon": [-84.4, -84.4]}))
    result = summarize(pd.DataFrame({"origin_id": proxies.id, "destination_id": ["d", "d"],
                                     "travel_time_minutes": [20.0, 30.0]}), proxies)
    assert result.loc[0, "proxy_min_minutes"] == 20.0
    assert result.loc[0, "proxy_max_minutes"] == 30.0
