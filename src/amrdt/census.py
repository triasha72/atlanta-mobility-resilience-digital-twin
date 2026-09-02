"""Build tract-level origin records from public ACS and Census geography data."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd


def parse_census_reporter(payload: dict[str, Any]) -> pd.DataFrame:
    """Normalize Census Reporter ACS results while retaining margins of error."""
    release = payload.get("release", {})
    rows: list[dict[str, Any]] = []
    for geoid, tables in payload.get("data", {}).items():
        population = tables["B01003"]
        income = tables["B19013"]
        rows.append(
            {
                "geoid": geoid.removeprefix("14000US"),
                "population": population["estimate"]["B01003001"],
                "population_moe": population["error"]["B01003001"],
                "median_household_income": income["estimate"]["B19013001"],
                "median_household_income_moe": income["error"]["B19013001"],
                "acs_release": release.get("id"),
                "acs_years": release.get("years"),
            }
        )
    return pd.DataFrame(rows).sort_values("geoid").reset_index(drop=True)


def read_gazetteer(path: str | Path) -> pd.DataFrame:
    """Read representative tract coordinates from a Census Gazetteer file."""
    frame = pd.read_csv(path, sep="\t", dtype={"GEOID": str}, skipinitialspace=True)
    frame.columns = frame.columns.str.strip()
    return frame.rename(
        columns={"GEOID": "geoid", "INTPTLAT": "lat", "INTPTLONG": "lon"}
    )[["geoid", "lat", "lon"]]


def _distance_km(lat: pd.Series, lon: pd.Series, center_lat: float, center_lon: float) -> pd.Series:
    """Vectorized haversine distance from a study center."""
    lat1 = lat.astype(float).map(math.radians)
    lon1 = lon.astype(float).map(math.radians)
    lat2 = math.radians(center_lat)
    lon2 = math.radians(center_lon)
    a = ((lat1 - lat2) / 2).map(math.sin) ** 2 + (
        lat1.map(math.cos) * math.cos(lat2) * ((lon1 - lon2) / 2).map(math.sin) ** 2
    )
    return 2 * 6371.0088 * a.map(math.sqrt).map(math.asin)


def build_tract_origins(
    payloads: list[dict[str, Any]],
    gazetteer_path: str | Path,
    *,
    center_lat: float,
    center_lon: float,
    radius_km: float,
    limit: int | None = None,
) -> pd.DataFrame:
    """Join ACS estimates to tract coordinates and apply a documented radius sample."""
    acs = pd.concat([parse_census_reporter(payload) for payload in payloads], ignore_index=True)
    frame = acs.merge(read_gazetteer(gazetteer_path), on="geoid", validate="one_to_one")
    frame["distance_to_center_km"] = _distance_km(
        frame["lat"], frame["lon"], center_lat, center_lon
    )
    frame = frame[(frame["distance_to_center_km"] <= radius_km) & (frame["population"] > 0)]
    frame = frame.sort_values(["population", "geoid"], ascending=[False, True])
    if limit is not None:
        frame = frame.head(limit)
    frame["population_weight"] = frame["population"] / frame["population"].sum()
    return frame.reset_index(drop=True)


def summary_record(frame: pd.DataFrame, source_hashes: dict[str, str]) -> dict[str, Any]:
    """Create a text-only evidence record without redistributing row-level estimates."""
    return {
        "dataset": "American Community Survey tract estimates and Census Gazetteer",
        "acs_release": frame["acs_release"].iloc[0],
        "acs_years": frame["acs_years"].iloc[0],
        "tract_count": len(frame),
        "represented_population_estimate": int(frame["population"].sum()),
        "population_moe_median": float(frame["population_moe"].median()),
        "median_household_income_median": float(frame["median_household_income"].median()),
        "source_hashes": source_hashes,
        "interpretation": (
            "ACS values are survey estimates with margins of error; representative tract "
            "coordinates are routing origins, not observed trip starts."
        ),
    }


def load_payload(path: str | Path) -> dict[str, Any]:
    """Load a cached source response."""
    return json.loads(Path(path).read_text(encoding="utf-8"))
