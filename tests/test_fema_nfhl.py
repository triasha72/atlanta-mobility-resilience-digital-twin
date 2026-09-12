import json

from scripts.download_fema_nfhl import nfhl_query_url, receipt


def test_nfhl_query_is_a_geojson_intersection_request() -> None:
    url = nfhl_query_url({"xmin": -84.4, "ymin": 33.7, "xmax": -84.3, "ymax": 33.8}, "SFHA_TF = 'T'")
    assert "MapServer/28/query" in url
    assert "f=geojson" in url
    assert "SFHA_TF" in url


def test_nfhl_receipt_checksums_payload() -> None:
    result = receipt(url="https://example.test/query", payload=b'{"type":"FeatureCollection"}', feature_count=2)
    assert result["feature_count"] == 2
    assert len(result["payload_sha256"]) == 64
    assert json.loads(json.dumps(result))["source_url"].endswith("MapServer/28/query")
