"""Record ordered, manually observed itinerary durations in a validation sample."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd


def parse_planner_outcomes(values: str, expected_count: int) -> tuple[list[float | None], list[bool]]:
    """Parse ordered planner durations, allowing `no_route` for an empty result."""
    tokens = [value.strip() for value in values.split(",")]
    if len(tokens) != expected_count:
        raise ValueError(f"received {len(tokens)} outcomes for {expected_count} cases")
    minutes: list[float | None] = []
    no_route: list[bool] = []
    for token in tokens:
        if token.lower() in {"no_route", "no-route", "none"}:
            minutes.append(None)
            no_route.append(True)
            continue
        try:
            duration = float(token)
        except ValueError as error:
            raise ValueError(f"invalid planner outcome: {token!r}") from error
        if duration <= 0:
            raise ValueError("planner durations must be positive")
        minutes.append(duration)
        no_route.append(False)
    return minutes, no_route


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--planner-outcomes",
        required=True,
        help="Comma-separated durations or no_route, ordered exactly as the input CSV rows.",
    )
    parser.add_argument("--reviewer", default="MARTA public trip planner")
    args = parser.parse_args()

    frame = pd.read_csv(args.input)
    values, no_route = parse_planner_outcomes(args.planner_outcomes, len(frame))

    frame["planner_minutes"] = values
    frame["planner_no_route"] = no_route
    frame["planner_itinerary_notes"] = [
        "No public planner itinerary returned" if result else "First displayed public planner itinerary"
        for result in no_route
    ]
    frame["reviewer"] = args.reviewer
    frame["reviewed_at"] = datetime.now(UTC).isoformat()
    frame.to_csv(args.input, index=False)
    print(f"recorded {len(frame)} manual checks in {args.input}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
