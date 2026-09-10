"""Create labeled area-equivalent tract access proxies for sensitivity analysis.

These are not asserted to fall inside tract boundaries.  They quantify how
single-centroid routing can vary until a polygon-backed residential sample is
available.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def build_proxies(origins: pd.DataFrame, gazetteer: pd.DataFrame, *, max_radius_m: float) -> pd.DataFrame:
    """Return centroid plus four area-equivalent radial sensitivity proxies."""
    areas = gazetteer.assign(GEOID=gazetteer["GEOID"].astype(str)).set_index("GEOID")["ALAND"]
    rows = []
    for origin in origins.itertuples(index=False):
        radius = min(max_radius_m, 0.5 * np.sqrt(float(areas[str(origin.geoid)]) / np.pi))
        offsets = [("centroid", 0.0, 0.0), ("north", radius, 0.0), ("south", -radius, 0.0),
                   ("east", 0.0, radius), ("west", 0.0, -radius)]
        for label, north_m, east_m in offsets:
            rows.append({"tract_geoid": str(origin.geoid), "proxy_label": label,
                         "lat": float(origin.lat) + north_m / 111_000,
                         "lon": float(origin.lon) + east_m / (111_000 * np.cos(np.radians(float(origin.lat)))),
                         "proxy_radius_m": radius, "population_weight": float(origin.population_weight) / len(offsets)})
    return pd.DataFrame(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origins", type=Path, required=True)
    parser.add_argument("--gazetteer", type=Path, required=True)
    parser.add_argument("--max-radius-m", type=float, default=1000.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.max_radius_m <= 0:
        raise ValueError("max-radius-m must be positive")
    gazetteer = pd.read_csv(args.gazetteer, sep="\t", dtype={"GEOID": str})
    result = build_proxies(pd.read_csv(args.origins, dtype={"geoid": str}), gazetteer, max_radius_m=args.max_radius_m)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print(f"wrote {len(result)} access sensitivity proxies to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
