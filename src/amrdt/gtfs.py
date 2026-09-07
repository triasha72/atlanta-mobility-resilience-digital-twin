"""Content-free validation and provenance for a MARTA GTFS schedule feed."""

from __future__ import annotations

import csv
import hashlib
import io
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
