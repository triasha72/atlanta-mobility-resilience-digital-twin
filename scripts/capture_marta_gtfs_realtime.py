"""Capture MARTA's public GTFS-Realtime Trip Updates feed with provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import Request, urlopen

MARTA_TRIP_UPDATES_URL = (
    "https://gtfs-rt.itsmarta.com/TMGTFSRealTimeWebService/tripupdate/tripupdates.pb"
)


def receipt(*, payload: bytes, source_url: str, captured_at: str, content_type: str | None) -> dict[str, object]:
    """Return a content-free receipt for one immutable realtime snapshot."""
    return {
        "schema_version": "1.0",
        "dataset": "MARTA Bus GTFS-Realtime Trip Updates",
        "source_url": source_url,
        "captured_at": captured_at,
        "content_type": content_type,
        "payload_bytes": len(payload),
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "scope": "point-in-time bus predictions; not a historical schedule archive",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=MARTA_TRIP_UPDATES_URL)
    parser.add_argument("--feed", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    # MARTA's public endpoint negotiates its protobuf response only with its
    # default Accept header; explicitly requesting a protobuf MIME type returns
    # HTTP 406.
    request = Request(args.url)
    with urlopen(request, timeout=30) as response:
        payload = response.read()
        content_type = response.headers.get_content_type()
    if not payload:
        raise ValueError("MARTA GTFS-Realtime endpoint returned an empty payload")
    captured_at = datetime.now(UTC).isoformat()
    args.feed.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.feed.write_bytes(payload)
    args.receipt.write_text(
        json.dumps(
            receipt(
                payload=payload,
                source_url=args.url,
                captured_at=captured_at,
                content_type=content_type,
            ),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"captured {len(payload)} bytes to {args.feed}")
    print(f"wrote receipt to {args.receipt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
