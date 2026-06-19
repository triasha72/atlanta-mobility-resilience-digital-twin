# Data guide

Version 1 intentionally uses a light data stack so the complete pipeline is reproducible:

- **Road network:** downloaded at run time from OpenStreetMap through OSMnx and cached locally as GraphML.
- **Origins/destinations:** illustrative coordinates in `configs/v1_demo.yaml`.
- **Equity variables:** Version 1 carries `population_weight` fields for origin weighting.
- **Transit:** Version 2 will add a documented MARTA GTFS Schedule feed and transit disruption scenarios.
