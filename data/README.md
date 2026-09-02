# Data guide

Version 1 intentionally uses a light data stack so the complete pipeline is reproducible:

- **Road network:** downloaded at run time from OpenStreetMap through OSMnx and cached locally as GraphML.
- **Origins:** `scripts/materialize_acs_origins.py` joins 2024 ACS five-year
  estimates from Census Reporter to the Census Bureau's 2024 Georgia tract
  Gazetteer. Raw responses and the row-level CSV stay ignored; their hashes and
  aggregate facts are recorded in `artifacts/acs_tract_origins_v1.json`.
- **Destinations:** still illustrative coordinates in `configs/v1_demo.yaml`.
- **Equity variables:** population and household income are survey estimates,
  and their margins of error are retained. They support descriptive weighting,
  not causal claims about individual travelers.
- **Transit:** Version 2 will add a documented MARTA GTFS Schedule feed and transit disruption scenarios.
