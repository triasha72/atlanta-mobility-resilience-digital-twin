"""Download a checksummed FEMA NFHL flood-hazard subset for a road graph extent."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import geopandas as gpd

from amrdt.network import _require_osmnx

FEMA_NFHL_FLOOD_HAZARD_AREAS_URL = (
    "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query"
)
FEMA_OBJECT_ID_BATCH_SIZE = 500


def graph_envelope(graph) -> dict[str, float]:
    """Return a WGS84 ArcGIS envelope covering graph nodes."""
    crs = str(graph.graph.get("crs", "EPSG:4326")).lower()
    if "4326" not in crs:
        raise ValueError("NFHL download currently requires a WGS84 road graph")
    xs = [float(data["x"]) for _, data in graph.nodes(data=True)]
    ys = [float(data["y"]) for _, data in graph.nodes(data=True)]
    return {"xmin": min(xs), "ymin": min(ys), "xmax": max(xs), "ymax": max(ys)}


def nfhl_query_parameters(envelope: dict[str, float], where: str) -> dict[str, str]:
    """Return shared ArcGIS REST parameters for one graph extent."""
    return {
        "f": "geojson",
        "where": where,
        "geometry": json.dumps(envelope, separators=(",", ":")),
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "OBJECTID,FLD_ZONE,SFHA_TF,DFIRM_ID",
        "returnGeometry": "true",
        "outSR": "4326",
    }


def nfhl_query_url(envelope: dict[str, float], where: str) -> str:
    """Build the documented ArcGIS REST GeoJSON query for one graph extent."""
    return f"{FEMA_NFHL_FLOOD_HAZARD_AREAS_URL}?{urlencode(nfhl_query_parameters(envelope, where))}"


def download_geojson(url: str) -> bytes:
    """Download one FEMA query response with a stable research user agent."""
    request = Request(url, headers={"User-Agent": "amrdt-research/0.1"})
    with urlopen(request, timeout=120) as response:
        payload = response.read()
    if not payload:
        raise ValueError("FEMA NFHL returned an empty response")
    return payload


def download_all_features(envelope: dict[str, float], where: str) -> tuple[list[dict], list[str]]:
    """Retrieve every matching FEMA feature by stable object-ID batches."""
    shared = nfhl_query_parameters(envelope, where)
    id_params = {**shared, "f": "json", "returnIdsOnly": "true", "returnGeometry": "false"}
    id_url = f"{FEMA_NFHL_FLOOD_HAZARD_AREAS_URL}?{urlencode(id_params)}"
    ids_payload = json.loads(download_geojson(id_url))
    object_ids = ids_payload.get("objectIds", [])
    if not object_ids:
        return [], [id_url]
    features: list[dict] = []
    urls = [id_url]
    for start in range(0, len(object_ids), FEMA_OBJECT_ID_BATCH_SIZE):
        page_params = {
            "f": "geojson",
            "objectIds": ",".join(map(str, object_ids[start:start + FEMA_OBJECT_ID_BATCH_SIZE])),
            "outFields": shared["outFields"],
            "returnGeometry": "true",
            "outSR": "4326",
        }
        page_url = f"{FEMA_NFHL_FLOOD_HAZARD_AREAS_URL}?{urlencode(page_params)}"
        page = json.loads(download_geojson(page_url))
        if page.get("type") != "FeatureCollection":
            raise ValueError("FEMA NFHL page was not GeoJSON FeatureCollection")
        features.extend(page.get("features", []))
        urls.append(page_url)
    return features, urls


def receipt(*, url: str, payload: bytes, feature_count: int, request_count: int = 1) -> dict[str, object]:
    """Return content-free provenance for one NFHL query response."""
    return {
        "source_url": FEMA_NFHL_FLOOD_HAZARD_AREAS_URL,
        "query_url": url,
        "request_count": request_count,
        "retrieved_at": datetime.now(UTC).isoformat(),
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "feature_count": feature_count,
        "license_note": "FEMA National Flood Hazard Layer; inspect FEMA terms before reuse.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", type=Path, required=True, help="WGS84 OSMnx GraphML extent.")
    parser.add_argument("--output", type=Path, required=True, help="Subset GeoJSON output path.")
    parser.add_argument("--receipt", type=Path, required=True, help="Content-free JSON receipt path.")
    parser.add_argument("--where", default="SFHA_TF = 'T'", help="ArcGIS SQL flood-zone filter.")
    parser.add_argument(
        "--allow-empty", action="store_true",
        help="Write an auditable empty GeoJSON/receipt rather than failing for a no-hazard extent.",
    )
    args = parser.parse_args()

    graph = _require_osmnx().load_graphml(args.graph)
    envelope = graph_envelope(graph)
    features, query_urls = download_all_features(envelope, args.where)
    collection = {"type": "FeatureCollection", "features": features}
    payload = json.dumps(collection, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if not features and not args.allow_empty:
        raise ValueError("FEMA NFHL query returned no flood hazard features for the graph extent")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if features:
        hazards = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")
        hazards.to_file(args.output, driver="GeoJSON")
    else:
        args.output.write_bytes(payload)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(
        json.dumps(
            receipt(
                url=nfhl_query_url(envelope, args.where),
                payload=payload,
                feature_count=len(features),
                request_count=len(query_urls),
            ),
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(features)} FEMA NFHL flood-hazard areas to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
