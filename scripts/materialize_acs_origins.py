"""Download and materialize a reproducible ACS tract-origin sample."""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

from amrdt.census import build_tract_origins, load_payload, summary_record

ACS_URL = (
    "https://api.censusreporter.org/1.0/data/show/acs2024_5yr?"
    "table_ids=B01003,B19013&geo_ids=140%7C05000US13{county}"
)
GAZETTEER_URL = (
    "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/"
    "2024_Gazetteer/2024_gaz_tracts_13.txt"
)


def _download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "amrdt-research/0.1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        path.write_bytes(response.read())


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data/external/acs2024"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/acs_tract_origins.csv"))
    parser.add_argument(
        "--summary", type=Path, default=Path("artifacts/acs_tract_origins_v1.json")
    )
    parser.add_argument("--radius-km", type=float, default=10.0)
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    sources = {
        "fulton_acs.json": ACS_URL.format(county="121"),
        "dekalb_acs.json": ACS_URL.format(county="089"),
        "2024_gaz_tracts_13.txt": GAZETTEER_URL,
    }
    for filename, url in sources.items():
        path = args.data_dir / filename
        if not path.exists():
            _download(url, path)

    paths = [args.data_dir / name for name in sources]
    frame = build_tract_origins(
        [load_payload(paths[0]), load_payload(paths[1])],
        paths[2],
        center_lat=33.7580,
        center_lon=-84.3880,
        radius_km=args.radius_km,
        limit=args.limit,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output, index=False)

    record = summary_record(frame, {path.name: _sha256(path) for path in paths})
    record.update(
        {
            "sources": sources,
            "selection": {
                "counties": ["Fulton County (121)", "DeKalb County (089)"],
                "center": {"lat": 33.7580, "lon": -84.3880},
                "radius_km": args.radius_km,
                "ranking": "population estimate descending, GEOID ascending",
                "limit": args.limit,
            },
            "output_sha256": _sha256(args.output),
        }
    )
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
