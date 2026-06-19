# Notebooks

Use notebooks for exploratory work only. Once a result becomes part of the reproducible pipeline, move it into `src/amrdt/` and add a test where practical.

Suggested notebook sequence:

1. `01_network_setup.ipynb` — inspect the OSM road graph.
2. `02_accessibility_baseline.ipynb` — validate OD routes and travel times.
3. `03_disruption_scenarios.ipynb` — compare closure strategies.
4. `04_equity_layer.ipynb` — add tract-level weights and impact maps.
5. `05_gnn_extension.ipynb` — later graph-learning experiments.
