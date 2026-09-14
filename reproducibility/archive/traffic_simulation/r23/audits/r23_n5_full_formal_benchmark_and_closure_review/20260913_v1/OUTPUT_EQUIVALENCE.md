# Output equivalence gate

The fresh baseline and V4 processes used the same rank01 input, p=1, lambda=4, parameters `[0.1,0.1]`, seed 17 and CPU Aer statevector. Objective expectation and decoded objective match exactly. P_feasible differs by `6e-20`, probability total by `8e-16`, and invalid mass by `7e-16`, all within 1e-12. P_optimal and decoded route match. Scientific equivalence gate: `PASSED`; performance comparison is valid for this fixed workload.

