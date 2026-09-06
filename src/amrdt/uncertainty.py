"""Propagate ACS population margins of error through accessibility summaries."""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd


def population_weighted_accessibility_intervals(
    scenario_accessibility: Mapping[str, pd.DataFrame],
    origins: pd.DataFrame,
    *,
    draws: int = 2_000,
    seed: int = 42,
) -> pd.DataFrame:
    """Monte Carlo intervals using ACS 90% margins of error as normal scales."""
    if draws < 100:
        raise ValueError("draws must be at least 100")
    required = {"geoid", "population", "population_moe"}
    missing = required.difference(origins.columns)
    if missing:
        raise ValueError(f"origins are missing columns: {sorted(missing)}")
    origin = origins.copy()
    origin["origin_id"] = origin["geoid"].astype(str)
    generator = np.random.default_rng(seed)
    estimates = origin["population"].to_numpy(dtype=float)
    standard_errors = origin["population_moe"].to_numpy(dtype=float) / 1.645
    populations = np.maximum(
        generator.normal(estimates, standard_errors, size=(draws, len(origin))), 0.0
    )
    totals = populations.sum(axis=1)
    if np.any(totals <= 0):
        raise ValueError("sampled population total must be positive")
    weights = populations / totals[:, None]
    rows = []
    for scenario, accessibility in sorted(scenario_accessibility.items()):
        joined = origin[["origin_id"]].merge(
            accessibility[["origin_id", "accessible_opportunities"]],
            on="origin_id", how="left", validate="one_to_one",
        )
        values = joined["accessible_opportunities"].fillna(0.0).to_numpy(dtype=float)
        samples = weights @ values
        rows.append({
            "scenario": scenario,
            "draws": draws,
            "population_weighted_accessibility_mean": float(np.mean(samples)),
            "population_weighted_accessibility_p05": float(np.quantile(samples, 0.05)),
            "population_weighted_accessibility_p95": float(np.quantile(samples, 0.95)),
        })
    return pd.DataFrame(rows)
