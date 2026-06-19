# Data guide

Version 1 intentionally uses a light data stack so the complete pipeline is reproducible:

- **Road network:** downloaded at run time from OpenStreetMap through OSMnx and cached locally as GraphML.
- **Origins/destinations:** illustrative coordinates in `configs/v1_demo.yaml`. Replace them with tract, TAZ, or parcel/point-of-interest data for research use.
- **Equity variables:** Version 1 carries `population_weight` fields for origin weighting. Add ACS variables only after the routing pipeline is stable.
- **Transit:** Version 2 will add a documented MARTA GTFS Schedule feed and transit disruption scenarios.

Do not commit restricted, personally identifiable, or large raw datasets to the repository. Store large files in cloud storage and add a reproducible download script or a data-access note.
