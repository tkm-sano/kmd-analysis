# R23 / Reduced Problem research status（現行）

| area | status |
|---|---|
| Routing Baseline | COMPLETE |
| Reduced Problem | ACCEPTED_WITH_LIMITATIONS |
| Limited scaling methodology review | COMPLETE; n=5 preflight required, n>=6 current exact CPU Aer statevector not recommended |
| N5 scaling authorization | NOT_AUTHORIZED_RESOURCE_LIMIT; frozen exact Aer runtime unavailable in current environment |
| N5 resource preflight remediation | PASSED; frozen Aer CPU statevector probe feasible; scientific execution not performed |
| N5 scaling execution authorization | AUTHORIZED_READY_TO_EXECUTE; execution deferred to next task |
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

EvidenceはReduced Problem scopeに限る。CPU AerはQPU runtimeではなく、exact best routeの一致はprobability=1、sampling success、convergence、quantum advantageを意味しない。n=5のresource preflightはPASSし、実行authorization V2を発行したが、科学実行は未実施である。次は`R23_N5_SCALING_EXECUTION`とする。
