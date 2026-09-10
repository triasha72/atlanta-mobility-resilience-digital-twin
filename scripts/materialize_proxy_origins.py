"""Convert labeled tract access proxies into evaluator-compatible origins."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def materialize(proxies: pd.DataFrame) -> pd.DataFrame:
    """Preserve tract/proxy identifiers while supplying the evaluator id/lat/lon shape."""
    required = {"tract_geoid", "proxy_label", "lat", "lon"}
    if missing := required - set(proxies.columns):
        raise ValueError(f"proxy input missing columns: {sorted(missing)}")
    result = proxies.copy()
    result["id"] = result["tract_geoid"].astype(str) + "::" + result["proxy_label"]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = materialize(pd.read_csv(args.input, dtype={"tract_geoid": str}))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print(f"wrote {len(result)} evaluator-compatible proxy origins to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
