# R23 next steps（現行）

`R23_LIMITED_SCALING_METHODOLOGY_REVIEW`とresource remediationは完了した。R23 n=5 rank01は完了し、exact optimumを回収したが、COBYLAは300評価上限に到達しており収束成功ではない。T_totalは約42時間37分、T_Aerは約5分7秒、peak RSSは約201.6 GiBである。rank02/rank03は未実行。T_totalとT_Aerの乖離が大きく、追加実行前にruntime bottleneckを診断する。

runtime reviewでは、全33,554,432状態のPython辞書化が主要候補として実測的に示唆された。120 feasible-index prototypeは大幅に短いが、元実装との完了済みn=5 cross-checkがないためrank02/rank03への採用は保留し、判定は`R23_N5_RUNTIME_OPTIMIZATION_EQUIVALENCE_FAILED`とした。次のtaskは`R23_N5_RUNTIME_OPTIMIZATION_REVIEW_REMEDIATION`。R24/Capacityにはまだ進まない。Full-EVRP R20=BLOCKED、R21=NOT_STARTED。
