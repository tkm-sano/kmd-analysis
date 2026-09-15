# Instance Validation Contract

## No-redraw invariant

`SAMPLE_ONCE_VALIDATE_RECORD = REQUIRED`. Every planned ID produces one permanent record. A rejection never changes seed, customers, repetition count, or suite membership and never causes a replacement draw.

## Selected-instance routing validation

For `V={DEP_006} union C`, compute on accepted run_3 every ordered pair `(i,j)` with `i != j`, including depot-to-customer, customer-to-depot, and all customer-to-customer directions. For every pair record reachability, fastest-model-time path travel time in seconds, distance in metres along that same path, origin/destination offsets, and an edge-sequence hash. Validate that every consecutive edge transition is an allowed SUMO `delivery` lane connection and that endpoint partial-edge accounting follows the Routing Baseline.

There must be exactly `(n+1)n` distinct ordered-pair records. Distances and times are recomputed on run_3; run_2 costs and population SCC membership cannot substitute. Asymmetry is preserved. A reachable zero cost is allowed only when exact endpoint/proxy semantics establish it and must be flagged.

## Duplicate proxy rule

Shared proxies do not merge or exclude building-based customers. Record: selected customers in shared proxies, number and membership of selected duplicate groups, ordered zero-distance arcs, and ordered zero-travel-time arcs. Duplicate membership or a validated zero arc is not invalidity.

## Frozen base hard-rejection reasons

`INSTANCE_HARD_REJECTION_REASON` is one or more of:

- `SOURCE_CUSTOMER_NOT_IN_FROZEN_ELIGIBLE_MANIFEST`
- `SOURCE_MANIFEST_HASH_MISMATCH`
- `MANIFEST_OR_OUTPUT_HASH_INCONSISTENCY`
- `CUSTOMER_ID_NOT_UNIQUE`
- `N_OR_SELECTION_RULE_MISMATCH`
- `Q_I_MISSING_CORRUPT_NONINTEGER_OR_NONPOSITIVE`
- `Q_I_EXCEEDS_Q`
- `CAPACITY_UNIT_MISMATCH`
- `ROUTING_PROXY_MISSING_OR_INVALID`
- `STRUCTURAL_COORDINATE_INVALID`
- `RUN3_GRAPH_ID_OR_HASH_MISMATCH`
- `RUN3_OD_COMPUTATION_FAILURE`
- `ORDERED_PAIR_MISSING_OR_DUPLICATED`
- `ORDERED_PAIR_UNREACHABLE`
- `OD_VALUE_MISSING_NONFINITE_OR_NEGATIVE`
- `SUMO_CONNECTION_OR_TURN_INVALID`
- `EDGE_SEQUENCE_OR_ENDPOINT_SEMANTICS_INVALID`

No other base rejection reason is allowed without a new protocol version. In particular, demand pattern, capacity strength, route geometry/difficulty, duplicates, validated zero arcs, solver/QAOA behavior, or scientific result are forbidden reasons.

## Acceptance

A base is `BASE_ACCEPTED` only if source/selection/provenance assertions pass, all q values are valid and at most Q, all required routing pairs and connection sequences pass, and artifact hashes are internally consistent. Otherwise it is `BASE_REJECTED`, with all reasons and partial diagnostics preserved. A base rejection blocks all its capacity conditions from routing optimization but never triggers redraw.

Packing feasibility is a **capacity-condition** acceptance rule, not a base-subset rejection rule. It is governed separately so an infeasible regime cannot bias customer sampling.
