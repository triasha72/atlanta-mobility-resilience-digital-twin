"""Score completed manual planner checks without treating them as ground truth."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def score_completed_checks(frame: pd.DataFrame) -> pd.DataFrame:
    """Summarize only reviewed rows with a numeric planner time."""
    reviewed = frame.dropna(subset=["planner_minutes"]).copy()
    comparable = reviewed.dropna(subset=["travel_time_minutes"]).copy()
    if reviewed.empty:
        raise ValueError("no numeric planner_minutes values found; complete manual checks first")
    if comparable.empty:
        raise ValueError("no cases contain both a model and planner travel time")
    reviewed["absolute_difference_minutes"] = (
        reviewed["travel_time_minutes"] - reviewed["planner_minutes"]
    ).abs()
    comparable = reviewed.dropna(subset=["travel_time_minutes"]).copy()
    return pd.DataFrame(
        [{
            "completed_planner_cases": len(reviewed),
            "comparable_numeric_cases": len(comparable),
            "model_no_arrival_with_planner_route": int(
                reviewed["travel_time_minutes"].isna().sum()
            ),
            "mean_absolute_difference_minutes": comparable["absolute_difference_minutes"].mean(),
            "median_absolute_difference_minutes": comparable["absolute_difference_minutes"].median(),
            "share_within_15_minutes": (comparable["absolute_difference_minutes"] <= 15).mean(),
        }]
    )


def passes_publication_gate(summary: pd.DataFrame) -> bool:
    """Return whether an independent holdout meets pre-registered publication gates."""
    if len(summary) != 1:
        raise ValueError("publication gate expects one summary row")
    row = summary.iloc[0]
    return bool(
        row["model_no_arrival_with_planner_route"] == 0
        and row["median_absolute_difference_minutes"] <= 10
        and row["share_within_15_minutes"] >= 0.8
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    parser.add_argument("--cases-output", type=Path, required=True)
    parser.add_argument("--gate-output", type=Path)
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
    # Preserve every checked pair, including model no-arrivals, so later
    # holdout sampling can exclude the entire calibration set.
    reviewed.to_csv(args.cases_output, index=False)
    if args.gate_output:
        args.gate_output.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame([{"publication_gate_passed": passes_publication_gate(summary)}]).to_csv(
            args.gate_output, index=False
        )
    print(f"wrote validation summary to {args.summary_output}")
    print(f"wrote reviewed cases to {args.cases_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
