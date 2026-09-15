# R24 Gate A request/event/temporal evidence decision
Decision ID: R24-GATE-A-EVIDENCE-20260915-v1. Date: 2026-09-15 JST.
Scope: EVIDENCE RECONSTRUCTION / SCHEMA / GATE-A DECISION ONLY.
Verdict: GATE_A_REQUIRES_TARGETED_REMEDIATION.
NEXT_EXECUTABLE_TASK = finalize Planning Horizon

The source chain is supported to synthetic household-day demand records → mapped building-day demand aggregation → historical routing proxies → reproducible synthetic-date membership. It does **not** establish individual shipments, compatible single-visit events, observed access points or operating schedules. No mandatory dispatch is inferred. No event/stop schema is implemented and no horizon/population is frozen.

## Facts and decision boundary
Saved daily_requests contains 73,547 unique synthetic request IDs and unique households, with 82,246 parcel-equivalents on 2026-01-01. 8,001 rows contain multiple parcel-equivalents; maximum 5. These IDs identify aggregated household-day demand, not individual parcel/transaction requests. Individual parcel, shipment and observed transaction IDs are absent.
Expected rates remain separate: all-household expectation 82023.000000/day; allocated-household expectation 81609.779892/day; mapped-positive-household expectation 16688.038865/day. None is the realized count or a load value. request_building_mapping.csv contains all 73,547 primary rows, including 347 null-building exceptions; 73,200 is its assigned subset, not the total file row count.
Scoped saved assignment supports 382,369 households / 85,690 buildings. Saved request mapping covers 73,200 rows / 81,859 content units. 347 positive rows / 387 units remain outside mapped scope; retain exclusion lineage. 39,956 positive building-day demand aggregates contain child request IDs. 17,652 buildings contain multiple request rows, maximum 12; maximum content per building 14. Full primary row/join/child/count checks passed; this verifies saved records, not original random generation.

The minimum upstream demand unit is SYNTHETIC_HOUSEHOLD_DAY_DEMAND_RECORD. The downstream building table is AGGREGATED_DELIVERY_DEMAND_RECORD. Existing stop_id is a building-day source ID, not an accepted service_event_id. Same building ≠ same service event. Same routing edge/node ≠ common access or service compatibility.

R03 saved connections cover all 39,956 building-day IDs on historical run_2 network: ROUTING_PROXY_STOP only. Routing Baseline's accepted run_3 geometry/edge-offset endpoints cover the old 10-customer fixture plus depot/charger, not an all-population OD matrix. Current-class/reachability compatibility is unaccepted. Physical entrances, access IDs, legal loading/parking and visit compatibility are unavailable in primary sources.

Request-linked temporal resolution is day-only. Source ss530 has aggregate weekday/hour receipt statistics, and manifests/legacy fixtures contain processing clocks and modeled timing; none establishes individual request timestamps, dispatch membership or real shifts. One synthetic day is DATA_SUPPORTED for immutable source membership, and MODEL_ASSUMPTION_REQUIRED as an operational one-tour horizon. Dispatch, wave and shift membership are UNSUPPORTED. Horizon may remain an abstract core concept, but A cannot pass with undefined reproducible benchmark membership and event compatibility.

## Gate decision
Accept evidence claims above and continued **read-only snapshot reconstruction** with incomplete historical generator lineage. Do not yet accept executable source adoption, event aggregation, physical access or concrete CVRP horizon. Full source-use decision for production requires scoped snapshot IDs/hashes, exclusions, request unit, horizon and access/event policy together. Gate A is not globally blocked by generator provenance; bounded remediation can proceed from saved bytes. Gate B remains gated by A passage.
Remaining A work: finalize reproducible horizon/source-use decision and versioned interface amendment; resolve event/access evidence or separately review explicitly labeled proxy assumptions; complete acceptance/conservation/exception contract and gate sign-off. Merely choosing a day does not resolve event/access. Vehicle/capacity remain OPEN; they are not conditions for this evidence audit.
Acceptance reviewer: Codex evidence audit under user-authorized scope. This is a negative/conditional gate decision, **not** approval of new model assumptions; no affirmative final A sign-off.

Next task rationale: horizon membership constrains event compatibility and schema; finalize Planning Horizon is first, using the documented alternatives and keeping event/access dependencies explicit. It is not executed here. Do not advance to B or freeze eligibility yet.

Arbitrariness risk: converting building/day/road-node co-location into a one-visit event or carrier batch. Validity risk: synthetic parcel-equivalents/proxy geometry relabeled observed parcels/physical stops. Compatibility risk: promoting old run_2 all-candidate mappings to accepted run_3/new-class endpoints and costs. Ota statistical/geographic grounding does not establish observed operations or representativeness.
Parent paths/hashes, source files, scripts/configs, Git state and output hashes are in INSPECTED_FILES.csv, PROVENANCE.md, GIT_STATUS.json and SHA256SUMS.txt. R23 closure, frozen R24 mathematics and sequential A→B→C→D remain unchanged. All scientific/experimental/generation/optimization execution = NONE.
