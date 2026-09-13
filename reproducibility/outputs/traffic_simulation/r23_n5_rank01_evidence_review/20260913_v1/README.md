# R23 n=5 rank01 formal Evidence Review

Date: 2026-09-13. Scope: completed `routing_v18_n5_rank01` only. rank02 and rank03 were not started.

The review confirms `EXACT_REFERENCE_INTEGRITY_PASS`: all 120 customer permutations were enumerated, the unique exact route and objective were recovered by the decoded best feasible route, and both gaps are zero. The probability denominator is the raw full-state mass without renormalization; `P_feasible=0.006366971625605308` and `P_optimal=0.00005447231886991554`.

COBYLA reached `nfev=300` and the objective-evaluation cap with `success=false`. The result must be described as the exact route being present in the state decoded at the evaluation cap, not as optimizer convergence.

The measured runtime is `T_total=153434.09043177636 s` (about 42 h 37 min), `T_Aer=306.781193879433 s`, and `T_transpile=16.943095699883997 s`. Aer is about 0.20% of the wall-clock envelope; phase-level values for the remaining time are not present in the compact artifact. Code inspection identifies candidate paths but does not prove a single dominant bottleneck. Peak RSS was 201.583 GiB, about 353x the 0.571 GiB minimal 25-qubit probe.

Classification: `R23_N5_REMAINING_RUNS_PAUSE_FOR_RUNTIME_DIAGNOSIS`. The remaining two runs have scientific value for instance robustness, but an unchanged execution would be an estimated additional roughly 85 hours if they match rank01. No scientific parameters were changed and no code was modified in this review.
