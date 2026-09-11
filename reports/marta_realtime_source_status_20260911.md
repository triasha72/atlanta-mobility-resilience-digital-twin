# MARTA realtime-source status

## Completed

MARTA's official developer page documents public bus GTFS-Realtime Trip Updates
and Vehicle Positions endpoints. The project now has a reproducible capture
script and a successfully captured Trip Updates snapshot:

- captured at `2026-09-11T17:27:25.047462+00:00`;
- payload size: 819,752 bytes;
- SHA-256: `3f198fcb595b16ea28101f0ab11515a5d01a0118fa114c71fc9ffb2582d72ad1`.

The content-free receipt is
[`marta_tripupdates_receipt_20260911T000000Z.json`](marta_tripupdates_receipt_20260911T000000Z.json).
The raw protobuf is intentionally ignored because it is a time-sensitive
operational snapshot.

## Validation boundary

The snapshot cannot be used to rerun the 14 September 08:00 polygon calibration:
it describes bus predictions at a different instant and MARTA's documented
GTFS-Realtime feed is not a historical schedule archive. MARTA's rail realtime
service requires an API key and only returns current station arrivals.

Therefore, a valid next validation cycle must capture the static GTFS, the
realtime snapshot, and the MARTA Planner results at the same operational time.
It must use fresh polygon-origin cases and retain the existing independent
holdout gate. The prior static-versus-planner calibration remains a diagnostic
failure, not a publishable result.
