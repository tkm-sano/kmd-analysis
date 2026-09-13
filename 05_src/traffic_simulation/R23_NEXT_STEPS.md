# R23 next steps（現行）

Current: standing audit `CODE_AUDIT_FAIL` / `CODE_AUDIT_RESULT_NOT_REPRODUCED`。`REMEDIATION_COMPLETED_PENDING_INDEPENDENT_REAUDIT`。

直近taskは `R23_N5_RUNTIME_OPTIMIZATION_CODE_AUDIT_POST_REMEDIATION_RERUN`。I03は14 fileを実条件gateへ修正し、positive/negative regressionとtargeted rescanを完了。B2 v2の6件の旧terminal-index SHA不整合を検出したため、そのFAILED結果も独立再監査へ渡す。旧indexやraw結果は修復していない。

完了後は別task `R23_N5_RUNTIME_OPTIMIZATION_CODE_AUDIT_POST_REMEDIATION_RERUN` とする。修正担当者はCODE_AUDIT_PASSを宣言しない。独立再監査でPASSした場合にのみ `R23_REDUCED_PROBLEM_PHASE_CLOSURE` → `R24_CAPACITY_EXTENSION_DESIGN`。R24は `NOT_AUTHORIZED_PENDING_R23_REMEDIATION`。rank02/03の旧recordsは保持し、execution/resource provenanceが閉じるまで再承認しない。再実行を自動開始しない。

既存route recovery=3/3、gap=0はoptimizer success=2/3と区別する。rank01はsuccess=falseかつcap reached。runtime/memory比較はPRELIMINARY_ONLY、n≥6は現行methodology非推奨。Full-EVRP R20=BLOCKED、R21=NOT_STARTED。
