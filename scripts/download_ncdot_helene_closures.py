"""Download a checksummed NCDOT Hurricane Helene historical closure layer.

This is a North Carolina transfer benchmark, not an Atlanta validation source.
It preserves the official event geometries and attributes needed to assess
whether a separate, event-labeled ML study has adequate coverage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

NCDOT_HELENE_LINES_URL = (
    "https://services.arcgis.com/NuWFvHYDMVmmxMeM/arcgis/rest/services/"
    "State_Maintained_Historical_TIMS_Incidents_Hurricane_Helene/FeatureServer/1/query"
)
PAGE_SIZE = 1_000
OUT_FIELDS = (
    "OBJECTID,EventID,EventName,CountyName,Road,Location,Closed,Condition,Reason,"
    "StartDateUTC,EndDateUTC,LastUpdateUTC"
)


def query_parameters(*, where: str, offset: int) -> dict[str, str]:
    """Build one documented, paginated ArcGIS GeoJSON request."""
    return {
        "f": "geojson",
        "where": where,
        "outFields": OUT_FIELDS,
        "returnGeometry": "true",
        "outSR": "4326",
        "resultOffset": str(offset),
        "resultRecordCount": str(PAGE_SIZE),
        "orderByFields": "OBJECTID",
    }


def query_url(*, where: str, offset: int) -> str:
    return f"{NCDOT_HELENE_LINES_URL}?{urlencode(query_parameters(where=where, offset=offset))}"


def download(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "amrdt-research/0.1"})
    with urlopen(request, timeout=120) as response:
        return response.read()


def download_all(*, where: str) -> tuple[list[dict], list[str]]:
    """Download all matching incident lines without silently truncating pages."""
    features: list[dict] = []
    urls: list[str] = []
    for offset in range(0, 100_000, PAGE_SIZE):
        url = query_url(where=where, offset=offset)
        payload = json.loads(download(url))
        if payload.get("type") != "FeatureCollection":
            raise ValueError("NCDOT response was not a GeoJSON FeatureCollection")
        page = payload.get("features", [])
        features.extend(page)
        urls.append(url)
        if len(page) < PAGE_SIZE:
            return features, urls
    raise ValueError("NCDOT pagination exceeded safe limit")


def receipt(*, payload: bytes, feature_count: int, where: str, request_count: int) -> dict[str, object]:
    """Return a content-free receipt for the merged official source response."""
    return {
        "source_url": NCDOT_HELENE_LINES_URL,
        "where": where,
        "retrieved_at": datetime.now(UTC).isoformat(),
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "feature_count": feature_count,
        "request_count": request_count,
        "study_scope": "North Carolina Hurricane Helene transfer benchmark; not Atlanta validation.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--county", help="Optional exact CountyName filter for a bounded benchmark.")
    args = parser.parse_args()
    escaped_county = args.county.replace("'", "''") if args.county else None
    where = "1=1" if escaped_county is None else f"CountyName = '{escaped_county}'"
    features, urls = download_all(where=where)
    if not features:
        raise ValueError("NCDOT query returned no closure records")
    collection = {"type": "FeatureCollection", "features": features}
    payload = json.dumps(collection, sort_keys=True, separators=(",", ":")).encode("utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(payload)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(
        json.dumps(
            receipt(
                payload=payload,
                feature_count=len(features),
                where=where,
                request_count=len(urls),
            ),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(features)} NCDOT Hurricane Helene incident lines to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
