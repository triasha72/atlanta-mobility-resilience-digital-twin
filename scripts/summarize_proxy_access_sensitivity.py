"""Summarize best/worst proxy travel-time variation by tract and destination."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def summarize(results: pd.DataFrame, proxies: pd.DataFrame) -> pd.DataFrame:
    """Return non-publishable proxy range statistics for each tract-destination pair."""
    lookup = proxies[["id", "tract_geoid"]].rename(columns={"id": "origin_id"})
    merged = results.merge(lookup, on="origin_id", validate="many_to_one")
    grouped = merged.groupby(["tract_geoid", "destination_id"])["travel_time_minutes"]
    return grouped.agg(proxy_min_minutes="min", proxy_max_minutes="max", proxy_count="count").reset_index()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--proxies", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = summarize(pd.read_csv(args.results), pd.read_csv(args.proxies, dtype={"tract_geoid": str}))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print(f"wrote {len(result)} tract-destination proxy ranges to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
