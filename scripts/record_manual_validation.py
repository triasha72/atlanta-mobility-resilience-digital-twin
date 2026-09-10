"""Record ordered, manually observed itinerary durations in a validation sample."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--planner-minutes",
        required=True,
        help="Comma-separated durations, ordered exactly as the input CSV rows.",
    )
    parser.add_argument("--reviewer", default="MARTA public trip planner")
    args = parser.parse_args()

    frame = pd.read_csv(args.input)
    values = [float(value) for value in args.planner_minutes.split(",")]
    if len(values) != len(frame):
        raise ValueError(f"received {len(values)} durations for {len(frame)} cases")
    if (pd.Series(values) <= 0).any():
        raise ValueError("planner durations must be positive")

    frame["planner_minutes"] = values
    frame["planner_no_route"] = False
    frame["planner_itinerary_notes"] = "First displayed public planner itinerary"
    frame["reviewer"] = args.reviewer
    frame["reviewed_at"] = datetime.now(UTC).isoformat()
    frame.to_csv(args.input, index=False)
    print(f"recorded {len(frame)} manual checks in {args.input}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
