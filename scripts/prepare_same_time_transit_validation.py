"""Prepare a source-aligned, fresh polygon-origin MARTA validation holdout."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

import pandas as pd

from amrdt.gtfs import audit_gtfs_feed

try:  # Supports both `python scripts/...` and package imports in tests.
    from scripts.capture_marta_gtfs_realtime import MARTA_TRIP_UPDATES_URL
    from scripts.capture_marta_gtfs_realtime import receipt as realtime_receipt
    from scripts.create_proxy_calibration_sample import exclude_prior_tract_destination_pairs
    from scripts.create_transit_validation_sample import build_sample
except ModuleNotFoundError:  # pragma: no cover - direct script execution only
    from capture_marta_gtfs_realtime import MARTA_TRIP_UPDATES_URL
    from capture_marta_gtfs_realtime import receipt as realtime_receipt
    from create_proxy_calibration_sample import exclude_prior_tract_destination_pairs
    from create_transit_validation_sample import build_sample


MARTA_STATIC_GTFS_URL = "https://itsmarta.com/google_transit_feed/google_transit.zip"
MARTA_TIMEZONE = ZoneInfo("America/New_York")


def output_paths(root: Path, run_id: str) -> dict[str, Path]:
    """Return deterministic artifact paths for one validation run."""
    return {
        "static_feed": root / "data/external/marta" / f"google_transit_{run_id}.zip",
        "static_receipt": root / "reports" / f"marta_gtfs_receipt_{run_id}.json",
        "realtime_feed": root / "data/external/marta" / f"tripupdates_{run_id}.pb",
        "realtime_receipt": root / "reports" / f"marta_tripupdates_receipt_{run_id}.json",
        "od": root / "outputs" / f"transit_accessibility_polygon_same_time_{run_id}.csv",
        "sample": root / "outputs" / f"transit_polygon_same_time_holdout_{run_id}.csv",
        "manifest": root / "reports" / f"transit_same_time_validation_manifest_{run_id}.json",
    }


def capture_is_source_aligned(
    captured_at: datetime, service_date: str, departure: str, window_minutes: int
) -> bool:
    """Return whether capture occurred near the modeled local MARTA departure."""
    expected = datetime.strptime(f"{service_date} {departure}", "%Y%m%d %H:%M").replace(
        tzinfo=MARTA_TIMEZONE
    )
    local_capture = captured_at.astimezone(MARTA_TIMEZONE)
    return abs((local_capture - expected).total_seconds()) <= window_minutes * 60


def download(url: str, path: Path, *, accept: str | None = None) -> tuple[bytes, str | None]:
    """Download one public artifact and write it to its versioned path."""
    headers = {"User-Agent": "amrdt-research/0.1 (+https://github.com/triasha72)"}
    if accept:
        headers["Accept"] = accept
    with urlopen(Request(url, headers=headers), timeout=60) as response:
        payload = response.read()
        content_type = response.headers.get_content_type()
    if not payload:
        raise ValueError(f"empty response from {url}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return payload, content_type


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--service-date", required=True)
    parser.add_argument("--departure", default="08:00")
    parser.add_argument("--run-id", default=datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"))
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--prior", type=Path, nargs="+", required=True)
    parser.add_argument("--seed", type=int, default=20260917)
    parser.add_argument(
        "--capture-window-minutes", type=int, default=15,
        help="Maximum allowed distance from local departure for a source-aligned capture.",
    )
    parser.add_argument(
        "--allow-outside-window", action="store_true",
        help="Create an explicitly non-source-aligned diagnostic run outside the capture window.",
    )
    args = parser.parse_args()
    if args.capture_window_minutes < 0:
        raise ValueError("capture window must be non-negative")
    root = args.root.resolve()
    paths = output_paths(root, args.run_id)
    captured_at_datetime = datetime.now(UTC)
    source_aligned = capture_is_source_aligned(
        captured_at_datetime, args.service_date, args.departure, args.capture_window_minutes
    )
    if not source_aligned and not args.allow_outside_window:
        raise ValueError(
            "capture is outside the source-alignment window; run near the requested MARTA "
            "departure or pass --allow-outside-window for a diagnostic-only run"
        )
    captured_at = captured_at_datetime.isoformat()

    download(MARTA_STATIC_GTFS_URL, paths["static_feed"])
    static_receipt = audit_gtfs_feed(paths["static_feed"], source_url=MARTA_STATIC_GTFS_URL)
    paths["static_receipt"].write_text(json.dumps(static_receipt, indent=2) + "\n", encoding="utf-8")

    realtime_payload, realtime_content_type = download(MARTA_TRIP_UPDATES_URL, paths["realtime_feed"])
    realtime = realtime_receipt(
        payload=realtime_payload,
        source_url=MARTA_TRIP_UPDATES_URL,
        captured_at=captured_at,
        content_type=realtime_content_type,
    )
    paths["realtime_receipt"].write_text(json.dumps(realtime, indent=2) + "\n", encoding="utf-8")

    command = [
        sys.executable, "scripts/evaluate_transit_accessibility.py",
        "--gtfs", str(paths["static_feed"]), "--service-date", args.service_date,
        "--departure", args.departure,
        "--origins", "data/processed/acs_tract_polygon_origins.csv",
        "--destinations", "data/processed/osm_essential_destinations.csv",
        "--walk-graph", "data/processed/atlanta_walk.graphml",
        "--output", str(paths["od"]),
    ]
    subprocess.run(command, cwd=root, check=True)
    prior = pd.concat([pd.read_csv(path, dtype={"origin_id": str}) for path in args.prior], ignore_index=True)
    candidate = exclude_prior_tract_destination_pairs(pd.read_csv(paths["od"], dtype={"origin_id": str}), prior)
    sample = build_sample(
        candidate,
        pd.read_csv(root / "data/processed/acs_tract_polygon_origins.csv", dtype={"id": str}),
        pd.read_csv(root / "data/processed/osm_essential_destinations.csv"),
        service_date=args.service_date,
        departure=args.departure,
        sample_per_band=4,
        seed=args.seed,
        allow_empty_bands=True,
    )
    sample["validation_split"] = "same_time_polygon_holdout"
    paths["sample"].parent.mkdir(parents=True, exist_ok=True)
    sample.to_csv(paths["sample"], index=False)
    manifest = {
        "schema_version": "1.0",
        "captured_at": captured_at,
        "captured_at_marta": captured_at_datetime.astimezone(MARTA_TIMEZONE).isoformat(),
        "service_date": args.service_date,
        "departure": args.departure,
        "capture_window_minutes": args.capture_window_minutes,
        "source_aligned": source_aligned,
        "static_gtfs_receipt": str(paths["static_receipt"].relative_to(root)),
        "realtime_trip_updates_receipt": str(paths["realtime_receipt"].relative_to(root)),
        "fresh_holdout_sample": str(paths["sample"].relative_to(root)),
        "planner_review_required": True,
        "publication_gate": (
            "not evaluated until same-time Planner review is recorded"
            if source_aligned
            else "not eligible: capture was explicitly outside the source-alignment window"
        ),
    }
    paths["manifest"].write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"prepared {len(sample)} fresh holdout cases in {paths['sample']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
