"""Test whether aggregate synthetic demand changes the road-resilience conclusion."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from amrdt.demand import resilience_conclusion


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demand", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--scenario", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = resilience_conclusion(
        pd.read_csv(args.demand, dtype={"origin_id": str, "destination_id": str}),
        pd.read_csv(args.baseline, dtype={"origin_id": str, "destination_id": str}),
        pd.read_csv(args.scenario, dtype={"origin_id": str, "destination_id": str}),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print(result.to_json(orient="records", indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
