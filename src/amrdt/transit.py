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


def earliest_arrival_seconds(
    stops: dict[str, Stop],
    connections: list[Connection],
    *,
    origin_lat: float,
    origin_lon: float,
    destination_lat: float,
    destination_lon: float,
    departure_seconds: int,
    max_walk_meters: float = 800.0,
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
    departure_seconds: int, max_walk_meters: float = 800.0, walking_speed_kph: float = 4.8,
    transfer_penalty_minutes: float = 2.0,
) -> dict[str, float]:
    """Scan one origin once, returning earliest scheduled arrival by stop."""
    arrival: dict[str, float] = {}
    for stop in stops.values():
        distance = haversine_meters(origin_lat, origin_lon, stop.lat, stop.lon)
        if distance <= max_walk_meters:
            arrival[stop.stop_id] = departure_seconds + walking_transfer_minutes(
                distance, walking_speed_kph=walking_speed_kph
            ) * 60
    initial_arrival = arrival.copy()
    boarded_trips: set[str] = set()
    for connection in connections:
        on_same_vehicle = connection.trip_id in boarded_trips
        if not on_same_vehicle:
            ready = arrival.get(connection.departure_stop)
            if ready is None:
                continue
            is_origin_walk = initial_arrival.get(connection.departure_stop) == ready
            transfer_seconds = 0 if is_origin_walk else transfer_penalty_minutes * 60
            if ready + transfer_seconds > connection.departure_seconds:
                continue
            boarded_trips.add(connection.trip_id)
        current = arrival.get(connection.arrival_stop)
        candidate = connection.arrival_seconds
        if current is None or candidate < current:
            arrival[connection.arrival_stop] = candidate
    return arrival


def arrival_at_destination(
    stops: dict[str, Stop], arrivals: dict[str, float], *, destination_lat: float,
    destination_lon: float, max_walk_meters: float = 800.0, walking_speed_kph: float = 4.8,
) -> int | None:
    """Finish one schedule scan with the final walking transfer to a destination."""

    candidates = []
    for stop_id, reached in arrivals.items():
        stop = stops[stop_id]
        distance = haversine_meters(destination_lat, destination_lon, stop.lat, stop.lon)
        if distance <= max_walk_meters:
            candidates.append(reached + walking_transfer_minutes(distance, walking_speed_kph=walking_speed_kph) * 60)
    return round(min(candidates)) if candidates else None
