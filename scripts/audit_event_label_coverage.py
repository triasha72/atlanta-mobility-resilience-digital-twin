"""Audit whether an official event layer supports supervised closure modeling."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

POSITIVE_VALUES = {"1", "true", "yes", "closed"}
NEGATIVE_VALUES = {"0", "false", "no", "open"}


def classification_readiness(features: list[dict], *, label_field: str) -> dict[str, object]:
    """Summarize explicit labels without treating unreported roads as open."""
    labels = [str(feature.get("properties", {}).get(label_field, "")).strip().lower() for feature in features]
    counts = Counter(labels)
    positive_count = sum(count for value, count in counts.items() if value in POSITIVE_VALUES)
    negative_count = sum(count for value, count in counts.items() if value in NEGATIVE_VALUES)
    return {
        "label_field": label_field,
        "label_counts": dict(sorted(counts.items())),
        "positive_count": positive_count,
        "negative_count": negative_count,
        "eligible_for_supervised_classification": positive_count > 0 and negative_count > 0,
        "decision": (
            "eligible"
            if positive_count > 0 and negative_count > 0
            else "blocked_missing_explicit_positive_or_negative_labels"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Official GeoJSON event layer.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--label-field", default="Closed")
    args = parser.parse_args()
    payload = args.input.read_bytes()
    collection = json.loads(payload)
    if collection.get("type") != "FeatureCollection":
        raise ValueError("input must be a GeoJSON FeatureCollection")
    features = collection.get("features", [])
    if not features:
        raise ValueError("input has no features")
    summary = {
        "schema_version": "1.0",
        "input": str(args.input),
        "input_sha256": hashlib.sha256(payload).hexdigest(),
        "feature_count": len(features),
        "geometry_types": sorted({str(feature.get("geometry", {}).get("type")) for feature in features}),
        **classification_readiness(features, label_field=args.label_field),
        "limitation": (
            "Absent event records are not treated as observed-open roads. "
            "Do not run the baseline or GNN unless the gate is eligible."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
