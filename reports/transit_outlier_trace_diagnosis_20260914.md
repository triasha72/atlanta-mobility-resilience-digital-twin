# Transfer-aware diagnosis of the failed MARTA holdout outliers

The transfer-aware trace was generated from the same static GTFS feed, cached
OSM pedestrian graph, 2,500-metre access/egress cap, and 250-metre
nearby-stop transfer rule used by the failed holdout. It confirms that none of
the four outliers is a missing-route issue.

| Origin → destination | Model / Rider Tools | Dominant modeled structure |
| --- | ---: | --- |
| 13121000202 → Station 38 | 70.95 / 50 min | 28.5 min access walk, 7.8 min wait, one vehicle trip, 4.0 min egress walk |
| 13121007900 → Station 13 | 87.60 / 68 min | 29.0 min access walk, then two nearby-stop transfer walks and three vehicle trips |
| 13089022403 → Station 8 | 112.47 / 75 min | 28.5 min access walk, two nearby-stop transfer walks, and three vehicle trips |
| 13121007900 → DeKalb Station 1 | 104.10 / 66 min | 28.1 min access walk, two nearby-stop transfer walks, and three vehicle trips |

## Finding

The local router’s high errors cluster around long origin access walks and
transfer-heavy paths. The evidence does **not** support changing a single
global transfer penalty: the one-vehicle Station 38 case is already 21
minutes high. The next calibration hypothesis should instead target the
origin-access model (tract-centroid representation and candidate stop
selection), while separately checking whether the 250-metre transfer links
correspond to Rider Tools’ actual interchange points.

## Safeguard

These four holdout routes remain diagnostic-only. They must not be used to
select a new cap, walking speed, or transfer penalty. Any alternate
origin-access approach must be calibrated on newly sampled routes, followed by
a holdout that excludes every route used so far.

## Sources

- `reports/transit_holdout_model_itineraries_transfer_20260914.csv`
- `reports/transit_validation_holdout_cases_20260914.csv`
