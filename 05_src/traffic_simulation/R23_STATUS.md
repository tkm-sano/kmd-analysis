# R23 / Reduced Problem research status（現行、2026-09-13）

| area | status |
|---|---|
| Routing Baseline | COMPLETE |
| Reduced Problem | ACCEPTED_WITH_LIMITATIONS |
| Limited scaling methodology review | COMPLETE; n=5 preflight required, n>=6 current exact CPU Aer statevector not recommended |
| N5 scaling authorization | AUTHORIZED_READY_TO_EXECUTE; rank01 completed under frozen V2 scope |
| N5 resource preflight remediation | PASSED; minimal 25q probe 0.571 GiB |
| N5 scaling execution | PARTIAL / UNDER_REVIEW; rank01 COMPLETE, rank02 NOT_RUN, rank03 NOT_RUN |
| N5 remaining-run decision | R23_N5_RUNTIME_OPTIMIZATION_EQUIVALENCE_FAILED; rank02/rank03 remain NOT_RUN |
| Formal A | COMPLETE |
| Experiment B1 | COMPLETE |
| Experiment B2 | COMPLETE |
| Capacity | NOT_STARTED |
| Time Window | NOT_STARTED |
| Battery/SOC | NOT_STARTED |
| Charging | NOT_STARTED |
| Multiple Vehicles | NOT_STARTED |
| Full EVRP R20 | BLOCKED |
| Full EVRP R21 | NOT_STARTED |

EvidenceはReduced Problem scopeに限る。rank01はn=5、25 logical qubits、p=1、lambda=4.0、COBYLA、fixed_0.1、CPU Aer statevectorで完了し、exact optimum routeを回収した。P_feasible=0.006366971625605308、P_optimal=0.00005447231886991554、T_total=153434.09043177636 s、T_Aer=306.781193879433 s、peak RSS=201.583 GiBである。COBYLAは300評価上限に到達し、optimizer convergence successではない。runtime prototypeは数学的に有望だが、元実装との完了済みn=5 cross-checkがないため、rank02/rank03には未採用。判定は`R23_N5_RUNTIME_OPTIMIZATION_EQUIVALENCE_FAILED`であり、これはscientific result failureではなくadoption gate未完了を意味する。CPU AerはQPU runtimeではなく、exact best routeの一致はprobability=1、sampling success、convergence、quantum advantageを意味しない。
