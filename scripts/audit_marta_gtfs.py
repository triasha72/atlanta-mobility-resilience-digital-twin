#!/usr/bin/env python3
"""Download a MARTA GTFS schedule ZIP and write a content-free receipt."""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

from amrdt.gtfs import audit_gtfs_feed

MARTA_GTFS_URL = "https://itsmarta.com/google_transit_feed/google_transit.zip"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=MARTA_GTFS_URL)
    parser.add_argument("--feed", type=Path, default=Path("data/external/marta/google_transit.zip"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    if args.refresh or not args.feed.exists():
        args.feed.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(
            args.url,
            headers={"User-Agent": "amrdt-research/0.1 (+https://github.com/triasha72)"},
        )
        with urllib.request.urlopen(request) as response, args.feed.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
    receipt = audit_gtfs_feed(args.feed, source_url=args.url)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
