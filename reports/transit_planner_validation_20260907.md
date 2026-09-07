# MARTA planner validation, 7 September 2026

The first 20-case, fixed-seed comparison was run against MARTA Tracker at an
08:00 scheduled departure. It is a diagnostic check of two schedule planners,
not an observed rider travel-time study.

All 20 cases returned a MARTA itinerary. The four sampled cases with no
arrival in the local router also returned a MARTA route. Among the 16 cases
with a numeric result from both systems, several long local routes were much
shorter in MARTA Tracker. The discrepancy is large enough that the local
accessibility percentages are not published as validated findings.

The likely missing mechanism is walking between nearby stops during a transfer.
The local router currently permits an 800-metre walk only at the origin and
destination. MARTA Tracker can use additional walking links between stops.

Next implementation: add a spatially indexed stop-to-stop walking-transfer
graph, rerun the same 20 cases, and compare the revised results before updating
the public accessibility headline.
