# 同一条件でのClassical／Quantum EVRP比較計画

## 2026-09-27 Study B完了：method scaleはBLOCKED

[Minimal EVRP量子resource静的監査](../reproducibility/outputs/traffic_simulation/r24_minimal_evrp_quantum_resource_audit/20260927_v1/MINIMAL_EVRP_QUANTUM_RESOURCE_AUDIT.md)を完了。現行Direct表現はn5/m1でも34変数・471coupler・raw256GiBで、凍結backend上限256MiBを超える。METHOD_COMPARISON_SCALE_AUTHORITY=BLOCKED、選定nなし、S0_QUANTUM_PROTOCOL_RESOURCE_GATE=BLOCKED。n3/n4は検証・pilot/referenceのまま。MODEL_VALIDATION_SCALE_AUTHORITY=FROZEN、scenario scaleはPARTIALLY_FROZEN、main S0はNOT_AUTHORIZED。

次は物理問題を変えない代替encoding/decompositionの静的比較。Study Aは別途未実行。凍結pilot/科学成果物/ledgerを保持し、新規最適化・Aer・QAOA・optimizer評価・circuits・shotsは全て0。以下の評価規模再整理段落はStudy B前の履歴であり、method状態と次taskは本段落が優先する。

## 2026-09-27（評価規模再整理）：small-Nは検証・pilot scope

[評価規模authority](../reproducibility/outputs/traffic_simulation/r24_evaluation_scale_authority/20260927_v1/EVALUATION_SCALE_AUTHORITY.md)を現在の規模選定正本とする。既存N002/N003/N004はMODEL_VALIDATION_SCALEとして保持し、N004はS0_PILOT、N003はS0_METHOD_IMPLEMENTATION_REFERENCEへ役割を限定する。既存pilot S0の物理・比較contract・成果物は不変。以下の旧S0_SCALE_AUTHORITY=FROZENはsmall-input scopeの値であり、main評価規模を意味しない。

MODEL_VALIDATION_SCALE_AUTHORITY=FROZEN、METHOD_COMPARISON_SCALE_AUTHORITY / SCENARIO_EVALUATION_SCALE_AUTHORITY / mainのS0_SCALE_AUTHORITY=PARTIALLY_FROZEN。候補は既存n20/R01のRandom・Clustered親sampleのnested prefix、n=3,4,5,8,10,15,20（3/4診断、5以上main候補）。最終二規模は未選定で、同じnを強制しない。量子現行Direct表現はn5/m1からmemory下限で不適合、scenario側は古典EVRP/Batteryの新規模証拠が必要。

次は入力受入→Study A（controlled Classical scaling/Battery relevance）とStudy B（Minimal EVRP QUBO/resource監査）→二規模選定→main S0 authority更新。study設計は固定したが今回は実行していない。main S0はNOT_AUTHORIZED、全最適化/量子実行0。人口39,930顧客への直接外挿や39,930/n倍の経済換算は禁止する。

## 2026-09-27：S0物理条件・共通contractの部分freeze

[S0 authority](../reproducibility/outputs/traffic_simulation/r24_s0_baseline_authority/20260926_v1/S0_BASELINE_AUTHORITY.md)を更新し、S0_PHYSICAL_AUTHORITY / S0_CLASSICAL_PROTOCOL / 共通条件contract / metricsをFROZEN、S0_QUANTUM_PROTOCOLをBLOCKED、S0_BASELINE_AUTHORITYをPARTIALLY_FROZENとした。scenario側は既存n4・最大3台の構造pilot、method比較は既存n3・1台で、同一規模とは扱わない。人口39,930顧客への代表性は主張しない。

CURRENTはmodel20 kWh・初期100%・最低10%・r=.127 kWh/km。全simple配送routeの消費上限がusable18 kWhを下回るため、両layerでcharger訪問decisionを除外し充電INACTIVEを固定した。実車充電出力は未解決のまま、この限定S0のblockerにはしない。経済authorityは別extensionとしてNOT_STARTED。

次作業は凍結S0条件に対するMinimal EVRP Quantum/QUBO encoding・同値性・資源監査。旧Exact/MILP sourceは保存Git treeでhash一致を確認済みだが、将来実行前の復元・runner接続は別途必要。S0/全最適化/量子実行はNOT_STARTED。本段落とS0正本が、以下の旧日付のS0未定義・経済必須記述に優先する。

更新日：2026-09-26。文書改訂COMPLETED、研究実行NOT_STARTED。段階順序は[master roadmap](RESEARCH_STAGE_ROADMAP.md)のみを正本とする。EVRP最適化と電子構造計算のClassical/Quantum比較は別の研究である。

## 1. 比較の目的と共通入力

Battery条件差を手法差と混同しないため、同じ条件IDの下でClassicalとQuantumを比較する。S0、劣化D、技術向上Tの各条件にC/Q両armを置く。需要、顧客集合・順序、depot、fleet/Q、道路network/OD/交通、到達可能性、TW/service、Battery/SOC、charger位置・アクセス・出力、目的の優先順位、独立validatorを両armで共有しhash固定する。

現在のMinimal EVRPは全顧客訪問、primary道路走行時間、secondary充電時間の辞書式目的である。過去の全体計画にあるDFR/未配送許容や別の目的を黙って導入しない。S0の目的を変更するなら別authority・共通参照検証を必要とする。検証用10kW・低SOCはS0へ移植しない。

Quantum用EV表現、連続充電量の扱い、精度・量子化誤差、encoding/decoder、budget、反復・seed・停止規則は今後定義するgateである。本計画はQUBOや回路を実装しない。離散化が必要なら比較用の同じdecision domainをClassicalにも適用し、continuous referenceとの差を別の近似誤差として保存する。物理入力が同じでもfeasible setが違うのに同じ問題の手法差としない。

## 2. S0と反復設計

S0は条件を変えない研究上の基準であり、過去のUniform B01/B02/B03でもMinimal EVRP model-validation caseでもない。現在Battery/charging、固定需要・道路・traffic・TW・EVモデル・経済パラメータ・目的を先に定義する。実車充電性能が未解決のため現時点のS0実行はBLOCKEDである。

sample数、反復数、budget、seed対応、feasible判定、集計単位、報告対象routeの選定規則をstage6実行前に事前登録する。stage7は既定指標の監査・正式freezeであり、結果を見て良い指標へ変更する工程ではない。手法間に意味のないseed同一性を強制せず、比較group/反復対応の理由を保存する。反復をshot合算して独立な一標本として扱わない。

## 3. Classical reference

可能なsmall-NではExact/referenceとMILPを使用する。optimal route集合、目的値、feasibility、充電decision、energy、SOC、時刻を保存する。PROVEN_OPTIMAL、PROVEN_INFEASIBLE、time limit、boundのみ、solver failureを区別する。最適性未証明のincumbentを最適値と呼ばない。物理的に不可能な条件と探索失敗を分ける。

## 4. Quantum sample semantics

最終sample countsと全constraint判定を保存する。各反復のoverall feasible count / total final samplesを有限標本のfeasible probability estimateとして報告し、真の確率と断定しない。feasible count、best feasible route/objective、feasible条件付きobjective distribution、optimal-hit count/probability、visit/route/physical capacity/capacity encoding/temporal/battery/charging/depot等のvalidityを分ける。未評価はNOT_EVALUABLE、比較不能はNOT COMPARABLEを保持する。

optimal hitは同じdecision domainのClassical最適性と目的定義が確立した場合のみ定義する。primary最適hitとlexicographic最適hitを区別し、ラベル対称な経路集合を扱う。feasible sampleなしではbest feasible objective/route、route energy、運用経済値はNOT COMPARABLEであり、0費用や最適性成功にしない。単一の良いrouteだけでarm全体を代表させない。

\[
Gap_Q=(T_{Q,best\ feasible}-T_{C,opt})/T_{C,opt}
\]

この式は同一問題の証明済みprimary最適値から、有限sample中の最良feasible道路時間がどれだけ離れたかを表す無次元比である。百分率は100倍して別表示する。T_C>0、両値が評価可能、同じ目的/単位/制約/精度が前提である。T_C=0、参照未証明、Classical infeasible、Quantum feasibleなしの場合はこのgapを定義しない。secondary充電時間差はprimary tieの範囲で別報告する。QUBO energyをroad objectiveや電気料金の代理にしない。

## 5. 共通比較表

| Family | 記録する指標 | 比較境界 |
|---|---|---|
| Optimization/feasibility | overall feasible、目的、gap、route sequence、optimality status | solver statusと物理判定を分離 |
| Routing | customer visit/order、charger visit、road distance、road travel time | 同じnetworkとOD |
| EV operation | q、charging time、Battery trajectory、final SOC | 同じ単位・reserve・充電規則 |
| Energy | total driving energy、battery-side charged energy、grid energy if modeled | 相互を合算して二重計上しない |
| Quantum | feasible counts/probability estimate、best feasible sample、optimal hit、objective distribution、constraint validity | 各反復とsample分母を保存 |
| Classical | Exact/MILP optimumまたはbound/incumbent、証明状態 | 未証明をoptimumにしない |
| Economic | operating electricity expenditure | 下記の固定会計境界。best-route値とdistributionを区別 |

将来schemaはcondition_id、arm、run/repetition_id、input_hashes、solver/backend/version、objective_definition、status、route_id、sample_count、shots_denominator、各family指標、units、missing_reason、validator_version、execution_context、authority_idsを持つ。Quantumのroute-level経済値がbest feasible routeの値か、feasible条件付き分布かを必ずラベル化する。成功確率を無視した期待費用・実運用便益を算出しない。

## 6. 電力量・限定経済指標

\[
C_{op}=E_{operation}\,p_{electricity}
\]

E_operation[kWh]とp_electricity[通貨/kWh]により、同じ評価境界のoperating electricity expenditure[通貨]を定義する。full logistics costではない。労務、車両購入、償却、Battery交換、充電設備CAPEX、保守、遅延費用は別モデルがない限り含めない。

S0経済extensionの実行前に電力量境界、初期充電の配賦、帰庫後の補充、battery/grid側と損失、価格の出典・適用日・通貨・税範囲・評価期間を固定する。充電0のrouteでも出発時電力を消費するため、route内qだけをE_operationとして費用0としない。同じSOC初終条件または明示的な補充会計で公平性を確保し、走行energyとその補充energyを二重計上しない。採用する電力量定義・価格値はUNRESOLVEDであり、本taskでは計算しない。経済値は結果指標でありrouting objectiveへ加えない。

## 7. 条件差と手法差

Y_{b,m}はBattery条件b∈{0,D,T}、手法m∈{C,Q}の**同じmetric/集計規則**の値である。たとえばClassical route energyとQuantum best-feasible route energyならその条件付けを明示する。決定論的feasibilityフラグとsample probabilityを無条件に同じYとして引き算しない。

\[
\Delta_{method,0}=Y_{0,Q}-Y_{0,C}
\]
同じS0で手法を変えた差を表す。

\[
\Delta_{battery,C}=Y_{D,C}-Y_{0,C},\quad
\Delta_{battery,Q}=Y_{D,Q}-Y_{0,Q}
\]
同じ手法の下でBattery条件だけを変えた差を表す。DをTへ置換して技術向上条件にも適用する。符号は常に後者条件/Quantum minus baseline/Classicalという定義を保持し、好ましい方向に合わせて反転しない。改善方向はmetric別に注記する。確率差はpercentage points、energyはkWh等の単位を保持する。

\[
I_D=(Y_{D,Q}-Y_{D,C})-(Y_{0,Q}-Y_{0,C})
\]
これはBattery条件によりmethod differenceが変化したかを記述する任意の後段interaction候補である。必須指標や因果効果の証明ではない。欠測・infeasible条件は差をNOT COMPARABLEとし、都合のよい値へ補完しない。

## 8. Freezeと主張境界

S0で両armのroute・feasibility・distance・travel time・charger use・q・charging time・total energy・final SOC・経済値・全optimization/sample指標・失敗/制限を保存してS0_BASELINE=FROZENとする。baselineが不利でも再実行で置換しない。その後D/Tの各条件で同じC/Q比較を行い、[scenario比較計画](BATTERY_SCENARIO_COMPARISON_PLAN.md)に従って差を解釈する。

Quantum routeの優越、quantum advantage、EV電力量削減、S0 Quantum最適性を前提にしない。runtime比較にはhardware、並列数、preprocessing、compile、queue、optimizer、shots、postprocessing、停止条件・精度・budgetを記録し、歴史的に異なる実行環境のelapsed timeを因果的speedupにしない。統計的有意性は事前設計なしに主張しない。本計画では科学実行0。
