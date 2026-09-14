# R23_N5_RUNTIME_OPTIMIZATION_REVIEW

Review date: 2026-09-13. Starting commit: `5bf803177b0c3640f0eeb6d12054e734bfc1c361`. rank02/rank03 were not started.

The original path was traced to `qaoa.py`: every objective evaluation rebuilds the circuit, creates an AerSimulator, transpiles, runs Aer, materializes a Statevector, rebuilds the cost operator, computes expectation, and converts all 33,554,432 basis states to a Python probability dictionary. `T_Aer` measures only `simulator.run(...).result()`. `T_transpile` measures each transpile call. Statevector conversion, expectation, probability dictionary creation, and final metrics are outside `T_Aer`.

The original direct micro-profile was intentionally stopped after more than 15 minutes and approximately 180 GiB RSS; it was not allowed to become a second long scientific run. The isolated equivalent-index prototype completed three direct evaluations in 14.28–16.35 seconds, with identical parameter and backend scope. It aggregates the analytically known 120 feasible route indices and derives invalid mass as total minus feasible mass. Small-n exhaustive checks passed. This is mathematically equivalent to the existing denominator and feasibility definitions.

However, the original full probability-dictionary micro-profile did not complete, so a completed n=5 original-vs-optimized numerical crosscheck was not obtained. The optimized candidate is therefore not authorized for rank02/rank03. Decision: `R23_N5_RUNTIME_OPTIMIZATION_EQUIVALENCE_FAILED` in the strict adoption-gate sense. This is not a scientific-result integrity failure; it is an incomplete equivalence gate.

The next task is remediation of the equivalence test with a bounded controlled harness, without changing QUBO, Hamiltonian, lambda, p, optimizer, initialization, backend, denominator, tolerance, or decoding rules.
