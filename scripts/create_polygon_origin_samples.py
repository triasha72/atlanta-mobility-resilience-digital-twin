"""Create deterministic tract-polygon-constrained transit origin samples."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point


def _seed(geoid: str, seed: int) -> int:
    return int(hashlib.sha256(f"{seed}:{geoid}".encode()).hexdigest()[:16], 16)


def interior_points(geometry, *, count: int, seed: int) -> list[Point]:
    """Use deterministic rejection sampling in a polygon bounding box."""
    if count <= 0:
        raise ValueError("count must be positive")
    rng = np.random.default_rng(seed)
    min_x, min_y, max_x, max_y = geometry.bounds
    points = []
    for _ in range(count * 10_000):
        point = Point(rng.uniform(min_x, max_x), rng.uniform(min_y, max_y))
        if geometry.contains(point):
            points.append(point)
            if len(points) == count:
                return points
    raise RuntimeError("could not draw enough interior points")


def build_samples(origins: pd.DataFrame, tracts: gpd.GeoDataFrame, *, count: int, seed: int) -> pd.DataFrame:
    """Create equally weighted, strictly interior samples for selected tract GEOIDs."""
    geometry_by_geoid = tracts.assign(GEOID=tracts["GEOID"].astype(str)).set_index("GEOID").geometry
    rows = []
    for origin in origins.itertuples(index=False):
        geoid = str(origin.geoid)
        if geoid not in geometry_by_geoid.index:
            raise ValueError(f"tract geometry missing for {geoid}")
        points = interior_points(geometry_by_geoid[geoid], count=count, seed=_seed(geoid, seed))
        for number, point in enumerate(points):
            rows.append({"id": f"{geoid}::polygon::{number}", "tract_geoid": geoid,
                         "sample_number": number, "lat": point.y, "lon": point.x,
                         "population_weight": float(origin.population_weight) / count})
    return pd.DataFrame(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origins", type=Path, required=True)
    parser.add_argument("--tracts", type=Path, required=True)
    parser.add_argument("--samples-per-tract", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20260915)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    origins = pd.read_csv(args.origins, dtype={"geoid": str})
    tracts = gpd.read_file(args.tracts).to_crs("EPSG:4326")
    result = build_samples(origins, tracts, count=args.samples_per_tract, seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print(f"wrote {len(result)} polygon-constrained origins to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
