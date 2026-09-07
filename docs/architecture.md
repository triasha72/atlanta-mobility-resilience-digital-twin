# System architecture

```mermaid
flowchart LR
    A[OpenStreetMap roads] --> B[Versioned road graph]
    C[ACS population estimates] --> D[Population-weighted origins]
    E[Mapped essential services] --> F[Destinations]
    B --> G[Baseline and disruption scenarios]
    D --> G
    F --> G
    G --> H[Shortest paths and reachability]
    H --> I[Travel-time and access changes]
    I --> J[Neighborhood burden and uncertainty]
    J --> K[Tables, maps, and run manifest]
```

The pipeline freezes its road graph and input tables before comparing the
baseline with random and high-betweenness closures. Each scenario uses the same
origins and destinations, which keeps the comparison attributable to the road
changes rather than changing demand data.

The current travel times are network estimates, not observed traffic. A city
operations version would need probe-speed calibration, live closures, validated
facility status, and an operational update schedule.
