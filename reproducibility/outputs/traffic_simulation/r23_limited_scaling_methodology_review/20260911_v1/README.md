# R23 Limited Scaling Methodology Review

Date: 2026-09-11. Classification: `R23_LIMITED_SCALING_METHODOLOGY_REVIEW_COMPLETED`.

This review is a design artifact, not a scientific execution. No n=5 or larger QAOA, benchmark, rerun, shots, noise, or QPU execution was performed.

The customer-only position encoding has `n²` logical qubits. Complex128 raw statevector memory grows as `16 × 2^(n²)` bytes: n=5 is 25 qubits, 33,554,432 amplitudes, and 0.5 GiB raw; n=6 is 36 qubits and 1 TiB raw. Actual Qiskit/Aer peak memory is higher because raw statevector memory is only a theoretical minimum.

Existing n=4 Formal A/B1/B2 evidence already shows roughly 371–530 s T_total and 253–402 s T_Aer means for p=2/3, with approximately 280–300 nfev. Therefore n=5 is classified `N5_REQUIRES_RESOURCE_PREFLIGHT_BEFORE_AUTHORIZATION`; n>=6 is not recommended with the current exact CPU Aer statevector method.

Validation is tiered: analytical coefficients, structural one-hot checks, targeted exhaustive checks, known valid/invalid states, fixed-seed sampling, and exact route enumeration. Full bitstring exhaustive validation is baseline-only for n<=4. Exact route reference remains n! (120, 720, 5,040, 40,320 for n=5–8), and is kept separate from `2^(n²)` state scaling.

See the JSON files in this directory for the formal policy, readiness gates, metrics, and stop conditions. λ=3.0 remains limited to n={2,3,4}; no n=5 λ was selected.
