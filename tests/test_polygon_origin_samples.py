import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon

from scripts.create_polygon_origin_samples import build_samples


def test_polygon_samples_are_reproducible_and_interior() -> None:
    origins = pd.DataFrame({"geoid": ["1"], "population_weight": [1.0]})
    tracts = gpd.GeoDataFrame({"GEOID": ["1"]}, geometry=[Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])])
    first = build_samples(origins, tracts, count=3, seed=7)
    second = build_samples(origins, tracts, count=3, seed=7)
    assert first.equals(second)
    assert all(tracts.geometry.iloc[0].contains(gpd.points_from_xy(first.lon, first.lat)))
    assert first.population_weight.sum() == 1.0
