# Network Completion Pipeline v17

This is the single current pipeline specification for the accepted three-tier Formal network.

```text
Source → Structural → Three-tier Formal → SUMO → Mapping → Routeability → Acceptance
```

The stages are normative and sequential. `SOURCE` is source truth; `STRUCTURAL` is topology and raw-normalized representation; `THREE_TIER_FORMAL` produces model-ready values using `DIRECT`, `INFERRED`, or `FALLBACK`; `SUMO` materializes and validates `net.xml`; `MAPPING` maps Requests/Stops; `ROUTEABILITY` validates delivery paths; and `ACCEPTANCE` authorizes the network.

Each stage consumes the previous stage's immutable output and publishes input hashes, method/version, Decision ID, and deterministic regeneration metadata. A failed gate stops publication of the next stage. Acceptance requires all prior gates, complete provenance, SUMO build and attribute validity, acceptable connectivity, the deterministic primary 100-pair delivery routeability gate (`100/100`), and Request/Stop mapping acceptance. The primary sample is a gate, not an all-pairs proof; additional sanity results remain known limitations.

The former hierarchical-hybrid and pre-three-tier blocker pipelines are historical and `SUPERSEDED`. They remain readable for traceability but are not current execution authorities.

Machine-readable authority: `reproducibility/config/traffic_simulation/network_completion_pipeline_v17.yml`.
