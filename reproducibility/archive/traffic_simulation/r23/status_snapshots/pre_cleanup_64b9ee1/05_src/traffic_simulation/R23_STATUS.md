# R23 current status（2026-09-14）

| Dimension | Current state |
|---|---|
| Scientific evidence | `R23_N5_SCALING_EVIDENCE_ACCEPTED_WITH_LIMITATIONS` |
| Independent code audit | `CODE_AUDIT_PASS_WITH_LIMITATIONS` |
| Result reproducibility | `RESULT_REPRODUCED_WITH_LIMITATIONS` |
| Provenance clean run | `R23_PROVENANCE_CLEAN_RUN_PASSED` |
| I03 | `RESOLVED` / `R23_I03_VALIDATION_GATE_REMEDIATION_PASSED` |
| B2 scientific integrity | 6/6 `VERIFIED`; formal acceptanceを追加しない |
| B2 artifact integrity | `FAILED`; `B2_TERMINAL_INDEX_SHA_INCONSISTENCY` 6件、`MODERATE` / `DERIVED_ARTIFACT_MISMATCH`、科学的数値影響は未確認 |
| R23 phase | `R23_CLOSED_WITH_DOCUMENTED_LIMITATIONS` |
| R24 | `R24_READY_TO_START`; `R24_NOT_STARTED` |

n=5: optimal route recovery = 3/3、relative route gap = 0（3/3）。optimizer reported success = 2/3、rank01はsuccess=false / 300 evaluation cap reached。P_feasible = 0.006366971625605308–0.007978143668511524、P_optimal = 5.447231886991554e-05–6.636000200882145e-05。rank01は153434.09043177636秒（42.62058時間）、absolute peak RSS 201.5834732055664 GiB。

rank01/02/03のexecution source再構成はSTRONGLY_INFERRED。rank02/03のprovenance・resource制約と未再承認を保持する。確率値はcompact recordの観測値でありhistorical optimizer trajectoryの再現を意味しない。runtime benchmarkはPRELIMINARY_ONLY。n≥6は現行exact CPU Aer statevector方法では非推奨。

独立closure reviewにより、scientific result independently reproduced、provenance-complete clean run passed、route recovery 3/3、optimizer success 2/3を確認した。unresolved CRITICAL/MAJORは0件で、independent auditはlimitations付きでPASS。残存事項はB2 derived-artifact mismatch、single n=5 benchmark、historical rank02/03 provenanceなどのdocumented non-blocking limitationsである。新clean-runを現行reproducibility authorityとし、historical artifactは変更しない。

n=5 fixed objective workload benchmarkはbaseline 1106.778772 s、V4 21.575394 s、観測比51.2982x、peak RSS比312.9934x。ただし各1 valid runの単一workloadであり、一般的scalability/runtime保証やquantum speedup/advantageを示さない。33.7x/327xは正式claimではない。

次工程はR24の設計・開始前レビュー。R24のscientific design/implementationは未開始。

[Authority map](../../reproducibility/outputs/traffic_simulation/r23_repository_rebaseline/20260913_v2/final_authority_map.json) · [Scientific facts](../../reproducibility/outputs/traffic_simulation/r23_repository_rebaseline/20260913_v2/scientific_fact_table.json) · [Findings](../../reproducibility/outputs/traffic_simulation/r23_repository_rebaseline/20260913_v2/current_finding_map.json) · [B2 SHA assessment](../../reproducibility/outputs/traffic_simulation/r23_repository_rebaseline/20260913_v2/b2_sha_impact_assessment.json) · [Re-audit checklist](../../reproducibility/outputs/traffic_simulation/r23_repository_rebaseline/20260913_v2/independent_reaudit_readiness.json)
