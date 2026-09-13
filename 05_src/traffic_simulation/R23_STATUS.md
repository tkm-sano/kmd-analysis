# R23 / Reduced Problem research status（現行、2026-09-13）

| area | status |
|---|---|
| Routing Baseline | COMPLETE |
| Reduced Problem | ACCEPTED_WITH_LIMITATIONS |
| Limited scaling methodology review | COMPLETE; n=5 preflight required, n>=6 current exact CPU Aer statevector not recommended |
| N5 scaling authorization | AUTHORIZED_READY_TO_EXECUTE; rank01 completed under frozen V2 scope |
| N5 resource preflight remediation | PASSED; minimal 25q probe 0.571 GiB |
| N5 scaling execution | PARTIAL / UNDER_REVIEW; rank01 COMPLETE, rank02 NOT_RUN, rank03 NOT_RUN |
| N5 remaining-run decision | R23_N5_RUNTIME_OPTIMIZATION_VALIDATED_READY_FOR_REMAINING_RUNS; rank02 AUTHORIZED_NOT_RUN, rank03 AUTHORIZED_NOT_RUN |
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

EvidenceはReduced Problem scopeに限る。rank01はn=5、25 logical qubits、p=1、lambda=4.0、COBYLA、fixed_0.1、CPU Aer statevectorで完了し、exact optimum routeを回収した。元実装とvalidated candidateのn=2/3/4 exhaustiveおよびn=5 independent numeric-array cross-checkは1e-12でPASS。candidateは120 feasible indicesのみを参照し、full Python probability dictionaryを生成しない。rank02/rank03の正式runは未実行。判定は`R23_N5_RUNTIME_OPTIMIZATION_VALIDATED_READY_FOR_REMAINING_RUNS`、次taskは`R23_N5_SCALING_REMAINING_EXECUTION_OPTIMIZED`である。CPU AerはQPU runtimeではなく、exact best routeの一致はprobability=1、sampling success、convergence、quantum advantageを意味しない。
