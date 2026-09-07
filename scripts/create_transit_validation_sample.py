"""Create a reproducible, stratified sample for manual MARTA planner checks."""

from __future__ import annotations

import argparse
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd


def time_band(minutes: float) -> str:
    """Assign an OD result to a practical scheduled-travel-time band."""
    if pd.isna(minutes):
        return "no_scheduled_arrival"
    if minutes <= 30:
        return "00_30_minutes"
    if minutes <= 60:
        return "31_60_minutes"
    if minutes <= 90:
        return "61_90_minutes"
    return "over_90_minutes"


def planner_url(
    *, origin_label: str, origin_lat: float, origin_lon: float,
    destination_label: str, destination_lat: float, destination_lon: float,
    service_date: str, departure: str,
) -> str:
    """Build a public MARTA Tracker URL for the exact sampled map points."""
    parameters = {
        "from": f"{origin_label}::{origin_lat},{origin_lon}",
        "to": f"{destination_label}::{destination_lat},{destination_lon}",
        "depArr": "DEPART",
        "date": f"{service_date[:4]}-{service_date[4:6]}-{service_date[6:]}",
        "time": departure,
    }
    return f"https://tracker.itsmarta.com/plan?{urlencode(parameters)}"


def build_sample(
    od: pd.DataFrame,
    origins: pd.DataFrame,
    destinations: pd.DataFrame,
    *,
    service_date: str,
    departure: str,
    sample_per_band: int,
    seed: int,
) -> pd.DataFrame:
    """Return a fixed-size stratified sample with empty human-review fields."""
    required_od = {"origin_id", "destination_id", "travel_time_minutes"}
    if missing := required_od - set(od.columns):
        raise ValueError(f"OD input is missing required columns: {sorted(missing)}")
    origins = origins.rename(columns={"geoid": "origin_id", "lat": "origin_lat", "lon": "origin_lon"})
    destinations = destinations.rename(
        columns={"id": "destination_id", "lat": "destination_lat", "lon": "destination_lon"}
    )
    merged = od.merge(origins[["origin_id", "origin_lat", "origin_lon"]], on="origin_id")
    merged = merged.merge(
        destinations[["destination_id", "label", "category", "destination_lat", "destination_lon"]],
        on="destination_id",
    )
    merged["model_time_band"] = merged["travel_time_minutes"].map(time_band)
    order = ["00_30_minutes", "31_60_minutes", "61_90_minutes", "over_90_minutes", "no_scheduled_arrival"]
    sampled = []
    for index, band in enumerate(order):
        candidates = merged[merged["model_time_band"] == band]
        if len(candidates) < sample_per_band:
            raise ValueError(f"need {sample_per_band} rows in {band}, found {len(candidates)}")
        sampled.append(candidates.sample(n=sample_per_band, random_state=seed + index))
    result = pd.concat(sampled, ignore_index=True)
    result["origin_label"] = "ACS tract centroid"
    result["planner_url"] = result.apply(
        lambda row: planner_url(
            origin_label=row.origin_label,
            origin_lat=row.origin_lat,
            origin_lon=row.origin_lon,
            destination_label=row.label,
            destination_lat=row.destination_lat,
            destination_lon=row.destination_lon,
            service_date=service_date,
            departure=departure,
        ),
        axis=1,
    )
    result["planner_minutes"] = pd.NA
    result["planner_no_route"] = pd.NA
    result["planner_itinerary_notes"] = pd.NA
    result["reviewer"] = pd.NA
    result["reviewed_at"] = pd.NA
    columns = [
        "origin_id", "origin_lat", "origin_lon", "destination_id", "label", "category",
        "destination_lat", "destination_lon", "travel_time_minutes", "model_time_band",
        "planner_url", "planner_minutes", "planner_no_route", "planner_itinerary_notes",
        "reviewer", "reviewed_at",
    ]
    return result[columns].sort_values(["model_time_band", "origin_id", "destination_id"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--od", type=Path, required=True)
    parser.add_argument("--origins", type=Path, required=True)
    parser.add_argument("--destinations", type=Path, required=True)
    parser.add_argument("--service-date", required=True)
    parser.add_argument("--departure", required=True)
    parser.add_argument("--sample-per-band", type=int, default=4)
    parser.add_argument("--seed", type=int, default=20260907)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.sample_per_band <= 0:
        raise ValueError("sample-per-band must be positive")
    sample = build_sample(
        pd.read_csv(args.od), pd.read_csv(args.origins), pd.read_csv(args.destinations),
        service_date=args.service_date, departure=args.departure,
        sample_per_band=args.sample_per_band, seed=args.seed,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sample.to_csv(args.output, index=False)
    print(f"wrote {len(sample)} validation cases to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
