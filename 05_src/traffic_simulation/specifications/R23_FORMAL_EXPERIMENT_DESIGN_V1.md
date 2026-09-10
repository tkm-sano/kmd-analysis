# R23 reduced formal experiment design V1

This is a research-design decision record. It freezes the initial formal
Experiment A conditions but does not execute the experiment and does not claim
`R23 PASS`.

## Frozen question and scope

The question is: how do problem scale and QAOA depth affect feasibility,
optimal-solution probability, decoded route quality, and classical
software-simulation burden for the validated reduced Single-Vehicle Route
Ordering Problem under controlled exact-expectation CPU simulation?

The scope remains fixed-depot, customer-only `n x n` position encoding with
`N_logical=n^2`, directed static travel time, complete reachability, and the
R20/R21/R22 validated reduced formulation. Capacity, time windows, battery,
charging, fleet, and multiple vehicles remain outside R23.

## Experiment A decision

The primary design is `n x instance x p`:

- `n={2,3,4}`;
- five Routing Baseline-derived, complete-reachability instances per n;
- `p={1,2,3}`;
- COBYLA, `maxiter=300`, objective cap `900`, expectation cap `901`;
- all parameters initialized to `0.1`, one deterministic repetition;
- exact CPU Aer statevector expectation, no shots;
- optimization level 1 and transpiler seed 17, with backend defaults recorded.

The selection seed is 2301. Candidate subsets are deterministically ranked by
SHA-256 and selected before any QAOA result is observed. The selected instance
manifest, matrix hashes, and exact permutation-enumeration references must be
frozen before execution. The resulting matrix is 15 instances and 45 runs.

## Outcomes

Primary outcomes are raw full-state `P_feasible`, raw full-state `P_optimal`,
and relative optimality gap. Absolute gap, best decoded route objective,
invalid mass, termination/evaluation counts, and cumulative software timing are
secondary. Final Hamiltonian expectation, energy variance, parameters, trace,
and circuit metadata are diagnostic. Expectation energy is never used as route
travel-time objective.

Runtime is a secondary software-simulation burden outcome. It is not QPU time,
future hardware performance, or quantum-advantage evidence. Inclusive and
nested timing fields follow the implementation contract and are never summed
twice.

## Deferred designs and gates

Experiment B (initialization/optimizer robustness) is a separate deferred
sensitivity experiment. Experiment C (finite-shot sensitivity) is deferred and
must be completed before future quantum-scenario modelling that relies on
sampling behavior. Neither is part of Experiment A.

Per-run resource, exact-reference, provenance, hash, numerical, and artifact
stop conditions are defined in the JSON configuration. A budget hit is a valid
completed run with a diagnostic flag when the result and provenance are sound;
it is not silently interpreted as convergence.

## Status boundary

The design is frozen as `R23_FORMAL_EXPERIMENT_DESIGN_V1` and ready for a
separate execution authorization. Formal runs, p/n expansion, shots,
scaling regression, future-QPU modelling, and Full-EVRP advancement are not
authorized by this record.
