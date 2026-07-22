# Research Simulation Requirements

## Authority and Scope

This specification defines when outputs may be reported as formal research results. `sumo_network.yml` is authoritative for machine-readable state and fixed values. The specifications in this directory are authoritative for component contracts. A conflict blocks formal execution.

Normative terms `MUST`, `MUST NOT`, `SHOULD` and `MAY` are interpreted as requirement keywords. A pending empirical threshold is an explicit blocker until preregistered, not an unspecified value.

## Research Objective

The study compares an unoptimized baseline, a classical optimizer and Qiskit Aer QAOA on the same frozen synthetic EV delivery instances. It reports delivery-capable population equivalents within Ota Ward and separates static optimization quality from realized SUMO traffic performance. Aer simulation does not demonstrate quantum advantage or performance on quantum hardware.

## Normative Requirements

| ID | Requirement | Verification |
|---|---|---|
| SIM-REQ-001 | All compared methods MUST receive the same customers, vehicles, demands, traffic scenario, distance/travel-time/energy matrices, objective, constraints and feasibility evaluator. | SIM-TST-001 |
| SIM-REQ-002 | Shared environment seeds and algorithm-specific seeds MUST follow `optimization_comparison_protocol.md`; equal integers across unlike roles MUST NOT be treated as equivalent randomness. | SIM-TST-002 |
| SIM-REQ-003 | Equal-budget and best-reference comparisons MUST be reported separately, with included preprocessing, QUBO, optimization, sampling, decoding and repair time declared. | SIM-TST-003 |
| SIM-REQ-004 | Raw and repaired solutions MUST both be retained and evaluated by the same final evaluator. | SIM-TST-004 |
| SIM-REQ-005 | A road network MUST satisfy `downstream_experiment_ready` before it supplies formal cost matrices or realized-traffic results. | SIM-TST-005 |
| SIM-REQ-006 | A network containing `structural_placeholder`, an unreviewed TLS mapping or an unclassified warning MUST NOT support formal results. | SIM-TST-006 |
| SIM-REQ-007 | Static objective quality, feasibility, logical qubits, binary/auxiliary variables, QAOA depth, shots, circuit metrics and realized traffic outcomes MUST be reported as distinct measures. | SIM-TST-007 |
| SIM-REQ-008 | Delivery-capable population MUST be described as a model-based population equivalent, not observed recipients or demonstrated people served. | SIM-TST-008 |

## Formal Outcome Set

Formal reporting includes `P_baseline`, `P_classical`, `P_qaoa`, their preregistered differences, objective value, raw/repaired feasibility, distance, energy, realized travel time, computation-time components and QAOA resource measures. Metric definitions, aggregation periods and acceptance thresholds MUST be registered before viewing formal outcomes.

## Out of Scope

- Reproducing all traffic in Tokyo.
- Claiming complete real-world delivery-system fidelity.
- Real-time orders, incidents or dynamic regulation unless a separately versioned online model is introduced.
- Quantum hardware, quantum annealing or quantum advantage claims.
- Direct comparison of a full-size classical problem with a differently reduced QAOA problem.

## Formal Use Decision

Formal use is allowed only when every upstream readiness gate is satisfied, all referenced artifacts share the same `config_id`, all required schemas validate and the post-build audit reports `formal_network_accepted=true`. Missing preregistration values remain explicit blockers rather than guessed defaults.
