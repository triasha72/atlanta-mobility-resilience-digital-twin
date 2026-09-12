# Atlanta Mobility Resilience Digital Twin

[Portfolio case study](https://triasha72.github.io/Portfolio/case-atlanta.html)

[![CI](https://github.com/triasha72/atlanta-mobility-resilience-digital-twin/actions/workflows/ci.yml/badge.svg)](https://github.com/triasha72/atlanta-mobility-resilience-digital-twin/actions/workflows/ci.yml)

A reproducible, research-oriented road-network resilience simulator for examining how targeted transportation disruptions affect travel time and access to opportunities in Atlanta.

> **Version 1 scope:** Road-network resilience prototype. It models shortest-path travel-time accessibility under simulated edge closures. It is not yet a calibrated traffic assignment model or a full multimodal digital twin.

## Project story

**Situation.** A road closure does not affect every neighborhood equally, and a
citywide average can hide who loses access to jobs, healthcare, or other useful
destinations.

**Task.** I built a transparent Atlanta baseline that can compare disruptions
without pretending that free-flow routing is observed traffic behavior.

**Action.** The pipeline downloads the real public OpenStreetMap road graph,
adds travel-time attributes, snaps origins and destinations, and compares random
closures with high-betweenness closures. Every run now writes a text-only
manifest that hashes the OSM graph cache, configuration, and CSV outputs.

**Result.** The first frozen public-data run covered a downtown Atlanta graph
with 672 nodes and 1,641 directed edges. Closing the selected high-betweenness
links increased mean travel time across the nine illustrative OD pairs by
`0.103` minutes; the three-edge random closure changed none of those paths.
Reachability and the toy opportunity count stayed unchanged. This is a
free-flow software demonstration, not a calibrated traffic or equity result.

The research data layer replaces the three hand-picked origin points with a
reproducible sample of 50 Census tracts. It joins 2024 ACS five-year population
and household-income estimates for Fulton and DeKalb counties to official
Census representative coordinates, then selects the most populous tracts whose
representative point lies within 10 km of downtown. The sample represents an
estimated 216,659 residents. ACS margins of error are retained instead of
treating survey estimates as exact counts.

`scripts/propagate_acs_uncertainty.py` carries those 90% margins of error
through every completed accessibility scenario with deterministic Monte Carlo
draws. It reports the mean and 5th/95th percentiles instead of treating each
tract population estimate as exact.

Random closure experiments can also use a deterministic ensemble by setting
`replicates` above one on a `random_edges` scenario. The pipeline writes one
result per sampled closure and `outputs/scenario_uncertainty_intervals.csv`
with empirical mean, 5th, and 95th percentiles across the ensemble. These
intervals reflect simulated closure selection only, not real-world traffic
uncertainty.

For a flood-overlay sensitivity scenario, annotate a cached road graph with a
versioned, CRS-declared hazard GeoJSON or GeoPackage, then configure a
`flood_exposed_edges` scenario. This removes intersecting edges; it does not
claim that those roads are actually closed.

For a reproducible public FEMA NFHL subset, derive the GeoJSON directly from
the road graph extent and retain its receipt before annotation:

```bash
PYTHONPATH=src python3 scripts/download_fema_nfhl.py \
  --graph data/processed/atlanta_drive.graphml \
  --output data/external/fema_nfhl_atlanta.geojson \
  --receipt reports/fema_nfhl_atlanta_receipt.json
```

The committed `configs/v1_atlanta_tract_study.yaml` defines the reproducible
12-km downtown road study area covering all 50 selected tract origins. Its
baseline, five random 10-edge closures, and targeted closure can be run with:

```bash
PYTHONPATH=src python3 -m amrdt.cli run --config configs/v1_atlanta_tract_study.yaml
```

If a deliberately small test extent returns no polygons, use `--allow-empty`
only to retain the result and receipt. Do not run `flood_exposed_edges` for an
empty hazard subset.

```bash
PYTHONPATH=src python3 scripts/annotate_flood_exposure.py \
  --graph data/processed/atlanta_drive.graphml \
  --hazards data/external/fema_nfhl_atlanta.geojson \
  --output data/processed/atlanta_drive_flood_annotated.graphml
```

The text-only evidence record is
[`artifacts/atlanta_demo_v1.json`](artifacts/atlanta_demo_v1.json). It includes
the public OSM/ODbL source, study boundary, graph and config hashes, scenario
results, and interpretation limit without redistributing the raw graph.

The tract materialization evidence is
[`artifacts/acs_tract_origins_v1.json`](artifacts/acs_tract_origins_v1.json).
Rebuild the ignored row-level file with:

```bash
PYTHONPATH=src python3 scripts/materialize_acs_origins.py
```

This does not yet establish an equity result: tract representative points are
routing origins, not observed trip starts. The matching destination layer uses
101 currently mapped OpenStreetMap facilities within 10 km of downtown: 42
clinics, 35 fire stations, 14 hospitals, and 10 shelters. Each mapped facility
counts as one opportunity because consistent capacity data is not available.
OpenStreetMap coverage can still be incomplete.

The transit track now starts from MARTA's public static GTFS schedule rather
than a hand-built station list. The audited feed contains 7,055 stops, 86
routes, 45,367 trips, and 2,076,118 stop-time rows; its content-free receipt is
[`reports/marta_gtfs_receipt_v1.json`](reports/marta_gtfs_receipt_v1.json).
Rebuild the ignored source ZIP and the receipt with:

```bash
PYTHONPATH=src python3 scripts/audit_marta_gtfs.py \
  --output reports/marta_gtfs_receipt_v1.json
```

This verifies the public schedule structure only. A road-plus-transit
accessibility result still needs a documented walking-transfer rule and a
service-date-specific routing model.

The first schedule-aware walk-transit-walk path is now available. It uses active
trips for one GTFS service date, a 2,500-metre origin/destination walk cap, a
250-metre nearby-stop transfer walk cap, and an
08:00 departure by default. The router keeps riders on the same scheduled
vehicle without an added transfer penalty and applies a two-minute penalty only
when boarding a different vehicle. It does not yet model fares, capacity,
walking-path barriers, or real-time delay.

```bash
PYTHONPATH=src python3 scripts/evaluate_transit_accessibility.py \
  --gtfs data/external/marta/google_transit.zip \
  --service-date 20260907 --departure 08:00 \
  --origins data/processed/acs_tract_origins.csv \
  --destinations data/processed/osm_essential_destinations.csv \
  --output outputs/transit_accessibility_20260907_0800.csv
```

Once runs are available for more than one departure time, build the report
used for review. It keeps the underlying OD files intact and applies practical
30-, 45-, 60-, and 90-minute limits only in the summary.

```bash
PYTHONPATH=src python3 scripts/summarize_transit_accessibility.py \
  --inputs outputs/transit_accessibility_20260907_0700.csv \
           outputs/transit_accessibility_20260907_0800.csv \
           outputs/transit_accessibility_20260907_0900.csv \
  --summary-output outputs/transit_accessibility_summary_20260907.csv \
  --origin-output outputs/transit_accessibility_by_origin_20260907.csv \
  --figure-output figures/transit_accessibility_summary_20260907.png
```

The report measures scheduled door-to-door access between tract centroids and
mapped essential facilities. Before using it as a project finding, manually
check a small, documented set of routes in the
[MARTA Trip Planner](https://tracker.itsmarta.com/plan). It is a static-GTFS
comparison, not a claim about real-time reliability, fares, capacity, or
walking barriers.

### Schedule run and validation status: 7 September 2026

The first completed schedule run covers 50 ACS tract centroids and 101 mapped
essential facilities, using MARTA's static GTFS feed and an 800-metre walk cap.
These are scheduled-access results, not observed rider travel times.

The first run produced schedule percentages for 07:00, 08:00, and 09:00, but a
fixed 20-case MARTA Planner review found that the local router missed walking
transfers between nearby stops. The router now indexes 250-metre nearby-stop
walks. A replacement-planner review on 14 September 2026 used timestamped
public URLs for all 20 cases: every MARTA route was returned, while the local
model had four no-arrival results under its original 800-metre access-walk cap.
The mean absolute difference across the 16 comparable cases was 8.66 minutes.

A network-walking calibration found that a 2,500-metre access-walk cap removes
those four false no-arrival cases; the 20-case calibration mean absolute
difference was 8.59 minutes
minutes. This is a calibration finding, not a final validation: a separate
holdout sample must be checked before any aggregate accessibility percentage is
published as a project result. The scored review is recorded in
[`reports/transit_validation_summary_20260914.csv`](reports/transit_validation_summary_20260914.csv).

The original three public route checks are recorded in
[`reports/transit_planner_sanity_checks_20260907.csv`](reports/transit_planner_sanity_checks_20260907.csv).
The fuller result and next implementation are in
[`reports/transit_planner_validation_20260907.md`](reports/transit_planner_validation_20260907.md).

### Reproducible manual validation sample

Use the following command to create 20 public-coordinate checks: four each
from the 0–30, 31–60, 61–90, over-90-minute, and no-scheduled-arrival bands.
The fixed seed means that another reviewer can reproduce the exact same sample.

```bash
PYTHONPATH=src python3 scripts/create_transit_validation_sample.py \
  --od outputs/transit_accessibility_20260907_0800.csv \
  --origins data/processed/acs_tract_origins.csv \
  --destinations data/processed/osm_essential_destinations.csv \
  --service-date 20260907 --departure 08:00 \
  --output outputs/transit_validation_sample_20260907_0800.csv
```

Each row includes a direct MARTA Trip Planner URL for the sampled public map
points. Record the first practical itinerary in `planner_minutes`, who checked
it, and the date checked. Do not replace missing model arrivals with a guessed
number. After completing the numeric planner times, score the completed rows:

```bash
PYTHONPATH=src python3 scripts/score_transit_validation.py \
  --input outputs/transit_validation_sample_20260907_0800.csv \
  --summary-output reports/transit_validation_summary_20260907.csv \
  --cases-output reports/transit_validation_cases_20260907.csv
```

This comparison is a diagnostic for schedule and walking assumptions. It is not
a rider survey, a real-time reliability study, or a substitute for observed
travel-time data.

To record an ordered review without editing the CSV by hand, supply a positive
duration for each returned itinerary and `no_route` for a planner result with
no itinerary. The count must match the CSV rows exactly:

```bash
PYTHONPATH=src python3 scripts/record_manual_validation.py \
  --input outputs/transit_polygon_same_time_holdout_20260914T120000Z.csv \
  --planner-outcomes 34,no_route,52.5 \
  --reviewer "MARTA Rider Tools"
```

### Independent holdout and publication gate

The calibrated router parameters and pre-registered holdout gate are frozen in
[`artifacts/transit_validation_protocol_v1.json`](artifacts/transit_validation_protocol_v1.json).
After regenerating the full OD run with those parameters, create a new sample
that excludes every reviewed calibration origin-destination pair:

```bash
PYTHONPATH=src python3 scripts/create_transit_holdout_sample.py \
  --od outputs/transit_accessibility_20260914_0800.csv \
  --origins data/processed/acs_tract_origins.csv \
  --destinations data/processed/osm_essential_destinations.csv \
  --reviewed reports/transit_validation_cases_20260914.csv \
  --service-date 20260914 --departure 08:00 \
  --output outputs/transit_validation_holdout_20260914_0800.csv
```

Record the Rider Tools results in that CSV, then score it with
`--gate-output reports/transit_validation_holdout_gate_20260914.csv`. The
aggregate report remains unpublished unless the gate passes.

The completed 14 September 2026 holdout did **not** pass that gate: it had zero
false no-arrivals and a 5.93-minute median absolute difference, but only 75%
of cases were within 15 minutes (the pre-registered threshold is 80%). The
full decision and next validation cycle are documented in
[`reports/transit_holdout_validation_20260914.md`](reports/transit_holdout_validation_20260914.md).
Accordingly, the aggregate accessibility outputs remain diagnostic artifacts,
not published project findings.

### Pedestrian-network walking legs

The default cap is a reproducible calibration approximation. To replace it with
walk-network travel time, cache an OpenStreetMap pedestrian graph and pass it
to the evaluator:

```bash
PYTHONPATH=src python3 scripts/cache_pedestrian_network.py

PYTHONPATH=src python3 scripts/evaluate_transit_accessibility.py \
  --gtfs data/external/marta/google_transit.zip \
  --service-date 20260914 --departure 08:00 \
  --origins data/processed/acs_tract_origins.csv \
  --destinations data/processed/osm_essential_destinations.csv \
  --walk-graph data/processed/atlanta_walk.graphml \
  --output outputs/transit_accessibility_20260914_0800.csv
```

This uses directed shortest-path walking time on cached OSM edges for access
and egress. It does not establish sidewalk condition, safety, accessibility,
or temporary closures.

### Tract-access sensitivity

The failed independent holdout showed that long centroid-to-stop walks are a
major source of error. Generate the labeled centroid sensitivity proxies with:

```bash
PYTHONPATH=src python3 scripts/create_tract_access_proxies.py \
  --origins data/processed/acs_tract_origins.csv \
  --gazetteer data/external/acs2024/2024_gaz_tracts_13.txt \
  --output data/processed/acs_tract_access_proxies.csv
```

These points are area-equivalent radial proxies based on tract land area; they
are a sensitivity layer, not asserted within-tract residential samples. A
future calibrated model must replace them with polygon-backed sampling before
using them for published tract estimates.

The initial proxy calibration is recorded in
[`reports/transit_proxy_calibration_20260914.md`](reports/transit_proxy_calibration_20260914.md).
It is promising diagnostic evidence, not a replacement for the failed
independent holdout or a permission to publish aggregate percentages.

Polygon-constrained samples now replace the proxy points for the current
calibration cycle. Their 16-case MARTA review also reached only 75% within 15
minutes. Direct pedestrian routing (up to 5 km), a 5-km access/egress
sensitivity run, and a fresh official GTFS download did not close that gap.
The decision, evidence, and required source-supported next step are recorded
in [`reports/transit_polygon_calibration_failure_20260914.md`](reports/transit_polygon_calibration_failure_20260914.md).
The polygon and aggregate accessibility outputs therefore remain diagnostic,
not publishable findings.

### Realtime capture for a future same-time validation cycle

MARTA officially publishes public bus GTFS-Realtime Trip Updates and Vehicle
Positions. The feeds are point-in-time operational snapshots, not a historical
schedule archive, so they cannot retroactively repair a static-versus-planner
mismatch. Capture and checksum a snapshot for a same-time validation run with:

```bash
PYTHONPATH=src python3 scripts/capture_marta_gtfs_realtime.py \
  --feed data/external/marta/tripupdates_YYYYMMDDTHHMMSSZ.pb \
  --receipt reports/marta_tripupdates_receipt_YYYYMMDDTHHMMSSZ.json
```

Use the snapshot only for a query at the matching timestamp. The static GTFS
schedule remains the reproducible basis for future-date accessibility runs.

For a source-aligned validation cycle, this one command captures both official
feeds, recomputes polygon-origin OD times, and creates a fresh tract-pair-
disjoint holdout. Complete the public Planner checks in the generated CSV
before applying the publication gate. Run it on the requested service date
within 15 minutes of the local departure; the command refuses an early or
stale capture unless explicitly marked diagnostic-only:

```bash
PYTHONPATH=src python3 scripts/prepare_same_time_transit_validation.py \
  --service-date 20260914 --departure 08:00 --run-id 20260914T120000Z \
  --prior reports/transit_network_calibration_cases_2500m_20260914.csv \
          reports/transit_validation_holdout_cases_20260914.csv \
          reports/transit_proxy_calibration_cases_20260914.csv \
          reports/transit_polygon_calibration_cases_20260914.csv
```

After recording every generated pair, verify the static and realtime checksums
and apply the gate in one step. This refuses partial reviews, duplicate pairs,
or altered source snapshots:

```bash
PYTHONPATH=src python3 scripts/finalize_same_time_transit_validation.py \
  --manifest reports/transit_same_time_validation_manifest_20260914T120000Z.json \
  --reviewed outputs/transit_polygon_same_time_holdout_20260914T120000Z.csv \
  --summary-output reports/transit_same_time_validation_summary_20260914T120000Z.csv \
  --cases-output reports/transit_same_time_validation_cases_20260914T120000Z.csv \
  --gate-output reports/transit_same_time_validation_gate_20260914T120000Z.csv
```

## Research motivation

Urban transportation networks can fail unevenly. A road closure may have limited impact on some neighborhoods but significantly reduce access to jobs, healthcare, or other destinations for others. This repository establishes a transparent baseline for measuring those differences and provides a foundation for later work in graph machine learning, GPU acceleration, multimodal transit disruption modeling, and synthetic mobility data.

## Version 1 research question

**How do targeted road-network disruptions change travel-time accessibility across a defined Atlanta study area?**

## What this project does

The data flow and its real-world limits are summarized in
[the system architecture](docs/architecture.md).

- downloads and caches a drivable road network from OpenStreetMap via OSMnx
- adds speed and travel-time attributes to road links
- snaps configured origins and destinations to the network
- computes baseline OD shortest-path travel times
- simulates random and high-betweenness road-edge closures
- measures reachability, travel-time changes, and threshold-based accessibility
- produces CSV outputs and diagnostic figures

## Technology stack

- Python 3.10+
- OSMnx / NetworkX
- GeoPandas / Shapely
- pandas / NumPy
- scikit-learn (reserved for the Version 1.1 ML baseline)
- matplotlib

## Quick start

```bash

# 1. Create an environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate

# 2. Install the project and development tools
pip install -e ".[dev]"

# 3. Run the manageable downtown demonstration
amrdt run --config configs/v1_demo.yaml

# 4. Run tests
pytest
```

The first run downloads and caches the configured road network in `data/processed/`. Later runs reuse the cached GraphML file.

Pull requests run Ruff and the deterministic core test suite in GitHub Actions.
The live OSM download remains an explicit local integration step because it
depends on an external service; the resulting GraphML cache makes later runs
repeatable.

## Outputs

![Scenario comparison](figures/scenario_summary.png)

The chart is generated from the same scenario table used by the written
analysis; it is not a hand-edited illustration.

After a successful run, one should see:

```text
outputs/
├── od_baseline.csv
├── od_random_3_edge_closure.csv
├── od_high_betweenness_3_edge_closure.csv
├── accessibility_baseline.csv
├── accessibility_random_3_edge_closure.csv
├── accessibility_high_betweenness_3_edge_closure.csv
└── scenario_summary.csv

figures/
├── scenario_summary.png
├── baseline_affected_nodes.png
├── random_3_edge_closure_affected_nodes.png
└── high_betweenness_3_edge_closure_affected_nodes.png
```

`outputs/run_manifest.json` records the OpenStreetMap/ODbL source boundary and
SHA-256 hashes for the cached graph, configuration, and result tables.

## Configuration

`configs/v1_demo.yaml` is the small software smoke test.
`configs/v1_atlanta_template.yaml` reads the generated ACS origin and
OpenStreetMap destination tables for the research run.

### Scenario types

| Scenario | Meaning |
|---|---|
| `baseline` | No network change. |
| `random_edges` | Randomly removes directed road edges. |
| `high_betweenness_edges` | Removes edges connecting node pairs with high travel-time-weighted edge betweenness. |

## Interpretation and limits

The default road-network travel times are network-based approximations. They are
useful for a reproducible resilience baseline but should not be interpreted as
observed congestion or real-time traffic conditions. The frozen Version 1 run
uses illustrative origins and destinations. The research configuration now
uses population-weighted ACS origins and mapped essential destinations;
observed travel calibration remains open.

## What the analysis establishes

The project demonstrates a reproducible way to compare baseline travel with
explicit road-disruption scenarios and to trace changes in travel time,
accessibility, and neighborhood burden back to the affected network elements.
Its conclusions are limited to the configured demonstration network,
illustrative origins and destinations, and network-based travel-time estimates.
It does not claim calibrated disruption probability, observed congestion,
real-time city operations, or causal equity impact.
