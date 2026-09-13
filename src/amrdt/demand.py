"""Aggregate-only synthetic origin-destination demand utilities."""

from __future__ import annotations

import numpy as np
import pandas as pd


def synthetic_gravity_demand(origins: pd.DataFrame, destinations: pd.DataFrame, *, trips: int, seed: int) -> pd.DataFrame:
    """Sample synthetic aggregate OD counts from public origin/destination weights."""
    if trips < 1:
        raise ValueError("trips must be positive")
    if "id" not in origins.columns and "geoid" in origins.columns:
        origins = origins.rename(columns={"geoid": "id"})
    if missing := {"id", "population"}.difference(origins.columns):
        raise ValueError(f"origins are missing columns: {sorted(missing)}")
    if missing := {"id", "opportunity_weight"}.difference(destinations.columns):
        raise ValueError(f"destinations are missing columns: {sorted(missing)}")
    origin_weights = origins["population"].clip(lower=0).to_numpy(dtype=float)
    destination_weights = destinations["opportunity_weight"].clip(lower=0).to_numpy(dtype=float)
    probabilities = np.outer(origin_weights, destination_weights).ravel()
    if probabilities.sum() <= 0:
        raise ValueError("origin and destination weights must have positive product")
    counts = np.random.default_rng(seed).multinomial(trips, probabilities / probabilities.sum())
    rows = pd.MultiIndex.from_product(
        [origins["id"].astype(str), destinations["id"].astype(str)], names=["origin_id", "destination_id"]
    ).to_frame(index=False)
    rows["synthetic_trip_count"] = counts
    return rows[rows["synthetic_trip_count"] > 0].reset_index(drop=True)


def margin_utility(demand: pd.DataFrame, origins: pd.DataFrame, destinations: pd.DataFrame) -> pd.DataFrame:
    """Report total-variation distance between synthetic and public aggregate margins."""
    if "id" not in origins.columns and "geoid" in origins.columns:
        origins = origins.rename(columns={"geoid": "id"})
    total = float(demand["synthetic_trip_count"].sum())
    synthetic_origin = demand.groupby("origin_id")["synthetic_trip_count"].sum() / total
    synthetic_destination = demand.groupby("destination_id")["synthetic_trip_count"].sum() / total
    expected_origin = origins.set_index(origins["id"].astype(str))["population"].clip(lower=0)
    expected_origin = expected_origin / expected_origin.sum()
    expected_destination = destinations.set_index(destinations["id"].astype(str))["opportunity_weight"].clip(lower=0)
    expected_destination = expected_destination / expected_destination.sum()
    return pd.DataFrame([{
        "origin_margin_total_variation": 0.5 * (synthetic_origin.reindex(expected_origin.index, fill_value=0) - expected_origin).abs().sum(),
        "destination_margin_total_variation": 0.5 * (synthetic_destination.reindex(expected_destination.index, fill_value=0) - expected_destination).abs().sum(),
    }])
