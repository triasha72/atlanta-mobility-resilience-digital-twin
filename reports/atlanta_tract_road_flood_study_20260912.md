# Atlanta tract-access road and FEMA flood-overlay study

## Study design

The road study uses the committed 12-km downtown Atlanta buffer in
`configs/v1_atlanta_tract_study.yaml`. It covers all 50 selected Census-tract
representative origins and 101 mapped essential destinations. The cached drive
graph contains 22,145 nodes and 56,516 directed edges.

The baseline was compared with five deterministic random 10-edge closures and
one 10-edge sampled-betweenness closure. The centrality scenario uses 200
seeded source nodes, so it is a scalable approximation rather than an exact
all-node betweenness ranking.

For the flood sensitivity, 3,575 FEMA National Flood Hazard Layer features
with `SFHA_TF = 'T'` were retrieved using nine object-ID-paginated ArcGIS
requests. The immutable query receipt is
[`fema_nfhl_atlanta_tract_study_receipt.json`](fema_nfhl_atlanta_tract_study_receipt.json).
The overlay marked 2,270 directed road edges as intersecting those polygons.

## Results

| Scenario | Reachable OD share | Mean reachable minutes | Population-weighted opportunities |
| --- | ---: | ---: | ---: |
| Baseline | 98.0% | 9.40 | 98.98 |
| Random 10-edge ensemble mean (5 runs) | 98.0% | 9.40 | 98.98 |
| Sampled-betweenness 10-edge closure | 98.0% | 9.60 | 98.98 |
| FEMA SFHA overlay closure | 73.4% | 9.73 | 75.83 |

Relative to baseline, the FEMA-overlay scenario changes reachable OD share by
-24.57 percentage points and population-weighted accessible opportunities by
-23.15. The random ensemble's mean travel time ranges from 9.40 to 9.41
minutes across its empirical 5th--95th percentile interval.

## Interpretation boundary

This is a spatial sensitivity analysis: it removes every graph edge that
intersects a FEMA special flood hazard area. It is not a forecast, an observed
flood event, a road-closure record, or a claim that every intersecting road is
impassable. The results are reproducible diagnostic evidence, and should be
paired with event-specific closure or depth data before operational use.
