# Roadmap

## Version 1: Road-network resilience baseline

- [x] OSM road-network download and GraphML caching
- [x] Baseline OD travel-time routing
- [x] Threshold-based accessibility score
- [x] Random and high-betweenness disruption scenarios
- [x] Scenario metrics, CSV outputs, and figures
- [x] Unit tests for core logic

## Version 1.1: Research-quality data layer

- [ ] Census tract or TAZ origins
- [ ] Essential destinations and opportunity weights
- [ ] ACS-derived population and equity weights
- [ ] documented study area and sampling decisions

## Version 2: Transit and climate disruptions

- [ ] MARTA GTFS schedule integration
- [ ] road plus transit multimodal accessibility
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
