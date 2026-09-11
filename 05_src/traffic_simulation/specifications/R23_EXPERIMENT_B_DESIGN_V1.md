# R23 Experiment B Design V1 — Initialization / Optimizer Robustness

## Status

This is a frozen research design, not an execution authorization.

- Design ID: `R23_EXPERIMENT_B_DESIGN_V1`
- Classification: `EXPERIMENT_B_DESIGN_IMPLEMENTATION_FIX_REQUIRED`
- Execution: not performed
- Preceding evidence: `FORMAL_EXPERIMENT_A_EVIDENCE_ACCEPTED_WITH_LIMITATIONS`
- Next scaling status after successful review: `R23_SCALING_EXTENSION_READY`

## Research question

How robust are the Formal Experiment A QAOA outcomes to parameter initialization and classical optimizer choice under fixed problem instances and QAOA depth?

Experiment B isolates robustness. It is not a new scaling experiment and does not include `n>=5`.

## Why B precedes scaling

Corrected Formal A shows a strong descriptive decline with problem size, non-monotonic depth effects at `n=3/4`, marked instance heterogeneity at `n=3,p=3` and `n=4,p=2/3`, and `TERMINATION_UNKNOWN` in all 45 conditions. The exact best decoded route is not enough to establish optimizer robustness or reliable finite-shot sampling. Initialization and optimizer dependence therefore must be characterized before an `n>=5` study.

## Adopted staged design

### B1 — initialization robustness

The smallest informative design focuses on the pre-scaling uncertainty regime:

- `n={4}`
- authoritative instances `routing_v18_n4_rank01`, `rank03`, `rank05`
- `p={2,3}`
- optimizer `COBYLA`
- six initializations: `fixed_0.1` plus deterministic random seeds `{11,23,37,53,71}`
- repetition `1` per unique initialization condition
- 36 unique runs

The rank rule is fixed before execution and is not selected from desirable QAOA outcomes. It is a deterministic robustness diagnostic sample, not a representative population sample.

### B2 — optimizer robustness

B2 is conditional on B1 review and implementation validation:

- same three `n=4` instances and `p={2,3}`
- same `fixed_0.1` initialization
- comparator: deterministic derivative-free `NELDER_MEAD`
- six incremental comparator runs
- COBYLA controls are reused from B1; they are not re-executed
- 6 incremental executions, 12 total comparison observations including B1 controls

Nelder-Mead is preferred over SPSA for this comparison because the expectation is exact and deterministic and the parameter dimension is small. SPSA is available in the authority environment but is not selected as the primary comparator.

## Initialization convention

The current repository parameter order is `[gamma_1..gamma_p, beta_1..beta_p]`. The current implementation accepts unconstrained angles and maps them directly into RZ/RX rotations. B therefore freezes the following diagnostic domain:

- gamma: independent `Uniform[-pi, pi)`
- beta: independent `Uniform[-pi/2, pi/2)`
- RNG: `numpy.random.Generator(numpy.random.PCG64(seed))`
- seeds: `11, 23, 37, 53, 71`

These are bounded symmetric design conventions, not physical parameter bounds.

## Fair optimizer comparison

The common research fairness constraint is `objective_evaluation_cap=900`. `maxiter=300` is retained as an optimizer-specific safety/configuration value and is not treated as equal computational work across optimizer interfaces. Each result must preserve `nfev`, `nit`, native success, native message, termination status, budget flags, and timing.

The amended policy is `NO_RESEARCH_WALL_TIME_CAP`. A separate non-binding infrastructure safety guard may exist, but it must be recorded as a safety event and never interpreted as optimizer failure.

## Metrics and interpretation

Primary outcomes remain the Formal A metrics:

- `P_feasible`
- `P_optimal`
- relative optimality gap

Secondary outcomes include objective evaluations, native optimizer metadata, final expectation, route gap, and CPU simulation timing. B1 additionally reports min/median/max and descriptive dispersion over the six initialization conditions for each fixed instance × `n` × `p`. These are diagnostic distributions, not population uncertainty estimates.

`gap=0` remains a route-quality result only. It does not establish high `P_optimal`, optimizer convergence, finite-shot success, or quantum advantage.

## Termination metadata gate

The current R23 implementation imports and invokes COBYLA directly and the schema accepts only COBYLA. Before B2, a new adapter/schema path is required for Nelder-Mead. The adapter must be smoke-validated and must capture native result metadata without changing optimizer behavior. Historical Formal A artifacts remain immutable.

If metadata remains unavailable, the result must preserve `None`/empty values and report convergence as unresolved; success must never be inferred from `nfev`.

## Candidate design comparison

| Candidate | Runs | Information | Burden assessment |
|---|---:|---|---|
| n=3/4, 3 ranks/n, p=2/3, 6 initializations, COBYLA | 72 | Adds direct n=3 robustness comparison | Approx. 4.7 h serial; n=4 dominates |
| n=4, 3 ranks, p=2/3, 6 initializations, COBYLA | 36 | Directly tests the pre-scaling uncertainty regime | Approx. 4.6 h serial; halves run count but saves little wall time because n=4 dominates |

The 36-run n=4-focused design is adopted because it is the smallest design that directly addresses the gating uncertainty. It does not claim that n=3 behavior is robust; that limitation is explicit.

## Scaling gate

After B, scaling may be designed only if initialization robustness, optimizer dependence, termination metadata, and implementation integrity are understood. This design does not authorize `n=5`. The scaling track must separately redesign CPU statevector/resource methodology and R22 validation.

Experiment C remains separate and is required before scenario modelling.

