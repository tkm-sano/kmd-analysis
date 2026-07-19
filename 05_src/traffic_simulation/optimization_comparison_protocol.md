# Classical and QAOA Comparison Protocol

## Common Instance

Both solvers receive the same frozen customers, vehicles, demands, distance/travel-time/energy matrices, constraints, feasibility checker, objective and final evaluator. Vehicle class is fixed by vehicle type: a small delivery van uses `delivery`, while a heavy freight vehicle uses `truck`.

The formal road review covers the candidate subgraph selectable by any compared algorithm, not only the route ultimately selected. It includes all reachable edges between depots, customers and charging facilities plus the preregistered alternative-route buffer.

## Seed Roles

Shared instance, demand and traffic seeds create common experimental conditions. Classical solver, QAOA parameter initialization and QAOA sampling use separate preregistered seed sets. Equal integers across solver-specific seeds do not imply equivalent randomness.

## Fairness and Outputs

Separate equal-budget comparisons from best-reference comparisons. Record what time is included: preprocessing, QUBO generation, optimization, circuit evaluation, shots, decoding, repair and final evaluation. Apply the same feasibility and evaluation functions to raw and repaired outputs, and retain both.

First compare objective and feasibility on the frozen static instance. Then map both visit orders with the same road-routing rule and evaluate them under the same SUMO traffic seeds. Report static optimization quality separately from realized traffic performance. Qiskit Aer results do not establish quantum advantage.
