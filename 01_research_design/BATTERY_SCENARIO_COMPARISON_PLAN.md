# Battery条件と最適化手法の比較計画

## 2026-09-27（評価規模再整理）：small-Nは検証・pilot scope

[評価規模authority](../reproducibility/outputs/traffic_simulation/r24_evaluation_scale_authority/20260927_v1/EVALUATION_SCALE_AUTHORITY.md)を現在の規模選定正本とする。既存N002/N003/N004はMODEL_VALIDATION_SCALEとして保持し、N004はS0_PILOT、N003はS0_METHOD_IMPLEMENTATION_REFERENCEへ役割を限定する。既存pilot S0の物理・比較contract・成果物は不変。以下の旧S0_SCALE_AUTHORITY=FROZENはsmall-input scopeの値であり、main評価規模を意味しない。

MODEL_VALIDATION_SCALE_AUTHORITY=FROZEN、METHOD_COMPARISON_SCALE_AUTHORITY / SCENARIO_EVALUATION_SCALE_AUTHORITY / mainのS0_SCALE_AUTHORITY=PARTIALLY_FROZEN。候補は既存n20/R01のRandom・Clustered親sampleのnested prefix、n=3,4,5,8,10,15,20（3/4診断、5以上main候補）。最終二規模は未選定で、同じnを強制しない。量子現行Direct表現はn5/m1からmemory下限で不適合、scenario側は古典EVRP/Batteryの新規模証拠が必要。

次は入力受入→Study A（controlled Classical scaling/Battery relevance）とStudy B（Minimal EVRP QUBO/resource監査）→二規模選定→main S0 authority更新。study設計は固定したが今回は実行していない。main S0はNOT_AUTHORIZED、全最適化/量子実行0。人口39,930顧客への直接外挿や39,930/n倍の経済換算は禁止する。

## 2026-09-27：S0物理条件・共通contractの部分freeze

[S0 authority](../reproducibility/outputs/traffic_simulation/r24_s0_baseline_authority/20260926_v1/S0_BASELINE_AUTHORITY.md)を更新し、S0_PHYSICAL_AUTHORITY / S0_CLASSICAL_PROTOCOL / 共通条件contract / metricsをFROZEN、S0_QUANTUM_PROTOCOLをBLOCKED、S0_BASELINE_AUTHORITYをPARTIALLY_FROZENとした。scenario側は既存n4・最大3台の構造pilot、method比較は既存n3・1台で、同一規模とは扱わない。人口39,930顧客への代表性は主張しない。

CURRENTはmodel20 kWh・初期100%・最低10%・r=.127 kWh/km。全simple配送routeの消費上限がusable18 kWhを下回るため、両layerでcharger訪問decisionを除外し充電INACTIVEを固定した。実車充電出力は未解決のまま、この限定S0のblockerにはしない。経済authorityは別extensionとしてNOT_STARTED。

次作業は凍結S0条件に対するMinimal EVRP Quantum/QUBO encoding・同値性・資源監査。旧Exact/MILP sourceは保存Git treeでhash一致を確認済みだが、将来実行前の復元・runner接続は別途必要。S0/全最適化/量子実行はNOT_STARTED。本段落とS0正本が、以下の旧日付のS0未定義・経済必須記述に優先する。

更新日：2026-09-26。文書作成COMPLETED、scenario execution NOT_STARTED。[研究順序](RESEARCH_STAGE_ROADMAP.md)と[共通C/Q比較](CLASSICAL_QUANTUM_EVRP_COMPARISON_PLAN.md)が実施条件を定義する。

## 条件freezeと比較行列

| Battery条件 | Classical | Quantum | 固定・変更 |
|---|---|---|---|
| S0/current（0） | Exact/MILP reference | finite-sample結果 | 非変更baseline。全物理/配送入力を共通化 |
| Degradation（D） | 同じDでreference | 同じDでsample評価 | 根拠付きBattery変更だけ。非Battery入力はS0固定 |
| Technology improvement（T） | 同じTでreference | 同じTでsample評価 | NEDO等の目標＋明示的換算で定義した変更だけ |

B_max、SOH、P_charge、rを別変数で管理する。B_current/B_degradation/B_technologyというcondition IDは変数の集合を指し、単一の性能scoreではない。容量変化とSOHによる減算の二重適用、容量向上からr改善を自動推定することは禁止する。SOC分母、reserve割合/絶対値、初期・終了energy、充電損失、充電速度の適用SOC範囲を各conditionで明示する。感度点には別IDとSENSITIVITY CONDITIONを付す。

[根拠計画](BATTERY_PERFORMANCE_EVIDENCE_PLAN.md)によりsource fact、research assumption、derived valueを別列で保存し、BATTERY_SCENARIO_AUTHORITY=FROZENとなるまで条件採用を完了扱いにしない。Minicab reference20kWhと検証10kWを実車usable容量/実車充電性能として採用しない。scenario値はこの文書では創作しない。

## 順序と解釈

1. Battery根拠・容量/SOH/技術容量/感度設計authorityはFROZENである（実車P_chargeは未解決）。
2. S0の物理・配送・Classical contractは二層pilot scopeでFROZEN。次はQuantum encoding/resource監査、実行BLOCKED。会計境界は経済extensionで後に定義する。
3. 同一S0でC/Qを比較し、既定metricを監査・固定、配送/EV/energy/限定経済結果を保存してS0をfreezeする（NOT_STARTED）。
4. DでC/Q、次にTでC/Qを実施する（各NOT_STARTED）。
5. condition内method差とmethod内condition差を分ける（NOT_STARTED）。
6. 代表条件周辺の感度分析を行う（NOT_STARTED）。

S0と同じ顧客、需要、depot、fleet、道路、traffic、TW、service、目的を保持する。変更するBatteryパラメータと変更しない入力hashを保存する。適用不整合やinfeasible結果も残し、TWや電費を後付け調整して成功にしない。規模変更は別軸・別taskであり、当初small-N境界を維持する。

評価式は比較計画のDelta_method,0、Delta_battery,C、Delta_battery,Qに従う。D/Tごとの手法差も保存する。任意interactionは後段候補である。Battery差を評価するときに手法も同時に替えた対角比較だけで結論を作らない。

## 感度分析と経済評価

範囲・刻み・固定量・計算budget・停止条件を事前定義する。結論頑健性、reserve/充電要否の閾値、route choice、feasibilityの変化を調べる。official/publicの代表条件とmethodological sensitivity値を混ぜない。C/Qの比較protocolを維持する。

S0と各変更条件の経済指標は同じE_operation境界・価格でC_op=E_operation×p_electricityを計算する計画である。運用電気料金に限定し、総物流費・経済便益とはしない。feasible結果なしを0費用にしない。価格やgrid/battery会計が未確定なら経済結果はBLOCKED/NOT COMPARABLEである。

量子化学の性能をD/Tの数値生成に使わない。将来の最終考察で材料R&D能力との関係を検討する。実行・経済計算・最適化は本taskで行わない。

## 採用条件への引継ぎ（2026-09-26）

[Battery authority](../reproducibility/outputs/traffic_simulation/r24_battery_scenario_authority/20260926_v1/BATTERY_SCENARIO_AUTHORITY.md)のCURRENT20、DEGRADATION_1=15、DEGRADATION_2=13、TECHNOLOGY_CAPACITY=80/3 kWhを将来比較する。感度設計10点もFROZEN、実行は全てNOT_STARTEDである。S0 Battery=CURRENTであり10kW検証値を使わない。次taskは完全なS0 authorityの定義である。
