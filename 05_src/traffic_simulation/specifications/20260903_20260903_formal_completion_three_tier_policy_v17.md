# Formal completion three-tier policy v17

Document ID: `SPEC-P13-FORMAL-COMPLETION-THREE-TIER-V17`
Role: `CURRENT_NORMATIVE`
Lifecycle: `CURRENT`
Created: `2026-09-03`
Last Updated: `2026-09-03`
Current Authority: `DEC-P13-FORMAL-COMPLETION-THREE-TIER-001`

Decision: `DEC-P13-FORMAL-COMPLETION-THREE-TIER-001`  
Registry: `reproducibility/config/traffic_simulation/formal_completion_three_tier_registry_v17.yml`

The prior hierarchical-hybrid Decision remains preserved as historical policy and is superseded by this Decision. Strict v17 baselines, blocker inventories, model-selection benchmarks, and missing-domain artifacts remain read-only evidence.

## Semantics

Structural is source truth: raw source representation, topology, lineage, and normalized source state. Formal is the complete model-ready network used by research and simulation. Formal values need not be source observations, but every value must retain its resolution tier, method, confidence, assumptions, original missing/blocker state, and provenance.

The only resolution tiers are `DIRECT`, `INFERRED`, and `FALLBACK`. `DIRECT` is source evidence or a unique adopted rule. `INFERRED` is a reproducible completion mechanism (external data, local propagation, empirical grouping, or statistical/ML). `FALLBACK` is a deterministic default or conservative rule. INFERRED and FALLBACK MUST NOT be represented as OBSERVED or DIRECT.

Confidence is `HIGH`, `MEDIUM`, `LOW`, or `FALLBACK`. DIRECT defaults HIGH. INFERRED confidence combines model probability, donor agreement, benchmark performance and feature applicability; absent missing-domain labels downgrade confidence but do not stop completion. FALLBACK is always FALLBACK.

## Resolution

Every governed lane, speed, permission/access, relation and conditional record follows `DIRECT → INFERRED → FALLBACK`. A failed inference must be recorded with its abstention reason before fallback is selected. A blocker is only a technical failure after all three tiers cannot produce an executable final value.

For lanes, external evidence is preferred when exact linkage is available; otherwise local propagation is selected where continuity, distance and transition guards hold, then empirical grouping or the deterministic ML mechanism, then a road-type/SUMO/MATSim-style/conservative fallback. Existing benchmark coverage, bias, MAE, determinism, available features, confidence and cost are recorded as selection metadata; explicit-domain performance is not presented as missing-domain evidence.

For speed, the materialized network attribute is `operational_speed_kph`. Legal/posted `maxspeed` remains separate and cannot be overwritten by an operational prediction. External, empirical or model mechanisms precede a deterministic road-type fallback.

For permission/access, explicit vehicle-specific evidence and deterministic OSM semantics take precedence. If unavailable, a deterministic policy fallback must resolve the governed delivery vehicle to allow or deny. ML or empirical prediction may identify review candidates but may not grant legal access.

Unsupported relations or conditional syntax use configured-time evaluation where available, otherwise a deterministic restriction fallback or an explicit ignore-with-provenance rule. Source syntax and the original blocker remain attached.

## Record contract

Each Formal record MUST include: `final_value`, `resolution_tier`, `method_id`, `method_version`, `confidence`, `source_evidence`, `source_identity`, `assumption_id`, `provenance`, and `original_missing_or_blocker_state`. Provenance includes source snapshot hash, source Way/record identity, Decision ID, method/version, feature/input hash, regeneration command, blocker ID and stop code. No silent fallback is allowed.

## Quality and acceptance

Primary quality accounting is tier percentage, confidence distribution, method distribution, attribute distribution, and unresolved technical failures—not historical blocker volume. `FORMAL_NETWORK_ACCEPTED=true` requires all governed attributes to have final values, complete provenance, SUMO build and validity checks, connectivity, delivery routeability, and Request/Stop mapping acceptance.

The new run is isolated from all prior runs and does not mutate any strict artifact or registry.
