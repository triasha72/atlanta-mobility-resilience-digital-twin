"""Fit a spatially held-out baseline for official road-closure labels."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.model_selection import GroupShuffleSplit

FEATURES = ["length_m", "travel_time_s", "speed_kph", "flood_exposed"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260920)
    parser.add_argument("--test-size", type=float, default=0.25)
    args = parser.parse_args()
    frame = pd.read_csv(args.input)
    required = set(FEATURES + ["observed_closed", "spatial_block"])
    if missing := required.difference(frame.columns):
        raise ValueError(f"input is missing columns: {sorted(missing)}")
    if frame.observed_closed.nunique() < 2:
        raise ValueError("official labels must include both closed and non-closed edges")
    splitter = GroupShuffleSplit(n_splits=1, test_size=args.test_size, random_state=args.seed)
    train_index, test_index = next(splitter.split(frame, groups=frame.spatial_block))
    train, test = frame.iloc[train_index], frame.iloc[test_index]
    if train.observed_closed.nunique() < 2 or test.observed_closed.nunique() < 2:
        raise ValueError("spatial split needs both classes in train and test; adjust --seed or --test-size")
    model = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=args.seed)
    model.fit(train[FEATURES], train.observed_closed)
    probability = model.predict_proba(test[FEATURES])[:, 1]
    prediction = probability >= 0.5
    precision, recall, f1, _ = precision_recall_fscore_support(test.observed_closed, prediction, average="binary", zero_division=0)
    payload = {"schema_version": "1.0", "model": "logistic_regression_balanced", "features": FEATURES,
               "train_edges": len(train), "test_edges": len(test), "train_blocks": int(train.spatial_block.nunique()),
               "test_blocks": int(test.spatial_block.nunique()), "test_prevalence": float(test.observed_closed.mean()),
               "average_precision": float(average_precision_score(test.observed_closed, probability)),
               "roc_auc": float(roc_auc_score(test.observed_closed, probability)), "precision_at_0_5": float(precision),
               "recall_at_0_5": float(recall), "f1_at_0_5": float(f1), "seed": args.seed}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
