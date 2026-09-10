"""Small schedule-aware GTFS transit router for reproducible accessibility studies."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path
from zipfile import ZipFile

from amrdt.gtfs import active_service_ids, haversine_meters, walking_transfer_minutes


@dataclass(frozen=True)
class Stop:
    stop_id: str
    lat: float
    lon: float


@dataclass(frozen=True)
class Connection:
    departure_stop: str
    arrival_stop: str
    departure_seconds: int
    arrival_seconds: int
    trip_id: str = ""


@dataclass(frozen=True)
class ItineraryLeg:
    """One explainable step in a modeled walk-transit-walk itinerary."""

    kind: str
    from_stop: str | None
    to_stop: str | None
    trip_id: str | None
    start_seconds: float
    end_seconds: float
    parent_kind: str | None = None


def _seconds(value: str) -> int:
    hours, minutes, seconds = (int(part) for part in value.split(":"))
    return hours * 3600 + minutes * 60 + seconds


def _read_rows(archive: ZipFile, name: str) -> list[dict[str, str]]:
    with archive.open(name) as raw:
        return list(csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")))


def load_active_schedule(path: str | Path, service_date: str) -> tuple[dict[str, Stop], list[Connection]]:
    """Load stops and consecutive active-trip connections for one GTFS service date."""

    active_services = active_service_ids(path, service_date)
    with ZipFile(path) as archive:
        stops = {
            row["stop_id"]: Stop(row["stop_id"], float(row["stop_lat"]), float(row["stop_lon"]))
            for row in _read_rows(archive, "stops.txt")
            if row.get("stop_lat") and row.get("stop_lon")
        }
        trip_services = {
            row["trip_id"]: row["service_id"] for row in _read_rows(archive, "trips.txt")
        }
        by_trip: dict[str, list[dict[str, str]]] = {}
        for row in _read_rows(archive, "stop_times.txt"):
            if trip_services.get(row["trip_id"]) in active_services:
                by_trip.setdefault(row["trip_id"], []).append(row)
    connections: list[Connection] = []
    for times in by_trip.values():
        ordered = sorted(times, key=lambda row: int(row["stop_sequence"]))
        for before, after in pairwise(ordered):
            if before["stop_id"] not in stops or after["stop_id"] not in stops:
                continue
            departure, arrival = _seconds(before["departure_time"]), _seconds(after["arrival_time"])
            if arrival >= departure:
                connections.append(
                    Connection(
                        before["stop_id"],
                        after["stop_id"],
                        departure,
                        arrival,
                        before["trip_id"],
                    )
                )
    return stops, sorted(connections, key=lambda item: item.departure_seconds)


def build_walking_transfer_index(
    stops: dict[str, Stop], *, max_walk_meters: float = 250.0
) -> dict[str, list[tuple[str, float]]]:
    """Index nearby stops that can be linked by a short transfer walk."""
    if max_walk_meters <= 0:
        raise ValueError("max_walk_meters must be positive")
    cell_size = max_walk_meters / 111_000
    cells: dict[tuple[int, int], list[Stop]] = {}
    for stop in stops.values():
        cell = (int(stop.lat // cell_size), int(stop.lon // cell_size))
        cells.setdefault(cell, []).append(stop)
    transfers: dict[str, list[tuple[str, float]]] = {stop_id: [] for stop_id in stops}
    for stop in stops.values():
        cell = (int(stop.lat // cell_size), int(stop.lon // cell_size))
        for lat_offset in (-1, 0, 1):
            for lon_offset in (-1, 0, 1):
                for neighbor in cells.get((cell[0] + lat_offset, cell[1] + lon_offset), []):
                    if neighbor.stop_id == stop.stop_id:
                        continue
                    distance = haversine_meters(stop.lat, stop.lon, neighbor.lat, neighbor.lon)
                    if distance <= max_walk_meters:
                        transfers[stop.stop_id].append((neighbor.stop_id, distance))
    return transfers


def earliest_arrival_seconds(
    stops: dict[str, Stop],
    connections: list[Connection],
    *,
    origin_lat: float,
    origin_lon: float,
    destination_lat: float,
    destination_lon: float,
    departure_seconds: int,
    max_walk_meters: float = 2500.0,
    walking_speed_kph: float = 4.8,
    transfer_penalty_minutes: float = 2.0,
) -> int | None:
    """Return earliest walk-transit-walk arrival with one service-day schedule.

    This connection-scan implementation allows transfers between scheduled
    vehicle legs. It does not model fares, vehicle capacity, real-time delays,
    or walking paths around barriers; those remain external calibration needs.
    """

    if max_walk_meters <= 0 or transfer_penalty_minutes < 0:
        raise ValueError("max_walk_meters must be positive and transfer penalty nonnegative")
    arrival = arrivals_at_stops(
        stops,
        connections,
        origin_lat=origin_lat,
        origin_lon=origin_lon,
        departure_seconds=departure_seconds,
        max_walk_meters=max_walk_meters,
        walking_speed_kph=walking_speed_kph,
        transfer_penalty_minutes=transfer_penalty_minutes,
    )
    best: float | None = None
    for stop_id, reached in arrival.items():
        stop = stops[stop_id]
        distance = haversine_meters(destination_lat, destination_lon, stop.lat, stop.lon)
        if distance <= max_walk_meters:
            candidate = reached + walking_transfer_minutes(distance, walking_speed_kph=walking_speed_kph) * 60
            best = candidate if best is None else min(best, candidate)
    return None if best is None else round(best)


def arrivals_at_stops(
    stops: dict[str, Stop], connections: list[Connection], *, origin_lat: float, origin_lon: float,
    departure_seconds: int, max_walk_meters: float = 1600.0, walking_speed_kph: float = 4.8,
    transfer_penalty_minutes: float = 2.0,
    walking_transfers: dict[str, list[tuple[str, float]]] | None = None,
    initial_walk_seconds: dict[str, float] | None = None,
) -> dict[str, float]:
    """Scan one origin once, returning earliest scheduled arrival by stop."""
    arrival: dict[str, float] = {}
    if initial_walk_seconds is not None:
        arrival = {stop_id: departure_seconds + seconds for stop_id, seconds in initial_walk_seconds.items()}
    else:
        for stop in stops.values():
            distance = haversine_meters(origin_lat, origin_lon, stop.lat, stop.lon)
            if distance <= max_walk_meters:
                arrival[stop.stop_id] = departure_seconds + walking_transfer_minutes(
                    distance, walking_speed_kph=walking_speed_kph
                ) * 60
    initial_arrival = arrival.copy()
    # Keep the walking-transfer relaxation separate from a vehicle arrival.
    # Looking up every neighbour for every scheduled connection makes a full
    # MARTA scan prohibitively expensive.  A walk can only become newly useful
    # when its source stop is reached, so relax its one-hop links at that point.
    walking_arrival: dict[str, float] = {}

    def relax_walking_transfers(stop_id: str, reached: float) -> None:
        for nearby_stop, distance in (walking_transfers or {}).get(stop_id, []):
            candidate = reached + walking_transfer_minutes(
                distance, walking_speed_kph=walking_speed_kph
            ) * 60
            current = walking_arrival.get(nearby_stop)
            if current is None or candidate < current:
                walking_arrival[nearby_stop] = candidate

    for stop_id, reached in initial_arrival.items():
        relax_walking_transfers(stop_id, reached)

    boarded_trips: set[str] = set()
    for connection in connections:
        on_same_vehicle = connection.trip_id in boarded_trips
        if not on_same_vehicle:
            direct_arrival = arrival.get(connection.departure_stop)
            transferred_arrival = walking_arrival.get(connection.departure_stop)
            candidates = [
                candidate
                for candidate in (direct_arrival, transferred_arrival)
                if candidate is not None
            ]
            if not candidates:
                continue
            ready = min(candidates)
            is_origin_walk = initial_arrival.get(connection.departure_stop) == ready
            transfer_seconds = 0 if is_origin_walk else transfer_penalty_minutes * 60
            if ready + transfer_seconds > connection.departure_seconds:
                continue
            boarded_trips.add(connection.trip_id)
        current = arrival.get(connection.arrival_stop)
        candidate = connection.arrival_seconds
        if current is None or candidate < current:
            arrival[connection.arrival_stop] = candidate
            relax_walking_transfers(connection.arrival_stop, candidate)
    return arrival


def arrival_at_destination(
    stops: dict[str, Stop], arrivals: dict[str, float], *, destination_lat: float,
    destination_lon: float, max_walk_meters: float = 1600.0, walking_speed_kph: float = 4.8,
    destination_walk_seconds: dict[str, float] | None = None,
) -> int | None:
    """Finish one schedule scan with the final walking transfer to a destination."""

    candidates = []
    for stop_id, reached in arrivals.items():
        if destination_walk_seconds is not None and stop_id in destination_walk_seconds:
            candidates.append(reached + destination_walk_seconds[stop_id])
            continue
        if destination_walk_seconds is not None:
            continue
        stop = stops[stop_id]
        distance = haversine_meters(destination_lat, destination_lon, stop.lat, stop.lon)
        if distance <= max_walk_meters:
            candidates.append(reached + walking_transfer_minutes(distance, walking_speed_kph=walking_speed_kph) * 60)
    return round(min(candidates)) if candidates else None


def trace_itinerary(
    stops: dict[str, Stop], connections: list[Connection], *, origin_lat: float, origin_lon: float,
    destination_lat: float, destination_lon: float, departure_seconds: int,
    initial_walk_seconds: dict[str, float], destination_walk_seconds: dict[str, float],
    transfer_penalty_minutes: float = 2.0,
    walking_transfers: dict[str, list[tuple[str, float]]] | None = None,
    walking_speed_kph: float = 4.8,
) -> list[ItineraryLeg] | None:
    """Return the modeled earliest itinerary with access, ride, and egress legs.

    This diagnostic helper intentionally uses the same connection-scan boarding
    rules as :func:`arrivals_at_stops`; it is for explaining a computed result,
    not a separate routing engine.
    """
    del stops, origin_lat, origin_lon, destination_lat, destination_lon
    arrivals = {stop_id: departure_seconds + seconds for stop_id, seconds in initial_walk_seconds.items()}
    previous: dict[str, ItineraryLeg] = {
        stop_id: ItineraryLeg("access_walk", None, stop_id, None, departure_seconds, reached)
        for stop_id, reached in arrivals.items()
    }
    walking_arrivals: dict[str, float] = {}
    walking_previous: dict[str, ItineraryLeg] = {}

    def relax(stop_id: str, reached: float) -> None:
        for nearby_stop, distance in (walking_transfers or {}).get(stop_id, []):
            candidate = reached + walking_transfer_minutes(distance, walking_speed_kph=walking_speed_kph) * 60
            if candidate < walking_arrivals.get(nearby_stop, float("inf")):
                walking_arrivals[nearby_stop] = candidate
                walking_previous[nearby_stop] = ItineraryLeg(
                    "transfer_walk", stop_id, nearby_stop, None, reached, candidate
                )

    for stop_id, reached in list(arrivals.items()):
        relax(stop_id, reached)
    boarded: dict[str, str] = {}
    for connection in connections:
        ride_parent_kind = "direct"
        if connection.trip_id not in boarded:
            options = [("direct", arrivals.get(connection.departure_stop)),
                       ("walking", walking_arrivals.get(connection.departure_stop))]
            options = [(kind, value) for kind, value in options if value is not None]
            if not options:
                continue
            parent_kind, reached = min(options, key=lambda item: item[1])
            access_leg = (previous if parent_kind == "direct" else walking_previous)[connection.departure_stop]
            penalty = 0 if access_leg.kind == "access_walk" else transfer_penalty_minutes * 60
            if reached + penalty > connection.departure_seconds:
                continue
            boarded[connection.trip_id] = parent_kind
            ride_parent_kind = parent_kind
        reached = connection.arrival_seconds
        if reached < arrivals.get(connection.arrival_stop, float("inf")):
            arrivals[connection.arrival_stop] = reached
            previous[connection.arrival_stop] = ItineraryLeg(
                "ride", connection.departure_stop, connection.arrival_stop, connection.trip_id,
                connection.departure_seconds, connection.arrival_seconds, ride_parent_kind,
            )
            relax(connection.arrival_stop, reached)
    candidates = [
        (reached + destination_walk_seconds[stop_id], stop_id)
        for stop_id, reached in arrivals.items() if stop_id in destination_walk_seconds
    ]
    if not candidates:
        return None
    final_time, stop_id = min(candidates)
    legs = [ItineraryLeg("egress_walk", stop_id, None, None, arrivals[stop_id], final_time)]
    current = stop_id
    while True:
        leg = previous[current]
        legs.append(leg)
        if leg.kind == "access_walk":
            return list(reversed(legs))
        if leg.kind == "ride" and leg.parent_kind == "walking":
            transfer = walking_previous[leg.from_stop]  # type: ignore[index]
            legs.append(transfer)
            current = transfer.from_stop
        else:
            current = leg.from_stop  # type: ignore[assignment]
