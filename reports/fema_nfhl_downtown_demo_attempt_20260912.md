# FEMA NFHL downtown-demo retrieval: no-hazard result

## Result

On 12 September 2026, the official FEMA National Flood Hazard Layer spatial
query was tested against the cached `downtown_atlanta_demo_drive.graphml`
extent using the default special-flood-hazard-area filter (`SFHA_TF = 'T'`).
FEMA returned a valid GeoJSON FeatureCollection with zero features. No flood
closure scenario was run for this small demonstration extent.

## Interpretation

This is not evidence that Atlanta has no flood exposure. It says only that no
filtered FEMA hazard polygon intersected this particular small cached downtown
graph extent. A citywide study must first cache the intended full Atlanta road
graph, run `scripts/download_fema_nfhl.py` for that graph's extent, retain the
receipt, and use the resulting hazard polygons to annotate the graph.

## Source and reproducibility

The query targets FEMA's public National Flood Hazard Layer flood-hazard-area
ArcGIS endpoint at
`https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query`.
Use `--allow-empty` only to preserve a checksum receipt for an empty extent;
it does not make an empty extent suitable for a flood-closure scenario.
