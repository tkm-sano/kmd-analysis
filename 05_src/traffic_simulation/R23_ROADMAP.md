# R23 Reduced Problem roadmap（現行）

Current: `CODE_AUDIT_FAIL` / `CODE_AUDIT_RESULT_NOT_REPRODUCED` / REMEDIATION_INCOMPLETE。I03のrepository-wide無条件PASS除去が未完了。既存scientific recordsは保持。

1. `R23_REDUCED_PROBLEM_REPOSITORY_CONSOLIDATION` — 完了
2. `R23_LIMITED_SCALING_METHODOLOGY_REVIEW` — 完了。n=5はresource preflight前提、n>=6は現行exact CPU Aer statevector方法では非推奨
3. `R23_N5_SCALING_AUTHORIZATION` — resource remediation完了、実行authorization V2発行
4. `R23_N5_RANK01_EVIDENCE_REVIEW` — 完了。EXACT_REFERENCE_INTEGRITY_PASS、rank01 COMPLETE
5. `R23_N5_RUNTIME_OPTIMIZATION_REVIEW` — 旧validationの無条件PASSを撤回。独立audit FAILが優先
6. `R23_N5_SCALING_REMAINING_EXECUTION_OPTIMIZED` — rank02/rank03 records保持、lineage/resource provenance制約により未再承認
7. `R23_N5_SCALING_EVIDENCE_REVIEW` — accepted with limitationsの旧観測値を保持、optimizer success=2/3、route recovery=3/3
8. `R23_N5_RUNTIME_OPTIMIZATION_CODE_AUDIT_POST_REMEDIATION_RERUN` — remediation後の別task
9. `R23_REDUCED_PROBLEM_PHASE_CLOSURE` — 独立audit PASS後のみ
10. `R24_CAPACITY_EXTENSION_DESIGN` — BLOCKED / NOT_AUTHORIZED_PENDING_R23_REMEDIATION
6. Capacity — 未着手
7. Time Window — 未着手
8. Battery / SOC — 未着手
9. Charging — 未着手
10. Multiple Vehicles — 未着手
11. Full EVRP integration — 未着手
12. Full EVRP validation — 未着手
13. external Deep Research — 未着手
14. evidence normalization — 未着手
15. hardware / capability stage definition — 未着手
16. Single A routing scenario — 未着手
17. Single B battery-material scenario — 未着手
18. Joint scenario — 未着手
19. delivery operation simulation — 未着手
20. operating energy calculation — 未着手
21. operating cost calculation — 未着手
22. future scenario comparison — 未着手
23. final discussion — 未着手

最終評価はfuture technology assumptions、route optimization capability、battery-performance assumptions、EV delivery operation、operating energy、operating costを接続する。運用コストは`C_op = E_operation × p_electricity`に限定し、labor、vehicle purchase、infrastructure CAPEX、delay penaltyは追加しない。Full-EVRP R20はBLOCKED、R21はNOT_STARTED。
