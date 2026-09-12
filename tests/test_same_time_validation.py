from datetime import UTC, datetime
from pathlib import Path

from scripts.prepare_same_time_transit_validation import capture_is_source_aligned, output_paths


def test_output_paths_are_versioned_and_do_not_overwrite_prior_runs() -> None:
    paths = output_paths(Path("/study"), "20260914T120000Z")
    assert paths["static_feed"] == Path("/study/data/external/marta/google_transit_20260914T120000Z.zip")
    assert paths["sample"] == Path("/study/outputs/transit_polygon_same_time_holdout_20260914T120000Z.csv")
    assert paths["manifest"].name == "transit_same_time_validation_manifest_20260914T120000Z.json"


def test_source_alignment_uses_marta_local_time() -> None:
    assert capture_is_source_aligned(
        datetime(2026, 9, 14, 12, 5, tzinfo=UTC), "20260914", "08:00", 15
    )
    assert not capture_is_source_aligned(
        datetime(2026, 9, 14, 12, 16, tzinfo=UTC), "20260914", "08:00", 15
    )
