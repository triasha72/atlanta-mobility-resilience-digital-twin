"""Score completed manual planner checks without treating them as ground truth."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def score_completed_checks(frame: pd.DataFrame) -> pd.DataFrame:
    """Summarize only reviewed rows with a numeric planner time."""
    reviewed = frame.dropna(subset=["planner_minutes"]).copy()
    if reviewed.empty:
        raise ValueError("no numeric planner_minutes values found; complete manual checks first")
    reviewed["absolute_difference_minutes"] = (
        reviewed["travel_time_minutes"] - reviewed["planner_minutes"]
    ).abs()
    return pd.DataFrame(
        [{
            "completed_numeric_cases": len(reviewed),
            "mean_absolute_difference_minutes": reviewed["absolute_difference_minutes"].mean(),
            "median_absolute_difference_minutes": reviewed["absolute_difference_minutes"].median(),
            "share_within_15_minutes": (reviewed["absolute_difference_minutes"] <= 15).mean(),
        }]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    parser.add_argument("--cases-output", type=Path, required=True)
    args = parser.parse_args()
    frame = pd.read_csv(args.input)
    summary = score_completed_checks(frame)
    reviewed = frame.dropna(subset=["planner_minutes"]).copy()
    reviewed["absolute_difference_minutes"] = (
        reviewed["travel_time_minutes"] - reviewed["planner_minutes"]
    ).abs()
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.cases_output.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.summary_output, index=False)
    reviewed.to_csv(args.cases_output, index=False)
    print(f"wrote validation summary to {args.summary_output}")
    print(f"wrote reviewed cases to {args.cases_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
