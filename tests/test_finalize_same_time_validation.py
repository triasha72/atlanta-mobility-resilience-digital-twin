import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from scripts.finalize_same_time_transit_validation import review_is_complete, verify_sources


def test_verify_sources_checks_both_captured_feeds(tmp_path: Path) -> None:
    root = tmp_path
    marta = root / "data/external/marta"
    reports = root / "reports"
    marta.mkdir(parents=True)
    reports.mkdir()
    static = marta / "google_transit_run.zip"
    realtime = marta / "tripupdates_run.pb"
    static.write_bytes(b"static")
    realtime.write_bytes(b"realtime")
    (reports / "marta_gtfs_receipt_run.json").write_text(
        json.dumps({"feed_sha256": hashlib.sha256(b"static").hexdigest()})
    )
    (reports / "marta_tripupdates_receipt_run.json").write_text(
        json.dumps({"payload_sha256": hashlib.sha256(b"realtime").hexdigest()})
    )
    verify_sources(root, {
        "static_gtfs_receipt": "reports/marta_gtfs_receipt_run.json",
        "realtime_trip_updates_receipt": "reports/marta_tripupdates_receipt_run.json",
    })


def test_review_must_cover_every_pair_once_and_have_a_disposition() -> None:
    sample = pd.DataFrame({"origin_id": ["1", "2"], "destination_id": ["a", "b"]})
    reviewed = sample.assign(
        planner_minutes=[12.0, float("nan")], planner_no_route=[False, True],
        reviewed_at=["2026-09-14T08:00:00+00:00"] * 2,
    )
    assert review_is_complete(sample, reviewed)
    with pytest.raises(ValueError, match="exactly once"):
        review_is_complete(sample, reviewed.iloc[:1])
