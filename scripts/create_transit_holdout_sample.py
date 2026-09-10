"""Create a stratified transit-validation holdout excluding reviewed OD pairs."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

try:  # Supports both `python scripts/...` and package imports in tests.
    from scripts.create_transit_validation_sample import build_sample
except ModuleNotFoundError:  # pragma: no cover - direct script execution only
    from create_transit_validation_sample import build_sample


def build_holdout(
    od: pd.DataFrame,
    origins: pd.DataFrame,
    destinations: pd.DataFrame,
    reviewed: pd.DataFrame,
    *,
    service_date: str,
    departure: str,
    sample_per_band: int,
    seed: int,
) -> pd.DataFrame:
    """Draw a new stratified sample after excluding prior reviewed OD pairs."""
    required = {"origin_id", "destination_id"}
    if missing := required - set(reviewed.columns):
        raise ValueError(f"reviewed input is missing required columns: {sorted(missing)}")
    reviewed_pairs = reviewed.loc[:, ["origin_id", "destination_id"]].drop_duplicates()
    candidate = od.merge(
        reviewed_pairs.assign(_reviewed=True), on=["origin_id", "destination_id"], how="left"
    )
    candidate = candidate[candidate["_reviewed"].isna()].drop(columns="_reviewed")
    result = build_sample(
        candidate, origins, destinations, service_date=service_date, departure=departure,
        sample_per_band=sample_per_band, seed=seed, allow_empty_bands=True,
    )
    result["validation_split"] = "holdout"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--od", type=Path, required=True)
    parser.add_argument("--origins", type=Path, required=True)
    parser.add_argument("--destinations", type=Path, required=True)
    parser.add_argument("--reviewed", type=Path, required=True)
    parser.add_argument("--service-date", required=True)
    parser.add_argument("--departure", required=True)
    parser.add_argument("--sample-per-band", type=int, default=4)
    parser.add_argument("--seed", type=int, default=20260914)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_holdout(
        pd.read_csv(args.od), pd.read_csv(args.origins), pd.read_csv(args.destinations),
        pd.read_csv(args.reviewed), service_date=args.service_date, departure=args.departure,
        sample_per_band=args.sample_per_band, seed=args.seed,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print(f"wrote {len(result)} holdout validation cases to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
