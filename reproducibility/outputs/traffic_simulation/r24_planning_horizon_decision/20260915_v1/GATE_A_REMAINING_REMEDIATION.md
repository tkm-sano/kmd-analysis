# Gate A remaining remediation after Planning Horizon freeze

Gate A remains **GATE_A_REQUIRES_TARGETED_REMEDIATION**. General Planning Horizon membership is no longer an active blocker.

| Item | Status after this decision | Required resolution |
|---|---|---|
| Source horizon / source-use boundary | CLOSED_WITH_LIMITATIONS | immutable 2026-01-01 snapshot; synthetic benchmark claims only |
| Generator provenance | BLOCKS_REGENERATION_ONLY | no historical regeneration claim; not a saved-snapshot Gate A blocker |
| Routing proxy / access | ACTIVE_GATE_A_STOP | decide whether saved building-to-road mappings are admissible modeled stops and specify identifiers/network/missing access limits |
| Service-event abstraction | ACTIVE_GATE_A_STOP_AFTER_PROXY | decide whether one routing proxy may be one benchmark customer node, without claiming observed one-visit events |
| Conservation / exceptions | OPEN | bind 73,547/82,246 source totals, 347/387 mapping exceptions, child records and later eligibility exclusions |
| Formal Gate A sign-off | OPEN | version interface amendments, verify A1-A6, record limitations and permit/deny Gate B |

Routing-proxy policy is next because a modeled visit-location identity is needed before a benchmark customer-node/event abstraction can be finalized. The horizon is independent: proxy remediation may narrow eligibility but cannot fabricate dispatch/wave/shift membership or change the frozen day silently.

`NEXT_EXECUTABLE_TASK = finalize routing-proxy stop policy`
