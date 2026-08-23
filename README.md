# Atlanta Mobility Resilience Digital Twin

[![CI](https://github.com/triasha72/atlanta-mobility-resilience-digital-twin/actions/workflows/ci.yml/badge.svg)](https://github.com/triasha72/atlanta-mobility-resilience-digital-twin/actions/workflows/ci.yml)

A reproducible, research-oriented road-network resilience simulator for examining how targeted transportation disruptions affect travel time and access to opportunities in Atlanta.

> **Version 1 scope:** Road-network resilience prototype. It models shortest-path travel-time accessibility under simulated edge closures. It is not yet a calibrated traffic assignment model or a full multimodal digital twin.

## Research motivation

Urban transportation networks can fail unevenly. A road closure may have limited impact on some neighborhoods but significantly reduce access to jobs, healthcare, or other destinations for others. This repository establishes a transparent baseline for measuring those differences and provides a foundation for later work in graph machine learning, GPU acceleration, multimodal transit disruption modeling, and synthetic mobility data.

## Version 1 research question

**How do targeted road-network disruptions change travel-time accessibility across a defined Atlanta study area?**

## What this project does

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

## Configuration

We start with `configs/v1_demo.yaml`. When the demo works, we duplicate `configs/v1_atlanta_template.yaml`, then we document our origin/destination sampling logic, and replace the illustration points with research-grade data such as census tract or TAZ centroids.

### Scenario types

| Scenario | Meaning |
|---|---|
| `baseline` | No network change. |
| `random_edges` | Randomly removes directed road edges. |
| `high_betweenness_edges` | Removes edges connecting node pairs with high travel-time-weighted edge betweenness. |

## Interpretation and limits

The default road-network travel times are network-based approximations. They are useful for a reproducible resilience baseline but should not be interpreted as observed congestion or real-time traffic conditions. Version 1 also uses illustrative origin/destination points. 

## What the analysis establishes

The project demonstrates a reproducible way to compare baseline travel with
explicit road-disruption scenarios and to trace changes in travel time,
accessibility, and neighborhood burden back to the affected network elements.
Its conclusions are limited to the configured demonstration network,
illustrative origins and destinations, and network-based travel-time estimates.
It does not claim calibrated disruption probability, observed congestion,
real-time city operations, or causal equity impact.
