"""Evaluate tract-to-destination walk-transit-walk accessibility for one service date."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from amrdt.transit import arrival_at_destination, arrivals_at_stops, load_active_schedule


def departure_seconds(value: str) -> int:
    hours, minutes = (int(part) for part in value.split(":"))
    if not 0 <= hours <= 23 or not 0 <= minutes <= 59:
        raise ValueError("departure must use 24-hour HH:MM")
    return (hours * 60 + minutes) * 60


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gtfs", type=Path, required=True)
    parser.add_argument("--service-date", required=True)
    parser.add_argument("--departure", default="08:00")
    parser.add_argument("--origins", type=Path, required=True)
    parser.add_argument("--destinations", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-walk-meters", type=float, default=800.0)
    args = parser.parse_args()
    stops, connections = load_active_schedule(args.gtfs, args.service_date)
    origins, destinations = pd.read_csv(args.origins), pd.read_csv(args.destinations)
    origin_id = "id" if "id" in origins else "geoid"
    start = departure_seconds(args.departure)
    rows = []
    for origin in origins.itertuples(index=False):
        arrivals = arrivals_at_stops(
            stops, connections, origin_lat=float(origin.lat), origin_lon=float(origin.lon),
            departure_seconds=start, max_walk_meters=args.max_walk_meters,
        )
        for destination in destinations.itertuples(index=False):
            arrival = arrival_at_destination(
                stops, arrivals, destination_lat=float(destination.lat),
                destination_lon=float(destination.lon), max_walk_meters=args.max_walk_meters,
            )
            rows.append({
                "origin_id": str(getattr(origin, origin_id)),
                "destination_id": str(destination.id),
                "departure_seconds": start,
                "arrival_seconds": arrival,
                "travel_time_minutes": None if arrival is None else (arrival - start) / 60,
                "reachable": arrival is not None,
            })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(args.output, index=False)
    print(f"wrote {len(rows)} OD rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
