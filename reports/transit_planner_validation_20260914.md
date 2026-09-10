# MARTA Rider Tools validation, 14 September 2026

This reproducible 20-case check compares the local static-GTFS router with
MARTA's replacement Rider Tools planner at a scheduled 08:00 departure on 14
September 2026. Each official itinerary was requested through the public,
timestamped Rider Tools URL recorded in the reviewed case table. The first
itinerary displayed was used as the planner travel time.

All 20 Rider Tools requests returned an itinerary. With the local router's
original 800-metre origin/destination access-walk cap, 16 cases had a numeric
local arrival. Their mean absolute difference from the planner was 8.66 minutes
(median 8.01 minutes), and 87.5% were within 15 minutes. Four local no-arrival
cases had a Rider Tools itinerary.

A post-hoc 1,600-metre access-walk sensitivity removed all four no-arrival
cases and reduced mean absolute difference to 7.34 minutes (median 7.67
minutes). The project adopts that cap as a calibrated development assumption.
It is not a final performance claim: a fresh holdout sample is required before
publishing aggregate accessibility percentages.

The machine-readable summary and comparable cases are
[`transit_validation_summary_20260914.csv`](transit_validation_summary_20260914.csv)
and [`transit_validation_cases_20260914.csv`](transit_validation_cases_20260914.csv).
