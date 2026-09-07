"""Content-free validation and provenance for a MARTA GTFS schedule feed."""

from __future__ import annotations

import csv
import hashlib
import io
import math
from pathlib import Path
from zipfile import ZipFile

REQUIRED_FILES = frozenset(
    {
        "agency.txt",
        "routes.txt",
        "trips.txt",
        "stops.txt",
        "stop_times.txt",
        "calendar.txt",
    }
)


def active_service_ids(path: str | Path, service_date: str) -> set[str]:
    """Return calendar services active on a YYYYMMDD date from a GTFS feed.

    This supports the base calendar only.  A caller must account for
    `calendar_dates.txt` exceptions before presenting a holiday-service result.
    """

    if len(service_date) != 8 or not service_date.isdigit():
        raise ValueError("service_date must use YYYYMMDD format")
    weekday = __import__("datetime").datetime.strptime(service_date, "%Y%m%d").strftime("%A").lower()
    with ZipFile(path) as archive, archive.open("calendar.txt") as raw:
        reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""))
        return {
            row["service_id"]
            for row in reader
            if row["start_date"] <= service_date <= row["end_date"] and row.get(weekday) == "1"
        }


def walking_transfer_minutes(distance_meters: float, *, walking_speed_kph: float = 4.8) -> float:
    """Convert a documented walk distance to time with input validation."""

    if distance_meters < 0 or walking_speed_kph <= 0:
        raise ValueError("distance_meters must be nonnegative and walking_speed_kph positive")
    return distance_meters / (walking_speed_kph * 1000 / 60)


def haversine_meters(lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> float:
    """Great-circle distance used only to screen a walk-transfer candidate."""

    radius = 6_371_000.0
    lat_delta = math.radians(lat_b - lat_a)
    lon_delta = math.radians(lon_b - lon_a)
    value = math.sin(lat_delta / 2) ** 2 + math.cos(math.radians(lat_a)) * math.cos(
        math.radians(lat_b)
    ) * math.sin(lon_delta / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(value))


def _row_count(archive: ZipFile, name: str) -> int:
    with archive.open(name) as raw:
        reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""))
        return sum(1 for _ in reader)


def audit_gtfs_feed(path: str | Path, *, source_url: str) -> dict[str, object]:
    """Validate a schedule ZIP and return a receipt without retaining its rows."""

    feed_path = Path(path)
    with ZipFile(feed_path) as archive:
        names = {Path(name).name for name in archive.namelist() if not name.endswith("/")}
        missing = sorted(REQUIRED_FILES - names)
        if missing:
            raise ValueError(f"GTFS feed is missing required files: {', '.join(missing)}")
        counts = {name: _row_count(archive, name) for name in sorted(REQUIRED_FILES)}
        route_types: dict[str, int] = {}
        with archive.open("routes.txt") as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""))
            for row in reader:
                route_type = row.get("route_type", "")
                route_types[route_type] = route_types.get(route_type, 0) + 1

    return {
        "schema_version": "1.0",
        "dataset": "MARTA GTFS Schedule",
        "source_url": source_url,
        "feed_sha256": hashlib.sha256(feed_path.read_bytes()).hexdigest(),
        "required_files": sorted(REQUIRED_FILES),
        "row_counts": counts,
        "route_type_counts": dict(sorted(route_types.items())),
        "contains_source_rows": False,
        "next_step": (
            "Join stop locations to the road graph with a documented walking-transfer "
            "rule before reporting multimodal accessibility."
        ),
    }
