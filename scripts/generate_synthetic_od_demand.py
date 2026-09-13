"""Create aggregate-only synthetic OD demand and a public-margin utility report."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from amrdt.demand import margin_utility, synthetic_gravity_demand


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origins", type=Path, required=True)
    parser.add_argument("--destinations", type=Path, required=True)
    parser.add_argument("--trips", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=20260912)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--utility-output", type=Path, required=True)
    args = parser.parse_args()
    origins, destinations = pd.read_csv(args.origins), pd.read_csv(args.destinations)
    demand = synthetic_gravity_demand(origins, destinations, trips=args.trips, seed=args.seed)
    utility = margin_utility(demand, origins, destinations)
    for path in (args.output, args.utility_output):
        path.parent.mkdir(parents=True, exist_ok=True)
    demand.to_csv(args.output, index=False)
    utility.assign(trips=args.trips, seed=args.seed).to_csv(args.utility_output, index=False)
    print(f"wrote {len(demand)} synthetic aggregate OD pairs to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
