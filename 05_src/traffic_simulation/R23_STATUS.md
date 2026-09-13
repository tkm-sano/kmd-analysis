# R23 / Reduced Problem research status（現行、2026-09-14）

| area | status |
|---|---|
| Routing Baseline | COMPLETE |
| Reduced Problem | ACCEPTED_WITH_LIMITATIONS |
| Limited scaling methodology review | COMPLETE; n=5 preflight required, n>=6 current exact CPU Aer statevector not recommended |
| N5 scaling authorization | AUTHORIZED_READY_TO_EXECUTE; rank01 completed under frozen V2 scope |
| N5 resource preflight remediation | PASSED; minimal 25q probe 0.571 GiB |
| N5 scaling execution | COMPLETE; rank01 COMPLETE, rank02 COMPLETE, rank03 COMPLETE |
| N5 Evidence Review | `R23_N5_SCALING_EVIDENCE_ACCEPTED_WITH_LIMITATIONS`; historical observations retained, rank02/03 not reauthorized |
| Runtime optimization audit | `CODE_AUDIT_FAIL`; `CODE_AUDIT_RESULT_NOT_REPRODUCED`; REMEDIATION_INCOMPLETE; I03 repository-wide validation PASS guards remain MAJOR |
| Reduced Problem scaling | Existing limited evidence retained; execution/resource provenance limitations remain |
| Formal A | COMPLETE |
| Experiment B1 | COMPLETE |
| Experiment B2 | COMPLETE |
| Capacity | `NOT_AUTHORIZED_PENDING_R23_REMEDIATION`; R24 BLOCKED pending independent re-audit |
| Time Window | NOT_STARTED |
| Battery/SOC | NOT_STARTED |
| Charging | NOT_STARTED |
| Multiple Vehicles | NOT_STARTED |
| Full EVRP R20 | BLOCKED |
| Full EVRP R21 | NOT_STARTED |

EvidenceはReduced Problem scopeに限る。既存recordではoptimal route recovered=3/3、relative route objective gap=0（3/3）。optimizer reported success=2/3（rank01=false、rank02=true、rank03=true）。rank01は300 evaluation cap reachedであり、route recoveryとoptimizer successを区別する。rank02/03はexecution lineage/resource provenanceの制約付きで保持し、再承認しない。

全rankでP_feasible<1%、P_optimalは約5.45e-5〜6.64e-5。rank01 originalは42.62h、peak RSS 201.58GiB。独立auditはCODE_AUDIT_FAIL、前回結果はCODE_AUDIT_RESULT_NOT_REPRODUCED。runtime benchmarkはPRELIMINARY_ONLYで、正式な33.7倍speedup・327倍memory reductionは支持されない。201.6GiB absolute peakと約0.615GiBのcandidate観測値/増分を直接比較しない。n≥6は現行exact CPU Aerでは非推奨。quantum advantage、一般的robustness、optimizer superiority、scaling lawを主張しない。

修正authorityと残存制約は[remediation artifact](../../reproducibility/outputs/traffic_simulation/r23_n5_runtime_optimization_audit_remediation/20260913_v1/README.md)および[R23 remediation contract](specifications/R23_RUNTIME_REMEDIATION_CONTRACT.md)。修正後の独立再監査は別taskとし、ここでCODE_AUDIT_PASSへ変更しない。R24はその独立再監査とphase closure後にのみ検討する。
