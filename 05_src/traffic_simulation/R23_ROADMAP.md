# R23 roadmap（現行）

現在: scientific evidence `R23_N5_SCALING_EVIDENCE_ACCEPTED_WITH_LIMITATIONS`、audit `CODE_AUDIT_FAIL_PENDING_POST_REMEDIATION_REAUDIT`、remediation `COMPLETED_PENDING_INDEPENDENT_REAUDIT`、I03 `RESOLVED`。B2 SHA不整合6件は独立した未解決事項で、scientific integrity 6/6 VERIFIED / artifact integrity FAILED。

1. Routing / Reduced Problem / Formal A / B1 / B2: evidenceを保存、authorityの役割別に保持。
2. n=5: 3 runsを制約付きで保持。optimal route recovery = 3/3、optimizer reported success = 2/3。rank02/03は未再承認。
3. Repository rebaseline: [current authority map](../../reproducibility/outputs/traffic_simulation/r23_repository_rebaseline/20260913_v2/final_authority_map.json)、B2 SHA scope、status、clean baselineを整備。
4. `R23_N5_RUNTIME_OPTIMIZATION_CODE_AUDIT_POST_REMEDIATION_RERUN`: 次task。
5. R23 phase closure: 未実施。独立監査と残存条件の解消後に別途検討。
6. R24: `R24_NOT_STARTED_BLOCKED_PENDING_R23_POST_REMEDIATION_REAUDIT`。
7. Capacity、Time Window、Battery/SOC、Charging、Multiple Vehicles、Full EVRP integration/validation: 未着手。
8. external Deep Research、evidence normalization、hardware/capability stage、Single A / Single B / Joint scenario、delivery operation、energy/cost calculation、future scenario comparison、final discussion: 未着手。

詳細なaudit履歴は[audit chronology](../../reproducibility/outputs/traffic_simulation/r23_repository_rebaseline/20260913_v2/audit_chronology.json)、残存事項は[finding map](../../reproducibility/outputs/traffic_simulation/r23_repository_rebaseline/20260913_v2/current_finding_map.json)。runtime benchmarkはPRELIMINARY_ONLY、n≥6は現行exact CPU Aer statevector方法では非推奨。

最終評価はfuture technology assumptions、route optimization capability、battery-performance assumptions、EV delivery operation、operating energy、operating costを接続する。運用コストは`C_op = E_operation × p_electricity`に限定し、labor、vehicle purchase、infrastructure CAPEX、delay penaltyは追加しない。Full-EVRP R20はBLOCKED、R21はNOT_STARTED。
