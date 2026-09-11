# R23 Reduced Problem roadmap（現行）

Current: `R23_LIMITED_SCALING_METHODOLOGY_REVIEW_COMPLETED`

1. `R23_REDUCED_PROBLEM_REPOSITORY_CONSOLIDATION` — 完了
2. `R23_LIMITED_SCALING_METHODOLOGY_REVIEW` — 完了。n=5はresource preflight前提、n>=6は現行exact CPU Aer statevector方法では非推奨
3. `R23_N5_SCALING_AUTHORIZATION` — 未認可（resource limit）。frozen exact Aer runtime再現がないためn=5実行不可
4. `R24_CAPACITY_EXTENSION_DESIGN` — 次。n=5実行を無理に進めず、容量拡張方法を設計
5. Capacity — 未着手
6. Time Window — 未着手
7. Battery / SOC — 未着手
8. Charging — 未着手
9. Multiple Vehicles — 未着手
10. Full EVRP integration — 未着手
11. Full EVRP validation — 未着手
12. external Deep Research — 未着手
13. evidence normalization — 未着手
14. hardware / capability stage definition — 未着手
15. Single A routing scenario — 未着手
16. Single B battery-material scenario — 未着手
17. Joint scenario — 未着手
18. delivery operation simulation — 未着手
19. operating energy calculation — 未着手
20. operating cost calculation — 未着手
21. future scenario comparison — 未着手
22. final discussion — 未着手

最終評価はfuture technology assumptions、route optimization capability、battery-performance assumptions、EV delivery operation、operating energy、operating costを接続する。運用コストは`C_op = E_operation × p_electricity`に限定し、labor、vehicle purchase、infrastructure CAPEX、delay penaltyは追加しない。Full-EVRP R20はBLOCKED、R21はNOT_STARTED。
