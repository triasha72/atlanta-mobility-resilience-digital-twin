#!/usr/bin/env python3
"""Propagate ACS population uncertainty through completed scenario outputs."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from amrdt.uncertainty import population_weighted_accessibility_intervals


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--origins", type=Path, required=True)
    parser.add_argument("--outputs", type=Path, default=Path("outputs"))
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/accessibility_population_uncertainty.csv")
    )
    parser.add_argument("--draws", type=int, default=2_000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    scenarios = {
        path.stem.removeprefix("accessibility_"): pd.read_csv(path)
        for path in sorted(args.outputs.glob("accessibility_*.csv"))
        if path != args.output
    }
    if not scenarios:
        raise ValueError("no accessibility scenario outputs found")
    result = population_weighted_accessibility_intervals(
        scenarios, pd.read_csv(args.origins), draws=args.draws, seed=args.seed
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
