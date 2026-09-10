"""Draw a fresh proxy-origin calibration sample excluding all prior OD routes."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

try:  # Supports both `python scripts/...` and package imports in tests.
    from scripts.create_transit_validation_sample import build_sample
except ModuleNotFoundError:  # pragma: no cover - direct script execution only
    from create_transit_validation_sample import build_sample


def tract_key(values: pd.Series) -> pd.Series:
    """Canonicalize centroid or proxy origin IDs to an underlying tract ID."""
    return values.astype(str).str.split("::").str[0]


def exclude_prior_tract_destination_pairs(od: pd.DataFrame, prior: pd.DataFrame) -> pd.DataFrame:
    """Exclude prior routes even when the candidate uses a proxy origin ID."""
    candidate = od.copy()
    candidate["tract_geoid"] = tract_key(candidate["origin_id"])
    used = prior.loc[:, ["origin_id", "destination_id"]].copy()
    used["tract_geoid"] = tract_key(used["origin_id"])
    used = used[["tract_geoid", "destination_id"]].drop_duplicates().assign(_used=True)
    return candidate.merge(used, on=["tract_geoid", "destination_id"], how="left").query("_used.isna()") \
        .drop(columns=["tract_geoid", "_used"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--od", type=Path, required=True)
    parser.add_argument("--origins", type=Path, required=True)
    parser.add_argument("--destinations", type=Path, required=True)
    parser.add_argument("--prior", type=Path, nargs="+", required=True)
    parser.add_argument("--service-date", required=True)
    parser.add_argument("--departure", required=True)
    parser.add_argument("--seed", type=int, default=20260915)
    parser.add_argument("--sample-per-band", type=int, default=4)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prior = pd.concat([pd.read_csv(path, dtype={"origin_id": str}) for path in args.prior], ignore_index=True)
    candidate = exclude_prior_tract_destination_pairs(pd.read_csv(args.od, dtype={"origin_id": str}), prior)
    result = build_sample(candidate, pd.read_csv(args.origins, dtype={"id": str}), pd.read_csv(args.destinations),
                          service_date=args.service_date, departure=args.departure,
                          sample_per_band=args.sample_per_band, seed=args.seed, allow_empty_bands=True)
    result["validation_split"] = "proxy_calibration"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print(f"wrote {len(result)} fresh proxy calibration cases to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
