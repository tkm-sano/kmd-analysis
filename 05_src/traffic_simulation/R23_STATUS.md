# R23 current status（2026-09-14）

| Dimension | Current state |
|---|---|
| Scientific evidence | `R23_N5_SCALING_EVIDENCE_ACCEPTED_WITH_LIMITATIONS` |
| Independent code audit | `CODE_AUDIT_FAIL_PENDING_POST_REMEDIATION_REAUDIT` |
| Original audit reproducibility | `CODE_AUDIT_RESULT_NOT_REPRODUCED` |
| Audit remediation | `R23_N5_RUNTIME_OPTIMIZATION_AUDIT_REMEDIATION_COMPLETED_PENDING_INDEPENDENT_REAUDIT` |
| I03 | `RESOLVED` / `R23_I03_VALIDATION_GATE_REMEDIATION_PASSED` |
| B2 scientific integrity | 6/6 `VERIFIED`; formal acceptanceを追加しない |
| B2 artifact integrity | `FAILED`; `B2_TERMINAL_INDEX_SHA_INCONSISTENCY` 6件、未修復・独立severity評価待ち |
| R23 phase | OPEN; closure未実施 |
| R24 | `R24_NOT_STARTED_BLOCKED_PENDING_R23_POST_REMEDIATION_REAUDIT` |

n=5: optimal route recovery = 3/3、relative route gap = 0（3/3）。optimizer reported success = 2/3、rank01はsuccess=false / 300 evaluation cap reached。P_feasible = 0.006366971625605308–0.007978143668511524、P_optimal = 5.447231886991554e-05–6.636000200882145e-05。rank01は153434.09043177636秒（42.62058時間）、absolute peak RSS 201.5834732055664 GiB。

rank01/02/03のexecution source再構成はSTRONGLY_INFERRED。rank02/03のprovenance・resource制約と未再承認を保持する。確率値はcompact recordの観測値でありhistorical optimizer trajectoryの再現を意味しない。runtime benchmarkはPRELIMINARY_ONLY。n≥6は現行exact CPU Aer statevector方法では非推奨。

Routing Baseline、Reduced Problem、Formal A、B1のauthorityと履歴は保持。scientific model・run・historical indexは変更しない。次taskは `R23_N5_RUNTIME_OPTIMIZATION_CODE_AUDIT_POST_REMEDIATION_RERUN`。

[Authority map](../../reproducibility/outputs/traffic_simulation/r23_repository_rebaseline/20260913_v2/final_authority_map.json) · [Scientific facts](../../reproducibility/outputs/traffic_simulation/r23_repository_rebaseline/20260913_v2/scientific_fact_table.json) · [Findings](../../reproducibility/outputs/traffic_simulation/r23_repository_rebaseline/20260913_v2/current_finding_map.json) · [B2 SHA assessment](../../reproducibility/outputs/traffic_simulation/r23_repository_rebaseline/20260913_v2/b2_sha_impact_assessment.json) · [Re-audit checklist](../../reproducibility/outputs/traffic_simulation/r23_repository_rebaseline/20260913_v2/independent_reaudit_readiness.json)
