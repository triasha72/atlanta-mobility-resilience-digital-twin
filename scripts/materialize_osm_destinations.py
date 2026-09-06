#!/usr/bin/env python3
"""Download and materialize essential Atlanta destinations from OpenStreetMap."""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.parse
import urllib.request
from pathlib import Path

from amrdt.destinations import destination_summary, parse_overpass_destinations

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def query(radius_m: int, lat: float, lon: float) -> str:
    selectors = (
        '["amenity"~"^(hospital|clinic|fire_station)$"]',
        '["healthcare"~"^(hospital|clinic)$"]',
        '["amenity"="social_facility"]["social_facility"="shelter"]',
    )
    clauses = "".join(
        f"nwr(around:{radius_m},{lat},{lon}){selector};" for selector in selectors
    )
    return f"[out:json][timeout:120];({clauses});out center tags;"


def download_overpass(statement: str, path: Path) -> None:
    request = urllib.request.Request(
        OVERPASS_URL,
        data=urllib.parse.urlencode({"data": statement}).encode(),
        headers={"User-Agent": "amrdt-research/0.1 (public portfolio study)"},
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(response.read())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("data/external/osm_destinations.json"))
    parser.add_argument(
        "--output", type=Path, default=Path("data/processed/osm_essential_destinations.csv")
    )
    parser.add_argument(
        "--summary", type=Path, default=Path("artifacts/osm_essential_destinations_v1.json")
    )
    parser.add_argument("--radius-km", type=float, default=10.0)
    parser.add_argument("--center-lat", type=float, default=33.7580)
    parser.add_argument("--center-lon", type=float, default=-84.3880)
    args = parser.parse_args()
    statement = query(round(args.radius_km * 1000), args.center_lat, args.center_lon)
    if not args.source.exists():
        download_overpass(statement, args.source)
    frame = parse_overpass_destinations(json.loads(args.source.read_text()))
    if frame.empty:
        raise ValueError("Overpass returned no supported essential destinations")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output, index=False)
    record = {
        "dataset": "OpenStreetMap essential-service destinations",
        "license": "Open Data Commons Open Database License (ODbL) 1.0",
        "attribution": "OpenStreetMap contributors",
        "source": OVERPASS_URL,
        "query": statement,
        "selection": {
            "center": {"lat": args.center_lat, "lon": args.center_lon},
            "radius_km": args.radius_km,
            "categories": ["hospital", "clinic", "fire_station", "shelter"],
        },
        "source_sha256": sha256(args.source),
        "output_sha256": sha256(args.output),
        **destination_summary(frame),
        "limitations": [
            "OpenStreetMap completeness and tags vary by place and time.",
            "A mapped facility is counted once; capacity and service quality are not inferred.",
        ],
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
