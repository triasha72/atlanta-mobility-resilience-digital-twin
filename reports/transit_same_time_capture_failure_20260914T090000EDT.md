# Same-time MARTA validation capture failure: 14 September 2026, 09:00 EDT

## Result

No source-aligned validation artifacts were created, and no publication gate
was evaluated. This is an invalid no-data attempt, not a failed transit-model
validation.

## Attempt

At 08:59 EDT, the validation cycle was re-scoped from the expired 08:00 window
to a 09:00 EDT departure. `prepare_same_time_transit_validation.py` was run
with a fresh `20260914T090000EDT` run ID and the previously reviewed pairs
excluded.

The first required official static GTFS request failed before any artifact was
written: `urllib.error.URLError: [Errno 8] nodename nor servname provided, or
not known` for `https://itsmarta.com/google_transit_feed/google_transit.zip`.
The in-app-browser fallback was blocked from opening the ZIP, and the text-web
fetcher does not support binary ZIP or Protocol Buffer content. Consequently,
there is no static-feed checksum, GTFS-Realtime receipt, holdout sample, or
Planner review to score.

## Safe retry

Run the existing command from a network that can resolve and download MARTA's
official binary feeds during a future 15-minute source-alignment window. Verify
that all three source receipts (static GTFS, Trip Updates, and Vehicle
Positions) are created before opening Planner URLs. Do not reuse this attempt's
time or represent it as a validation result.
