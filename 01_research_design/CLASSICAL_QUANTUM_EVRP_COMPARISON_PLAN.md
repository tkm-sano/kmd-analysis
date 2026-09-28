<a id="同一条件でのclassicalquantum-evrp比較計画"></a>

# 同一条件での古典計算／量子計算 電気自動車配送経路問題比較計画

<a id="2026-09-27-study-b完了method-scaleはblocked"></a>

## 2026-09-27 調査B完了：手法比較の規模は実行不可

[最小構成の電気自動車配送経路問題量子資源静的監査](../reproducibility/outputs/traffic_simulation/r24_minimal_evrp_quantum_resource_audit/20260927_v1/MINIMAL_EVRP_QUANTUM_RESOURCE_AUDIT.md)を完了。現行直接表現表現はn5/m1でも34変数・471coupler・raw256GiBで、凍結計算方式上限256メビバイトを超える。METHOD_COMPARISON_SCALE_AUTHORITY=実行不可、選定nなし、S0_QUANTUM_PROTOCOL_RESOURCE_GATE=実行不可。n3/n4は検証・pilot/referenceのまま。MODEL_VALIDATION_SCALE_AUTHORITY=固定済み、想定条件評価の規模は一部固定済み、本実験の第0段階は未許可。

次は物理問題を変えない代替encoding/decompositionの静的比較。調査Aは別途未実行。凍結予備試験/科学成果物/台帳を保持し、新規最適化・Aer・量子近似最適化アルゴリズム・最適化処理評価・回路・回測定は全て0。以下の評価規模再整理段落は調査B前の履歴であり、手法状態と次作業は本段落が優先する。

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

更新日：2026-09-26。文書改訂COMPLETED、研究実行未着手。段階順序は[全体の研究段階計画](RESEARCH_STAGE_ROADMAP.md)のみを正本とする。電気自動車配送経路問題最適化と電子構造計算のClassical/Quantum比較は別の研究である。

## 1. 比較の目的と共通入力

電池条件差を手法差と混同しないため、同じ条件識別子の下で古典計算と量子計算を比較する。第0段階、劣化D、技術向上Tの各条件にC/Q両armを置く。需要、顧客集合・順序、配送拠点、fleet/Q、道路network/OD/交通、到達可能性、TW/service、Battery/SOC、充電設備位置・アクセス・出力、目的の優先順位、独立検証器を両armで共有しハッシュ値固定する。

現在の最小構成の電気自動車配送経路問題は全顧客訪問、主要な道路走行時間、secondary充電時間の辞書式目的である。過去の全体計画にある配送需要充足率/未配送許容や別の目的を黙って導入しない。第0段階の目的を変更するなら別正本・共通参照検証を必要とする。検証用10kW・低充電率は第0段階へ移植しない。

量子計算用電気自動車表現、連続充電量の扱い、精度・量子化誤差、encoding/decoder、予算、反復・乱数の種・停止規則は今後定義する判定基準である。本計画は制約なし二値二次最適化や回路を実装しない。離散化が必要なら比較用の同じ判断 領域を古典計算にも適用し、continuous 参照との差を別の近似誤差として保存する。物理入力が同じでも実行可能 setが違うのに同じ問題の手法差としない。

<a id="2-s0と反復設計"></a>

## 2. 第0段階と反復設計

第0段階は条件を変えない研究上の基準であり、過去のUniform B01/B02/B03でも最小構成の電気自動車配送経路問題 モデル-検証 事例でもない。現在Battery/charging、固定需要・道路・交通・時間窓・電気自動車モデル・経済パラメータ・目的を先に定義する。実車充電性能が未解決のため現時点の第0段階実行は実行不可である。

標本数、反復数、予算、乱数の種対応、実行可能判定、集計単位、報告対象経路の選定規則をstage6実行前に事前登録する。stage7は既定指標の監査・正式固定であり、結果を見て良い指標へ変更する工程ではない。手法間に意味のない乱数の種同一性を強制せず、比較群/反復対応の理由を保存する。反復をshot合算して独立な一標本として扱わない。

<a id="3-classical-reference"></a>

## 3. 古典参照解

可能な小規模ではExact/referenceと混合整数線形計画を使用する。最適 経路集合、目的値、実行可能性、充電判断、電力量、充電率、時刻を保存する。PROVEN_OPTIMAL、PROVEN_INFEASIBLE、時間 limit、境界のみ、求解器 不具合を区別する。最適性未証明の暫定最良解を最適値と呼ばない。物理的に不可能な条件と探索失敗を分ける。

<a id="4-quantum-sample-semantics"></a>

## 4. 量子計算 標本 意味

最終標本 測定度数と全constraint判定を保存する。各反復のoverall 実行可能 件数 / 合計 最終 標本を有限標本の実行可能 確率 estimateとして報告し、真の確率と断定しない。実行可能 件数、best 実行可能 route/objective、実行可能条件付き目的 distribution、最適-hit count/probability、visit/route/physical capacity/capacity encoding/temporal/battery/charging/depot等のvalidityを分ける。未評価はNOT_EVALUABLE、比較不能はNOT COMPARABLEを保持する。

最適 hitは同じ判断 領域の古典計算最適性と目的定義が確立した場合のみ定義する。主要な最適hitとlexicographic最適hitを区別し、ラベル対称な経路集合を扱う。実行可能 標本なしではbest 実行可能 objective/route、経路 電力量、運用経済値はNOT COMPARABLEであり、0費用や最適性成功にしない。単一の良い経路だけでarm全体を代表させない。

\[
Gap_Q=(T_{Q,best\ feasible}-T_{C,opt})/T_{C,opt}
\]

この式は同一問題の証明済み主要な最適値から、有限標本中の最良実行可能道路時間がどれだけ離れたかを表す無次元比である。百分率は100倍して別表示する。T_C>0、両値が評価可能、同じ目的/単位/制約/精度が前提である。T_C=0、参照未証明、古典計算 infeasible、量子計算 実行可能なしの場合はこの隔たりを定義しない。secondary充電時間差は主要な 同順位の範囲で別報告する。制約なし二値二次最適化 電力量をroad 目的や電気料金の代理にしない。

## 5. 共通比較表

| Family | 記録する指標 | 比較境界 |
|---|---|---|
| Optimization/feasibility | overall 実行可能、目的、隔たり、経路 sequence、optimality 状況 | 求解器 状況と物理判定を分離 |
| Routing | customer visit/order、charger visit、road distance、road travel time | 同じ道路網と出発地・到着地 |
| EV operation | q、charging time、Battery trajectory、final SOC | 同じ単位・reserve・充電規則 |
| 電力量 | total driving energy、battery-side charged energy、grid energy if modeled | 相互を合算して二重計上しない |
| 量子計算 | feasible counts/probability estimate、best feasible sample、optimal hit、objective distribution、constraint validity | 各反復と標本分母を保存 |
| 古典計算 | Exact/MILP optimumまたはbound/incumbent、証明状態 | 未証明をoptimumにしない |
| Economic | operating electricity expenditure | 下記の固定会計境界。best-経路値とdistributionを区別 |

将来データ構造はcondition_id、arm、run/repetition_id、input_hashes、solver/backend/version、objective_definition、状況、route_id、sample_count、shots_denominator、各family指標、単位、missing_reason、validator_version、execution_context、authority_idsを持つ。量子計算の経路-level経済値がbest 実行可能 経路の値か、実行可能条件付き分布かを必ずラベル化する。成功確率を無視した期待費用・実運用便益を算出しない。

## 6. 電力量・限定経済指標

\[
C_{op}=E_{operation}\,p_{electricity}
\]

E_operation[kWh]とp_electricity[通貨/kWh]により、同じ評価境界のoperating 電力 expenditure[通貨]を定義する。全体 logistics 費用ではない。労務、車両購入、償却、電池交換、充電設備CAPEX、保守、遅延費用は別モデルがない限り含めない。

第0段階経済拡張の実行前に電力量境界、初期充電の配賦、帰庫後の補充、battery/grid側と損失、価格の出典・適用日・通貨・税範囲・評価期間を固定する。充電0の経路でも出発時電力を消費するため、経路内qだけをE_operationとして費用0としない。同じ充電率初終条件または明示的な補充会計で公平性を確保し、走行電力量とその補充電力量を二重計上しない。採用する電力量定義・価格値は未解決であり、本作業では計算しない。経済値は結果指標であり経路計算 目的へ加えない。

## 7. 条件差と手法差

Y_{b,m}は電池条件b∈{0,D,T}、手法m∈{C,Q}の**同じ評価指標/集計規則**の値である。たとえば古典計算 経路 電力量と量子計算 best-実行可能 経路 電力量ならその条件付けを明示する。決定論的実行可能性フラグと標本 確率を無条件に同じYとして引き算しない。

\[
\Delta_{method,0}=Y_{0,Q}-Y_{0,C}
\]
同じ第0段階で手法を変えた差を表す。

\[
\Delta_{battery,C}=Y_{D,C}-Y_{0,C},\quad
\Delta_{battery,Q}=Y_{D,Q}-Y_{0,Q}
\]
同じ手法の下で電池条件だけを変えた差を表す。DをTへ置換して技術向上条件にも適用する。符号は常に後者条件/量子計算 minus baseline/Classicalという定義を保持し、好ましい方向に合わせて反転しない。改善方向は評価指標別に注記する。確率差はpercentage points、電力量はkWh等の単位を保持する。

\[
I_D=(Y_{D,Q}-Y_{D,C})-(Y_{0,Q}-Y_{0,C})
\]
これは電池条件により手法 differenceが変化したかを記述する任意の後段interaction候補である。必須指標や因果効果の証明ではない。欠測・infeasible条件は差をNOT COMPARABLEとし、都合のよい値へ補完しない。

<a id="8-freezeと主張境界"></a>

## 8. 固定と主張境界

第0段階で両armの経路・実行可能性・距離・移動 時間・充電設備 use・q・充電 時間・合計 電力量・最終 充電率・経済値・全optimization/sample指標・失敗/制限を保存してS0_BASELINE=固定済みとする。基準が不利でも再実行で置換しない。その後D/Tの各条件で同じC/Q比較を行い、[想定条件比較計画](BATTERY_SCENARIO_COMPARISON_PLAN.md)に従って差を解釈する。

量子計算 経路の優越、量子優位性、電気自動車の電力量削減、第0段階 量子計算最適性を前提にしない。実行時間比較には実機、並列数、preprocessing、compile、待ち行列、最適化処理、回測定、postprocessing、停止条件・精度・予算を記録し、歴史的に異なる実行環境のelapsed 時間を因果的高速化にしない。統計的有意性は事前設計なしに主張しない。本計画では科学実行0。
