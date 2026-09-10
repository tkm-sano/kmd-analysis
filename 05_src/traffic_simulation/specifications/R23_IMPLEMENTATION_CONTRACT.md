# R23 reduced implementation contract (forward-looking)

This document records implementation and provenance requirements for a future
formal R23 artifact. It does not adopt formal research factors, change the
frozen pilot, or authorize a new run. The artifact at
`reproducibility/outputs/traffic_simulation/r23_reduced_pilot/20260911_frozen_v1/`
is historical evidence and remains immutable.

## Optimizer termination and budget

Every result records `objective_evaluation_count`, `configured_maxiter`,
`configured_objective_cap`, `budget_hit`, `termination_status`,
`termination_message`, `optimizer_success`, `nit`, and `nfev` when supplied by
the optimizer API. `budget_hit` is a factual boundary flag. An API result with
`nfev` at a boundary but no termination reason is classified as
`BUDGET_BOUNDARY_REACHED_TERMINATION_UNKNOWN`; `maxiter` boundary is recognized
only from optimizer `nit`, while the objective cap is recognized from `nfev`.
Evaluation count alone is not used to infer non-convergence. The supported statuses are `CONVERGED`,
`BUDGET_BOUNDARY_REACHED_TERMINATION_UNKNOWN`, `OPTIMIZER_FAILURE`, and
`TERMINATION_UNKNOWN`.

## Cumulative timing and trace

For each objective evaluation, the trace stores the evaluation index,
parameters, expectation, elapsed callback time, circuit construction time,
transpilation time, Aer time, expectation-processing time, and cumulative
elapsed/component time. The result-level contract is:

* `T_total`: wall-clock envelope from runner start through final result.
* `T_optimizer_total`: inclusive wall time of `optimizer.minimize`, including
  all objective callbacks and optimizer overhead.
* `T_objective_eval_total`: sum of objective callback wall times.
* `T_circuit_build_total`, `T_transpile_total`, `T_Aer_total`, and
  `T_expectation_total`: exclusive measured subcomponents summed over objective
  evaluations only.
* `T_decode_total`: post-final-evaluation metric/decode processing.
* `T_final_evaluation`: separate post-optimizer evaluation timing object.

Nested components must not be added to `T_optimizer_total` or `T_total`.
`T_final_evaluation` must not be added to optimizer totals. This is an
inclusion contract, not a claim that all wall time is decomposed.

## Provenance lineage

The formal manifest schema requires standalone R20, R21, R22, and R23 lineage.
R20 records specification path, SHA-256, and formulation identifier. R21 and
R22 record authoritative result/manifest paths and hashes, coefficient/hash
references, and PASS status. R23 records configuration identity and SHA-256
plus hashes for `qaoa.py`, `hamiltonian.py`, `metrics.py`, `schema.py`,
`artifact.py`, and the execution entry point when supplied. Per-run artifacts
must carry the same lineage.

## Memory and transpiler contracts

`memory_preflight` estimates complex128 statevector storage and a conservative
four-statevector peak before Aer execution. A failed estimate stops execution.
This is a software execution-safety guard only; it is not a QPU limit or a
formal problem-size claim.

The current implementation records optimization level and `seed_transpiler`,
and explicitly records backend-default basis/backend-dependent settings. The
historical pilot used the implementation default and must be labelled
`PILOT_USED_IMPLEMENTATION_DEFAULT`; no formal transpiler value is adopted by
this patch.

## Probability contract

Probability range, sum, and `isclose` tolerances are each `1e-12`. Probabilities
use raw full-state probability mass as denominator. Invalid states are not
repaired and are excluded only from decoded feasible-route analysis; their raw
mass is retained as `invalid_probability_mass`. No implicit renormalization is
permitted.

## Test and provenance strategy

The recommended validation path is a test-capable environment or CI job tied
to the exact source hashes used for the formal artifact. Cloning the frozen
runtime and adding pytest is a possible test-only path only with an explicit
research-governance decision. Installing pytest into the frozen runtime is not
permitted. The current frozen runtime has no pytest, so this patch adds test
requirements but does not alter that environment.

## Status boundary

Formal problem-size ladder, instance count, p range, initialization and
repetition policy, optimizer comparison, budget values, shots policy, primary
metrics, and runtime inclusion remain `USER_RESEARCH_DECISION`. This contract
does not change R23 status (`PILOT_COMPLETED_PENDING_REVIEW`) or Full-EVRP
status.
