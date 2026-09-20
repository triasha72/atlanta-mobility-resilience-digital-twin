# Hurricane Helene Atlanta closure-source assessment

**Assessment date:** 2026-09-20  
**Candidate event:** Hurricane Helene, City of Atlanta, 2024-09-27  
**Decision:** do not run flood-overlay calibration or the edge-closure ML
baseline from the currently located evidence.

## What was located

The City of Atlanta's Hurricane Helene preparedness/update page is an official
contemporaneous source. It reports a closure at Lake Forrest Drive NW because
of a sinkhole, a closure of Bolton Road between Marietta Boulevard and Marietta
Road, and a submerged closure on Bohler Road between Battleview Drive and Cross
Creek Parkway. The page is useful event evidence, but it is not a downloadable
road-closure layer and does not provide geometries or complete network coverage.

An Internet Archive capture of the official page from 2024-09-28 16:38:43 UTC
is retained locally under `data/external/helene/`. Its archive URL and SHA-256
are recorded in `reports/atlanta_helene_archived_source_receipt_20260920.json`.
The capture contains the Bohler Road, Bolton Road, and Lake Forrest Drive
statements. It improves provenance and timing, but still does not provide line
geometry or observed-open coverage.

Georgia 511 documents an Events API with closure fields, an event identifier,
roadway attributes, and a developer key requirement. Its documented endpoint
returns traffic events; no public historical-event archive was located in the
API documentation. A current API response cannot reconstruct September 2024.

Sources:

- City of Atlanta, [Hurricane Helene preparedness and updates](https://www.atlantaga.gov/government/mayor-s-office/executive-offices/office-of-emergency-preparedness/city-of-atlanta-hurricane-helene-preparedness)
- Georgia 511, [Events API documentation](https://511ga.org/help/endpoint/event)
- Georgia 511, [developer API documentation](https://511ga.org/developers/doc)

## Why the study cannot proceed from these notices

The three published locations are neither a complete line/polygon closure layer
nor observed open-road labels. Geocoding the prose into road segments would add
researcher-created geometry and would make unreported edges look falsely
observed-open. That would bias both FEMA-overlay precision/recall and a
spatially held-out classifier. A GNN cannot repair missing outcome labels.

Consequently, this event remains suitable as a **qualitative sensitivity
context**, not as an Atlanta event-calibrated flood or ML study.

## Required source to close the Atlanta validation gap

Request a GDOT/Georgia 511 event extract for 2024-09-27 through 2024-09-30 ET
covering the Atlanta study extent. Ask for the original geometry and these
fields where available: event ID, source organization, roadway/location,
closed/full-closure status, lanes closed, start/end/update timestamps, reason,
and event lifecycle. Also request a coverage statement describing whether roads
absent from the extract were actively observed as open or merely unreported.

With that receipt-backed extract, retain the original file and SHA-256 checksum,
convert only losslessly to CRS-declared GeoJSON, run
`scripts/calibrate_flood_overlay.py`, then run the spatial baseline only if
both closed and observed-open edges occur in independent spatial blocks.

## Separate technical alternative

NCDOT publishes an official historical Hurricane Helene TIMS feature service
with 1,430 line incidents, closure status, reasons, and start/end/update
timestamps. It is a viable **North Carolina transfer benchmark** for testing
the closure-learning workflow, but it cannot validate an Atlanta flood model.
Any use of it must be reported as a different geography and must still define a
defensible observed-open/control set before classification or GNN evaluation.

The repository now includes a paginated, checksummed downloader and label
coverage gate for this purpose. The bounded Buncombe County retrieval on
2026-09-20 contained 80 line records, all explicitly labelled `Closed=yes`.
The resulting gate correctly blocked supervised classification because it had
no explicit observed-open records. Its receipt and audit are retained in
`reports/ncdot_helene_buncombe_closures_receipt_20260920.json` and
`reports/ncdot_helene_buncombe_label_audit_20260920.json`.

```bash
PYTHONPATH=src python3 scripts/download_ncdot_helene_closures.py \
  --county Buncombe \
  --output data/external/ncdot_helene_buncombe_closures.geojson \
  --receipt reports/ncdot_helene_buncombe_closures_receipt.json

PYTHONPATH=src python3 scripts/audit_event_label_coverage.py \
  --input data/external/ncdot_helene_buncombe_closures.geojson \
  --output reports/ncdot_helene_buncombe_label_audit.json
```

Source: [NCDOT Hurricane Helene response map](https://www.arcgis.com/home/item.html?id=66d0698a5ba846e5989d282301f4405d).
