# R24 Instance Generation Specification

Specification ID: `R24-INSTANCE-GEN-20260915-v1`

Status: **`R24_INSTANCE_GENERATION_SPEC_FROZEN_WITH_LIMITATIONS`**

Effective date: 2026-09-15 JST

## 1. Authority and scope

This package is the executable design authority for generation of R24 benchmark instances. It freezes selection before any instance, route matrix, capacity condition, optimization result, or scientific result is generated. If a summary conflicts with a contract in this package, the contract governs.

No scientific experiment, instance generation, OD generation, capacity-condition generation, or optimization occurred in this specification-freeze task.

The source population is the immutable `C_ELIGIBLE_MANIFEST.csv` with 39,930 `ELIGIBLE` building-based customers and total demand 81,793 `METHODOLOGICAL_PARCEL_EQUIVALENT`. Its SHA-256 is `245aad97ea49f7676dcebd414b46eb364d64e9d0fbeb4defa0c8e8b90604ca5c`. The depot is `DEP_006`. The routing graph is accepted run_3, network ID `P13-THREE-TIER-RUN-3-GEOMETRY-REACCEPTANCE`, SHA-256 `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`.

## 2. Frozen suite hierarchy

1. **Primary — Repeated Random Suite:** SRSWOR subsets used for primary methodological comparison and instance-to-instance variation.
2. **Secondary — Controlled Structural Suite:** `CLUSTERED`, `DISPERSED`, and `MIXED` deterministic spatial stress tests. They do not claim Ota-wide statistical representativeness.
3. **Reference — Fixed Anchor Suite:** immutable aliases of prespecified primary subsets for regression and implementation, QUBO, solver, and version comparisons.

Every base customer subset is generated once. Its identical customers and OD matrix feed all three capacity conditions; customers are never resampled by capacity regime.

## 3. Frozen numerical design

| Item | Frozen value |
|---|---|
| Quantum-comparable core | `n = {2,3,4}` |
| Classical extension | `n = {5,8,10,15,20}` |
| Random repetitions | `10` independently keyed deterministic SRSWOR realizations per n |
| Structural sizes | `n = {4,10,20}` |
| Structural repetitions | `3` per `(structure,n)` |
| Anchor sizes | `n = {4,10,20}` |
| Anchors | exact aliases of corresponding random `R01` base subsets |
| Capacity | `Q=14` |
| Target regimes | `0.50`, `0.70`, `0.90` |

This defines 80 primary base instances, 27 structural base instances, and 3 anchor aliases. Anchors are not additional independent samples and must not be double-counted. Each base or alias has three capacity-condition records.

## 4. Sampling and selection

Primary selection is equal-probability sampling without replacement:

\[
C_{n,r}\sim\operatorname{SRSWOR}(C_{eligible},n).
\]

There is no demand weighting, PPS, quartile-by-tertile stratification, manual replacement, nesting requirement, or solver-informed choice. The exact seed and hash-ranked realization procedure are frozen in `SEED_POLICY.md` and `RANDOM_SUITE_SPEC.md`.

The no-redraw rule is **sample once, validate, record**. Demand mix, weak or strong capacity effects, easy routes, duplicate proxies, zero arcs, QAOA inconvenience, solver behavior, or an unattractive result can never trigger redraw or substitution.

## 5. Validation and capacity

Every selected set is re-routed on run_3 for all ordered distinct pairs over `{DEP_006} union customers`. Population SCC membership is only a screening result and never supplies instance costs. Base and condition acceptance, hard rejection enums, connection validation, duplicate-proxy reporting, exact packing preflight, and degenerate-regime treatment are governed by `INSTANCE_VALIDATION_CONTRACT.md` and `CAPACITY_CONDITION_CONTRACT.md`.

Duplicate-proxy customers remain eligible because customer identity is building-based. The frozen frame contains 28,274 eligible customers in 10,016 shared-proxy groups. Duplicate proxy membership, groups, zero-distance arcs, and zero-travel-time arcs must be recorded; none is invalid by itself.

## 6. Claim boundary and limitations

The allowed description is: **repeated random subsets of the Ota-grounded eligible synthetic benchmark population**. The suite is not representative of all Ota deliveries, real carrier routes, or operational samples. `n` is computational benchmark size, not statistical sample size or an empirical route stop count. `Q`, `m`, and `rho` are methodological, not observed or physical fleet quantities.

Limitations are the inherited synthetic-demand provenance gap, routing-proxy rather than physical-stop semantics, run_3 model/free-flow costs, non-physical capacity, small computational sizes, and a future R24 QUBO whose encoding/resource count is not yet frozen. These limit claims but do not block deterministic generation.

## 7. Decision and next task

No material specification field remains open. The verdict is:

`R24_INSTANCE_GENERATION_SPEC_FROZEN_WITH_LIMITATIONS`

`NEXT_EXECUTABLE_TASK = generate R24 benchmark instance suite`
