import json

from scripts.download_ncdot_helene_closures import (
    NCDOT_HELENE_LINES_URL,
    query_parameters,
    query_url,
    receipt,
)


def test_ncdot_query_is_paginated_and_requests_closure_fields() -> None:
    parameters = query_parameters(where="CountyName = 'Buncombe'", offset=1000)
    assert parameters["f"] == "geojson"
    assert parameters["resultOffset"] == "1000"
    assert parameters["returnGeometry"] == "true"
    assert "Closed" in parameters["outFields"]
    assert query_url(where="1=1", offset=0).startswith(NCDOT_HELENE_LINES_URL)


def test_ncdot_receipt_is_serializable_and_checksummed() -> None:
    result = receipt(payload=b'{"type":"FeatureCollection"}', feature_count=80, where="1=1", request_count=1)
    assert result["feature_count"] == 80
    assert result["request_count"] == 1
    assert len(result["payload_sha256"]) == 64
    assert "not Atlanta" in str(result["study_scope"])
    assert json.loads(json.dumps(result))["source_url"].endswith("FeatureServer/1/query")
