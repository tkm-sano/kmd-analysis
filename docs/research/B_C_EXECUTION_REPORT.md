# B・Cの共通条件実行

2026-11-12。小規模6/20/120/240→S1。以下は保存した実測で、一般的な優劣の証明ではない。

|規模|方法/条件|判定|D［km］|W［分］|T_program［秒］|
|---|---|---|---|---|---|
|ROAD_N120|B/B_primaryD_epsW_1|FEASIBLE|101.762900|0.000000|0.251296|
|ROAD_N120|C/C_primaryD_epsW_1|FEASIBLE|90.126300|0.000000|60.283343|
|ROAD_N20|B/B_primaryD_epsW_1|FEASIBLE|42.792500|0.000000|0.211912|
|ROAD_N20|C/C_primaryD_epsW_1|FEASIBLE|38.962100|0.000000|60.247420|
|ROAD_N240|B/B_primaryD_epsW_1|FEASIBLE|164.796000|0.000000|0.355155|
|ROAD_N240|C/C_primaryD_epsW_1|FEASIBLE|145.372700|0.000000|60.425641|
|ROAD_N6|B/B_primaryD_epsW_1|FEASIBLE|21.862900|0.000000|0.227148|
|ROAD_N6|C/C_primaryD_epsW_1|FEASIBLE|20.715900|0.000000|60.228713|
|S1|B/B_primaryD_epsW_1|FEASIBLE|444.176800|285.750000|33.057801|
|S1|B/B_primaryD_epsW_1.25|FEASIBLE|444.176800|342.400000|33.025602|
|S1|B/B_primaryD_epsW_1.5|FEASIBLE|444.176800|306.000000|33.161628|
|S1|B/B_primaryW_epsD_1|FEASIBLE|444.176800|282.000000|33.184325|
|S1|B/B_primaryW_epsD_1.1|FEASIBLE|444.176800|282.000000|33.106226|
|S1|B/B_primaryW_epsD_1.25|FEASIBLE|444.176800|282.000000|33.032120|
|S1|B/B_repeat_primaryD_epsW_1|FEASIBLE|444.176800|285.750000|33.048897|
|S1|C/C_primaryD_epsW_1|FEASIBLE|410.109800|342.000000|93.138680|
|S1|C/C_primaryD_epsW_1.25|FEASIBLE|410.109800|323.366667|93.086885|
|S1|C/C_primaryD_epsW_1.5|FEASIBLE|410.109800|298.716667|93.146336|
|S1|C/C_primaryW_epsD_1|FEASIBLE|410.109800|314.366667|93.619493|
|S1|C/C_primaryW_epsD_1.1|FEASIBLE|410.109800|314.366667|93.565429|
|S1|C/C_primaryW_epsD_1.25|FEASIBLE|410.109800|314.366667|93.170044|
|S1|C/C_repeat_primaryD_epsW_1|FEASIBLE|410.109800|342.000000|93.073433|


BはVeRyPyの節約量計算を再利用。上流parallel_savings_initは対称距離前提なので、そのまま有向ODで実行したとは記載しない。有向tail→head結合・逆転なしのCW派生法。容量60、便数過多なら最小便を他便へ最小増分挿入し、物理車両/バースは共通CP-SATで完成する。名称は「有向CW＋共通古典完成器」。外部コードは改変せずcommit/LICENSE/hashをVERY_PY_PROVENANCE.jsonに保存。

CはOR-Tools9.14.6206 Routing、2V仮想便、容量、directed decimeter arc、CW初期解、PCI/GLSで60秒。その最終経路集合と初期経路集合の和集合を、同じ共通CP-SATで物理車両2便とバースへ接続する。勤務/積込排他はRouting内ではなく最終完成器で満たす。有限route poolからの選択で、全VRPの最適性保証ではない。[公式Routing文書](https://developers.google.com/optimization/routing)。

完成器は1 worker/seed20261112/最大30秒。第1便readyは固定、第2便readyは変数の第1便帰着。積込1800秒のoptional interval cumulative B。顧客被覆・容量・帰着・便数を同時制約化。Dは0.1m整数費用、Wは整数秒。主目的と副目的の厳密lexicographic tie breakを使い、恣意的な加重和のトレードオフは導入しない。D/Wの主評価は両方向ε。

S1共通参照は事前のA順で最初に可行な A2 offset=0、D_ref=551.139800km、W_ref=422.450000分。ε_D=D_ref×[1,1.1,1.25]、ε_W=W_ref×[1,1.25,1.5]。EPSILON_REFERENCES.jsonをB/C/D実行前に保存。A1失敗を隠して参照を作っていない。

Tは毎回新プロセスで読込・初期構築・Routing・CP完成・共通検査までを含む。比較CSVにinput/optimization/validation内訳、raw timing_eventsに細分化を保存。60秒上限のため探索結果は同seedでもwall環境で終端が変わり得る。時間平均や統計的優位性は単発条件集合から主張しない。RSSも各プロセス実測。

証拠根：`output/toc_delivery/ad_pipeline_20261112_route_v2/`。設定：`configs/toc_delivery/ad_pipeline_v2_route.json`。実行前計画：`docs/research/A_TO_D_PIPELINE_IMPLEMENTATION_PLAN.md`。共通schema差分：`docs/research/A_TO_D_COMMON_INTERFACE.md`。
