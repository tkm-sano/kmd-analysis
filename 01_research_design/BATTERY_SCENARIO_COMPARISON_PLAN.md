<a id="battery条件と最適化手法の比較計画"></a>

# 電池条件と最適化手法の比較計画

<a id="2026-09-27評価規模再整理small-nは検証pilot-scope"></a>

## 2026-09-27（評価規模再整理）：小規模は検証・予備試験の範囲

[評価規模正本](../reproducibility/outputs/traffic_simulation/r24_evaluation_scale_authority/20260927_v1/EVALUATION_SCALE_AUTHORITY.md)を現在の規模選定正本とする。既存N002/N003/N004はMODEL_VALIDATION_SCALEとして保持し、N004はS0_PILOT、N003はS0_METHOD_IMPLEMENTATION_REFERENCEへ役割を限定する。既存予備試験 第0段階の物理・比較取り決め・成果物は不変。以下の旧S0_SCALE_AUTHORITY=固定済みはsmall-入力 範囲の値であり、本番評価規模を意味しない。

MODEL_VALIDATION_SCALE_AUTHORITY=固定済み、METHOD_COMPARISON_SCALE_AUTHORITY / SCENARIO_EVALUATION_SCALE_AUTHORITY / 本番のS0_SCALE_AUTHORITY=PARTIALLY_FROZEN。候補は既存n20/R01の無作為・集積型親標本の入れ子構成の先頭部分、n=3,4,5,8,10,15,20（3/4診断、5以上本番候補）。最終二規模は未選定で、同じnを強制しない。量子現行直接表現表現はn5/m1からメモリー下限で不適合、想定条件側は古典EVRP/Batteryの新規模証拠が必要。

次は入力受入→調査A（条件を統制した 古典計算 scaling/Battery 関連性）と調査B（最小構成の電気自動車配送経路問題 QUBO/resource監査）→二規模選定→本実験の第0段階 正本更新。調査設計は固定したが今回は実行していない。本実験の第0段階は未許可、全最適化/量子実行0。人口39,930顧客への直接外挿や39,930/n倍の経済換算は禁止する。

<a id="2026-09-27s0物理条件共通contractの部分freeze"></a>

## 2026-09-27：第0段階物理条件・共通取り決めの部分固定

[第0段階 正本](../reproducibility/outputs/traffic_simulation/r24_s0_baseline_authority/20260926_v1/S0_BASELINE_AUTHORITY.md)を更新し、S0_PHYSICAL_AUTHORITY / S0_CLASSICAL_PROTOCOL / 共通条件取り決め / 評価指標を固定済み、S0_QUANTUM_PROTOCOLを実行不可、S0_BASELINE_AUTHORITYを一部固定済みとした。想定条件側は既存n4・最大3台の構造予備試験、手法比較は既存n3・1台で、同一規模とは扱わない。人口39,930顧客への代表性は主張しない。

現行はmodel20 kWh・初期100%・最低10%・r=.127 kWh/km。全単純な配送経路の消費上限がusable18 kWhを下回るため、両層で充電設備訪問判断を除外し充電無効を固定した。実車充電出力は未解決のまま、この限定第0段階の阻害要因にはしない。経済正本は別拡張として未着手。

次作業は凍結第0段階条件に対する最小構成の電気自動車配送経路問題 Quantum/QUBO 符号化・同値性・資源監査。旧Exact/MILP 出典は保存Git treeでハッシュ値一致を確認済みだが、将来実行前の復元・実行器接続は別途必要。S0/全最適化/量子実行は未着手。本段落と第0段階正本が、以下の旧日付の第0段階未定義・経済必須記述に優先する。

更新日：2026-09-26。文書作成COMPLETED、想定条件 実行 NOT_STARTED。[研究順序](RESEARCH_STAGE_ROADMAP.md)と[共通C/Q比較](CLASSICAL_QUANTUM_EVRP_COMPARISON_PLAN.md)が実施条件を定義する。

<a id="条件freezeと比較行列"></a>

## 条件固定と比較行列

| 電池条件 | 古典計算 | 量子計算 | 固定・変更 |
|---|---|---|---|
| S0/current（0） | Exact/MILP reference | 有限-標本結果 | 非変更基準。全物理/配送入力を共通化 |
| Degradation（D） | 同じDで参照 | 同じDで標本評価 | 根拠付き電池変更だけ。非電池入力は第0段階固定 |
| Technology improvement（T） | 同じTで参照 | 同じTで標本評価 | NEDO等の目標＋明示的換算で定義した変更だけ |

B_max、健全度、P_charge、rを別変数で管理する。B_current/B_degradation/B_technologyという条件 識別子は変数の集合を指し、単一の性能得点ではない。容量変化と健全度による減算の二重適用、容量向上からr改善を自動推定することは禁止する。充電率分母、reserve割合/絶対値、初期・終了電力量、充電損失、充電速度の適用充電率範囲を各条件で明示する。感度点には別識別子とSENSITIVITY CONDITIONを付す。

[根拠計画](BATTERY_PERFORMANCE_EVIDENCE_PLAN.md)により出典 fact、研究 仮定、導出済み 値を別列で保存し、BATTERY_SCENARIO_AUTHORITY=固定済みとなるまで条件採用を完了扱いにしない。Minicab reference20kWhと検証10kWを実車利用可能な容量/実車充電性能として採用しない。想定条件値はこの文書では創作しない。

## 順序と解釈

1. 電池根拠・容量/健全度/技術容量/感度設計正本は固定済みである（実車P_chargeは未解決）。
2. 第0段階の物理・配送・古典計算 取り決めは二層予備試験の範囲で固定済み。次は量子計算 encoding/resource監査、実行実行不可。会計境界は経済拡張で後に定義する。
3. 同一第0段階でC/Qを比較し、既定評価指標を監査・固定、配送/EV/energy/限定経済結果を保存して第0段階を固定する（NOT_STARTED）。
4. DでC/Q、次にTでC/Qを実施する（各未着手）。
5. 条件内手法差と手法内条件差を分ける（NOT_STARTED）。
6. 代表条件周辺の感度分析を行う（NOT_STARTED）。

第0段階と同じ顧客、需要、配送拠点、車両群、道路、交通、時間窓、作業、目的を保持する。変更する電池パラメータと変更しない入力ハッシュ値を保存する。適用不整合やinfeasible結果も残し、時間窓や電費を後付け調整して成功にしない。規模変更は別軸・別作業であり、当初小規模境界を維持する。

評価式は比較計画のDelta_method,0、Delta_battery,C、Delta_battery,Qに従う。D/Tごとの手法差も保存する。任意interactionは後段候補である。電池差を評価するときに手法も同時に替えた対角比較だけで結論を作らない。

## 感度分析と経済評価

範囲・刻み・固定量・計算予算・停止条件を事前定義する。結論頑健性、reserve/充電要否の閾値、経路 choice、実行可能性の変化を調べる。official/publicの代表条件とmethodological 感度値を混ぜない。C/Qの比較手順を維持する。

第0段階と各変更条件の経済指標は同じE_operation境界・価格でC_op=E_operation×p_electricityを計算する計画である。運用電気料金に限定し、総物流費・経済便益とはしない。実行可能結果なしを0費用にしない。価格やgrid/battery会計が未確定なら経済結果はBLOCKED/NOT COMPARABLEである。

量子化学の性能をD/Tの数値生成に使わない。将来の最終考察で材料研究開発能力との関係を検討する。実行・経済計算・最適化は本作業で行わない。

## 採用条件への引継ぎ（2026-09-26）

[電池 正本](../reproducibility/outputs/traffic_simulation/r24_battery_scenario_authority/20260926_v1/BATTERY_SCENARIO_AUTHORITY.md)のCURRENT20、DEGRADATION_1=15、DEGRADATION_2=13、TECHNOLOGY_CAPACITY=80/3 kWhを将来比較する。感度設計10点も固定済み、実行は全て未着手である。第0段階 電池=現行であり10kW検証値を使わない。次作業は完全な第0段階 正本の定義である。
