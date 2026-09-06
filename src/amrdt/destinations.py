"""Normalize public OpenStreetMap essential-service destinations."""

from __future__ import annotations

from collections import Counter
from typing import Any

import pandas as pd


def _category(tags: dict[str, str]) -> str | None:
    amenity = tags.get("amenity")
    healthcare = tags.get("healthcare")
    social = tags.get("social_facility")
    if amenity == "fire_station":
        return "fire_station"
    if amenity == "hospital" or healthcare == "hospital":
        return "hospital"
    if amenity == "clinic" or healthcare == "clinic":
        return "clinic"
    if amenity == "social_facility" and social == "shelter":
        return "shelter"
    return None


def parse_overpass_destinations(payload: dict[str, Any]) -> pd.DataFrame:
    """Return routable, named essential services from an Overpass response."""
    rows = []
    seen = set()
    for element in payload.get("elements", []):
        tags = element.get("tags", {})
        category = _category(tags)
        center = element.get("center", element)
        lat, lon = center.get("lat"), center.get("lon")
        key = (element.get("type"), element.get("id"))
        if category is None or lat is None or lon is None or key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "id": f"osm-{key[0]}-{key[1]}",
                "label": tags.get("name") or f"Unnamed {category.replace('_', ' ')}",
                "category": category,
                "lon": float(lon),
                "lat": float(lat),
                "opportunity_weight": 1.0,
                "osm_type": key[0],
                "osm_id": int(key[1]),
            }
        )
    return pd.DataFrame(rows).sort_values(["category", "id"]).reset_index(drop=True)


def destination_summary(frame: pd.DataFrame) -> dict[str, Any]:
    """Build an aggregate record suitable for version control."""
    counts = Counter(frame["category"])
    return {
        "destination_count": len(frame),
        "counts_by_category": dict(sorted(counts.items())),
        "weighting": "one opportunity per mapped facility; categories are reported separately",
    }
