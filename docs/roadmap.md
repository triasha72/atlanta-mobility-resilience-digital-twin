# Roadmap

[Project overview and current scope](../README.md)

## Version 1: Road-network resilience baseline

- [x] OSM road-network download and GraphML caching
- [x] Baseline OD travel-time routing
- [x] Threshold-based accessibility score
- [x] Random and high-betweenness disruption scenarios
- [x] Scenario metrics, CSV outputs, and figures
- [x] Unit tests for core logic
- [x] checksummed run manifest for the public OSM graph, config, and CSV outputs
- [x] execute and review the first frozen Atlanta demo run

## Version 1.1: Research-quality data layer

- [x] Census tract origins from official representative coordinates
- [x] Essential destinations and transparent facility-count opportunity weights
- [x] ACS-derived population weights with margins of error retained
- [x] documented study area and tract sampling decisions
- [x] propagate ACS population uncertainty through accessibility comparisons

## Version 2: Transit and climate disruptions

- [x] Audit MARTA's public GTFS schedule and record its checksum, scale, and route types
- [x] Implement a schedule-aware GTFS walk-transit-walk router with a frozen
  walking-transfer rule, service-date selection, and exceptions.
- [x] Run the router against MARTA's downloaded feed for 50 ACS tract centroids,
  101 mapped essential facilities, and 07:00, 08:00, and 09:00 departures.
- [x] Fix same-vehicle transfer handling after three MARTA Trip Planner checks
  exposed inflated travel times.
- [x] Generate a fixed-seed, 20-case manual validation sample and scorer.
- [x] Complete the 20 documented MARTA planner checks and publish the routing
  gap they exposed. This is a schedule-model check, not an observed-trip study.
- [x] Add spatially indexed walking links between nearby stops and regenerate
  the 07:00, 08:00, and 09:00 schedule runs.
- [x] Recheck the fixed 20-case sample in MARTA's replacement Trip Planner at
  the same 08:00 departure using timestamped public URLs.
- [x] Check a separate holdout sample after the 2,500-metre access-walk
  calibration; it failed the pre-registered 80% within-15-minute gate.
- [ ] Diagnose the four long-trip holdout outliers and validate a revised
  routing model on a new, independent polygon-origin holdout before publishing
  percentages. Polygon calibration repeated the 75% within-15-minute failure;
  direct-walk, wider-access, and refreshed-feed alternatives did not resolve it.
- [x] Add checksummed capture of MARTA's official bus GTFS-Realtime Trip Updates
  endpoint. It supports a future same-time validation cycle, but cannot
  retrospectively resolve the fixed-date static-versus-planner mismatch.
- [x] Add a receipt-verifying finalizer that refuses incomplete or altered
  same-time holdouts before applying the pre-registered publication gate.
- [ ] flood, heat, or severe-weather disruption layers
- [ ] repeated simulations and uncertainty intervals

## Version 3: NVIDIA-facing technical extension

- [ ] GPU-accelerated graph metrics with RAPIDS cuGraph
- [ ] graph neural network for impact prediction
- [ ] benchmark CPU vs GPU runtime and scale
- [ ] research poster or workshop-paper submission

## Version 4: Privacy-aware synthetic mobility data

- [ ] baseline synthetic OD-demand generation
- [ ] privacy/utility evaluation
- [ ] test whether synthetic demand preserves resilience conclusions
