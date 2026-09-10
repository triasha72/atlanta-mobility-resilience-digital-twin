# Polygon-origin calibration: unresolved routing gap

## Decision

Do not create a new publication holdout or publish aggregate transit-accessibility
percentages from this router. The polygon-constrained calibration did not meet
the 80% within-15-minute criterion used for the earlier independent holdout.

## Evidence

Sixteen public-coordinate origin/destination pairs were sampled strictly inside
official 2024 Census tract polygons, across four modeled time bands. MARTA's
public Trip Planner returned an itinerary for every case at 08:00 on 14
September 2026. The base network-walking router had a 4.29-minute median
absolute difference, 9.58-minute mean absolute difference, and 12/16 (75%) of
cases within 15 minutes. The four misses were all 20.17--31.30 minutes slower
than the planner.

The reviewed cases and score are in
[`transit_polygon_calibration_cases_20260914.csv`](transit_polygon_calibration_cases_20260914.csv)
and
[`transit_polygon_calibration_summary_20260914.csv`](transit_polygon_calibration_summary_20260914.csv).

## Alternatives tested

1. **Direct pedestrian itinerary:** The router now considers a directed OSM
   pedestrian-network route up to 5 km alongside walk--transit--walk. The
   calibration remained 75% within 15 minutes (median 4.58 minutes). This is a
   valid model capability but does not explain the four misses.
2. **Wider transit access and egress cap:** Raising the cap from 2.5 km to 5 km
   also remained 75% within 15 minutes (median 5.79 minutes).
3. **Fresh official GTFS download:** On 10 September 2026 the public MARTA
   GTFS download had the same SHA-256 as the cached feed:
   `f4a36309f42858d3c55bf46298395471621ba6ec1888a141c543a1190a52e2e1`.
   A stale local copy is therefore not the explanation.

The two sensitivity outputs are
[`transit_polygon_calibration_rerouted_summary_20260914.csv`](transit_polygon_calibration_rerouted_summary_20260914.csv)
and
[`transit_polygon_calibration_5000m_summary_20260914.csv`](transit_polygon_calibration_5000m_summary_20260914.csv).

## Remaining gap and safe next step

The remaining discrepancy is concentrated in longer paths and reflects a
planner-versus-static-schedule source mismatch. A targeted leg comparison makes
the boundary concrete: for the largest miss, MARTA displays a 34-minute Route
14 itinerary beginning at 08:01 with 0.9 miles of walking. The static GTFS has
active Route 14 stops reachable from the sampled origin in 11.31 minutes on
the OSM pedestrian graph, but no catchable Route 14 departure at any such stop
until 10:00. The local scan's 65.3-minute itinerary is therefore consistent
with the downloaded static schedule; it cannot reproduce the planner's
08:01 Route 14 service from that source alone.

The defensible next step is to obtain a MARTA-authoritative schedule source
that matches the planner for the validation date (or an approved realtime/
planner API), version and checksum it, then rerun a fully disjoint
polygon-origin holdout. Aggregate publication remains blocked until that
holdout passes.
