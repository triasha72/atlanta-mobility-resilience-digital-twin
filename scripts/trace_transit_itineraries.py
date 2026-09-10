"""Produce modeled itinerary legs for paired transit diagnostic routes."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from evaluate_transit_accessibility import departure_seconds

from amrdt.transit import build_walking_transfer_index, load_active_schedule, trace_itinerary
from amrdt.walking import load_walk_graph, walk_seconds_from_stops_to_point, walk_seconds_to_stops


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gtfs", type=Path, required=True)
    parser.add_argument("--pairs", type=Path, required=True)
    parser.add_argument("--walk-graph", type=Path, required=True)
    parser.add_argument("--service-date", required=True)
    parser.add_argument("--departure", default="08:00")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    stops, connections = load_active_schedule(args.gtfs, args.service_date)
    walking_transfers = build_walking_transfer_index(stops)
    graph = load_walk_graph(args.walk_graph)
    rows = []
    for pair in pd.read_csv(args.pairs).itertuples(index=False):
        legs = trace_itinerary(
            stops, connections, origin_lat=float(pair.origin_lat), origin_lon=float(pair.origin_lon),
            destination_lat=float(pair.destination_lat), destination_lon=float(pair.destination_lon),
            departure_seconds=departure_seconds(args.departure),
            initial_walk_seconds=walk_seconds_to_stops(graph, lat=float(pair.origin_lat), lon=float(pair.origin_lon), stops=stops, max_walk_meters=2500),
            destination_walk_seconds=walk_seconds_from_stops_to_point(graph, stops=stops, lat=float(pair.destination_lat), lon=float(pair.destination_lon), max_walk_meters=2500),
            walking_transfers=walking_transfers,
        )
        for order, leg in enumerate(legs or []):
            rows.append({"origin_id": pair.origin_id, "destination_id": pair.destination_id, "leg_order": order, **leg.__dict__})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(args.output, index=False)
    print(f"wrote {len(rows)} itinerary legs to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
