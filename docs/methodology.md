# Version 1 methodology

## Research question

How do targeted road-network disruptions change travel-time accessibility across a defined Atlanta study area?

## Scope and interpretation

Version 1 is a **road-network resilience simulation prototype**, not a calibrated operational traffic model. The travel-time estimates are network-based free-flow approximations derived from road geometry and speed attributes. They do not yet model real-time congestion, departure-time variation, demand rerouting, transit schedules, or observed incident duration.

## Baseline workflow

1. Download and cache a directed drivable road network.
2. Attach edge speed and travel-time estimates.
3. Snap configured origins and destinations to network nodes.
4. Compute baseline shortest-path travel times for all origin-destination pairs.
5. Calculate threshold-based opportunity accessibility.

## Disruption scenarios

- `random_edges`: removes a random set of directed road edges.
- `high_betweenness_edges`: removes edges connecting node pairs ranked highly by travel-time-weighted edge betweenness.

Set `replicates` on a `random_edges` scenario to sample an independent,
deterministically seeded closure ensemble. The pipeline retains one OD and
accessibility file per replicate and writes empirical mean, 5th-percentile,
and 95th-percentile intervals to `scenario_uncertainty_intervals.csv`.
These describe variation across simulated edge selections, not confidence
intervals for observed traffic conditions.

## Flood-exposure scenarios

`scripts/annotate_flood_exposure.py` overlays a user-supplied, CRS-declared
flood-hazard GeoJSON or GeoPackage on the cached road graph and labels every
intersecting directed edge. A `flood_exposed_edges` scenario then removes those
edges. The result is a transparent hazard-overlay sensitivity scenario, not a
forecast, a statement of road closure, or a substitute for an agency closure
feed.

`scripts/download_fema_nfhl.py` can retrieve the official FEMA NFHL flood
hazard-area layer for the WGS84 graph extent using an ArcGIS REST spatial query.
It saves the exact query URL, timestamp, feature count, and response checksum
in a receipt so the selected hazard source can be audited later.

## Core outcomes

- reachable OD share
- mean travel time among reachable OD pairs
- average accessible opportunity weight
- population-weighted accessible opportunity score

## Version 2 upgrades

- MARTA transit schedule and service disruption scenarios
- Census tract origins and ACS-derived equity indicators
- hospitals, grocery stores, jobs, and other destination opportunities
- Monte Carlo closure ensembles and uncertainty quantification
- observed hazard/flood exposure and scenario calibration
- graph neural network emulator
- GPU acceleration with RAPIDS cuGraph and PyTorch Geometric
