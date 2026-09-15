# SCC reachability policy

## Population stage

Build the directed graph whose vertices are run_3 non-internal edges permitting SUMO `delivery`. Add `e -> f` only when the network contains a connection from a delivery-permitted lane of `e` to a delivery-permitted lane of `f`. Compute SCCs once.

A candidate is population-eligible only when its transferred edge-offset proxy is valid and:

\[
edge(i)\in SCC(edge(DEP\_006)).
\]

For any two eligible vertices `u,v` in one SCC, the SCC definition supplies paths `u -> v` and `v -> u`. Therefore the criterion establishes directed pairwise reachability at the graph-topology level as well as depot round-trip reachability.

The audit also reproduces the current R13 node-edge reachability rule. Its outbound/inbound result matches the stricter connection-aware result for all 39,956 candidates.

## Instance stage

For `{DEP_006} union C_instance` only:

1. construct every ordered pair `i != j`;
2. compute travel-time-minimizing paths on run_3 with edge offsets;
3. store distance, travel time, reachability, path and hashes;
4. validate every consecutive edge transition/turn and `delivery` permission;
5. reject null/error/unreachable pairs;
6. inspect duplicate-proxy zero-distance/zero-time arcs explicitly.

SCC membership proves existence, not numerical cost correctness. It does not replace instance-level OD computation.

## Resource boundary

No 39,956-customer all-pairs OD was executed. That would require 1,596,441,980 ordered customer-to-customer pairs excluding self-pairs, before depot pairs. Population SCC plus small selected-instance OD is the frozen two-stage policy.
