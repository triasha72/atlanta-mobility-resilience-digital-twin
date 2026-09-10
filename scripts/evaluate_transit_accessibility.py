"""Evaluate tract-to-destination walk-transit-walk accessibility for one service date."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from amrdt.transit import (
    arrival_at_destination,
    arrivals_at_stops,
    build_walking_transfer_index,
    load_active_schedule,
)
from amrdt.walking import (
    load_walk_graph,
    walk_seconds_from_stops_to_point,
    walk_seconds_to_points,
    walk_seconds_to_stops,
)


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
    parser.add_argument("--origins", type=Path)
    parser.add_argument("--destinations", type=Path)
    parser.add_argument(
        "--od-pairs",
        type=Path,
        help="Optional paired validation rows with origin_lat/origin_lon and destination_lat/destination_lon.",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-walk-meters", type=float, default=2500.0)
    parser.add_argument("--max-transfer-walk-meters", type=float, default=250.0)
    parser.add_argument("--max-direct-walk-meters", type=float, default=5000.0)
    parser.add_argument("--walk-graph", type=Path)
    args = parser.parse_args()
    if args.od_pairs is None and (args.origins is None or args.destinations is None):
        parser.error("provide --origins and --destinations, or --od-pairs")
    if args.od_pairs is not None and (args.origins is not None or args.destinations is not None):
        parser.error("--od-pairs cannot be combined with --origins or --destinations")
    stops, connections = load_active_schedule(args.gtfs, args.service_date)
    walking_transfers = build_walking_transfer_index(
        stops, max_walk_meters=args.max_transfer_walk_meters
    )
    walk_graph = load_walk_graph(args.walk_graph) if args.walk_graph else None
    if args.od_pairs is not None:
        pairs = pd.read_csv(args.od_pairs)
        required_columns = {
            "origin_id", "origin_lat", "origin_lon", "destination_id",
            "destination_lat", "destination_lon",
        }
        missing = required_columns - set(pairs.columns)
        if missing:
            raise ValueError(f"paired input missing columns: {sorted(missing)}")
        origins = destinations = None
    else:
        origins, destinations = pd.read_csv(args.origins), pd.read_csv(args.destinations)
    start = departure_seconds(args.departure)
    walk_destinations = (
        pairs[["destination_id", "destination_lat", "destination_lon"]]
        .drop_duplicates("destination_id")
        .rename(columns={"destination_id": "id", "destination_lat": "lat", "destination_lon": "lon"})
        if args.od_pairs is not None
        else destinations
    )
    # Egress walking depends only on the destination.  Cache it once rather
    # than rerunning a network shortest-path search for every origin.
    destination_walks = (
        {
            str(destination.id): walk_seconds_from_stops_to_point(
                walk_graph,
                stops=stops,
                lat=float(destination.lat),
                lon=float(destination.lon),
                max_walk_meters=args.max_walk_meters,
            )
            for destination in walk_destinations.itertuples(index=False)
        }
        if walk_graph is not None
        else {}
    )
    rows = []
    if args.od_pairs is not None:
        for pair in pairs.itertuples(index=False):
            direct_walk = {} if walk_graph is None else walk_seconds_to_points(
                walk_graph, lat=float(pair.origin_lat), lon=float(pair.origin_lon),
                points={str(pair.destination_id): (float(pair.destination_lat), float(pair.destination_lon))},
                max_walk_meters=args.max_direct_walk_meters,
            )
            initial_walk_seconds = None if walk_graph is None else walk_seconds_to_stops(
                walk_graph, lat=float(pair.origin_lat), lon=float(pair.origin_lon), stops=stops,
                max_walk_meters=args.max_walk_meters,
            )
            arrivals = arrivals_at_stops(
                stops, connections, origin_lat=float(pair.origin_lat), origin_lon=float(pair.origin_lon),
                departure_seconds=start, max_walk_meters=args.max_walk_meters,
                walking_transfers=walking_transfers, initial_walk_seconds=initial_walk_seconds,
            )
            destination_walk_seconds = (
                None if walk_graph is None else destination_walks[str(pair.destination_id)]
            )
            arrival = arrival_at_destination(
                stops, arrivals, destination_lat=float(pair.destination_lat),
                destination_lon=float(pair.destination_lon), max_walk_meters=args.max_walk_meters,
                destination_walk_seconds=destination_walk_seconds,
            )
            direct_seconds = direct_walk.get(str(pair.destination_id))
            if direct_seconds is not None:
                direct_arrival = start + direct_seconds
                arrival = direct_arrival if arrival is None else min(arrival, direct_arrival)
            row = pair._asdict()
            row.update({
                "origin_id": str(pair.origin_id), "destination_id": str(pair.destination_id),
                "departure_seconds": start, "arrival_seconds": arrival,
                "travel_time_minutes": None if arrival is None else (arrival - start) / 60,
                "reachable": arrival is not None,
            })
            rows.append(row)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).to_csv(args.output, index=False)
        print(f"wrote {len(rows)} paired OD rows to {args.output}")
        return 0

    origin_id = "id" if "id" in origins else "geoid"
    for origin in origins.itertuples(index=False):
        direct_walk = {} if walk_graph is None else walk_seconds_to_points(
            walk_graph, lat=float(origin.lat), lon=float(origin.lon),
            points={
                str(destination.id): (float(destination.lat), float(destination.lon))
                for destination in destinations.itertuples(index=False)
            },
            max_walk_meters=args.max_direct_walk_meters,
        )
        initial_walk_seconds = None if walk_graph is None else walk_seconds_to_stops(
            walk_graph, lat=float(origin.lat), lon=float(origin.lon), stops=stops,
            max_walk_meters=args.max_walk_meters,
        )
        arrivals = arrivals_at_stops(
            stops, connections, origin_lat=float(origin.lat), origin_lon=float(origin.lon),
            departure_seconds=start, max_walk_meters=args.max_walk_meters,
            walking_transfers=walking_transfers,
            initial_walk_seconds=initial_walk_seconds,
        )
        for destination in destinations.itertuples(index=False):
            destination_walk_seconds = (
                None
                if walk_graph is None
                else destination_walks[str(destination.id)]
            )
            arrival = arrival_at_destination(
                stops, arrivals, destination_lat=float(destination.lat),
                destination_lon=float(destination.lon), max_walk_meters=args.max_walk_meters,
                destination_walk_seconds=destination_walk_seconds,
            )
            direct_seconds = direct_walk.get(str(destination.id))
            if direct_seconds is not None:
                direct_arrival = start + direct_seconds
                arrival = direct_arrival if arrival is None else min(arrival, direct_arrival)
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
