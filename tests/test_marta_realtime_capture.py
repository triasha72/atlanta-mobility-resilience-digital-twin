from scripts.capture_marta_gtfs_realtime import receipt


def test_receipt_is_content_free_and_checksums_payload() -> None:
    result = receipt(
        payload=b"realtime snapshot", source_url="https://example.test/tripupdates.pb",
        captured_at="2026-09-11T12:00:00+00:00", content_type="application/octet-stream",
    )
    assert result["payload_bytes"] == 17
    assert result["payload_sha256"] == "458605dbf94e2cc913b482b5774954f2f88759b73fe09cdd76b3182f02f69007"
    assert "realtime snapshot" not in str(result)
