# Phase 2 and 3 readiness update

## Flood-overlay calibration

The tract-scale FEMA sensitivity study is complete. The repository now also
contains `scripts/calibrate_flood_overlay.py`, which compares the FEMA-exposed
edge labels with a CRS-declared, official event-specific road-closure dataset
and reports edge-level precision and recall. No closure dataset for a defined
Atlanta flood event was supplied or found in the repository, so calibration
metrics are intentionally not fabricated.

## Acceleration and learning readiness

The tract-scale CPU benchmark routed 5,050 OD pairs over the 22,145-node,
56,516-edge graph in 4.82 seconds. This host is macOS on Apple M4 and reports
neither CUDA runtime nor cuGraph availability. A CUDA-capable host is required
before a valid RAPIDS cuGraph comparison or CUDA GNN training can be claimed.

## Aggregate synthetic OD demand

The baseline synthetic-demand workflow samples 100,000 aggregate OD counts
from public tract population and destination-opportunity margins. It contains
no individual trips or trajectories. The completed fixed-seed sample has
origin-margin total variation 0.01118 and destination-margin total variation
0.01401 relative to those public margins. This is a margin-utility check, not
a formal differential-privacy guarantee or a validation against observed demand.
