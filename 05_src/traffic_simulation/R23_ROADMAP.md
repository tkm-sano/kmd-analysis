# R23 roadmap（現行）

現在: R23 `R23_CLOSED_WITH_DOCUMENTED_LIMITATIONS`、audit `CODE_AUDIT_PASS_WITH_LIMITATIONS`、reproducibility `RESULT_REPRODUCED_WITH_LIMITATIONS`、provenance clean run `R23_PROVENANCE_CLEAN_RUN_PASSED`。route recovery 3/3、optimizer success 2/3。B2 SHA不整合6件は`MODERATE` / `DERIVED_ARTIFACT_MISMATCH`のdocumented non-blocking limitationで、scientific integrity 6/6 VERIFIED / 数値影響未確認。

1. Routing / Reduced Problem / Formal A / B1 / B2: evidenceを保存、authorityの役割別に保持。
2. n=5: 3 runsを制約付きで保持。optimal route recovery = 3/3、optimizer reported success = 2/3。rank02/03は未再承認。
3. Repository rebaseline: [current authority map](../../reproducibility/outputs/traffic_simulation/r23_repository_rebaseline/20260913_v2/final_authority_map.json)、B2 SHA scope、status、clean baselineを整備。
4. R23 independent closure review: `CODE_AUDIT_PASS_WITH_LIMITATIONS`、`RESULT_REPRODUCED_WITH_LIMITATIONS`。historical rank02/03 provenance limitationとsingle n=5 benchmark limitationを保持。
5. R23 phase: `R23_CLOSED_WITH_DOCUMENTED_LIMITATIONS`。historical scientific artifactsは不変。
6. R24: `R24_READY_TO_START`、`R24_NOT_STARTED`。R24 design/implementationは別承認後に開始。
7. Capacity、Time Window、Battery/SOC、Charging、Multiple Vehicles、Full EVRP integration/validation: 未着手。
8. external Deep Research、evidence normalization、hardware/capability stage、Single A / Single B / Joint scenario、delivery operation、energy/cost calculation、future scenario comparison、final discussion: 未着手。

詳細なaudit履歴は[audit chronology](../../reproducibility/outputs/traffic_simulation/r23_repository_rebaseline/20260913_v2/audit_chronology.json)、残存事項は[finding map](../../reproducibility/outputs/traffic_simulation/r23_repository_rebaseline/20260913_v2/current_finding_map.json)。runtime benchmarkはPRELIMINARY_ONLY、n≥6は現行exact CPU Aer statevector方法では非推奨。

最終評価はfuture technology assumptions、route optimization capability、battery-performance assumptions、EV delivery operation、operating energy、operating costを接続する。運用コストは`C_op = E_operation × p_electricity`に限定し、labor、vehicle purchase、infrastructure CAPEX、delay penaltyは追加しない。Full-EVRP R20はBLOCKED、R21はNOT_STARTED。
