# MARTA schedule-router independent holdout: 14 September 2026

## Result

The pre-registered publication gate **did not pass**. Sixteen holdout OD pairs
were sampled with a fixed seed after excluding every calibration pair. MARTA
Rider Tools was queried at 08:00 on 14 September 2026 using the timestamped
public coordinate URLs stored with each case.

| Metric | Result | Gate |
| --- | ---: | ---: |
| Completed planner cases | 16 | — |
| Model no-arrival where planner returned a route | 0 | 0 |
| Median absolute difference | 5.93 minutes | <= 10 minutes |
| Share within 15 minutes | 75% | >= 80% |

The failure is driven by four long-trip cases whose absolute differences range
from 19.6 to 38.1 minutes. The model generally overestimates these trips. This
is evidence that the static GTFS plus cached OSM-walking approximation is not
yet sufficiently accurate for publishing aggregate accessibility percentages.

## Decision

Do not publish or represent the 07:00, 08:00, or 09:00 aggregate accessibility
outputs as project findings. The outputs remain reproducible diagnostic
artifacts only.

## Remaining technical work

1. Diagnose the four long-trip outliers at itinerary-leg level, including stop
   choices, route pattern, transfer wait, and access/egress walk assumptions.
2. Make any revised assumptions on a new calibration set, then freeze a new
   protocol version before drawing a fresh independent holdout.
3. Re-run the full OD scenarios only after that new holdout meets the gate.

Source files: `reports/transit_validation_holdout_summary_20260914.csv`,
`reports/transit_validation_holdout_cases_20260914.csv`, and
`reports/transit_validation_holdout_gate_20260914.csv`.
