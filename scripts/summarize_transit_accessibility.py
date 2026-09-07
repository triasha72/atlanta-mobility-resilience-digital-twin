"""Summarize schedule-based MARTA accessibility runs at practical trip-time limits."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {
    "origin_id",
    "destination_id",
    "departure_seconds",
    "travel_time_minutes",
}


def departure_label(seconds: int) -> str:
    """Format seconds after midnight as a 24-hour departure label."""
    return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}"


def load_run(path: Path) -> pd.DataFrame:
    """Load one OD result file and attach its departure label."""
    frame = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"{path} is missing required columns: {sorted(missing)}")
    departures = frame["departure_seconds"].dropna().unique()
    if len(departures) != 1:
        raise ValueError(f"{path} must contain exactly one departure time")
    frame["departure"] = departure_label(int(departures[0]))
    return frame


def summarize_runs(inputs: list[Path], thresholds: list[int]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return system-wide and per-origin accessibility summaries."""
    summary_rows: list[dict[str, object]] = []
    origin_rows: list[dict[str, object]] = []
    for path in inputs:
        frame = load_run(path)
        departure = frame["departure"].iloc[0]
        od_pairs = len(frame)
        origin_count = frame["origin_id"].nunique()
        destination_count = frame["destination_id"].nunique()
        for threshold in thresholds:
            reachable = frame["travel_time_minutes"].le(threshold)
            reachable_pairs = int(reachable.sum())
            summary_rows.append(
                {
                    "source_file": path.name,
                    "departure": departure,
                    "time_limit_minutes": threshold,
                    "od_pairs": od_pairs,
                    "origins": origin_count,
                    "destinations": destination_count,
                    "reachable_pairs": reachable_pairs,
                    "reachable_od_share": reachable_pairs / od_pairs if od_pairs else 0.0,
                }
            )
            by_origin = (
                frame.assign(reachable_within_limit=reachable)
                .groupby("origin_id", as_index=False)["reachable_within_limit"]
                .agg(["sum", "count"])
                .reset_index()
                .rename(
                    columns={
                        "sum": "reachable_destinations",
                        "count": "total_destinations",
                    }
                )
            )
            by_origin["departure"] = departure
            by_origin["time_limit_minutes"] = threshold
            by_origin["reachable_destination_share"] = (
                by_origin["reachable_destinations"] / by_origin["total_destinations"]
            )
            origin_rows.extend(by_origin.to_dict("records"))
    summary = pd.DataFrame(summary_rows).sort_values(["departure", "time_limit_minutes"])
    origins = pd.DataFrame(origin_rows).sort_values(
        ["departure", "time_limit_minutes", "reachable_destination_share", "origin_id"],
        ascending=[True, True, False, True],
    )
    return summary, origins


def plot_summary(summary: pd.DataFrame, output: Path) -> None:
    """Write a transparent comparison of scheduled access across departure times."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, axis = plt.subplots(figsize=(8, 5))
    for departure, group in summary.groupby("departure", sort=True):
        axis.plot(
            group["time_limit_minutes"],
            group["reachable_od_share"] * 100,
            marker="o",
            linewidth=2,
            label=departure,
        )
    axis.set_xlabel("Maximum door-to-door trip time (minutes)")
    axis.set_ylabel("OD pairs reachable (%)")
    axis.set_title("Scheduled MARTA access to mapped essential destinations")
    axis.set_xticks(sorted(summary["time_limit_minutes"].unique()))
    axis.set_ylim(bottom=0)
    axis.grid(axis="y", alpha=0.25)
    axis.legend(title="Departure")
    figure.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=180)
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, nargs="+", required=True)
    parser.add_argument("--thresholds", type=int, nargs="+", default=[30, 45, 60, 90])
    parser.add_argument("--summary-output", type=Path, required=True)
    parser.add_argument("--origin-output", type=Path, required=True)
    parser.add_argument("--figure-output", type=Path, required=True)
    args = parser.parse_args()
    if any(threshold <= 0 for threshold in args.thresholds):
        raise ValueError("thresholds must be positive minutes")
    summary, origins = summarize_runs(args.inputs, sorted(set(args.thresholds)))
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.origin_output.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.summary_output, index=False)
    origins.to_csv(args.origin_output, index=False)
    plot_summary(summary, args.figure_output)
    print(f"wrote {len(summary)} summary rows to {args.summary_output}")
    print(f"wrote {len(origins)} origin rows to {args.origin_output}")
    print(f"wrote figure to {args.figure_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
