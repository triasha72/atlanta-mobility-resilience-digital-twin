"""Verify and score a completed source-aligned MARTA validation holdout."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

try:  # Supports both `python scripts/...` and package imports in tests.
    from scripts.score_transit_validation import passes_publication_gate, score_completed_checks
except ModuleNotFoundError:  # pragma: no cover - direct script execution only
    from score_transit_validation import passes_publication_gate, score_completed_checks


def sha256_file(path: Path) -> str:
    """Return a file checksum without loading the whole artifact into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_sources(root: Path, manifest: dict[str, object]) -> None:
    """Check captured artifacts still agree with their immutable receipts."""
    if manifest.get("source_aligned") is not True:
        raise ValueError("publication gate requires a source-aligned capture")
    static_receipt_path = root / str(manifest["static_gtfs_receipt"])
    realtime_receipt_path = root / str(manifest["realtime_trip_updates_receipt"])
    vehicle_receipt_path = root / str(manifest["realtime_vehicle_positions_receipt"])
    static_receipt = json.loads(static_receipt_path.read_text(encoding="utf-8"))
    realtime_receipt = json.loads(realtime_receipt_path.read_text(encoding="utf-8"))
    vehicle_receipt = json.loads(vehicle_receipt_path.read_text(encoding="utf-8"))
    run_id = static_receipt_path.stem.removeprefix("marta_gtfs_receipt_")
    static_feed = root / "data/external/marta" / f"google_transit_{run_id}.zip"
    realtime_feed = root / "data/external/marta" / f"tripupdates_{run_id}.pb"
    vehicle_feed = root / "data/external/marta" / f"vehiclepositions_{run_id}.pb"
    if sha256_file(static_feed) != static_receipt["feed_sha256"]:
        raise ValueError("static GTFS checksum does not match its receipt")
    if sha256_file(realtime_feed) != realtime_receipt["payload_sha256"]:
        raise ValueError("GTFS-Realtime checksum does not match its receipt")
    if sha256_file(vehicle_feed) != vehicle_receipt["payload_sha256"]:
        raise ValueError("vehicle-position checksum does not match its receipt")


def review_is_complete(sample: pd.DataFrame, reviewed: pd.DataFrame) -> bool:
    """Require exactly one source-review disposition for every fresh pair."""
    required = {"origin_id", "destination_id", "planner_minutes", "planner_no_route", "reviewed_at"}
    missing = required - set(reviewed.columns)
    if missing:
        raise ValueError(f"review file is missing columns: {', '.join(sorted(missing))}")
    pair_columns = ["origin_id", "destination_id"]
    sample_pairs = set(map(tuple, sample[pair_columns].astype(str).to_numpy()))
    reviewed_pairs = set(map(tuple, reviewed[pair_columns].astype(str).to_numpy()))
    if sample_pairs != reviewed_pairs or len(reviewed) != len(sample):
        raise ValueError("review must contain each fresh holdout pair exactly once")
    numeric = reviewed["planner_minutes"].notna()
    def parse_no_route(value: object) -> bool | None:
        if value is True or value == 1 or value in {"true", "True"}:
            return True
        if value is False or value == 0 or value in {"false", "False"}:
            return False
        return None

    no_route = reviewed["planner_no_route"].map(parse_no_route)
    if no_route.isna().any():
        raise ValueError("planner_no_route must be true or false")
    if (numeric == no_route).any():
        raise ValueError("each reviewed case needs either planner_minutes or planner_no_route")
    if reviewed["reviewed_at"].isna().any():
        raise ValueError("each reviewed case needs a review timestamp")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--reviewed", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    parser.add_argument("--cases-output", type=Path, required=True)
    parser.add_argument("--gate-output", type=Path, required=True)
    args = parser.parse_args()

    manifest_path = args.manifest.resolve()
    root = manifest_path.parent.parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    verify_sources(root, manifest)
    sample = pd.read_csv(root / str(manifest["fresh_holdout_sample"]), dtype={"origin_id": str})
    reviewed = pd.read_csv(args.reviewed, dtype={"origin_id": str})
    review_is_complete(sample, reviewed)
    summary = score_completed_checks(reviewed)
    gate_passed = passes_publication_gate(summary)
    for path in (args.summary_output, args.cases_output, args.gate_output):
        path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.summary_output, index=False)
    reviewed.to_csv(args.cases_output, index=False)
    pd.DataFrame(
        [{"publication_gate_passed": gate_passed, "source_receipts_verified": True}]
    ).to_csv(args.gate_output, index=False)
    print(f"source receipts verified; publication gate passed: {gate_passed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
