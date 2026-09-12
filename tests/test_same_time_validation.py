from pathlib import Path

from scripts.prepare_same_time_transit_validation import output_paths


def test_output_paths_are_versioned_and_do_not_overwrite_prior_runs() -> None:
    paths = output_paths(Path("/study"), "20260914T120000Z")
    assert paths["static_feed"] == Path("/study/data/external/marta/google_transit_20260914T120000Z.zip")
    assert paths["sample"] == Path("/study/outputs/transit_polygon_same_time_holdout_20260914T120000Z.csv")
    assert paths["manifest"].name == "transit_same_time_validation_manifest_20260914T120000Z.json"
