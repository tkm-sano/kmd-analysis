# R23 / Reduced Problem research status（現行、2026-09-14）

| area | status |
|---|---|
| Routing Baseline | COMPLETE |
| Reduced Problem | ACCEPTED_WITH_LIMITATIONS |
| Limited scaling methodology review | COMPLETE; n=5 preflight required, n>=6 current exact CPU Aer statevector not recommended |
| N5 scaling authorization | AUTHORIZED_READY_TO_EXECUTE; rank01 completed under frozen V2 scope |
| N5 resource preflight remediation | PASSED; minimal 25q probe 0.571 GiB |
| N5 scaling execution | COMPLETE; rank01 COMPLETE, rank02 COMPLETE, rank03 COMPLETE |
| N5 Evidence Review | COMPLETE; `R23_N5_SCALING_EVIDENCE_ACCEPTED_WITH_LIMITATIONS` |
| Reduced Problem scaling | `R23_REDUCED_PROBLEM_SCALING_COMPLETED_WITH_LIMITATIONS` |
| Formal A | COMPLETE |
| Experiment B1 | COMPLETE |
| Experiment B2 | COMPLETE |
| Capacity | NEXT: `R24_CAPACITY_EXTENSION_DESIGN` |
| Time Window | NOT_STARTED |
| Battery/SOC | NOT_STARTED |
| Charging | NOT_STARTED |
| Multiple Vehicles | NOT_STARTED |
| Full EVRP R20 | BLOCKED |
| Full EVRP R21 | NOT_STARTED |

EvidenceはReduced Problem scopeに限る。rank01はoriginal implementation、rank02/rank03はSHA一致のvalidated V4 implementationで、3件ともexact optimum route回収・probability integrity・resource gateにPASSした。COBYLA convergenceも3/3で確認したが、これはsampling successやquantum advantageを意味しない。n=5 Evidence Reviewは`reproducibility/outputs/traffic_simulation/r23_n5_scaling_evidence_review/20260913_v1/`、n≥6はraw exact statevector scalingのため現methodologyで実行しない。次taskは`R24_CAPACITY_EXTENSION_DESIGN`である。
