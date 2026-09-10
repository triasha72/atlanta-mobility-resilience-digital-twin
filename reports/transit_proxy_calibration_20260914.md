# Proxy-origin calibration: 14 September 2026

Sixteen fresh proxy-origin routes were checked in MARTA Rider Tools at 08:00 on
14 September 2026. The sampler excluded every tract-destination pair used by
the earlier 20-case calibration and 16-case failed holdout.

| Metric | Proxy calibration result |
| --- | ---: |
| Planner routes checked | 16 |
| Model no-arrival where planner returned a route | 0 |
| Mean absolute difference | 7.69 minutes |
| Median absolute difference | 3.22 minutes |
| Share within 15 minutes | 87.5% |

## Interpretation

This calibration is materially better than the failed centroid-based holdout,
but it is **not** a publication pass and cannot be used as one. The proxy
points are area-equivalent radial sensitivity points, not verified residential
locations within tract polygons. Their performance demonstrates that
origin-location representation is a plausible driver of error; it does not
justify replacing tract centroids in published outputs.

## Next required evidence

Obtain tract polygons and create reproducible, polygon-constrained residential
sample points. Re-run this calibration workflow with those points, freeze a new
protocol, and only then draw a fresh holdout excluding all previous routes.

Sources: `outputs/transit_proxy_calibration_sample_20260914_0800.csv` and
`reports/transit_proxy_calibration_summary_20260914.csv`.
