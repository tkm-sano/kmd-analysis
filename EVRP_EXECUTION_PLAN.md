# EVRP Execution Plan

文書ID: `EVRP-EXECUTION-PLAN-001`  
作成・更新日: 2026-09-09  
計画版: 1.0  
役割: 本研究の**唯一の進行管理・実行記録文書**。仕様・原本・code・machine-readable成果物は各既存pathで保持し、工程status・次工程・実行判断は本書だけで管理する。

初回監査・計画作成を完了した後、利用者の継続指示により、計画順に1工程ずつ実行する。各工程の完了記録と停止判定を本書へ先に反映する。

# Objective

東京の住宅向けlast-mile EV配送を対象に、公的統計・実道路ネットワーク・EV性能条件から共通配送インスタンスを構築する。古典最適化と量子最適化を同一条件で比較し、配送需要充足率と計算資源要求を評価する。

# Scope

Residential / B2C last-mile parcel delivery。Baseline problemはE-VRPTWを基礎とするEV routing problem。現在の地理基盤は大田区。古典手法はOR-Tools、量子手法はQUBO → Ising Hamiltonian → QAOA → Qiskit Aer。

39,956地点は候補母集団 $C_{\mathrm{all}}$ であり、全件を1つのEVRPとして解かない。$C_s\subset C_{\mathrm{all}}$、$n=|C_s|$ をproblem-size実験パラメータとする。25/50/100等を固定scenarioとして採択しない。Baselineは単一depotを原則固定する。

[最新B2C仕様](RESEARCH_PIPELINE_REFERENCE.md#b2c-pipeline-20260909)を参照するが、今回の指示で時間窓を**service開始**に適用し、Operating timeは**最大運行時間を設定した場合に適用**すると具体化した。本書がこれらと実行順序・停止条件の最新記録である。旧ロードマップ、CLIやPortalの「Routing NEXT」「Demand DONE」は既存実装の表示であり、本書の次工程やPASSを上書きしない。

# Existing State Audit

既存成果物分類と工程statusは別の軸である。`ACCEPTED`は確認した受入範囲内、`IMPLEMENTED_NOT_VALIDATED`は実装があるが対象検証未完、`PARTIAL`は一部のみ、`NOT_IMPLEMENTED`は現行source/runnerなし、`UNKNOWN`は証拠不足を意味する。

| 対象 | 分類 | 監査証拠と範囲 |
|---|---|---|
| 現行B2C仕様 | ACCEPTED | 2026-09-09の利用者採択。研究実装の受入ではない。 |
| Formal SUMO network | ACCEPTED | current authority → run_2/network_acceptance.json、FORMAL_NETWORK_ACCEPTED=true。今回hash照合・既存authority validator PASS。 |
| Stop-road mapping | ACCEPTED | 39,956/39,956、delivery許可edge。edge中点index・overrideという既存方式の受入範囲。 |
| 39,956 candidate populationの新用途 | PARTIAL | CSVは39,956行、stop_id/building_idとも重複・空欄0、WKT座標は経緯度範囲内。新しい住宅候補母集団の代表性・mesh対応・再生成契約はR03で検証する。 |
| Candidate生成方法 | PARTIAL | stop_generation_run_summary.jsonに世帯→建物割当seed 20260830、85,690割当建物のうち39,956 active建物。正式再生成source/runnerは現行checkoutにない。 |
| 国勢調査2020 500m | PARTIAL | ZIP hashは台帳一致。人口列の既存利用あり、世帯列採用と秘匿・合算の解釈は未確定。ZIPは指定memberだけを読む。 |
| 個人のモノの受取調査2024 | PARTIAL | manifest 20 entries / 19 unique files、全hash一致。ss515重複entryは同一hashで原本を変更しない。新しい需要/TWの採用契約は未完。 |
| 既存人口・parcel-equivalent生成 | ACCEPTED | prepare_baseline_demand.pyの既存tests 13 PASS。旧proxyの範囲に限り、新しい配送件数生成のPASSではない。 |
| 新B2C weight/sampling/demand/TW/service生成 | NOT_IMPLEMENTED | 旧CSV・仕様はあるが新契約の本番生成器・検証器はない。 |
| OSM/SUMO runtime | PARTIAL | SUMO/duarouter 1.24.0のbinaryあり。Python環境でsumolib/traciのdistribution metadataなし。SUMO付属toolsのimportは未検証。 |
| Routing code | PARTIAL | research_cli/routing.pyは入口・未実装通知。network routeability検査codeはあるが本番必要OD runnerはない。 |
| Routing validation | PARTIAL | 受入主sample 100/100、追加sanity 91/100。全必要ODの証明ではなく、将来R14を代替しない。 |
| Depot | PARTIAL | legacyの公的物流施設proxy候補CSVあり。Baseline拠点・受入網接続は未採択。 |
| EV specification | PARTIAL | managed_urban_ev_delivery_v1は明示model assumption（delivery、payload 2000kg）。EV catalog派生表もあるがbattery/energy/SOCのinstance採択は未完。 |
| Charging stations | PARTIAL | 現行raw chargingは.gitkeep、legacyのOCM候補あり。public access不明の行があり、利用可能性・互換性・網接続は未受入。 |
| OR-Tools package | IMPLEMENTED_NOT_VALIDATED | 9.12.4544導入済み。13制約付き本番model/runner/解検証はNOT_IMPLEMENTED。 |
| Common instance / independent EVRP validator | NOT_IMPLEMENTED | 05_src/optimizationには古い__pycache__のみ。source不在を実装済みとしない。 |
| QUBO / Ising / QAOA runner | NOT_IMPLEMENTED | 文献・設計・CLIのみ。本番encoding、等価性fixture、decoderなし。 |
| Qiskit / Aer | NOT_IMPLEMENTED | 今回の.conda Pythonには未導入。導入・version固定・smoke検証は後続R23の開始前作業。 |
| 運用パラメータの実測根拠 | UNKNOWN | 住宅service time、採択EVの消費率、charger利用条件等は未確定。 |
| Tests / manifests / generated reports | PARTIAL | 既存portal 6検査PASS・旧需要13 tests PASS。下流EVRP実験の受入manifestとreportはない。 |

主な証拠:

- [道路網authority](reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml)
- [geometry/length再受入authority](reproducibility/config/traffic_simulation/current_network_completion_authority_v18_geometry_reaccepted.yml)
- [候補生成要約](03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/stop_generation_run_summary.json)
- [旧pipeline要約](03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/pipeline_run_summary.json)
- [宅配統計取得記録](03_data/metadata/acquisition/20260825_tokyo_metropolitan_goods_movement_delivery_receipt_tables.md)
- [需要code](05_src/traffic_simulation/demand/prepare_baseline_demand.py)
- [routing入口](05_src/research_cli/routing.py)
- [比較規約](05_src/traffic_simulation/optimization_comparison_protocol.md)
- [EV profile](reproducibility/config/traffic_simulation/scenario_profiles/managed_urban_ev_delivery_v1.yml)
- [Depot proxy](legacy/non_sumo_route_proxy_analysis/data/processed/evrp_constraint_gap_inputs/depot_candidates_public_proxy_snapshot.csv)
- [Charging proxy](legacy/non_sumo_route_proxy_analysis/data/processed/charger_access/eligible_charger_candidates.csv)

旧pipeline summaryのstops=0/未割当と、後続stop summary・network acceptanceの39,956は異なる生成段階を示す。旧summaryのblocked snap ruleを現在のnetwork受入へ適用しない。一方、候補再生成の完全な連鎖は未確認なのでR03のGateで説明を要求する。39,956が旧日のactive建物に限られる選択偏りは、新しい母集団の研究上の限界として残す。より大きい建物母集団へ黙って置換しない。

# Pipeline Overview

工程順序は以下に固定する。Definition工程に必要な小規模fixture検査はその工程内で行い、本番計算の先行実行はしない。

1. `R01_EXISTING_STATE_AUDIT` — Existing State Audit
2. `R02_PUBLIC_STATISTICS_DEFINITION` — Public Statistics Definition
3. `R03_CANDIDATE_DELIVERY_LOCATIONS_VALIDATION` — Candidate Delivery Locations Validation
4. `R04_DEMAND_WEIGHT_DEFINITION` — Demand Weight Definition
5. `R05_CUSTOMER_SAMPLING_DEFINITION` — Customer Sampling Definition
6. `R06_CUSTOMER_DEMAND_DEFINITION` — Customer Demand Definition
7. `R07_TIME_WINDOW_DEFINITION` — Time Window Definition
8. `R08_SERVICE_TIME_DEFINITION` — Service Time Definition
9. `R09_DEPOT_DEFINITION` — Depot Definition
10. `R10_EV_DEFINITION` — EV Definition
11. `R11_CHARGING_STATION_DEFINITION` — Charging Station Definition
12. `R12_ROUTING_SPECIFICATION` — Routing Specification
13. `R13_ROUTING_COMPUTATION` — Routing Computation
14. `R14_ROUTING_VALIDATION` — Routing Validation
15. `R15_COMMON_DELIVERY_INSTANCE_DEFINITION` — Common Delivery Instance Definition
16. `R16_COMMON_HARD_CONSTRAINT_DEFINITION` — Common Hard Constraint Definition
17. `R17_ORTOOLS_FORMULATION` — OR-Tools Formulation
18. `R18_ORTOOLS_EXECUTION` — OR-Tools Execution
19. `R19_ORTOOLS_VALIDATION` — OR-Tools Validation
20. `R20_QUBO_FORMULATION` — QUBO Formulation
21. `R21_QUBO_VALIDATION` — QUBO Validation
22. `R22_ISING_CONVERSION` — Ising Conversion
23. `R23_QAOA_AER_EXECUTION` — QAOA / Qiskit Aer Execution
24. `R24_QUANTUM_SOLUTION_DECODE` — Quantum Solution Decode
25. `R25_COMMON_INDEPENDENT_VALIDATION` — Common Independent Validation
26. `R26_DEMAND_FULFILLMENT_EVALUATION` — Demand Fulfillment Evaluation
27. `R27_CLASSICAL_QUANTUM_COMPARISON` — Classical–Quantum Comparison
28. `R28_PROBLEM_SIZE_SCALING` — Problem-Size Scaling
29. `R29_EV_TECHNOLOGY_SCENARIO_EVALUATION` — EV Technology Scenario Evaluation
30. `R30_FINAL_REPRODUCIBILITY_VALIDATION` — Final Reproducibility Validation

# Common Hard Constraints

| # | 制約 | 共通の正式な意味 |
|---|---|---|
| 1 | Customer Visit Constraint | 配送するcustomerは高々1回訪問する。未充足は許容する。 |
| 2 | Depot Departure and Return Constraint | 使用車両は同一depotから出発し帰着する。 |
| 3 | Flow Conservation Constraint | nodeに入った車両は同じ車両で出る。 |
| 4 | Subtour Elimination Constraint | depotから切り離された独立cycleを禁止する。 |
| 5 | Vehicle Assignment Constraint | customerを複数車両へ重複割当しない。 |
| 6 | Capacity Constraint | 積載上限を絶対に超えない。 |
| 7 | Time Window Constraint | $e_i\le b_i\le l_i$、$b_i$はservice開始時刻。 |
| 8 | Time Propagation Constraint | travel、service、waiting、chargingを同じ時刻軸で正しく累積する。 |
| 9 | Operating-Time Constraint | 最大運行時間を設定した場合、その上限を超えない。無効の場合も共通適用flagに記録。 |
| 10 | Battery / SOC Constraint | route全体でSOCが最低許容値を下回らない。 |
| 11 | Initial / Final SOC Constraint | 出発時SOCを定義し、必要な場合は帰着時最低SOCを満たす。 |
| 12 | Charging Constraint | 充電可能地点のみ、battery capacity以下、充電量とcharger powerに対応した時間を計上する。 |
| 13 | Reachability Constraint | OSM/SUMOで実際に到達可能なarcのみ使用する。 |

R16で各意味・許容誤差・離散化と適用flagを凍結する。両手法で制約を変更しない。充電局の再訪問をcustomer高々1回制約と混同しない。全customer訪問を必須にしないため、無配送の空計画がfeasibleならDFR=0は正当な解であり、問題全体のinfeasibilityとは異なる。

# Data Classification Rules

全入力値に`classification`, `source`, `source_hash`, `unit`, `transformation`, `assumption_reason`（該当時）を付ける。分類はOBSERVED / PUBLIC_STATISTICS_DERIVED / PROXY / SYNTHETIC_CALIBRATED / ASSUMED / COMPUTEDの6種。

公表人口・世帯値はOBSERVED、集計・配賦値はPUBLIC_STATISTICS_DERIVED、住宅需要を代理する使い方はPROXYとして派生来歴をつなぐ。customer発生とTime Windowは統計較正後にSYNTHETIC_CALIBRATED、道路d/t/aはCOMPUTED、仮定service timeは理由付きASSUMED。未較正の合成値をSYNTHETIC_CALIBRATEDと偽らない。

依頼文のcatalog battery「OBSERVED / PUBLIC_SPECIFICATION」は、分類をOBSERVED、出典種別をPUBLIC_SPECIFICATIONとする（実測値という意味ではない）。分類集合を黙って増やさない。根拠不明値はUNKNOWNのissueとしてBLOCKEDにし、silently ASSUMEDにしない。

# Demand Weight Definition

$w_i$は相対sampling weightで、配送量$q_i$とは別概念である（$w_i\neq q_i$は意味の区別であり、偶然の数値一致を禁止しない）。住宅では利用可能な世帯数を人口より優先的proxyとして検討する。

候補式は $w_i=H_m/N_m$、地域宅配発生率が利用可能なら $w_i=H_m r_m/N_m$。$H_m$はmesh世帯数、$N_m$は同mesh内候補数。全candidateに$H_m$をそのまま付与しない。mesh内重み和が$H_m$（または$H_mr_m$）となることを検証する。N_m=0の需要は未配賦として記録し、隣接meshへ黙って移さない。採用式・秘匿/合算・境界処理はR02〜R04で確定し、初回は未採択。

# Customer Sampling Rules

Spatial stratification + weighted sampling + without replacement。層と割当数、algorithm、候補順序、RNG種類・version・random seedを保存する。nは入力パラメータ。OR-Tools/QAOA直接比較はsame instance_id / customer IDs / instance seed / demand / time windows / routing costs / vehicle conditions。solver固有のseedは役割別に別途保存する。

# Time Window Rules

個別住宅の実配送ログではなく、東京都市圏の日時指定・受取統計で較正したsynthetic $[e_i,l_i]$。出典、変換、窓幅、指定なし、時刻原点・単位・seedを保存する。受取時刻分布をそのまま許容窓とはしない。判定はservice開始時刻。

# Routing Baseline Rules

$d_{ij}$=road-network distance、$t_{ij}$=travel time、$a_{ij}$=reachability。全39,956完全ODを無条件に生成しない。depot/customer/chargerの必要ODと端点位置を固定する。正当な$a_{ij}=0$自体はFAILではない。経路なしを実装失敗と区別できなければFAIL。未到達のd/tはnull等の明示表現にし、0としてsolverへ投入しない。

R12〜R14ではR05〜R11の生成契約からrouting端点を固定する。R15は検証済costと他入力の最終統合・schema lockを行うため循環依存はない。既存mappingのmidpoint近似と道路offsetの扱い、異なる地点が同一edgeにある場合のzero distanceの妥当性はR12で定義する。

# Common Delivery Instance

$I_s$はinstance_id、customer IDs、depot、vehicles、charging stations、demand、time windows、service times、road distance、travel time、reachability、vehicle capacity、battery capacity、energy consumption、SOC assumptions、charging assumptions、source hashes、random seeds、schema versionを最低限含む。

加えて単位、node順、constraint version、目的優先順、生成config/code hashを固定する。R15以降の変更は新instance_idと変更記録が必要で、同じ比較対の片側だけ変更しない。energy行列はEV依存なので技術Scenarioで再計算してよいが、道路距離・旅行時間は原則固定する。

# Classical Branch

OR-Toolsを用い、Baselineは各抽出customer=1配送要求として $\max\sum_i y_i$。この1件対応は配送件数とcustomer数を一致させるための明示したモデル規約（実測主張ではない）で、複数件を導入するなら件数$c_i$と分母を再定義する。荷量を主目的に採用する実験は $\max\sum_i q_i y_i$ として両手法を同時に変更・記録する。同一充足なら第二目的の距離等を最小化する。二段階solveまたは優先順位を保証する重みの根拠をR17で示す。OR-Tools内部判定だけでfeasibilityを認定しない。

# Quantum Branch

同一$I_s$からQUBOを生成し、logical variables、binary variables、auxiliary variables、encoding、penalty formulation/coefficients、discretization、QUBO matrix、binary variable数、logical qubit countを保存する。未表現のHard Constraintは対応表に明示し、共同比較branchをBLOCKEDにする。制約を削除した問題を同一比較と称しない。

連続時間/SOCの離散化が実行可能集合を変える場合、OR-Toolsにも同じ離散化を適用した新共通instanceで比較するか、同値性が確立するまで停止する。小規模厳密fixtureはOR-Toolsの「良いincumbent」を厳密最適値と見なさず、列挙や証明済値を使う。penaltyが低energyの違反解を許しても独立validatorで除外する。

# Common Independent Validator

両手法で同じvalidator・version・入力hashを使用する。customer duplication、depot発着、flow、subtour、vehicle assignment、capacity、time window、time propagation、operating time、SOC、initial/final SOC、charging、reachabilityを経路から再計算する。Hard Constraint違反解はfeasible扱いしない。checker自体の異常はFAIL、正常checkerが量子sampleを違反と判定することは研究結果として区別する。

# Execution Status

| Status | 意味と遷移 |
|---|---|
| NOT_STARTED | 未実行。開始・終了日時を捏造しない。 |
| IN_PROGRESS | 記録した1工程だけを実行中。 |
| PASS | 工程とValidationがAcceptance Gateを満たした。 |
| RESULT_INFEASIBLE | 正常処理だがfeasible解なし。証明済infeasibleとsolver未発見をreasonで区別する。 |
| LIMIT_REACHED | 事前上限に到達。対象branch/scalingのみ停止。incumbentは保存・検証する。 |
| BLOCKED | 必須データ・仕様・根拠不足。次工程へ進まない。 |
| FAIL | 実装異常・破損・検証不整合・再現不能。次工程へ進まない。 |

UNKNOWNは監査項目の分類でありstage statusには使用しない。未実行の下流はNOT_STARTEDのまま、Issuesへ潜在blockerを記録する。

# Global Stop Rules

必須入力なし、期待hash不一致、schema不合格、必須parameterのprovenance不明、データ分類不明、Acceptance不達、validator実行不能、再現性test不合格、同seed/configで非再現、受入成果物との不整合を説明不能、のいずれかで停止する。欠落・未定義はBLOCKED、破損・誤実装・検証矛盾はFAIL。受入済network/mappingを再生成・上書きして解消しない。

# Data Stop Rules

candidate ID duplicate、invalid coordinates、negative weight、total weight=0、母集団不足、非復元抽出でduplicate customer、negative demand、invalid window/e_i>l_i、negative service time、unsupported units、required statistical source unavailable、transformation undefinedで停止する。数値はfiniteも確認する。既知欠損の規則未定義はBLOCKED、規則違反出力はFAIL。

# Routing Stop Rules

説明のないrequired OD欠落、reachable=true/pathなし、negative distance/time、異なる端点の説明不能zero distance、one-way/access/vehicle-class違反、pathとd/t不整合、network hash不一致、routing config未記録はFAIL。正当なunreachableは正常結果として保存する。

# Common Instance Stop Rules

customer必須なのに0、depotなし、車両0、payload/battery容量非正、customer/chargerのrouting mapping欠落、ID不整合、必須parameter不足は停止。出典未解決はBLOCKED、schema/生成違反はFAIL。

# OR-Tools Termination Rules

feasible解かつ独立validator合格でPASS。正常model/runで解なしはRESULT_INFEASIBLE（証明有無を記録）。time/memory上限はLIMIT_REACHEDでincumbentを保存。exception、invalid model、crash、feasibility矛盾、feasible宣言解のHard Constraint違反はFAIL。

# QUBO Stop Rules

binary/decoder mapping未定義、penalty未定義、unsupported constraint未記録、NaN/Inf、malformed QUBO、小規模同値性失敗、logical/binary対応不能でBLOCKEDまたはFAIL。未表現制約を記録するだけではGate通過にならない。R21 PASSなしでR22/R23へ進まない。

# Quantum Resource Preflight

監査環境: AMD EPYC 9684X、384 logical CPUs、physical RAM 1,622,707,548,160 bytes（約1511 GiB）。監査時MemAvailable 1,555,386,302,464 bytes。sessionとuser階層のcgroup memory.max/highはmax、cpu.maxはmax 100000。共有hostの全資源を占有可能と解釈しない。

以下は**実測性能限界ではなくASSUMEDの保守的実行予算**として初期採択する。各run直前に空きメモリ・cgroupを再確認し、より低い実上限を優先する。

| 項目 | 初期ceiling / 設定 |
|---|---|
| branch同時実行 | 1、CPU threads上限8、GPU使用なし |
| OR-Tools memory / wall-clock | 8 GiB / 300秒 per instance |
| Aer memory / wall-clock | 8 GiB / 600秒 per instance |
| Aer logical qubits | 最大26（encodingから計算しnで代用しない） |
| transpiled circuit depth / gate count | 最大10,000 / 100,000（parameter binding後の代表回路を計測） |
| QAOA p / shots | 初期p=1、shots=1024 per objective evaluation。変更は事前記録 |
| optimizer | 初期候補COBYLA、max iterations=100、objective相対変化tolerance=1e-6、no-improvement=20 evaluations |
| optimizer終端 | tolerance/no-improvementは正常収束、iteration/wall ceilingはLIMIT_REACHED。最良sampleを保存 |
| 小規模厳密検証 | binary variables<=20、wall-clock<=60秒、memory<=1 GiB。超過時は検証fixtureを縮小する変更を記録 |

初期backend方式はCPU double-precision statevectorを計画し、採用可否とAer versionはR23で確認する。状態要素数$2^Q$、state bytes=$16\times2^Q$、保守的estimated peak=$4\times16\times2^Q+1$ GiB（作業領域用の明示仮定）。Q=26でraw 1 GiB、推定5 GiB。推定が8 GiB、または直前有効空き量の25%を超える場合は起動せずLIMIT_REACHED。dense QUBO行列や回路構築のメモリも加算する。density-matrix等へ変更したら式から再審査する。

logical qubits、state size、estimated memory、circuit depth、gate countを必ず保存する。package/実行環境未準備はBLOCKED。OOM/crashまで試さず、監視と終了処理をR23で検証してから本runを開始する。

# QAOA Termination Rules

max iterations、wall-clock、convergence tolerance、no-improvement count、shotsは上表で事前定義する。実装optimizerのiterationとobjective evaluationの数え方を別記する。feasible sample=0はRESULT_INFEASIBLE、reason=NO_FEASIBLE_QAOA_SAMPLE（上限に達したrunはLIMIT_REACHEDを優先しsample結果を併記）。これは実装FAILではない。

# Problem-Size Scaling Stop Rules

R28開始前に増加するn列・seed列・合計run予算を本書へ記録する。初期nや増分を未検討の固定scenarioから流用しない。OR-Toolsは300秒/8GiB、または同branchの連続3 runでfeasible解未発見を停止閾値とする。QAOAはqubit/memory/depth/gate/wall ceiling到達でそのbranchの拡大を停止する。

依頼の$n_{\max}^{classical}$、$n_{\max}^{quantum}$は各branchの停止境界nとして保存し、last_attempted_n、largest_validated_feasible_n、first_limit_n、stop_reasonも併記する。最初の失敗nを最大成功nと誤記しない。両branch成功の同一I_sだけを直接比較する。

# Valid Research Outcomes That Must NOT Stop the Whole Pipeline

一部未配送、低DFR、DFR=0、正当なunreachable、optimality未証明のfeasible incumbent、QAOAが古典より悪い、QAOA feasible sampleなし、Aer resource limit、技術scenarioで100%未達はFAILではない。invalid解しかない場合のDFRはfeasible planのDFR=0と区別してN/Aにし、no-feasible件数を報告する。

非PASSの許可遷移: R18 RESULT_INFEASIBLE/LIMIT_REACHED → R19で証拠・incumbentを検証 → R20。R19で有効解なしを正常記録できればRESULT_INFEASIBLEとしてR20へ進めるが、R21は独立の厳密小規模fixtureが必要。R23 LIMIT_REACHED/RESULT_INFEASIBLE → R24でsampleまたは非実行理由を記録 → R25 → R26 → R27。取得できなかった解のdecodeやDFRを創作しない。R24/R25の正常な結果不在はRESULT_INFEASIBLE、R26/R27は欠測理由の正常集計でPASS可能。R28/R29は許可されたbranch・子runのみ継続。BLOCKED/FAILは例外なく先へ進まない。

# Execution Protocol After Creating the MD

最初のNOT_STARTEDかつpreconditions充足stageを1つ選びIN_PROGRESSへ記録 → Method実行 → Validation → Stop Conditions評価 → command/hash/version/resultsを記録 → status/Decision確定 → Next Allowed Stage。PASS以外は上記の明示例外のみ遷移可能。R03がBLOCKEDになったため、R04以降は開始しない。

# Execution Order Rule

Plan → Execute → Validate → Record → Decide → Nextを厳守し、複数stageを先行実行しない。監査中の複数ファイル確認はR01内部であり、R02以降の採択・生成を行ったとは扱わない。

R28/R29では必須の反復を子runとして扱い、本書内にR13〜R27の必要工程を同じ順序で記録する。変化しないGateはhash一致の再利用根拠を残す。各子runも本書のStage Record Templateを使い、並列に先行しない。新データ定義が必要なら先に変更管理を行い、該当上流Gateを開き直す。

# Change-Control Rule

変更前・変更後・理由・影響stage・既存結果への影響・再実行stageを本書へ先に記載してからcodeを変更する。既受入物はhash付きで保存し、新出力はrun_id別の分離pathとする。

| 記録 | 変更前 | 変更後 | 理由・影響・再実行 |
|---|---|---|---|
| 2026-09-09 initial plan | 旧Stage 1 Routing NEXT、TW開始/完了未確定、最大運行時間必須の表現 | 本書R01→R30、TW=service開始、operating上限は設定時適用 | 最新利用者指示。R02〜R30の今後設計へ適用、旧受入network再実行不要。 |
| 2026-09-09 governance | 複数文書に研究進行記録 | 本書だけで進行・実行を管理 | 旧仕様・機械成果物は参照証拠。本書以外のstatusから次工程を選ばない。 |
| 2026-09-09 R03 unblock attempt | R03は候補生成runner/configと候補別道路接続表が不足しBLOCKED | 受入済候補CSV・受入済networkを入力として、候補CSVを変更せず候補別SUMO edge接続表と検証manifestを新run pathへ生成する。既存受入artifactは再生成・上書きしない | R03の道路接続証拠を補完する。候補生成runner自体は新たに発見できない限り未解決のため、R03は再判定後もBLOCKEDの可能性がある。再実行stage: R03のみ |
| 2026-09-09 R13 runner restoration | R13はR12固定contractのrunner欠損でBLOCKED | 既存SUMO/sumolibを使用し、R12の`travel_time_minimizing`、delivery edge permissions、directed graph、endpoint offset、unreachable null semanticsを実装する`compute_routing.py`を固定pathへ追加する。fixture validationを新run_idへ保存し、PASS後にR13本計算を再開する | R12仕様を変更せず欠損runner blockerを解消するため。R12 artifactは変更しない。影響stage: R13のみ。R14以降は実行しない。 |
| 2026-09-09 R14 independent routing validation | R13 routing outputはrunner内validation済みだが、独立したmatrix/graph/geometry validationは未実装 | R13 outputをimmutable inputとして、独立validatorでOD completeness、endpoint coverage、schema/numeric、delivery connectivity、offset component、代表route再構成、travel-time objective、speed/asymmetry/detour diagnosticsを別run pathへ保存する。R13 outputは再生成・上書きしない | R13 routing matrixをEVRP入力として採択可能か独立に判定するため。影響stage: R14のみ。R15以降は実行しない。 |
| 2026-09-09 R14 spatial gate revision | 旧判定はoriginal endpoint座標間のstraight-line distance違反を即Critical FAILとしていた | 新判定は実際のmapped SUMO positions間の`road_distance >= straight(mapped)-epsilon`をCritical Gateとし、original coordinate比較はmapping距離を考慮したdiagnostic warningへ変更。`epsilon=1e-6 m`を数値丸め用に固定 | routing endpointと比較対象を一致させるため。R13 output、accepted network、endpoint mappingは変更しない。影響stage: R14のみ。R15以降は実行しない。 |
| 2026-09-09 R14 root-cause decomposition | R14のmapped-position Critical anomaly 44件は原因未確定 | R13 route edge sequenceを読み取り専用で分解し、SUMO declared edge length、lane length、shape polyline、edge connection gap、offset partial、internal edge、CRSを正常ODと比較するroot-cause investigation artifactを追加 | 44件のFAIL原因を分類するため。R13 output、accepted network、endpoint mappingは変更しない。影響stage: R14のみ。修正はR14で行わず、R13/R12の再実行要否を記録する。 |
| 2026-09-09 network geometry/length re-acceptance scope | accepted networkのtopology/connectivity、stop mapping、delivery access、routing geometry/lengthを単一の受入範囲として扱っていた | topology/connectivity、39,956 stop mapping、delivery access、one-way/permissionは既存受入を保持し、routing distance用geometry/declared-length consistencyだけを新runで再検証・修正する。旧accepted networkとR13 outputは不変。 | R14 root-causeで44件がnetwork geometry/length inconsistencyと分類されたため。新networkが全受入条件を満たした場合だけauthorityを更新し、R12/R13/R14の再実行は今回行わない。 |
| 2026-09-09 R12 V18 re-specification | R12 endpoint/OD/configはV17 accepted network hash `4625...40f`を参照 | V18 authority/hash `460554...51b2`でendpoint mapping・offset範囲・132 directed OD・schema・R13 command contractを新runへ再固定。旧R12 artifactは保持し、R13本番計算は未実行。 | geometry/length再受入後のrouting入力を固定するため。影響stage: R12のみ。R13以降は今回実行しない。 |
| 2026-09-09 R16 charger revisit resolution | chargerはcustomer visit制約の対象外だが、複数回訪問の許可/禁止が未定義でR16 BLOCKED | charger複数回訪問を許可し、各訪問を独立charging eventとして扱う。effective power 70 kW、各event 30分以下、連続eventによるsession上限回避は禁止。R16では恣意的回数上限を置かず、QUBO copy上限はR20/R21へ延期。 | 利用者の明示採択により唯一のR16 blockerを解消。HC12とvalidator contractを更新しR16のみ再validation。影響stage: R16。R17以降は今回実行しない。 |
| 2026-09-09 R17 formulation boundary | R16 semanticsをOR-Toolsへ写すformulationとR18設定は未固定 | RoutingModelをnode/flow/depot/visitの骨格、CP-SAT/custom stateをSOC・charging eventの候補として仕様化し、HC mapping・R18 contract・output schemaを新run pathへ保存。charger event copy数、q_i（件数）とpayload（kg）の変換、solver詳細設定は未採択のままBLOCKED。 | R16意味論を黙って近似せず、R18実行前に未解決点を可視化するため。影響stage: R17のみ。R18以降は実行しない。 |

# 2026-09-09 R09 V18 authority closure attempt

- **Change control:** R09 artifact is V17/legacy-network based; current R15 also points to the old R09 run and a constraint placeholder. Re-map the unchanged `DEP_006` identity/coordinates/PROXY to the V18 accepted network in a new run, validate all requested mapping/topology/hash/reproducibility fields, and compare with R12/R13/R14.
- **Stop rule:** If edge ID, offset, or mapping distance differs from the currently accepted R12/R13/R14 endpoint mapping, stop with R12→R14 re-execution required; do not propagate to R15–R18. Old artifacts remain immutable and R18 is not executed.

# Execution Status Snapshot

2026-09-09 preparation record: payload model, charger event upper bound, and fixture solver configuration were fixed for R17 revalidation. R18 and later stages remain NOT_STARTED and are not executed in this turn.

R01 Existing State Audit〜R15 Common Delivery Instance DefinitionをPASSとして記録した。R03では、既存候補別道路接続表の検証結果を再利用し、git history内の候補生成source/configと入力hashを追跡して一時pathでexact regenerationを実行し、39,956候補の完全一致を確認した。R12ではfixture端点12件と必要OD132本を固定し、R13ではその全ODを実道路routingした。今回のR09 V18 authority closureにより、R15 currentとR17 currentも新runとしてPASSし、R16 semanticsは変更せず参照hashを更新した。R18は未実行、現在実行中stageなし。旧network/mapping/旧需要testsの受入を下流stageへ自動昇格させない。

authority closure前の停止工程は**R17_ORTOOLS_FORMULATION**だった。R09 V18 mappingとR12–R14比較、R15/R17 propagation、independent validationがPASSしたため、現在のauthority closure statusはPASSである。R18〜R30は未実行であり、本番用nは未採択のまま保持する。

# 2026-09-09 R09 V18 authority closure and R15→R17 propagation record

- **Scope:** R09 V18 re-mapping/revalidation and downstream hash/reference propagation only. `R18_ORTOOLS_EXECUTION` was not executed.
- **R09 V18 run:** `20260909_r09_depot_fixture_n10_v18_geometry_reaccepted`; repeat run `20260909_r09_depot_fixture_n10_v18_geometry_reaccepted_repeat` was used for deterministic reproducibility. Old V17 R09 artifacts were not overwritten.
- **R09 result:** `PASS`. DEP_006 / 京浜トラックターミナル, coordinates `139.745306, 35.586971`, `PROXY`, delivery access PASS, adopted edge `617631294`, edge length `38.346827 m`, offset `12.507432581420328 m`, mapping distance `1.4616751655855091 m`, topology PASS, network hash `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`, manifest input hashes PASS, deterministic repeat PASS. The V18 validation report is `reproducibility/outputs/traffic_simulation/demand/evrp_r09_depot/20260909_r09_depot_fixture_n10_v18_geometry_reaccepted/r09_v18_validation_report.json`.
- **V17→V18 difference:** identity, facility, coordinates, classification, edge ID, and mapping distance were preserved. Offset changed `7.496943583328211 m → 12.507432581420328 m` (`+5.010488998092117 m`); declared edge length changed `28.41 m → 38.346827 m`; network hash changed V17 `4625dbbc150cbcf72964bed0e90a8b33fe03f190ff4264aecaaf89e3aab0e40f → V18 460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`.
- **R12–R14 rerun decision:** no rerun required. Current accepted V18 R12/R13/R14 endpoint manifests already have the same edge `617631294`, offset `12.507432581420328 m`, mapping distance `1.4616751655855091 m`, coordinates, and V18 network hash. Therefore the V18 R09 mapping is substantively identical to the mapping used by accepted R12–R14.
- **R15 current run:** `20260909_r15_common_instance_fixture_n10_v18_r09_v18_authority_closed`. Existing values and semantics were preserved; R09 source changed to the V18 artifact, the formal `evrp-common-hard-constraints-v1` reference replaced the stale placeholder, and the new instance validation PASSed. New R15 `common_instance.json` SHA-256: `7ca39facf83de619db7ec37daa90409834d89b4b75bfeb4e7c501ddef94b2ac4`.
- **R16 propagation:** current constraint artifact retained without semantic modification. R16 constraint hash propagated to R17: `1b1c3132b44a542605b19f354a5d9c7464a093aa4cb23b04583ca92e0841ec67`; version remains `evrp-common-hard-constraints-v1`.
- **R17 current run:** `20260909_r17_ortools_formulation_fixture_n10_v18_r09_v18_authority_closed`. Independent validation PASSed. R15 instance hash and R16 artifact hash match exactly; HC01–HC13 mapping, HC12 `E_max(n)=n+1` with n=10 → 11 event slots, formulation semantics, payload separation, charger semantics, and solver config show no semantic drift. R18 contract remains `READY_PENDING_R18` / `R18_ONLY_NOT_EXECUTED`.
- **Current-chain stale audit:** current R09 V18, R15, R16, R17, and R18 contract contain no V17 network hash, V17 current-authority reference, superseded R09 reference, old R15 constraint placeholder, BLOCKED R16/R17 reference, stale HC12 text, or legacy payload path. Historical artifacts may retain those values but are not referenced by the current chain.
- **Closed dependency chain:** `candidate → R04 → R05 → R06 → R07 → R08 → R09 V18 → R10 → R11 → R13/R14 V18 → R15 current → R16 current → R17 current → R18 contract` is uniquely closed. R12 is the accepted V18 routing authority specification used by R13/R14; no alternate current R09/R15/R16/R17 reference remains in the chain.
- **R18 readiness:** `READY` for the next allowed execution stage, with the explicit restriction that the R18 solver has not been executed in this turn.
- **Next Allowed Stage:** `R18_ORTOOLS_EXECUTION` (only after separate explicit execution instruction; do not infer execution from this closure record).

# Stage Records

全工程で以下の21欄を使う。未実行command/hash/versionはNOT_RUN / NOT_FIXEDであり仮の実行結果ではない。Outputsは予定成果物名、正式pathは実行前に本書へ固定する。

## R01_EXISTING_STATE_AUDIT — Existing State Audit

- **Stage ID:** R01_EXISTING_STATE_AUDIT
- **Objective:** 既存成果物と受入範囲を確定する
- **Inputs:** 仕様・code・raw・tests・manifest・環境
- **Preconditions:** repositoryをread-onlyで確認できること。既存受入物を変更しない。
- **Method:** read-only棚卸し、hash照合、既存検証を実行
- **Validation:** 5分類・来歴・欠落・環境を記録し受入物が不変ことを独立検査し、実行記録に診断を残す。
- **Acceptance Criteria:** 5分類・来歴・欠落・環境を記録し受入物が不変
- **Stop Conditions:** Global Stop Rulesと当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義はBLOCKED、検証不一致・実行異常はFAIL。
- **Outputs:** 監査一覧・環境・hash台帳
- **Status:** PASS
- **Started At:** 2026-09-09T10:53:52+09:00
- **Completed At:** 2026-09-09T10:53:52+09:00
- **Commands:** 本書Audit Commands参照（実行済み）
- **Input Hashes:** 本書Input Hash Ledger参照
- **Output Hashes:** 本書自体は自己hash対象外。監査logのhashはAudit Commands参照
- **Software Versions:** 本書Environment参照
- **Results:** 既存受入を確認し、監査時点ではR02以降未実行だった。継続後にR02はPASS、R03はBLOCKEDとなった。分類と潜在blockerを記録。
- **Validation Results:** portal 6検査PASS、旧需要13 tests PASS、統計19原本hash一致、候補ID/座標監査PASS
- **Issues:** candidate再生成と住宅母集団代表性は未確認。旧summaryは生成段階が異なる。既存working treeはDIRTY
- **Decision:** 監査工程の範囲を満たすためPASS。下流の実装受入は主張しない。後続工程はR02/R03の記録に従う。
- **Next Allowed Stage:** R02_PUBLIC_STATISTICS_DEFINITION（初回タスクでは実行しない）

## R02_PUBLIC_STATISTICS_DEFINITION — Public Statistics Definition

- **Stage ID:** R02_PUBLIC_STATISTICS_DEFINITION
- **Objective:** 人口／世帯・宅配受取統計の採用契約を固定する
- **Inputs:** 国勢調査ZIP・定義書・受取調査19原本とmanifest
- **Preconditions:** 前工程 `R01_EXISTING_STATE_AUDIT` のPASSと、Inputsの存在・hash・根拠を確認する。R01の監査記録により充足。
- **Method:** 列・分母・単位・地域・年次・秘匿処理・日時指定集計を照合
- **Validation:** 採用列と変換・欠損処理・データ分類・出典hashを、定義PDF・raw manifest・XLSX/XML・ZIPで独立照合し、実行記録に診断を残す。
- **Acceptance Criteria:** 採用列と変換・欠損処理・データ分類・出典hashが全て確定
- **Stop Conditions:** Global Stop Rulesと当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義はBLOCKED、検証不一致・実行異常はFAIL。
- **Outputs:** 統計入力仕様・採用列台帳
- **Status:** PASS
- **Started At:** 2026-09-09T11:02:00+09:00
- **Completed At:** 2026-09-09T11:05:00+09:00
- **Commands:** `python` read-only ZIP/XLSX/XML/hash audit; `pdftotext -layout 03_data/raw/traffic_simulation/population/estat_2020_500m_jgd2011/T001141_definition.pdf -`
- **Input Hashes:** Census ZIP `8a8b47563ffe88ec1afb5a17b8d29ac987b40df65498bec4c2fcf1829777f67d`; receipt manifest `b218db3c37faeb0ba21ac9b0b6a92ea4fc0d07feef423db9c9c97db82da38a5e`; all 20 manifest entries hash-match (19 unique filenames; duplicate `ss515_r06a.xlsx` entry is byte-identical).
- **Output Hashes:** No separate generated file. This stage's adopted definition and column ledger are recorded in this section of `EVRP_EXECUTION_PLAN.md`; the plan file is not self-hashed.
- **Software Versions:** Python 3.11.15; standard-library `zipfile`, `xml.etree.ElementTree`, `hashlib`; `pdftotext` available.
- **Results:** 採用原本を固定した。国勢調査500mメッシュ（JGD2011）は `T001141001`（人口総数）と `T001141034`（世帯総数）を採用候補列として固定し、`T001141034`を住宅sampling weightの第一候補とする。両列は定義PDFで単位（人／世帯）を確認した。秘密処理は`HTKSYORI`/`HTKSAKI`/`GASSAN`を保持し、一般世帯の内訳列を合算先へ再配賦しない。宅配受取調査は `ss508_r06a.xlsx`（受取曜日×時間帯、単位: 件）、`ss515_r06a.xlsx`（日時指定区分、単位: 件）、`ss519_r06a.xlsx`（地域別受取頻度・再配達頻度、単位: 回/週・割合）を採用入力として固定した。ss508/ss515はTime Window較正、ss519は地域差の補助較正に使用し、個人調査の回答を大田区の実測注文へ直接同一視しない。
- **Validation Results:** Census header/XMLと定義PDFの列番号・単位一致、受取調査XLSXのタイトル・単位・カテゴリ存在を確認。選択原本はmanifest hash一致。採用値はOBSERVED（raw表）、PUBLIC_STATISTICS_DERIVED（後続の集計・変換）、PROXY（住宅需要への利用）、SYNTHETIC_CALIBRATED（後続customer/TW生成）を工程ごとに分離する。未取得の表は必須入力にしていない。PASS。
- **Issues:** 世帯数からcandidateへのmesh配賦式、境界・秘密処理の実装、宅配統計からの時間窓幅変換、地域差の適用はR04/R07で固定する。これはR02の列・出典定義未完了ではなく、後続変換の未実装事項である。
- **Decision:** 採用列、単位、調査範囲、秘密処理、データ分類、入力hashが確定したためPASS。新しい需要値・customer・Time Windowは生成していない。
- **Next Allowed Stage:** R03_CANDIDATE_DELIVERY_LOCATIONS_VALIDATION（Gate通過時のみ）

## R03_CANDIDATE_DELIVERY_LOCATIONS_VALIDATION — Candidate Delivery Locations Validation

- **Stage ID:** R03_CANDIDATE_DELIVERY_LOCATIONS_VALIDATION
- **Objective:** 39,956候補の固定と住宅proxyとしての範囲を検証する
- **Inputs:** 候補CSV・旧生成要約・PLATEAU来歴・受入mapping
- **Preconditions:** 前工程 `R02_PUBLIC_STATISTICS_DEFINITION` のPASS（明示された正常結果遷移は例外）と、Inputsの存在・hash・根拠を確認する。
- **Method:** ID/座標/CRS/道路接続を全件照合、過去active建物選択の偏りと生成手順を監査
- **Validation:** 39,956の一意ID、妥当座標、全件mapping、選択偏り・再生成可否の根拠を明記ことを独立検査し、実行記録に診断を残す。
- **Acceptance Criteria:** 39,956の一意ID、妥当座標、全件mapping、選択偏り・再生成可否の根拠を明記
- **Stop Conditions:** Global Stop Rulesと当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義はBLOCKED、検証不一致・実行異常はFAIL。
- **Outputs:** 候補集合lock・candidate validation
- **Status:** PASS
- **Started At:** 2026-09-09T12:44:00+09:00
- **Completed At:** 2026-09-09T12:56:00+09:00
- **Commands:** `git log --all --follow -- 05_src/household_parcel/run_scoped_stop_generation.py`; `git show`/`git ls-tree` read-only provenance audit; historical source/config extraction from commit `d44195360092e131584be9d936c22a5b85f97454`; temporary regeneration with `PYTHONPATH=<temporary>/05_src .conda/bin/python <temporary>/05_src/household_parcel/run_scoped_stop_generation.py`; independent CSV/hash comparison. Existing candidate-edge connection validation was not rerun.
- **Input Hashes:** current `synthetic_households.csv` `fbb7ace4fa84e927898088885db727576cf3b33490562ca43928fbd1470f69be`; current `daily_requests.csv` `4bb78cf27b2a3e9a0648cca39266cb06de4dee0789febed9cd74b61a8e4c2f99`; historical `residential_building_candidates.parquet` `d8381d02f57f502d44eeb19ed0126caa96f6f1ec5604eeae470b8a452a234f6f`; historical `plateau_buildings_all_with_chocho_points.geo.parquet` `6779656a0719bb91b9bf97513e23498d88f5bc9eacdebccfcc7d5b1b5e161fa0`; historical config `pipeline.yml` `a9c8cb4bff2b087db7e5848efafe24acfa39a2ce974722ffbfdb13a7599cd68a`; current top-down demand input `e7caeb262665ba3396834bb54e2dff296b3cbbd02af6922e906eb683829f5048`.
- **Output Hashes:** existing candidate CSV `fcfca5cb87bc482f1d98306c98823773e872f200c58ecb9090aa12985e3e80e0`; existing stop summary `9d4b087462f17897524878d15a6db842efb34f583e02c2f9b120517e1be6c47a`; temporary regenerated candidate CSV had the same `fcfca5cb87bc482f1d98306c98823773e872f200c58ecb9090aa12985e3e80e0`; temporary regenerated stop summary had the same `9d4b087462f17897524878d15a6db842efb34f583e02c2f9b120517e1be6c47a`.
- **Software Versions:** historical source commit `d44195360092e131584be9d936c22a5b85f97454`; `run_scoped_stop_generation.py` SHA-256 `67e843cacab2d81b2026fb7346897b8e8a411b9fc85e31fe4252e497c4a4abd0`; `pipelines.py` SHA-256 `4b0f87e1e9deef4dd0a0c9bdf48e6e0c9360e321d22a301251163024228a17c2`; Python 3.11.15; NumPy 2.2.5; pandas 2.2.3; GeoPandas/PyArrow environment used by the historical runner.
- **Results:** Provenance chain: Census-derived synthetic household frame and daily requests → historical accepted PLATEAU/chocho residential candidate table and representative-point table → `household_parcel.pipelines.run_scoped_stop_generation` → uniform building assignment with `housing_seed=20260830`, evaluation date `2026-01-01`, accepted mapping statuses `{matched, matched_cross_boundary}`, no capacity or nearest fallback → aggregation by `(evaluation_date, building_id)` → `building_delivery_stops_scoped.csv`. The runner records `active_buildings=39956`, `stop_count=39956`, `sumo_mapping_executed=false`, and the exact input/config hashes.
- **Validation Results:** Temporary regeneration produced 39,956 rows. `stop_id` sequence/set, `building_id` sequence/set, representative coordinates, all CSV fields, and output SHA-256 matched the existing candidate exactly. The regenerated stop summary was byte-identical. This proves exact regeneration from the recorded historical source/config and input artifacts without modifying accepted or current artifacts.
- **Issues:** The generation source/config were absent from the current checkout but were recovered from git history commit `d441953...`; the provenance depends on retaining that reachable history/ref. The cohort remains a 2026-01-01 active/mapped-building scope and is not a claim of all residential locations.
- **Decision:** PASS. R03 Acceptance Gate is satisfied; no R03 failure or blocker remains. Existing candidate-edge mapping validation remains accepted from the prior R03 run and was not duplicated.
- **Next Allowed Stage:** R04_DEMAND_WEIGHT_DEFINITION（Gate通過時のみ）

## R04_DEMAND_WEIGHT_DEFINITION — Demand Weight Definition

- **Stage ID:** R04_DEMAND_WEIGHT_DEFINITION
- **Objective:** w_iをq_iから分離し保存則を定義する
- **Inputs:** 採用世帯／人口列・候補mesh対応
- **Preconditions:** 前工程 `R03_CANDIDATE_DELIVERY_LOCATIONS_VALIDATION` のPASS（明示された正常結果遷移は例外）と、Inputsの存在・hash・根拠を確認する。
- **Method:** H_m/N_mを第一候補にmesh配賦し必要ならr_mを検討
- **Validation:** 非負・総和正、mesh別配賦保存、N_m=0/秘匿/境界処理の規則確定ことを独立検査し、実行記録に診断を残す。
- **Acceptance Criteria:** 非負・総和正、mesh別配賦保存、N_m=0/秘匿/境界処理の規則確定
- **Stop Conditions:** Global Stop Rulesと当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義はBLOCKED、検証不一致・実行異常はFAIL。
- **Outputs:** weight仕様・重み台帳
- **Status:** PASS
- **Started At:** 2026-09-09T12:58:00+09:00
- **Completed At:** 2026-09-09T13:05:00+09:00
- **Commands:** R04 demand-weight generation and validation commands recorded in the preceding R04 execution record.
- **Input Hashes:** R04 accepted inputs are recorded in the Input Hash Ledger and prior R04 execution record.
- **Output Hashes:** R04 accepted output hashes are recorded in the Input Hash Ledger and prior R04 execution record.
- **Software Versions:** Python 3.11.15; R04 generator/validator versions recorded in the prior R04 execution record.
- **Results:** `w_i=H_m/N_m` accepted for the frozen fixture; `q_i` remains separate from sampling weight.
- **Validation Results:** Nonnegative finite weights, positive total, per-mesh conservation, and n=10 fixture input contract PASS.
- **Issues:** Production estimand interpretation remains fixture-only and is not changed by R18.
- **Decision:** PASS; existing R04 artifact remains frozen.
- **Next Allowed Stage:** R05_CUSTOMER_SAMPLING_DEFINITION（Gate通過時のみ）

## R05_CUSTOMER_SAMPLING_DEFINITION — Customer Sampling Definition

- **Stage ID:** R05_CUSTOMER_SAMPLING_DEFINITION
- **Objective:** 層化・重み付き非復元抽出を定義する
- **Inputs:** 候補lock・weights・空間層
- **Preconditions:** 前工程 `R04_DEMAND_WEIGHT_DEFINITION` のPASS（明示された正常結果遷移は例外）と、Inputsの存在・hash・根拠を確認する。
- **Method:** 層別割当・抽出algorithm・seed・n引数を固定し小規模再現検査
- **Validation:** n件・重複なし・母集団内・同一seed/configで一致・層の保持ことを独立検査し、実行記録に診断を残す。
- **Acceptance Criteria:** n件・重複なし・母集団内・同一seed/configで一致・層の保持
- **Stop Conditions:** Global Stop Rulesと当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義はBLOCKED、検証不一致・実行異常はFAIL。
- **Outputs:** sampling仕様・検証用configuration
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **Commands:** NOT_RUN — 実行前に採択command・cwd・出力pathを記録
- **Input Hashes:** NOT_FIXED — 実行前にlock
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **Issues:** 未実行。Acceptance Criteriaの未固定項目を実行開始時に解消し、解消不能ならBLOCKED
- **Decision:** NOT_RUN
- **Next Allowed Stage:** R06_CUSTOMER_DEMAND_DEFINITION（Gate通過時のみ）

## R06_CUSTOMER_DEMAND_DEFINITION — Customer Demand Definition

- **Stage ID:** R06_CUSTOMER_DEMAND_DEFINITION
- **Objective:** 抽出customerの配送要求を定義する
- **Inputs:** sampling仕様・宅配受取統計
- **Preconditions:** 前工程 `R05_CUSTOMER_SAMPLING_DEFINITION` のPASS（明示された正常結果遷移は例外）と、Inputsの存在・hash・根拠を確認する。
- **Method:** Baselineは1customerに1配送要求を置く単位契約を明示し追加q_iを別管理
- **Validation:** 配送件数と荷物量とw_iを区別、非負、全customerに要求、分母を固定ことを独立検査し、実行記録に診断を残す。
- **Acceptance Criteria:** 配送件数と荷物量とw_iを区別、非負、全customerに要求、分母を固定
- **Stop Conditions:** Global Stop Rulesと当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義はBLOCKED、検証不一致・実行異常はFAIL。
- **Outputs:** demand仕様・生成契約
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **Commands:** NOT_RUN — 実行前に採択command・cwd・出力pathを記録
- **Input Hashes:** NOT_FIXED — 実行前にlock
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **Issues:** 未実行。Acceptance Criteriaの未固定項目を実行開始時に解消し、解消不能ならBLOCKED
- **Decision:** NOT_RUN
- **Next Allowed Stage:** R07_TIME_WINDOW_DEFINITION（Gate通過時のみ）

## R07_TIME_WINDOW_DEFINITION — Time Window Definition

- **Stage ID:** R07_TIME_WINDOW_DEFINITION
- **Objective:** 統計較正したsynthetic時間窓を定義する
- **Inputs:** 受取時間帯・日時指定統計・customer生成契約
- **Preconditions:** 前工程 `R06_CUSTOMER_DEMAND_DEFINITION` のPASS（明示された正常結果遷移は例外）と、Inputsの存在・hash・根拠を確認する。
- **Method:** 指定割合と時間帯から窓を生成する変換・窓幅・指定なし・seedを固定
- **Validation:** e_i<=l_i、service開始を判定、単位・時刻原点・分布較正診断と再現性ことを独立検査し、実行記録に診断を残す。
- **Acceptance Criteria:** e_i<=l_i、service開始を判定、単位・時刻原点・分布較正診断と再現性
- **Stop Conditions:** Global Stop Rulesと当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義はBLOCKED、検証不一致・実行異常はFAIL。
- **Outputs:** time-window仕様・較正検証
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **Commands:** NOT_RUN — 実行前に採択command・cwd・出力pathを記録
- **Input Hashes:** NOT_FIXED — 実行前にlock
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **Issues:** 未実行。Acceptance Criteriaの未固定項目を実行開始時に解消し、解消不能ならBLOCKED
- **Decision:** NOT_RUN
- **Next Allowed Stage:** R08_SERVICE_TIME_DEFINITION（Gate通過時のみ）

## R08_SERVICE_TIME_DEFINITION — Service Time Definition

- **Stage ID:** R08_SERVICE_TIME_DEFINITION
- **Objective:** 住宅での配送作業時間を定義する
- **Inputs:** 作業時間の根拠または明示仮定
- **Preconditions:** 前工程 `R07_TIME_WINDOW_DEFINITION` のPASS（明示された正常結果遷移は例外）と、Inputsの存在・hash・根拠を確認する。
- **Method:** s_iの単位・値/分布・分類・seedを設定
- **Validation:** 有限かつ非負、出典またはASSUMED採択理由、再現可能ことを独立検査し、実行記録に診断を残す。
- **Acceptance Criteria:** 有限かつ非負、出典またはASSUMED採択理由、再現可能
- **Stop Conditions:** Global Stop Rulesと当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義はBLOCKED、検証不一致・実行異常はFAIL。
- **Outputs:** service-time仕様
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **Commands:** NOT_RUN — 実行前に採択command・cwd・出力pathを記録
- **Input Hashes:** NOT_FIXED — 実行前にlock
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **Issues:** 未実行。Acceptance Criteriaの未固定項目を実行開始時に解消し、解消不能ならBLOCKED
- **Decision:** NOT_RUN
- **Next Allowed Stage:** R09_DEPOT_DEFINITION（Gate通過時のみ）

## R09_DEPOT_DEFINITION — Depot Definition

- **Stage ID:** R09_DEPOT_DEFINITION
- **Objective:** 単一depotを固定する
- **Inputs:** 物流施設proxy候補・受入道路網
- **Preconditions:** 前工程 `R08_SERVICE_TIME_DEFINITION` のPASS（明示された正常結果遷移は例外）と、Inputsの存在・hash・根拠を確認する。
- **Method:** 候補範囲・位置・通行可否を検討し1拠点を選択
- **Validation:** 位置と道路接続が有効、同じn/seed比較で原則同一、proxy明記ことを独立検査し、実行記録に診断を残す。
- **Acceptance Criteria:** 位置と道路接続が有効、同じn/seed比較で原則同一、proxy明記
- **Stop Conditions:** Global Stop Rulesと当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義はBLOCKED、検証不一致・実行異常はFAIL。
- **Outputs:** depot lock
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **Commands:** NOT_RUN — 実行前に採択command・cwd・出力pathを記録
- **Input Hashes:** NOT_FIXED — 実行前にlock
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **Issues:** 未実行。Acceptance Criteriaの未固定項目を実行開始時に解消し、解消不能ならBLOCKED
- **Decision:** NOT_RUN
- **Next Allowed Stage:** R10_EV_DEFINITION（Gate通過時のみ）

## R10_EV_DEFINITION — EV Definition

- **Stage ID:** R10_EV_DEFINITION
- **Objective:** 車両・容量・energy・SOCを定義する
- **Inputs:** managed vehicle profile・EV仕様表・出典
- **Preconditions:** 前工程 `R09_DEPOT_DEFINITION` のPASS（明示された正常結果遷移は例外）と、Inputsの存在・hash・根拠を確認する。
- **Method:** fleet・payload・battery・消費率・usable/initial/final SOC・運行時間適用を固定
- **Validation:** 正容量、単位整合、SOC境界とenergy計算法・全値の根拠、車種権限を固定ことを独立検査し、実行記録に診断を残す。
- **Acceptance Criteria:** 正容量、単位整合、SOC境界とenergy計算法・全値の根拠、車種権限を固定
- **Stop Conditions:** Global Stop Rulesと当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義はBLOCKED、検証不一致・実行異常はFAIL。
- **Outputs:** vehicle仕様・energy契約
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **Commands:** NOT_RUN — 実行前に採択command・cwd・出力pathを記録
- **Input Hashes:** NOT_FIXED — 実行前にlock
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **Issues:** 未実行。Acceptance Criteriaの未固定項目を実行開始時に解消し、解消不能ならBLOCKED
- **Decision:** NOT_RUN
- **Next Allowed Stage:** R11_CHARGING_STATION_DEFINITION（Gate通過時のみ）

## R11_CHARGING_STATION_DEFINITION — Charging Station Definition

- **Stage ID:** R11_CHARGING_STATION_DEFINITION
- **Objective:** 利用可能な充電条件を定義する
- **Inputs:** 充電proxy資料・EV互換性・道路網
- **Preconditions:** 前工程 `R10_EV_DEFINITION` のPASS（明示された正常結果遷移は例外）と、Inputsの存在・hash・根拠を確認する。
- **Method:** 位置/出力/connector/利用時間/アクセスと充電量→時間の式を確認
- **Validation:** 採用局の必須項目とmappingが完全、unknownを利用可能と見なさないことを独立検査し、実行記録に診断を残す。
- **Acceptance Criteria:** 採用局の必須項目とmappingが完全、unknownを利用可能と見なさない
- **Stop Conditions:** Global Stop Rulesと当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義はBLOCKED、検証不一致・実行異常はFAIL。
- **Outputs:** charger集合・充電モデル
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **Commands:** NOT_RUN — 実行前に採択command・cwd・出力pathを記録
- **Input Hashes:** NOT_FIXED — 実行前にlock
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **Issues:** 未実行。Acceptance Criteriaの未固定項目を実行開始時に解消し、解消不能ならBLOCKED
- **Decision:** NOT_RUN
- **Next Allowed Stage:** R12_ROUTING_SPECIFICATION（Gate通過時のみ）

## R12_ROUTING_SPECIFICATION — Routing Specification

- **Stage ID:** R12_ROUTING_SPECIFICATION
- **Objective:** 必要ODと経路意味論を先に固定する
- **Inputs:** candidate/customer生成契約・depot・EV・charger・受入network
- **Preconditions:** 前工程 `R11_CHARGING_STATION_DEFINITION` のPASS（明示された正常結果遷移は例外）と、Inputsの存在・hash・根拠を確認する。
- **Method:** 選択端点集合・有向arc・出発/到着offset・車種・cost・異常閾値を定義
- **Validation:** d/t/aの単位・必要OD一覧・unreachable判別・hash/version/command契約が完備ことを独立検査し、実行記録に診断を残す。
- **Acceptance Criteria:** d/t/aの単位・必要OD一覧・unreachable判別・hash/version/command契約が完備
- **Stop Conditions:** Global Stop Rulesと当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義はBLOCKED、検証不一致・実行異常はFAIL。
- **Outputs:** routing仕様・OD manifest
- **Status:** PASS
- **Started At:** 2026-09-09T17:45:00+09:00
- **Completed At:** 2026-09-09T17:49:00+09:00
- **Commands:** `.conda/bin/python 05_src/traffic_simulation/evrp_r12_routing/define_routing_specification.py --run-id 20260909_r12_routing_spec_fixture_n10_v18_geometry_reaccepted --network-authority reproducibility/config/traffic_simulation/current_network_completion_authority_v18_geometry_reaccepted.yml --network reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_3_geometry_reacceptance/three_tier.net.xml --expected-network-hash 460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`。独立validation: `.conda/bin/python 05_src/traffic_simulation/evrp_r12_routing/validate_routing_specification_v18.py --run-dir reproducibility/outputs/traffic_simulation/demand/evrp_r12_routing/20260909_r12_routing_spec_fixture_n10_v18_geometry_reaccepted --authority reproducibility/config/traffic_simulation/current_network_completion_authority_v18_geometry_reaccepted.yml`。R13本番計算は実行していない。
- **Input Hashes:** V18 network `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`; V18 authority `29ee5fe979c85eb1d11b0f5a55f33782b7b5b08fcf09b48d2fad3e47c0ae33ee`; R09 depot `3b7b168f1ae9159234f812cb476c0721364554e03db7ebadfd2b155295b40eeb`; R05 customer IDs `a3307ac024c639b2690b120d11cd163abbbf83820428d090abb09fa18b0e4d0e`; R04 weights `e7694dd7461ae048d1de9289408faa91f6d3924defaf06b15b09341e38842ad8`; R11 revision manifest `f60bad51c7a6ad8936ce5094f7821da2df965cdc050fc9bba3c9ce07f2592bf9`。
- **Output Hashes:** endpoint manifest `9f0d0cdd289fad73c696e7a3efe56af7bb4385fa5f268cb5db6e6d8844335913`; OD manifest `bee697860ab422d0eacdc8ac4d3019bb3caf1673bcbd2f31ae903e977f530b74`; config `12c32ada0b3d615e8acdc32c033138fb309ccf434d3b3f3aaaea3c05b40fb5c8`; schema `7ef7a66cd221376b7f3e7588934439cd00164721283d2eaca540cc4b9428544b`; generator validation `a38c1fec8b106ceb620511534a7afdd359d8e3407e1db9d170ae34c796e5be70`; independent V18 validation `fe645a7a432e87072e67d56e48c87b6623ba8c30e6d126f6fe7a5b1cdca30e52`; manifest `f6194ec010e1cd97fbcfd9e97b080bfe9a7bb46fdfcc5112cbc8c1d1eb55fc3e`。
- **Software Versions:** Python 3.11.15、SUMO/sumolib 1.24.0。R12は仕様固定のみで、本番routing計算を実行していない。
- **Results:** V18 authorityに整合する新runを生成した。endpoint 12件（depot 1、customer 10、charger 1）、必要OD 132本、self-loop除外、directed、`travel_time_minimizing`、distance[m]、travel time[s]、reachable[boolean]、unreachable null semantics、offset semantics、V18 network hash、R13 command contractを再固定した。V18では全endpointのedge IDが有効でdelivery permissionを持ち、全offsetがedge length範囲内だった。
- **Validation Results:** 独立validatorでauthority status、network hash、endpoint uniqueness/role、V18 edge mapping、delivery access、offset範囲、finite値、OD completeness、originあたり11本、units/null semantics、offset semantics、objective、unreachable/failure distinction、R13 contractを全てPASS。R13本番artifact `routing_arcs.csv`は存在せず、R13未実行を確認した。
- **Issues:** なし。旧V17 R12 artifactは保持し、V18 runを新pathへ分離した。本番problem-size nは未採択のまま。R13は次工程として未実行。
- **Decision:** V18 authorityとの整合、manifest、schema、command contract、独立validationが全てPASSしたため、V18向けR12をPASSとする。
- **Next Allowed Stage:** R13_ROUTING_COMPUTATION（V18 authorityでのGate通過時のみ）

## R13_ROUTING_COMPUTATION — Routing Computation

- **Stage ID:** R13_ROUTING_COMPUTATION
- **Objective:** 必要ODの実道路costを計算する
- **Inputs:** 採択routing仕様・端点・network lock
- **Preconditions:** 前工程 `R12_ROUTING_SPECIFICATION` のPASS（明示された正常結果遷移は例外）と、Inputsの存在・hash・根拠を確認する。
- **Method:** 分離出力で必要ODのみ計算しpathと診断を保存
- **Validation:** 全必要ODにpathまたは根拠あるunreachable、実行例外なしことを独立検査し、実行記録に診断を残す。
- **Acceptance Criteria:** 全必要ODにpathまたは根拠あるunreachable、実行例外なし
- **Stop Conditions:** Global Stop Rulesと当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義はBLOCKED、検証不一致・実行異常はFAIL。
- **Outputs:** d_ij/t_ij/a_ij・paths・run manifest
- **Status:** PASS
- **Started At:** 2026-09-09T18:01:49+09:00
- **Completed At:** 2026-09-09T18:04:30+09:00
- **Commands:** preflight（R12 V18 artifact、manifest/hash、network hash、endpoint/OD、role、vehicle class、objectiveをread-only検査）; fixture: `.conda/bin/python 05_src/traffic_simulation/evrp_r13_routing/validate_routing_fixture.py --output reproducibility/outputs/traffic_simulation/demand/evrp_r13_routing/20260909_r13_routing_fixture_n10_v18_geometry_reaccepted/runner_fixture_validation.json`; production: `.conda/bin/python 05_src/traffic_simulation/evrp_r13_routing/compute_routing.py --config reproducibility/outputs/traffic_simulation/demand/evrp_r12_routing/20260909_r12_routing_spec_fixture_n10_v18_geometry_reaccepted/r12_routing_config.json --output-dir reproducibility/outputs/traffic_simulation/demand/evrp_r13_routing/20260909_r13_routing_fixture_n10_v18_geometry_reaccepted`; basic: `.conda/bin/python 05_src/traffic_simulation/evrp_r13_routing/validate_routing_basic.py --r12-dir reproducibility/outputs/traffic_simulation/demand/evrp_r12_routing/20260909_r12_routing_spec_fixture_n10_v18_geometry_reaccepted --r13-dir reproducibility/outputs/traffic_simulation/demand/evrp_r13_routing/20260909_r13_routing_fixture_n10_v18_geometry_reaccepted`。
- **Input Hashes:** endpoint manifest `9f0d0cdd289fad73c696e7a3efe56af7bb4385fa5f268cb5db6e6d8844335913`; OD manifest `bee697860ab422d0eacdc8ac4d3019bb3caf1673bcbd2f31ae903e977f530b74`; R12 config `12c32ada0b3d615e8acdc32c033138fb309ccf434d3b3f3aaaea3c05b40fb5c8`; output schema `7ef7a66cd221376b7f3e7588934439cd00164721283d2eaca540cc4b9428544b`; V18 network `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`; V18 authority `29ee5fe979c85eb1d11b0f5a55f33782b7b5b08fcf09b48d2fad3e47c0ae33ee`。
- **Output Hashes:** routing arcs `29c1a68a71838bb44629cbf4bf7230a0492e9484c0a97d0c2fb2e370f2ca2ec1`; execution log `8ce3c0747d7e793d5d813f9c6ee0db417772acfd134342691ecab188f6763e77`; basic validation `c084785bdf642ab02e3050453752625a4f9a2c34a80bf8aa8b1611ee97424a15`; summary `1ee5873dbdcdc08da568b3f86981acbf0cbef0cb3ae5f2c0c1e77992e8642294`; manifest `b3367f49e8fee9f9971cdf88eb426b58df7f04b477d2c77e78b4f5a7224b601e`; fixture `d9739978b2b15d2e75f5635c7c3771c474c6bb42d3add6d1914a475fc19504ed`。
- **Software Versions:** Python 3.11.15、SUMO/sumolib 1.24.0。新規外部dependencyは導入していない。runner `compute_routing.py` hash `13c89a026363256f60900488b9c77808a207f2b4d9546d4158d266ea50d10f54`、basic validator hash `1540b6f3bddcbb0ff047bfe8171f8e027a4214c154c53bdac5abd3da6264588b`。
- **Results:** V18専用runで、R12固定の12 endpoint・132 directed ODのみを実行。generated 132、reachable 132、unreachable 0、routing exception 0。distanceはm、travel timeはs、selected pathは`travel_time_minimizing`、offset componentsとpath referenceを保存した。distance統計: min 603.8403355348、max 11361.9776978131、mean 5503.4970219848、median 5666.0612792584 m。travel time統計: min 93.8332519304、max 771.3335528117、mean 429.4312502215、median 426.7058239354 s。
- **Validation Results:** endpoint/role、OD完全性、self-loop 0、duplicate 0、missing/unexpected 0、schema、network hash、vehicle class、objective、reachable値、path edge存在・delivery permission、finite/nonnegativeをR13基本検証としてPASS。R14のgeometry下限・path再計算・offset独立検証は未実行。
- **Issues:** なし。R13は`n=10` fixtureで実行。本番problem-size nは未採択であり、R13 fixture runと区別して管理する。
- **Decision:** preflight、fixture validation、実道路routing、R13基本検証、成果物保存を全てPASSしたためR13 PASS。旧R13 artifactは変更していない。
- **Next Allowed Stage:** R14_ROUTING_VALIDATION（今回未実行）

## R14_ROUTING_VALIDATION — Routing Validation

- **Stage ID:** R14_ROUTING_VALIDATION
- **Objective:** routingを独立検証する
- **Inputs:** OD manifest・paths・d/t/a・SUMO network
- **Preconditions:** 前工程 `R13_ROUTING_COMPUTATION` のPASS（明示された正常結果遷移は例外）と、Inputsの存在・hash・根拠を確認する。
- **Method:** OD完全性、方向/進入/車種、offset、距離時間再計算・異常値・再現を照合
- **Validation:** routing停止条件が0件、unreachableと実装failureを識別ことを独立検査し、実行記録に診断を残す。
- **Acceptance Criteria:** routing停止条件が0件、unreachableと実装failureを識別
- **Stop Conditions:** Global Stop Rulesと当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義はBLOCKED、検証不一致・実行異常はFAIL。
- **Outputs:** routing validation・accepted routing lock
- **Status:** PASS
- **Started At:** 2026-09-09T18:18:00+09:00
- **Completed At:** 2026-09-09T18:24:00+09:00
- **Commands:** independent validation: `.conda/bin/python 05_src/traffic_simulation/evrp_r14_routing_validation/validate_routing.py --r12-dir reproducibility/outputs/traffic_simulation/demand/evrp_r12_routing/20260909_r12_routing_spec_fixture_n10_v18_geometry_reaccepted --r13-dir reproducibility/outputs/traffic_simulation/demand/evrp_r13_routing/20260909_r13_routing_fixture_n10_v18_geometry_reaccepted --output-dir reproducibility/outputs/traffic_simulation/demand/evrp_r14_routing_validation/20260909_r14_routing_validation_fixture_n10_v18_geometry_reaccepted`; route geometry/length: `.conda/bin/python 05_src/traffic_simulation/evrp_r14_routing_validation/validate_v18_route_geometry.py --network reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_3_geometry_reacceptance/three_tier.net.xml --r13-dir reproducibility/outputs/traffic_simulation/demand/evrp_r13_routing/20260909_r13_routing_fixture_n10_v18_geometry_reaccepted --output reproducibility/outputs/traffic_simulation/demand/evrp_r14_routing_validation/20260909_r14_routing_validation_fixture_n10_v18_geometry_reaccepted/v18_route_geometry_length_validation.json`。R13 output、V18 network、endpoint mappingは読み取り専用。
- **Input Hashes:** R13 routing output `29c1a68a71838bb44629cbf4bf7230a0492e9484c0a97d0c2fb2e370f2ca2ec1`; R12 endpoint manifest `9f0d0cdd289fad73c696e7a3efe56af7bb4385fa5f268cb5db6e6d8844335913`; R12 OD manifest `bee697860ab422d0eacdc8ac4d3019bb3caf1673bcbd2f31ae903e977f530b74`; V18 network `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`; V18 authority `29ee5fe979c85eb1d11b0f5a55f33782b7b5b08fcf09b48d2fad3e47c0ae33ee`。
- **Output Hashes:** validation report `489516593b6c125bfd32a8b5c10572d59c1d1da11bd7d6adf4796e6e7bb57ea2`; statistics `469387eee1afb79cd28d198be4063a6bacbb86f6cf885b6bcca35fb101c448ea`; anomaly report `b21182697b7f6b9447cea4e0d6b7ccc84cdffd0c9bc3d426192a54c60f7aec38`; spatial diagnostics `548f56bf17d334c6fe5e45774e72c89ad2a204943d874eadd44bb04abdc4d1c6`; geometry/length `d50799973ceb576be6139f1af46ef92cc3e988b6599839b1233635081fabcc17`; manifest `9218f4bfc8139ef910a67a7bc62486d0a184497b8f047a0c6f8642a2ea6fa2cf`。
- **Software Versions:** Python 3.11.15、SUMO/sumolib 1.24.0。R14 validator `validate_routing.py` hash `88e7092f003667287e581ee8cdaf2decef61de4c75870202cc2821935aec4beb`、geometry validator `validate_v18_route_geometry.py` hash `51ddb9e15f4d71580251eefa752487abff93b7b3e2dc64dd0a8896eeabde2f7a`。R13 runnerは変更していない。
- **Results:** V18 R13の132/132 ODを独立検証。endpoint coverageは各endpointがorigin/destination各11件、reachable 132、unreachable 0。R13 output hash、network hash、delivery access、one-way edge graph、schema、numeric、offset、path/distance/time、travel-time objectiveをPASSした。
- **Validation Results:** mapped-position Critical Gate `road_distance >= straight(mapped)-1e-6m`は132件中132件PASS、Critical anomaly 0件。original-coordinate diagnostic warning 0件。R13 pathの独立distance/time再計算差は全件許容誤差内、partial edge二重計上0件、same-edge処理とspot route再構成PASS。V18 route上の4,507 laneについてdeclared lengthとshape polylineの不整合0件、lane connection geometry gap 0件。代表edge shape endpoint gapは5件（最大2.359984m）だが、multi-lane代表shapeとlane connection geometryの差による診断値でCritical Gateには使用しない。速度・detour・非対称性は診断として保存し、critical anomalyなし。
- **Issues:** lane connection recordがないedge-level遷移18件を診断記録した。これはR13固定contractのedge-level graphで生成された遷移で、実接続geometry gapやdelivery permission違反としては検出されなかった。R13 output、V18 network、endpoint mappingは変更していない。
- **Decision:** 旧V17の44件はV18でmapped-position Critical anomaly 0件、original-coordinate warning 0件へ解消。R14の全Acceptance Criteriaを満たしたためPASS。
- **Next Allowed Stage:** R15_COMMON_DELIVERY_INSTANCE_DEFINITION（今回未実行）

## R15_COMMON_DELIVERY_INSTANCE_DEFINITION — Common Delivery Instance Definition

- **Stage ID:** R15_COMMON_DELIVERY_INSTANCE_DEFINITION
- **Objective:** solver非依存I_sを定義・生成・凍結する
- **Inputs:** 採択需要/窓/service/depot/EV/charger・検証済routing
- **Preconditions:** 前工程 `R14_ROUTING_VALIDATION` のPASS（明示された正常結果遷移は例外）と、Inputsの存在・hash・根拠を確認する。
- **Method:** schema、ID順序、生成config、source hashes、seedを統合
- **Validation:** 必須field充足・schema合格・全ID対応・同一seed再生成一致ことを独立検査し、実行記録に診断を残す。
- **Acceptance Criteria:** 必須field充足・schema合格・全ID対応・同一seed再生成一致
- **Stop Conditions:** Global Stop Rulesと当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義はBLOCKED、検証不一致・実行異常はFAIL。
- **Outputs:** instance schema・I_s・hash lock
- **Status:** PASS
- **Started At:** 2026-09-09T18:25:00+09:00
- **Completed At:** 2026-09-09T18:28:40+09:00
- **Commands:** `.conda/bin/python 05_src/traffic_simulation/evrp_r15_instance/build_common_instance.py --output-dir reproducibility/outputs/traffic_simulation/demand/evrp_r15_common_instance/20260909_r15_common_instance_fixture_n10_v18`; `.conda/bin/python 05_src/traffic_simulation/evrp_r15_instance/validate_common_instance.py --instance-dir reproducibility/outputs/traffic_simulation/demand/evrp_r15_common_instance/20260909_r15_common_instance_fixture_n10_v18`; 同一入力で `/tmp/evrp_r15_repro_check_20260909`へ再生成し`common_instance.json` hashを比較。
- **Input Hashes:** R05 customer IDs `a3307ac024c639b2690b120d11cd163abbbf83820428d090abb09fa18b0e4d0e`; R06 demand `9c321d63d5c611d0f348f8e9eb6c5581e4db9dbefa3e4db9e9c747ebde746825`; R07 windows `4915372ccc64131631cc1bcd0850b823e2c916663d869e93dd76622e7d4aa6c3`; R08 service `3d0ac325e0c5bf7686fc8501d9bfaa207a77a4ddc77527b6ea4b014508a2d6e2`; R09 depot `3b7b168f1ae9159234f812cb476c0721364554e03db7ebadfd2b155295b40eeb`; R10 vehicle `53b1122a76f2f65661991d9f4b0b9091efa93108b8a8763b4e079c140a56f96c`; R11 station `3077eb1ed6d41ae16c5c7262706755a3dd042f4cb822a76b445cb7a1484a0c72`; R12 endpoint `9f0d0cdd289fad73c696e7a3efe56af7bb4385fa5f268cb5db6e6d8844335913`; R12 OD `bee697860ab422d0eacdc8ac4d3019bb3caf1673bcbd2f31ae903e977f530b74`; R13 routing `29c1a68a71838bb44629cbf4bf7230a0492e9484c0a97d0c2fb2e370f2ca2ec1`; R14 validation `489516593b6c125bfd32a8b5c10572d59c1d1da11bd7d6adf4796e6e7bb57ea2`; V18 network `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`。
- **Output Hashes:** common instance `1d01afb5b871dc0cfdbeda701f5853827e0d24bb126d86d958644cb36ec5f1ca`; node mapping `a9ab24fab2129b2c7fb8203adcfb9c123c9d697605292f0493265c420143954c`; provenance ledger `9f8d3206991dd6eaeb08ad1b21f62926dd09f4ece85c6ae8857a21c0bb2f0493`; config `6a57af71934a9db4f6718f3ae2cd59ec791f9ae3eb8c33eb0a361ae8a74971de`; validation `5a615f02814cf4c15e81a14fa7201eebf66dcba82fbecabe57abd8ded6a359e7`; manifest `33aba4e492fa96103b7516472ec9d1f8b7433f5752c632096d903cc705cda19c`。
- **Software Versions:** Python 3.11.15。builder `build_common_instance.py`、validator `validate_common_instance.py`、NumPy/solver/QUBOは未使用。builder code hashはmanifestに保存。
- **Results:** `instance_id=evrp_fixture_n10_v18_common_20260909`としてfixture n=10を固定。nodeは12件（depot 1、customer 10、charger 1）、vehicle 1、required/validated routing OD 132/132。R13 accepted routingを再計算せず取り込み、V18 authority/hashを保持した。R10のinitial SOC 1.00、minimum SOC 0.20、operational available energy 32.8 kWh、R11 effective charging power 70 kW、session limit 30分、external operator accessのASSUMEDを保持した。
- **Validation Results:** customer ID重複0、全customerのdemand/TW/service存在、node/index一意、endpoint mapping存在、OD 132/132、distance/time/reachability整合、EV/SOC/charging値、source hash/provenance、単位をPASS。同一入力の一時再生成でcommon instance hash一致（`1d01afb5b871dc0cfdbeda701f5853827e0d24bb126d86d958644cb36ec5f1ca`）。
- **Issues:** 本番problem-size nは未採択。`constraint_version`はR16参照placeholder、`objective_priority`はR17参照placeholderとして保存した。R16以降は実行していない。
- **Decision:** R05〜R14の確定成果物を同一node/index/orderとprovenanceで統合し、common instanceのAcceptance Criteriaを満たしたためR15 PASS。既存R05〜R14 artifactは変更していない。
- **Next Allowed Stage:** R16_COMMON_HARD_CONSTRAINT_DEFINITION（今回未実行）

## R16_COMMON_HARD_CONSTRAINT_DEFINITION — Common Hard Constraint Definition

- **Stage ID:** R16_COMMON_HARD_CONSTRAINT_DEFINITION
- **Objective:** 13制約の共通意味論と独立checkerを固定する
- **Inputs:** I_s・本書の13制約
- **Preconditions:** 前工程 `R15_COMMON_DELIVERY_INSTANCE_DEFINITION` のPASS（明示された正常結果遷移は例外）と、Inputsの存在・hash・根拠を確認する。
- **Method:** 時間/SOC遷移・許容誤差・適用flagを定式化しvalidatorと手計算fixtureを用意
- **Validation:** 各制約の正常/違反fixture、複数車両/充電/subtourの検査、solver非依存ことを独立検査し、実行記録に診断を残す。
- **Acceptance Criteria:** 各制約の正常/違反fixture、複数車両/充電/subtourの検査、solver非依存
- **Stop Conditions:** Global Stop Rulesと当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義はBLOCKED、検証不一致・実行異常はFAIL。
- **Outputs:** 制約仕様・共通validator・fixture結果
- **Status:** PASS
- **Started At:** 2026-09-09T18:39:00+09:00
- **Completed At:** 2026-09-09T18:40:00+09:00
- **Commands:** `.conda/bin/python 05_src/traffic_simulation/evrp_r16_constraints/build_constraint_spec.py --instance reproducibility/outputs/traffic_simulation/demand/evrp_r15_common_instance/20260909_r15_common_instance_fixture_n10_v18 --output-dir reproducibility/outputs/traffic_simulation/demand/evrp_r16_constraints/20260909_r16_common_hard_constraints_v1_fixture_n10_charger_revisit_resolved`; `.conda/bin/python 05_src/traffic_simulation/evrp_r16_constraints/validate_constraint_spec.py --spec-dir reproducibility/outputs/traffic_simulation/demand/evrp_r16_constraints/20260909_r16_common_hard_constraints_v1_fixture_n10_charger_revisit_resolved`。
- **Input Hashes:** R15 common instance `1d01afb5b871dc0cfdbeda701f5853827e0d24bb126d86d958644cb36ec5f1ca`。
- **Output Hashes:** constraint spec `f5532f521b00855eeda7e74286c76e169ad4b5ac890ea093402d92f5c5a90313`; constraint config `809fa1bd989a279c2a64169b8278258145728c319e1dabac4178962d3eb1bd83`; validator contract `176656214dbc42fb91dd298911e28a7da39567d43d7945f13f1dc2d6ac858fe4`; validation report `f93dc13bb7e40b4e6e32bf4c182704ce89546f9593bc218c99976c2586030924`; manifest `bf390f8f1018855a39ee659481e6d54d13d2ef23fa33a5f86e4353edc375d2b7`。
- **Software Versions:** Python 3.11.15。solver・QUBO・量子環境は未使用。
- **Results:** `constraint_version=evrp-common-hard-constraints-v1`として13制約を一意IDで定義。HC01〜HC08、HC10〜HC13をenabled、HC09 Operating-TimeはBaselineの`maximum_operating_time_enabled=false`に対応してdisabledとした。customer未配送許容、DFR/objective分離、SOC 1.00/0.20、charging 70 kW/30分/post-SOC<=1.00、R15 reachability/null semantics、OR-Tools/QUBO共通validator contractを維持した。toleranceはexact discrete、distance 1e-6 m、time 1e-9 s、energy 1e-9 kWh、SOC 1e-9、payload 1e-9 kgを変更していない。charger複数回訪問を許可し、各訪問を独立eventとした。
- **Validation Results:** unresolved semantics 0、13 IDs、required fields、R15 instance hash、units/tolerances、objective separation、共通version参照、validator contractをPASS。HC12は各charger eventの70 kW・30分・post-SOC<=1.00、連続eventによる上限回避禁止、customer visit制約非適用、R16の回数上限なしを検査対象とする。QUBO copy上限はR20/R21へ延期する。
- **Issues:** なし。R16ではQUBO encodingを実装していない。
- **Decision:** 利用者採択のcharger再訪問semanticsにより唯一のBLOCKED要因を解消し、R16 PASS。
- **Next Allowed Stage:** R17_ORTOOLS_FORMULATION（今回未実行）

## R17_ORTOOLS_FORMULATION — OR-Tools Formulation (initial blocked record; superseded by revalidation record below)

- **Stage ID:** R17_ORTOOLS_FORMULATION
- **Objective:** 同一制約と辞書式目的をOR-Toolsへ写す
- **Inputs:** I_s・制約仕様・共通validator
- **Preconditions:** 前工程 `R16_COMMON_HARD_CONSTRAINT_DEFINITION` のPASS（明示された正常結果遷移は例外）と、Inputsの存在・hash・根拠を確認する。
- **Method:** 訪問選択・車両割当・充電を表現し小規模手計算と照合
- **Validation:** 13制約の対応表・目的優先の保証・整数化と単位整合・モデル妥当ことを独立検査し、実行記録に診断を残す。
- **Acceptance Criteria:** 13制約の対応表・目的優先の保証・整数化と単位整合・モデル妥当
- **Stop Conditions:** Global Stop Rulesと当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義はBLOCKED、検証不一致・実行異常はFAIL。
- **Outputs:** OR-Tools formulation・model tests
- **Status:** BLOCKED
- **Started At:** 2026-09-09T18:55:00+09:00
- **Completed At:** 2026-09-09T18:56:32+09:00
- **Commands:** `python -m py_compile 05_src/traffic_simulation/evrp_r17_ortools/build_formulation_spec.py 05_src/traffic_simulation/evrp_r17_ortools/validate_formulation_spec.py`; `.conda/bin/python 05_src/traffic_simulation/evrp_r17_ortools/build_formulation_spec.py --instance reproducibility/outputs/traffic_simulation/demand/evrp_r15_common_instance/20260909_r15_common_instance_fixture_n10_v18 --constraints reproducibility/outputs/traffic_simulation/demand/evrp_r16_constraints/20260909_r16_common_hard_constraints_v1_fixture_n10_charger_revisit_resolved --output-dir reproducibility/outputs/traffic_simulation/demand/evrp_r17_ortools/20260909_r17_ortools_formulation_fixture_n10_v18`; `.conda/bin/python 05_src/traffic_simulation/evrp_r17_ortools/validate_formulation_spec.py --spec-dir reproducibility/outputs/traffic_simulation/demand/evrp_r17_ortools/20260909_r17_ortools_formulation_fixture_n10_v18`; OR-Tools solver本番実行は未実施。
- **Input Hashes:** R15 `common_instance.json` `1d01afb5b871dc0cfdbeda701f5853827e0d24bb126d86d958644cb36ec5f1ca`; R16 `constraint_spec.json` `f5532f521b00855eeda7e74286c76e169ad4b5ac890ea093402d92f5c5a90313`; R16 validator contract `176656214dbc42fb91dd298911e28a7da39567d43d7945f13f1dc2d6ac858fe4`。
- **Output Hashes:** formulation spec `370bdd0369411a81328346f98733ee93938f0777b4fc7cda1b661775b16fdef0`; HC mapping `2f338d925535344c54be732ed54c6ccd37bb4c038e93340cfb37a00767c917ac`; validation report `41949fe54e76dfd5eb5152be7b078741085bdcb9ff2372eb2713c07a3c8fa94a`; R18 contract `64d57d32e3ef890af1c232033e7b525968a5cfcd313b89a6aba8f4b66f20216a`; output schema `b9ae2a2b695a45b4536ba707d9ed813b9f87f8185a4ccc6cbbe1c84a4f715571`; solver config `9da8d141314022e6ab1a6128341207ca77a681a605cb8e965ab1a08d19c6d57d`; manifest `871d9afda8fab42d672e93f4aaa2c32836fbf1f5b1064eb2c25a346af6378c18`。
- **Software Versions:** Python 3.11.15; OR-Tools 9.12.4544。新規dependencyなし。solver未実行。
- **Results:** R15を唯一のinstance authority、R16をconstraint authorityとして、RoutingModelのnode/order、depot start/end、directed transit、optional customer、capacity/time callback、unreachable arc restrictionを定義した。SOCはplain RoutingDimensionではなくCP-SAT/custom energy-state候補、chargingはevent-expanded候補としてR18 output schemaまで固定した。目的は第1段階でunserved最小、第2段階でtotal travel time最小。HC01〜HC13 mappingを生成し、HC09はBaseline disabledとして保持した。
- **Validation Results:** 13 unique IDs、instance/constraint version、unserved、reachability、SOC、charging semantics、R18 schemaの構造検証はPASS。formulation acceptanceはBLOCKED。R16の「charger再訪問回数上限なし」を有限RoutingModelで表すevent copy/slot数が未採択、R15の`q_i`（配送要求件数）をR10 payload capacity（kg）へ変換する根拠がなくcapacityを意味保存できない、first solution/metaheuristic/seed/workers/logging/solution limitが未採択。
- **Issues:** 上記3点。特にcharger copy数を推測で固定したり、q_iをkgへ黙って同一視したり、solver設定を恣意採択してR18へ進めない。
- **Decision:** BLOCKED。R16 semanticsを近似・変更せずにR18を開始できるformulation acceptanceに未達。必要な変更は、charger event表現の有限化根拠またはR16と整合する別solver formulation、q_iとpayloadの明示的変換規約、solver設定の採択。
- **Next Allowed Stage:** NONE

## R17 preparation and revalidation record — 2026-09-09

- **Scope:** A payload model → B charger event upper bound → C fixture solver config の順に準備。R18 solver executionは未実行。
- **Repo audit:** 現行R06 `reproducibility/outputs/traffic_simulation/demand/evrp_r06_customer_demand/20260909_r06_customer_demand_final/customer_demand.csv` は `q_i=1`（delivery request/customer）と `w_i`（household-equivalent sampling weight）のみで、parcel/customer重量は未定義。legacy `legacy/non_sumo_route_proxy_analysis/src/scenario_generation/scenario_utils.py:31-32,148-175` と `legacy/.../monte_carlo_utils.py:552-559` に `demand_kg` の整数一様5–30 kg synthetic assumptionがあるが、旧proxy・非観測・本R06 contract外。vehicle `payload_kg` はR10の車両容量でありcustomer payloadではない。現行B2C baselineへ直接再利用しない。
- **External candidate audit:** (1) MLIT `平成19年度 貨物純流動調査`（2008公表、全国貨物、宅配便の1件重量10.8 kg）は件数/個数の定義がB2C parcel requestと一致せず、分布・中央値なし、直接baseline不採用。 (2) Japan Post Yu-Pack（現行service specification）は25–30 kg階級と上限30 kgを示すが、population distributionではなくサービス上限、直接baseline不採用。 (3) Dalla Chiara et al. (2020,査読、Singapore/UPS-linked observed delivery weights) は観測配送重量の中央値1.1 kgを報告し、B2C/urban parcelに近いが日本代表ではない。 (4) Nuzzolo et al./European Transport Research Review (2021, Munich urban parcel simulation) は平均約7.5 kgを使い、10 kg超をcargo bike対象外とし、地域・carrier差が大きい。 (5) Sustainability São Paulo case（2022, retailer historical distribution）は9 kg未満のparcel weight distributionを使うが、図ベースで再現用パラメータが本repoにない。候補間でmean/medianが大きく異なるため、日本のB2C母集団推定としては採択しない。
- **Payload decision:** fixture implementation validationには、再現性・`q_i=1`との互換性・解釈性を優先し、Dalla Chiara et al. (2020) の観測中央値を外部proxyとしてconstant modelに採択。これは日本の実測推定ではなく `ASSUMED_FIXTURE_BASELINE_EXTERNAL_PROXY`。`m_i=1.1 kg` を全selected customerへコピーし、random seedは `not_applicable_constant`。empirical categorical/continuous distributionは根拠の母集団・階級/パラメータが揃わないためfixture baselineには採択せず、将来の日本operatorデータ置換点として残す。
- **Final payload fields:** `delivery_request_count=q_i=1`（count/customer、R06 model convention）と `payload_mass_kg=m_i=1.1`（kg/customer、R17 fixture payload model）を完全分離。HC06は各segmentの `sum(m_i)` [kg] ≤ `vehicle.payload_capacity_kg=2000` [kg] のみで判定し、`q_i`をkgとして扱わない。SOC/chargingはR16の単位・semanticsを変更しない。
- **Charger bound proof:** served customer数を `k` とする。non-charging visitsは `depot_departure + k customers + depot_return = k+2`。その間のgapは `depot→customer_1`、customer間 `k-1`、`customer_k→depot` の合計 `k+1`。同一chargerへの連続charging visitを禁止するため、各gapには高々1 eventしか置けず、`E_max(k)=k+1`。fixture全customer数 `n=10` では安全上限 `E_max(n)=n+1=11`。general fixtureは `n+1` copies/slots、実際にk<nを訪問したrouteでは未使用slotを空にする。indexは `charger_event_slot_01..charger_event_slot_(n+1)`、対応copyは `charger_copy_01..charger_copy_(n+1)`、solver indexはR15 node indexとは別namespace。これは恣意的な2/3回制限ではなく、R16のroute構造から導出したfinite encodingであり、R16の複数回訪問許可・連続event禁止・30分/event上限を切り詰めない。
- **Fixture solver config:** OR-Tools `9.12.4544`; first solution `PATH_CHEAPEST_ARC`; local search `GUIDED_LOCAL_SEARCH`; time limit `300 s`; random seed `20260909`; `num_workers=1`; deterministic `true`; logging `true`; solution limit `1000`; scope `fixture_implementation_validation_only; not production_tuning`。本番scenario tuningは未採択・未実行。
- **R17 artifacts:** new run `reproducibility/outputs/traffic_simulation/demand/evrp_r17_ortools/20260909_r17_ortools_formulation_fixture_n10_v18_payload_charger_solver_fixed`。R15 payload-fixed instance validation PASS (`common_instance.json` SHA-256 `cbbe1c70e3a227ae0a17104f184c7d24f9676f4beaac6a5a38c9277a6d35eb3c`)、R16 validation PASS、R17 formulation validation PASS (`ortools_formulation_spec.json` SHA-256 `52ece569821b69260de37545d8a53d1df9c8abfaaf4fcb1bed8af3d00bc55cd2`)。HC01〜HC13 mapping count/uniqueness PASS、HC12 semantics保持 PASS、SOC/charging/reachability/output schema PASS。
- **R18 execution contract:** `r18_execution_contract.json` is `READY_PENDING_R18`; runner remains `NOT_IMPLEMENTED_R17_ONLY`; `R18_ONLY_NOT_EXECUTED`。solver実行、route生成、R19 validationは行っていない。
- **Final R17 decision:** `R17_ORTOOLS_FORMULATION = PASS`。Unresolved issuesは、(i) 1.1 kgは日本実測ではないfixture-only external proxyであり本番分布ではない、(ii) production n/scenario tuningは未採択、(iii) R18 runner実装・実行は未実施。これらはR17 blockerではなく、R18以降の実行前提として明示保存した。**Next Allowed Stage: R18_ORTOOLS_EXECUTION**。ただし本turnではR18を開始しない。

## R18 pre-execution repository authority / dependency / demand-usage audit — 2026-09-09

**Scope and stop rule:** read-only audit plus this record only. R18 solver/runner was not executed. Existing R05–R17 PASS statuses were not changed.

### 1. Authority and dependency classification

| Artifact / script | Classification | Audit result |
|---|---|---|
| `reproducibility/config/traffic_simulation/current_network_completion_authority_v18_geometry_reaccepted.yml` | CURRENT_AUTHORITY | V18 network hash `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`; current R12/R13 V18 fixture artifacts use it. `source_authority: V17` is provenance, not the active network. |
| V17 authority, V17 R12/R13 outputs, V17 R14 outputs | SUPERSEDED | retained, but must not feed current R18. V17 authority file itself still says `status: CURRENT`, creating repository-level ambiguity. |
| current R13 V18 `routing_arcs.csv` and manifest | CURRENT_AUTHORITY | network hash is V18 only; no V17 hash in the current V18 artifact. |
| current payload-fixed R15 `common_instance.json` | AMBIGUOUS | R05–R14 paths and routing hash are current fixture paths, but `r09_depot` provenance points to an artifact generated against V17, and the embedded `constraint_version` remains a historical R16 placeholder. R16/R17 downstream use their own current PASS constraint authority, but R15 itself is not a clean latest-authority closure. |
| current payload-fixed R16 `constraint_spec.json` | CURRENT_AUTHORITY | `evrp-common-hard-constraints-v1`, input R15 payload-fixed hash `cbbe1c70...`; validation PASS. |
| current payload/charger/solver-fixed R17 formulation and solver config | CURRENT_AUTHORITY | payload model, `n+1` charger bound, fixture solver config, and R16 hash are referenced; validation PASS. |
| current R18 execution contract | CURRENT_AUTHORITY_FOR_PENDING_EXECUTION | references only current instance hash, `evrp-common-hard-constraints-v1`, current formulation version, local `r18_output_schema`, and local `r18_solver_config.json`; no old run_id, V17 hash, legacy config path, or BLOCKED run reference. Status is `READY_PENDING_R18`, but runner is intentionally not implemented/executed. |
| `05_src/traffic_simulation/evrp_r12_routing/define_routing_specification.py` defaults | AMBIGUOUS | default authority/network are V17; the recorded current run was made with explicit V18 arguments. A future default invocation can accidentally select V17. |
| `05_src/traffic_simulation/evrp_r15_instance/build_common_instance.py` | AMBIGUOUS | hard-coded R05–R14 paths identify the recorded fixture, but R15 code still writes a historical `constraint_version` placeholder and R09 V17-derived artifact. |
| old initial R17 blocked run, old R16 run, non-final/repeat R04–R08 runs | SUPERSEDED / UNUSED | retained for provenance and reproducibility comparison; not referenced by current R18 contract. |
| `legacy/non_sumo_route_proxy_analysis/**` | LEGACY_REFERENCE_ONLY | old proxy inputs/logic. Some accepted R09/R10/R11 artifacts retain explicit legacy provenance; no direct current R18 contract reference. |

**Authority conclusion:** current R18 contract is clean as a direct dependency graph, but repository-wide authority is not unambiguous because V17 remains labeled `CURRENT`, current R09 depot provenance is V17-based, and the current R17 `hc_mapping_table.json` still contains the stale text `BLOCKED pending finite event encoding` for HC12 even though the formulation spec records the derived `n+1` bound. This is an artifact consistency issue, not a solver execution. No artifact was deleted or overwritten and no semantic regeneration was performed.

**Obsolete-path correction performed:** only `define_routing_specification.py` default authority/network was changed from V17 to the V18 authority/network. Existing V17/R09 artifacts were not overwritten. No R12/R13/R15 regeneration was performed.

### 2. Reconstructed current demand-generation pipeline

`candidate delivery locations → 500m census household count → R04 weight → R05 successive PPS sample → R06 q_i=1 request convention → R07 synthetic service-start window → R08 fixed service-time assumption → R17 fixture payload m_i=1.1 kg → R15/R17 solver input`

| Stage | Input / transformation / output | Source, classification, seed/parameter | Represents | Does not represent |
|---|---|---|---|---|
| Candidate locations | `building_delivery_stops_scoped.csv` (39,956 rows): active building-level stop candidates from scoped historical household/parcel pipeline; representative point retained. | PLATEAU/chocho residential candidate tables plus synthetic household/request artifacts; current accepted processed artifact, not observed orders. `housing_seed=20260830`; evaluation date `2026-01-01`. | Potential building-level delivery point population. | Not 39,956 observed homes, customers, orders, or unique households. One row is one active building stop; rows can aggregate multiple households/requests. |
| Census household input | Decode 500m JGD2011 mesh, use e-Stat `T001141034` as `H_m`; map candidate points to mesh and count `N_m`. | Public e-Stat 2020 Census; `H_m` observed household count, unit households; no random seed. | Household-count proxy for spatial residential exposure. | Does not observe parcel orders, order frequency, or delivery probability. |
| R04 weight | `w_i=H_m/N_m`; `N_m=0` recorded with no reallocation; mesh is an input unit, not a sampling stratum. Weight sums conserve candidate-linked household totals; recorded total is 438,455. | R04 computed artifact; `classification_H_m=OBSERVED`, `classification_w_i=COMPUTED`; no seed. | Household-equivalents assigned equally to candidate points within each mesh. | Not household existence probability, delivery demand, order frequency, or observed customer probability by itself. |
| R05 customer sampling | Successive PPS without replacement: `p_i^(k)=w_i/sum(w_j)` over remaining units; n=10, seed=20260909, Python `random.Random`. | R04 weight artifact → R05 sample; conditional draw probability recorded; first-order inclusion probability not calculated; `sampling_stratification=false`. | A reproducible household-weighted candidate sample. | Not spatially balanced sampling and not an observed delivery-demand sample. |
| R06 request count | Left-preserving join to selected R05 IDs; set `q_i=1` for every selected customer. | `ASSUMED`; model convention; no random seed. | One sampled customer equals one model delivery request. | Not empirical parcel count, observed order count, or household delivery frequency. |
| Payload | Set `m_i=1.1 kg` for fixture customers. | Dalla Chiara et al. median as external proxy; `ASSUMED_FIXTURE_BASELINE_EXTERNAL_PROXY`; constant, no seed. | Fixture payload mass for capacity testing. | Not Japan-specific B2C distribution or production scenario payload model. Legacy 5–30 kg path is not in current R17 payload model. |
| R07 time window | Draw receipt-specification category from `ss515`; draw hour anchor from `ss508`; transform to service-start interval (`[0,24]`, clipped bands, or one-hour clock proxy). | `SYNTHETIC_CALIBRATED`; seed=20260909; public Tokyo Metropolitan Goods Movement Survey 2024. | Reproducible synthetic allowable service-start window calibrated to aggregate receipt statistics. | Not customer-level records, Ota-ku order history, or literal requested delivery intervals. |
| R08 service time | Copy `s_i=2.5 minutes/customer` to each R07 customer; travel/waiting/charging excluded. | `ASSUMED (external empirical reference)`; deterministic; 4–15 min is sensitivity candidate, not executed. | Fixture service-time assumption. | Not Ota observed service time or a result of current customer-level measurement. |

### 3. Candidate population and household interpretation

The 39,956 candidates are active building-level stops after the historical scoped mapping process: `active_households=73,200`, `active_buildings=39,956`, `stop_count=39,956`; `requests_per_stop` ranges 1–12 and `parcel_equivalent_per_stop` ranges 1–14. The upstream `384,353 synthetic_households` artifact is a synthetic household frame, not the candidate count. Households were assigned to buildings using a uniform assignment rule and `housing_seed=20260830`; multiple households can map to one building. Therefore `1 candidate != 1 household` and `1 candidate != 1 observed delivery`; current candidate semantics are one active building-level potential delivery point with aggregated upstream synthetic activity.

The R04 equality `sum_i w_i = 438,455` is a conservation result for candidate-linked census households, not evidence that 438,455 orders or deliveries exist. `N_m=0` meshes are retained as no-candidate records and are not reallocated.

### 4. Data-usage field boundary table

| Variable / field | Current value / rule | Source type | Classification | Geography / unit | Transformation | Current status |
|---|---|---|---|---|---|---|
| `H_m` / `T001141034` | census household count per 500m mesh | public statistic | OBSERVED | Japan Census mesh / households | point-in-mesh join; confidentiality fields preserved | current R04 input |
| `N_m` | candidate count per mesh | computed from candidate artifact | COMPUTED | Ota candidate mesh / count | group candidate points by mesh | current R04 input |
| `w_i` | `H_m/N_m` | public-statistic-derived | COMPUTED | Ota candidate / household-equivalents per candidate | equal allocation inside mesh | current sampling weight; interpretation requires decision |
| `customer_selected` | R05 inclusion | synthetic sampling | COMPUTED | Ota fixture / boolean | successive PPS without replacement | fixture-only sample |
| `q_i` / `delivery_request_count` | 1 per selected customer | model assumption | ASSUMED | customer / requests per customer | constant convention | current fixture model; not observed |
| `m_i` / `payload_mass_kg` | 1.1 per selected customer | external research proxy | ASSUMED_FIXTURE_BASELINE_EXTERNAL_PROXY | customer / kg | constant copy; no q-to-kg conversion | fixture-only; production decision pending |
| `time_window_category`, `e_i`, `l_i` | seeded category/hour and transformed interval | public statistic calibrated synthetic | SYNTHETIC_CALIBRATED | Tokyo aggregate → customer / hours from local midnight | `ss515` category + `ss508` hour; interval rules | fixture-only; production decision pending |
| `s_i` / `service_time_min` | 2.5 | external empirical reference | ASSUMED | urban parcel reference → customer / minutes/customer | fixed copy; excludes travel/wait/charge | fixture-only baseline; 4–15 not executed |

### 5. Time-window source usage audit

`ss508_r06a.xlsx` is used for receipt weekday/time-band hour distribution; `ss515_r06a.xlsx` is used for date/time-specification category distribution. The current R07 generator does not read `ss519_r06a.xlsx`; it is not a current R07 dependency. `ss519` contains regional receipt/re-delivery frequency information and may be useful for future regional calibration, but the plan's earlier statement that it is used as supplemental calibration is not reflected in the current generator or R07 manifest. This source/documentation mismatch is recorded; no automatic change was made. Weekday, date designation, and redelivery statistics are not currently separate solver variables.

### 6. Suitability assessment

| Dimension | Assessment |
|---|---|
| population / household representation | ACCEPTABLE_AS_CURRENT_BASELINE for a synthetic fixture input; REQUIRES_FUTURE_REFINEMENT for observed-population claims |
| spatial representation | ACCEPTABLE_FOR_FIXTURE_ONLY; building representative points and historical mapping are proxies |
| customer sampling | ACCEPTABLE_FOR_FIXTURE_ONLY; reproducible PPS sample, not spatially balanced or observed demand |
| delivery frequency | REQUIRES_USER_DECISION_BEFORE_R18; `q_i=1` is a convention and suppresses frequency variation |
| parcel count | REQUIRES_FUTURE_REFINEMENT; parcel_count/delivery_count are explicitly not defined in R06 |
| payload | ACCEPTABLE_FOR_FIXTURE_ONLY; 1.1 kg is external proxy, not Japan production distribution |
| time window | ACCEPTABLE_FOR_FIXTURE_ONLY; aggregate-statistic-calibrated synthetic intervals |
| service time | ACCEPTABLE_FOR_FIXTURE_ONLY; explicit external-reference assumption |
| reproducibility | ACCEPTABLE_AS_CURRENT_BASELINE for fixed fixture artifacts, hashes, and seeds |
| production/scenario analysis | REQUIRES_USER_DECISION_BEFORE_R18; current fixture assumptions must not be silently promoted |

### 7. Research decisions required before R18

| Decision | Current policy | Rationale | Limitation | Alternative | Fixture impact | Production impact |
|---|---|---|---|---|---|---|
| household weight as customer probability | use `w_i` in PPS | preserves spatial household exposure proxy | not demand probability | uniform/spatially balanced/explicit inclusion-probability design | yes | yes |
| successive PPS baseline | use R05 PPS without replacement | reproducible household-weighted sample | no spatial balance; conditional probabilities only | stratified/spatially balanced sampling | yes | yes |
| one customer = one request | `q_i=1` | simple fixture objective | no frequency variation | household/order-frequency model | yes | yes |
| constant payload 1.1 kg | fixture-only `m_i` | reproducible external proxy | not Japanese distribution | categorical/continuous Japanese/operator data | yes | yes, if promoted |
| R07 synthetic TW | use ss508+ss515 calibration | public aggregate data available | no customer-level interval; ss519 unused | integrate ss519 or order/operator data | yes | yes |
| service time 2.5 min | fixed assumed baseline | explicit external urban reference | not Ota measurement | 4–15 sensitivity or empirical stop-time data | yes | yes |
| V17/V18 authority closure | use V18 artifact, retain V17 provenance | current output is V18 | V17 file/default/R09 remain ambiguous | regenerate R09/R12/R13 closure against V18 | no current contract, but preflight yes | yes |

**Required confirmation format:** each item must be answered `YES`, `NO`, or `CHOOSE` before any R18 execution. No code, artifact, or execution decision is changed based on an unanswered item.

### 8. Dependency chain and R18 readiness

**Superseded by the 2026-09-09 R09 V18 authority closure and R15→R17 propagation record above.** The hashes and readiness statement in this historical pre-closure audit are retained as audit history only; the current chain is the new R09 V18 / R15 current / R16 current / R17 current chain recorded above.

Current recorded chain and hashes:

`03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/building_delivery_stops_scoped.csv` (`fcfca5cb87bc482f1d98306c98823773e872f200c58ecb9090aa12985e3e80e0`) → `03_data/raw/traffic_simulation/population/estat_2020_500m_jgd2011/tblT001141H5339.zip` (`8a8b47563ffe88ec1afb5a17b8d29ac987b40df65498bec4c2fcf1829777f67d`) + `reproducibility/outputs/traffic_simulation/demand/evrp_r04_demand_weight/20260909_r04_demand_weight_v3/candidate_demand_weights.csv` (`e7694dd7461ae048d1de9289408faa91f6d3924defaf06b15b09341e38842ad8`) → `reproducibility/outputs/traffic_simulation/demand/evrp_r05_pps_sampling/20260909_r05_pps_n10_seed20260909_final/customer_ids.csv` (`a3307ac024c639b2690b120d11cd163abbbf83820428d090abb09fa18b0e4d0e`, seed `20260909`) → `reproducibility/outputs/traffic_simulation/demand/evrp_r06_customer_demand/20260909_r06_customer_demand_final/customer_demand.csv` (`9c321d63d5c611d0f348f8e9eb6c5581e4db9dbefa3e4db9e9c747ebde746825`) → `reproducibility/outputs/traffic_simulation/demand/evrp_r07_time_window/20260909_r07_time_window_fixture_n10_v2/customer_time_windows.csv` (`4915372ccc64131631cc1bcd0850b823e2c916663d869e93dd76622e7d4aa6c3`) → `reproducibility/outputs/traffic_simulation/demand/evrp_r08_service_time/20260909_r08_service_time_fixture_n10_final/customer_service_times.csv` (`3d0ac325e0c5bf7686fc8501d9bfaa207a77a4ddc77527b6ea4b014508a2d6e2`) → `reproducibility/outputs/traffic_simulation/demand/evrp_r15_common_instance/20260909_r15_common_instance_fixture_n10_v18_payload_fixed/common_instance.json` (`cbbe1c70e3a227ae0a17104f184c7d24f9676f4beaac6a5a38c9277a6d35eb3c`) → `reproducibility/outputs/traffic_simulation/demand/evrp_r16_constraints/20260909_r16_common_hard_constraints_v1_fixture_n10_charger_revisit_resolved_payload_fixed/constraint_spec.json` (`1b1c3132b44a542605b19f354a5d9c7464a093aa4cb23b04583ca92e0841ec67`) → `reproducibility/outputs/traffic_simulation/demand/evrp_r17_ortools/20260909_r17_ortools_formulation_fixture_n10_v18_payload_charger_solver_fixed/ortools_formulation_spec.json` (`52ece569821b69260de37545d8a53d1df9c8abfaaf4fcb1bed8af3d00bc55cd2`) / `r18_execution_contract.json` (`6439a080bc318a157958e60a41fdd4e1787973b71a5e7fcfbb0a5937569b5d98`). Network side dependency is `reproducibility/config/traffic_simulation/current_network_completion_authority_v18_geometry_reaccepted.yml` (`29ee5fe979c85eb1d11b0f5a55f33782b7b5b08fcf09b48d2fad3e47c0ae33ee`) and V18 network hash `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`.

**Historical pre-closure result: `NOT READY`.** This statement is superseded by the later authority-closure record above. The fixture research decisions remain documented, but they were not changed by the closure.

## R04/R05 candidate-generation and household-weight double-correction audit — 2026-09-09

**Scope and stop rule:** read-only audit and this record only. R04/R05 were not regenerated, parameters were not changed, and R18 was not executed. Existing R04–R17 statuses were not changed.

### 1. 39,956 candidate generation reconstruction

The current candidate artifact is `03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/building_delivery_stops_scoped.csv` (39,956 data rows; SHA-256 `fcfca5cb87bc482f1d98306c98823773e872f200c58ecb9090aa12985e3e80e0`). Its upstream chain is:

`census_000032163278_ota.csv` small-area household margins → `synthetic_households.csv` (384,353 synthetic household rows) → household-size delivery propensity and top-down parcel-equivalent calibration → `daily_requests.csv` (73,547 generated requests; Poisson, seed `20260829`) → multinomial housing-type assignment (Ota municipal housing distribution, seed `20260830`) → uniform compatible-building assignment from accepted PLATEAU/chocho residential building candidates → request-to-building mapping → group by `(evaluation_date, building_id)` → `building_delivery_stops_scoped.csv`.

The historical pipeline implementation is recorded in git commit `d441953`, `05_src/household_parcel/pipelines.py`; the materialized scoped-stop run summary is `03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/stop_generation_run_summary.json`. The current stop-generation summary records: `assigned_households=382,369`, `active_requests=73,547`, `mapped_requests=73,200`, `active_households=73,200`, `active_buildings=39,956`, `requests_per_stop` 1–12, and `parcel_equivalent_per_stop` 1–14. The accepted building candidate inputs are `residential_building_candidates.parquet` and `plateau_buildings_all_with_chocho_points.geo.parquet`; the stop-generation gate accepts only `matched` and `matched_cross_boundary` mappings.

The candidate-generation code does use household and request information upstream, but not the R04 500m `H_m` field: synthetic household rows are expanded from small-area Census household margins; requests are generated by a household-size propensity and top-down parcel-equivalent model; households are randomly assigned to compatible buildings; only buildings with at least one mapped request become active stops. It does not use observed household coordinates, dwelling-unit counts, entrances, a building capacity constraint, or observed orders. `384,353` is the synthetic household frame, not the candidate population. Multiple synthetic households and requests can aggregate into one building candidate.

**Candidate meaning:** one row is one active building-level potential delivery point with aggregated synthetic activity. It is not one real house, one real household, one real order, or one synthetic request. It is also not a household-equivalent count by itself. Candidate count is affected indirectly by synthetic household/request activity and building assignment, but the generation code does not use the later R04 500m household count `H_m` to allocate candidates.

### 2. Quantitative mesh audit

Read-only aggregation joined the 39,956 candidate buildings to the R04 mesh assignment and joined assigned synthetic households by building. There are 172 candidate-containing meshes:

| Quantity | Result |
|---|---:|
| `sum(H_m)` | 438,455 households |
| `sum(N_m)` | 39,956 building candidates |
| assigned synthetic households in candidate buildings | 288,016 |
| Pearson correlation `N_m,H_m` | 0.7098 |
| Spearman correlation `N_m,H_m` | 0.7728 |
| Pearson correlation `N_m, synthetic households` | 0.9414 |
| Spearman correlation `N_m, synthetic households` | 0.9526 |
| median `N_m/H_m` | 0.1027 candidates per Census household |
| median `H_m/N_m` | 9.7399 household-equivalents per candidate |
| `N_m/H_m` range | 0.000805–0.2000 |
| `H_m/N_m` range | 5.0–1,242.5 |

The `N_m/H_m` distribution has 8 meshes at or below 0.01, 20 in (0.01, 0.05], 52 in (0.05, 0.10], and 92 in (0.10, 0.20]. Eight meshes have `H_m/N_m > 100`; the largest is mesh `533935084` with `H_m=7,455`, `N_m=6`, and 139 assigned synthetic households. The highest candidate density is mesh `533926501` with `H_m=15`, `N_m=3`, and 6 assigned synthetic households. Candidate share minus Census-household share has mean absolute difference 0.00168 and maximum absolute difference 0.01685 across the 172 meshes.

These figures do not establish that candidate generation is Census-household proportional: `N_m` is a building count after activity filtering and uniform within-chocho compatible-building assignment. They do establish that candidate count already strongly follows the synthetic household/request pathway (`rho_s=0.9526`), while its relationship with the independent R04 `H_m` is weaker and materially uneven. The high `N_m`–synthetic-household association is evidence that household information has already entered candidate creation, not evidence that candidates are observed households.

### 3. Meaning of current `w_i=H_m/N_m`

`w_i` assigns the mesh's observed Census household total equally to each active building candidate in that mesh. R05 then treats this household-equivalent as the conditional PPS draw weight. It is not an order rate, parcel count, delivery probability, or first-order inclusion probability.

| Candidate interpretation | Meaning of adding `H_m/N_m` |
|---|---|
| Candidate population already household-distribution-representative | Reweights an already household-informed active-building population toward the same mesh household totals; potential double correction. |
| Candidate population is only building locations | A defensible post-stratification/household-equivalent correction, assuming every candidate is an exchangeable potential point inside the mesh. |
| Candidate population partially reflects households/activity | A correction may be useful, but its magnitude and estimand are not identified without a calibrated joint model; it can overcorrect in meshes where activity filtering already tracks households. |

### 4. Double-counting classification

**判定: `POSSIBLE_DOUBLE_COUNTING`.** It is not `NO_DOUBLE_COUNTING` because the candidate-generation path already expands household margins, generates household-level demand, and assigns households to buildings before active buildings are formed. It is not `CONFIRMED_DOUBLE_COUNTING` because the upstream synthetic frame is built at chocho/small-area level and the R04 `H_m` is a separate 500m mesh statistic; the repository does not contain a proof that the same household total is applied once in candidate selection and again with the same estimand. The exact overlap between the small-area household margins/top-down demand and `T001141034` is not documented as an identity mapping.

Evidence: `05_src/household_parcel/pipelines.py` (`build_synthetic_household_frame`, `generate_daily_requests`, `assign_housing`, uniform compatible-building assignment, building aggregation); `reproducibility/config/traffic_simulation/household_parcel_v1/pipeline.yml` (`multinomial` housing assignment, Poisson requests, uniform building assignment); `stop_generation_run_summary.json`; current R04 config and `candidate_demand_weights.csv` (`H_m/N_m`).

### 5. Sampling alternatives

| Option | Statistical meaning | Candidate consistency / household reproduction | Double-counting risk | Interpretability / reproducibility | Fixture | Production |
|---|---|---|---|---|---|---|
| A. Uniform `1/N` | Equal probability per active building stop | Treats all 39,956 active buildings as the population; does not impose Census household exposure | low additional risk, but preserves upstream synthetic-selection effects | very clear and reproducible | suitable | only if building-stop estimand is intended |
| B. Current PPS `H_m/N_m` | Household-equivalent PPS over active building stops | Reproduces the R04 mesh household proxy under equal within-mesh allocation | possible, because candidate formation already used household/activity information | clear formula and fixed seed; conditional draw probabilities only | currently implemented | only after estimand decision |
| C. Existing candidate-level household/request weight | Sample by `household_count`, `request_count`, or `parcel_equivalent` already aggregated in each candidate | Directly uses the upstream synthetic activity represented by each building; not observed household/order probability | avoids adding a second Census correction, but can overweight activity if used as demand truth | interpretable as synthetic activity-weighted sampling, reproducible; not empirical demand | requires new contract | requires model validation |

No option is automatically adopted. Option C is not currently a valid substitute merely because fields exist: `household_count`, `request_count`, and `parcel_equivalent` are aggregated synthetic pipeline outputs and have different meanings. Selecting among A–C is a research estimand decision.

### 6. Re-execution impact if `w_i` changes

If the research decision removes or changes `w_i`, the minimum demand dependency chain is: R04 weight definition/output → R05 customer sample → R06 `q_i=1` rows → R07 time windows → R08 service times. Because the selected customer IDs change, fixture-specific customer endpoints/OD/routing artifacts R12–R14 and their validation must also be regenerated or explicitly revalidated; R15 common instance, R16 constraint input hash, R17 formulation, and the pending R18 contract must then be rebuilt/revalidated. R09 depot authority, R10 vehicle capacity, R11 charger authority, and the V18 network authority do not become invalid merely because demand sampling changes; only demand-dependent joins and downstream fixture artifacts require propagation. No such propagation was performed in this audit.

### 7. Research decision status

Recommendation: **`INSUFFICIENT_EVIDENCE`** for automatic adoption. The repository supports both interpretations: active building-stop sampling and household-equivalent correction. The strong `N_m`–synthetic-household association makes `KEEP_CURRENT_WI_PPS` non-neutral, but it does not alone prove that `USE_UNIFORM_SAMPLING` is correct. The appropriate choice depends on whether the intended fixture estimand is (i) an active building-stop route sample, (ii) a Census-household-exposure sample, or (iii) a synthetic activity-weighted sample. Do not change R04/R05 or run R18 until the researcher selects the estimand and sampling option.

### 8. Confirmation required before R18

| Question | YES / NO / CHOOSE |
|---|---|
| Should the fixture target equal active building-level potential delivery points rather than household exposure? | `CHOOSE: A Uniform / B Current PPS / C Existing candidate-level field` |
| Is `H_m/N_m` intended as a household-exposure post-stratification correction even though candidate creation already used synthetic household/request activity? | `YES / NO` |
| If NO, should R04/R05 be redesigned before R18? | `YES / NO` |
| If C is selected, which field is the estimand: `household_count`, `request_count`, or `parcel_equivalent`? | `CHOOSE` |
| May the current R04/R05 sample remain unchanged for the fixture while the production sampling policy is deferred? | `YES / NO` |

**Audit conclusion:** current statuses R04–R17 are unchanged; no regeneration or execution occurred. R18 execution readiness remains **`REQUIRES_USER_DECISION`**. `EVRP_EXECUTION_PLAN.md` remains the sole progress/execution record.

## R04/R05 candidate population double-correction re-audit — 2026-09-09

**Scope:** audit only. R04/R05 were not regenerated, parameters were not changed, and R18 was not executed. Existing R04–R17 statuses remain unchanged.

### 1. Candidate-generation authority and meaning

The current artifact is `03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/building_delivery_stops_scoped.csv` (39,956 data rows, 39,956 unique `building_id`; SHA-256 `fcfca5cb87bc482f1d98306c98823773e872f200c58ecb9090aa12985e3e80e0`). The upstream generator is recorded in git commit `d441953`, `05_src/household_parcel/pipelines.py`; the materialized run is documented by `stop_generation_run_summary.json` and the historical config `reproducibility/config/traffic_simulation/household_parcel_v1/pipeline.yml`.

The actual path is:

`census_000032163278_ota.csv` small-area household margins → `synthetic_households.csv` (384,353 synthetic rows) → household-size delivery propensity and top-down parcel-equivalent calibration → `daily_requests.csv` (73,547 Poisson-generated requests, seed `20260829`) → Ota housing-type multinomial assignment (seed `20260830`) → uniform compatible-building assignment from accepted PLATEAU/chocho residential building data → request/building mapping → aggregation by `(evaluation_date, building_id)` → `building_delivery_stops_scoped.csv`.

The generation uses household attributes (`chocho_code`, size class), synthetic household/request activity, housing-type attributes, building usage/residential compatibility, and building representative points. It does not use observed household coordinates, observed orders, dwelling-unit counts, entrances, building capacity, or the later R04 500m `H_m` value. Accepted mapping statuses are `matched` and `matched_cross_boundary`; unmapped/ambiguous states are excluded and not nearest-filled.

The stop summary records `synthetic_households=384,353`, `assigned_households=382,369`, `active_requests=73,547`, `mapped_requests=73,200`, `active_households=73,200`, `active_buildings=39,956`, and `stop_count=39,956`. Therefore one candidate is one active building-level potential delivery point with aggregated synthetic activity. It is not one real building-as-household, one real household, one observed order, or one synthetic request. Multiple synthetic households and requests can be aggregated into one candidate. Candidate count is indirectly affected by household/request generation and building assignment, but not by R04 `H_m` during the candidate-generation step.

### 2. Mesh remeasurement

The current candidate and R04 weight artifacts were joined read-only for all 172 candidate-containing 500m meshes:

| Metric | Result |
|---|---:|
| `sum(H_m)` | 438,455 |
| `sum(N_m)` | 39,956 |
| assigned synthetic households in candidate buildings | 288,016 |
| Pearson `corr(N_m,H_m)` | 0.7098 |
| Spearman `corr(N_m,H_m)` | 0.7728 |
| Pearson `corr(N_m,synthetic_households)` | 0.9414 |
| Spearman `corr(N_m,synthetic_households)` | 0.9526 |
| median `N_m/H_m` | 0.1027 |
| median `H_m/N_m` | 9.7399 |
| `N_m/H_m` range | 0.000805–0.2000 |
| `H_m/N_m` range | 5.0–1,242.5 |

The `N_m/H_m` quartiles are 0.0741, 0.1027, and 0.1158; 8 meshes are at or below 0.01 and 8 meshes have `H_m/N_m > 100`. The lowest candidate density is mesh `533935084` (`H_m=7,455`, `N_m=6`, synthetic households 139). The highest is mesh `533926501` (`H_m=15`, `N_m=3`, synthetic households 6). Thus candidate density is not uniformly proportional to Census household count. The much stronger relationship with synthetic household count shows that household/request information is already reflected in candidate formation; correlation alone is not being used as the conclusion.

### 3. Interpretation of `w_i=H_m/N_m`

R04 assigns the mesh's observed e-Stat household count equally to each active building candidate. R05 then uses this household-equivalent value in successive PPS. It is not an observed delivery probability, order frequency, parcel count, or first-order inclusion probability.

| Candidate population interpretation | Effect of adding `H_m/N_m` |
|---|---|
| Already reflects household distribution | Adds another household-based spatial correction; possible double correction. |
| Pure building locations | Acts as a defensible mesh post-stratification weight if the estimand is household exposure. |
| Partially household-informed | May correct residual spatial mismatch, but the correct magnitude/estimand is not identified. |

### 4. Double-counting result

**判定: `POSSIBLE_DOUBLE_COUNTING`.**

Evidence for possibility: `build_synthetic_household_frame` expands household margins; `generate_daily_requests` generates household-level activity; `assign_buildings` assigns households to compatible buildings; active stops are then formed only from buildings with mapped requests. R04 subsequently applies the separate 500m Census quantity `H_m/N_m`. This is not `NO_DOUBLE_COUNTING` because household information enters both stages. It is not `CONFIRMED_DOUBLE_COUNTING` because the upstream household margins/top-down demand are small-area/derived inputs and the repository does not establish that they are identical to `T001141034` at the same mesh-level estimand. The appropriate research interpretation remains unresolved.

### 5. Sampling alternatives

| Option | Meaning / spatial reproduction | Double-counting risk | Interpretability / reproducibility | Fixture | Production |
|---|---|---|---|---|---|
| A. Uniform `1/N` | Equal active building-stop probability; preserves the candidate population as generated | Low additional risk, but retains upstream synthetic-selection effects | Highest simplicity and reproducibility | Suitable | Suitable only for a building-stop estimand |
| B. Current PPS `H_m/N_m` | Household-equivalent PPS; explicitly restores R04 mesh household exposure | Possible, because candidate creation already used synthetic household/request activity | Formula and seed are clear; conditional draw probabilities only | Current implementation suitable | Requires estimand decision |
| C. Existing candidate-level `household_count` / `request_count` / `parcel_equivalent` | Directly weights by upstream synthetic activity aggregated at building | Avoids a second Census correction, but risks treating synthetic activity as observed demand | Reproducible but the three fields have different meanings and are not interchangeable | Requires new contract | Requires model validation |

No option is auto-adopted. In particular, candidate-level fields cannot be selected without deciding whether the target is household count, request count, or parcel-equivalent activity.

### 6. Dependency impact if `w_i` is removed or changed

The demand dependency is `R04 → R05 → R06 → R07 → R08`. A changed R05 sample changes customer IDs, so customer-dependent R12–R14 fixture endpoint/OD/routing artifacts and then R15, R16, R17 and the pending R18 contract require regeneration or revalidation. R09 depot, R10 EV, R11 charger, and V18 network authority do not need to be invalidated merely because sampling changes; only their demand-dependent joins, if any, must be checked. No propagation was performed.

### 7. Recommendation and decision gate

Recommended status: **`INSUFFICIENT_EVIDENCE`**. The repository supports a building-stop estimand, a household-exposure estimand, and a synthetic-activity estimand, but does not uniquely select one. Do not change `w_i`, R04/R05, or R18 execution automatically.

User decisions required:

1. Sampling estimand: `CHOOSE A Uniform / B Current PPS / C Candidate-level field`.
2. If B is retained, confirm that household exposure should be applied after a candidate population already formed from synthetic household/request activity: `YES / NO`.
3. If C is selected, choose field: `CHOOSE household_count / request_count / parcel_equivalent`.
4. May the current R04/R05 fixture sample remain frozen while production sampling is deferred: `YES / NO`.

**Final audit status:** R18 execution readiness remains **`REQUIRES_USER_DECISION`**. `EVRP_EXECUTION_PLAN.md` remains the sole execution record.

## R04/R05 PPS role-separation audit — 2026-09-09

**Scope and stop rule:** audit only. R04/R05 were not regenerated, no parameter or downstream artifact was changed, and R18 was not executed. Existing R04/R05/R17 statuses remain unchanged.

### 1. Candidate-generation role

The materialized `building_delivery_stops_scoped.csv` contains 39,956 unique active building stops. The upstream implementation recorded in git commit `d441953`, `05_src/household_parcel/pipelines.py`, performs the following:

| Input / operation | Observed evidence | Role classification |
|---|---|---|
| Synthetic household frame | 384,353 rows expanded from small-area household margins; household ID, chocho, size class, composition-unresolved fields | support/eligibility input; not R05 sampling intensity |
| Housing type | multinomial Ota housing distribution, seed `20260830` | building compatibility/eligibility input |
| Request generation | 73,547 positive household-level requests, Poisson, seed `20260829`, based on household-size propensity and top-down parcel-equivalent calibration | activity gate and synthetic delivery-frequency generation upstream; not final R05 probability |
| Building data | accepted PLATEAU/chocho residential candidates; compatibility filtered by housing type | potential delivery-point support |
| Building assignment | uniform compatible-building selection within chocho; no capacity or nearest fallback | maps synthetic households to potential buildings; indirectly affects which buildings become active |
| Aggregation | requests grouped by `(evaluation_date, building_id)` | candidate-level aggregation, not R05 weighting |
| Active inclusion | only buildings with mapped requests enter `building_delivery_stops_scoped.csv`; unmapped/unsupported households excluded | active candidate support/eligibility |

The summary artifact records `assigned_households=382,369`, `mapped_requests=73,200`, `active_households=73,200`, `active_buildings=39,956`, with multiple household/request rows allowed per building. Candidate fields include `household_count`, `request_count`, and `parcel_equivalent`, but current R04/R05 code does not use them as sampling weights. Thus the candidate generator does not explicitly compute or persist the final R05 customer-selection probability. It constructs an activity-conditioned active-building support; it also affects the support composition through synthetic activity, so it is not a purely neutral geometric building frame.

### 2. R04/R05 role

The current R04 code maps each candidate representative point into a 500m mesh, computes `N_m` as the number of active candidates in that mesh, reads e-Stat `T001141034` as `H_m`, and sets `w_i=H_m/N_m`. It records `mesh_role: statistical_input_unit_only`, `sampling_stratification: false`, and no mesh quota. The implementation proves exact per-mesh conservation:

\[
\sum_{i\in m} w_i = \sum_{i\in m} H_m/N_m = H_m.
\]

Therefore, before PPS depletion from earlier draws, the mesh-level total sampling mass is proportional to Census household count. Within a mesh, every active candidate building has exactly the same `w_i`; R04 does not distinguish buildings by `household_count`, `request_count`, `parcel_equivalent`, building size, or housing type.

R05 reads only the R04 weight artifact and applies successive PPS without replacement:

\[
p_i^{(k)}=w_i/\sum_{j\in U_k}w_j.
\]

It has no mesh quota and does not calculate first-order inclusion probabilities. Its role is sample selection from the already-defined active-building candidate support, with Census household-calibrated mesh mass and equal within-mesh candidate treatment.

### 3. Double-counting re-evaluation

**判定: `PARTIAL_OVERLAP_BUT_INTERPRETABLE`.**

The implementation is closer to the user's two-role hypothesis (B) than to confirmed same-purpose double counting (A):

1. Synthetic household/request information determines activity-conditioned candidate support: which compatible buildings have at least one mapped synthetic request and therefore enter the 39,956-row population.
2. R04 Census weighting determines a separate mesh-level sampling-mass calibration over that support.
3. R05 performs the actual customer-location sample selection; no candidate-level request/household intensity is passed into R05.

The overlap is real but partial: candidate inclusion is not independent of synthetic household/request activity, so R04 is not correcting a pure building-only frame. However, the same candidate-level intensity is not applied a second time: R04 uses independent mesh-level `H_m/N_m`, and within each mesh makes candidates equal. The repository does not prove that the synthetic small-area margins/top-down request calibration and e-Stat 500m `H_m` have identical estimands. Accordingly, `CONFIRMED_DOUBLE_COUNTING` is not supported; `NO_DOUBLE_COUNTING_DIFFERENT_ROLES` is too strong because the support itself is activity-conditioned.

### 4. Semantics of one sampled customer

The proposed description is **正しい**, with one qualification:

> 39,956 active potential delivery buildingsをcandidate populationとし、500m meshのCensus household countに比例するようmesh-level customer-location sampling massを較正し、同一mesh内ではactive candidate buildingsを等しく扱ってsuccessive PPS without replacementで抽出する。

The qualification is that the 39,956 support is already conditioned on synthetic household/request activity and accepted building mapping. The resulting sampled customer is a selected active building-level potential delivery point under a synthetic, Census-calibrated sampling design. It must not be described as an actual order probability, an actual household, or an empirical customer probability.

### 5. Current PPS versus Uniform

| Aspect | Current PPS | Uniform |
|---|---|---|
| Candidate population | 39,956 active building stops | same 39,956 active building stops |
| Mesh household quantity | mesh mass sums to `H_m` | no direct Census calibration; mass follows `N_m` |
| Within-mesh treatment | equal `H_m/N_m` for every candidate | equal `1/N` globally and within mesh |
| Census use | explicit R04 input | none in sampling |
| Synthetic household relation | support is activity-conditioned; Census adds mesh calibration | support is activity-conditioned; no second mesh calibration |
| Residential B2C interpretation | synthetic active buildings sampled to household exposure | synthetic active buildings sampled as equal potential stops |
| Spatial demand representation | household-count-oriented at mesh level | building-count-oriented; can underrepresent high-household/low-building meshes |
| Double-counting risk | partial overlap, interpretable but not zero | lower additional risk, but upstream activity conditioning remains |
| Reproducibility | fixed formula, seed, candidate order | fixed uniform rule, seed, candidate order |

Switching to Uniform would make mesh-level selection mass depend on `N_m`, not `H_m`; it would not preserve the current Census-household calibration.

### 6. Current PPS assessment and decision gate

**Assessment: `JUSTIFIED_FOR_FIXTURE_ONLY`.**

The role separation is sufficiently interpretable for a reproducible fixture: synthetic activity creates the active-building support, while Census household counts calibrate mesh-level sampling mass and equalize active buildings within each mesh. It is not justified as an empirical B2C customer-probability model or as a production demand model because the candidate support is synthetic/activity-conditioned and the overlap between small-area synthetic household inputs and 500m Census calibration is not formally decomposed.

No automatic keep/change decision is made. Before R18, the researcher must answer: **`KEEP CURRENT PPS` / `REDESIGN` / `CHOOSE`**. If `KEEP CURRENT PPS` is chosen, the above fixture-only semantics must be accepted. If `REDESIGN` is chosen, R04/R05 and dependent customer-demand artifacts require a separate authorized change; no such change was made here.

**Audit conclusion:** candidate generation, R04 Census weighting, and R05 PPS have distinguishable primary roles, with partial estimand overlap. R04/R05/R17 statuses are unchanged, and R18 remains unexecuted.

## Fixture baseline formalization and R18 pre-readiness recheck — 2026-09-09

**Scope and stop rule:** The current R04/R05 PPS is formally recorded as a fixture baseline. No R04/R05 regeneration, parameter change, downstream-stage execution, or R18 execution was performed. Existing R04/R05/R17 status fields were not changed.

### Fixture baseline definition

In this repository, **fixture** means a small, fixed validation instance used to verify implementation, constraints, solver formulation, and reproducibility. **Baseline** means the fixed configuration used as the comparison and reproducibility reference within that fixture. This is explicitly distinct from a **production baseline**: the fixture baseline is not the final empirical demand model or final production/scenario-analysis model.

The adopted fixture baseline is therefore:

- candidate population: 39,956 active potential delivery buildings;
- R04: `w_i=H_m/N_m`, where `H_m` is the 500m Census household count and `N_m` is the active candidate-building count in that mesh;
- same-mesh candidates receive equal `w_i`, so `sum(i in m) w_i = H_m` and mesh sampling mass is calibrated to Census household count;
- R05: successive PPS without replacement, with conditional draw probability `p_i^(k)=w_i/sum(j in U_k) w_j`;
- purpose: synthetic residential B2C customer-location generation for fixture validation, not actual order probability, observed customer probability, an actual household sample, or empirical delivery demand.

Candidate-generation synthetic household/request information and R04 Census weighting remain documented as different roles: candidate support/eligibility formation versus mesh-level sampling-mass calibration. The prior audit classification **`PARTIAL_OVERLAP_BUT_INTERPRETABLE`** is retained. Current PPS is formally assessed as **`JUSTIFIED_FOR_FIXTURE_ONLY`**, not as a production demand-model decision.

### Fixture-specific inputs and classifications

The current R18 input closure identifies these fixture-specific assumptions: `n=10`; R05 current PPS; R06 `q_i=1` delivery-request convention; R17 `m_i=1.1 kg/customer` (`ASSUMED_FIXTURE_BASELINE_EXTERNAL_PROXY`); R08 `2.5 min/customer` (`ASSUMED`); one vehicle; one depot; one charger; and the fixed OR-Tools 9.12.4544 fixture solver configuration. R07 time windows are `SYNTHETIC_CALIBRATED` from aggregate public statistics, not customer-level observations. These labels are fixture/synthetic/assumed classifications and are not production claims.

The following remain explicitly outside the production specification and require future reconsideration: production customer count; production customer-location sampling design; delivery frequency/parcel-count model; payload distribution; service-time distribution; demand scenario generation; and production solver tuning.

### Authority and stale-reference recheck

- The V17 network authority file was corrected from `status: CURRENT` to `status: SUPERSEDED`. Its historical V17 run and provenance remain retained.
- R09 remains unresolved for current authority closure. `evrp_r09_depot_v1.yml` and `r09_depot_manifest.json` point to the V17 network hash `4625dbbc...` and the legacy depot candidate path. The current accepted network is V18 hash `460554c7...`; V18 depot remapping/revalidation is **required before R18**, but R09 was not regenerated.
- The payload-fixed R15 common instance still contains `constraint_version: R16_NOT_STARTED_REFERENCE_EV_RP_COMMON_HARD_CONSTRAINTS`. This is a stale placeholder and cannot be silently relabeled because changing the accepted R15 bytes would require downstream hash propagation. R15 must be rebuilt against the accepted R16 constraint artifact before R18.
- The R17 HC12 text `BLOCKED pending finite event encoding` was corrected to state the fixed route-derived `n+1` finite event-slot encoding; the corresponding formulation and HC mapping hashes are now `f572b338ed14aa0ab87301bf4f10ce4195e405d017f15e205903ea1d59055c73` and `c0716140d93b5fa2f54fddd61cb852c6bc9bec9dd2837ad0d3f8ec15465c0493`. This changes stale wording only; the event bound and semantics are unchanged.
- The current R18 execution contract directly references the current R15 instance hash `cbbe1c70...`, current constraint version `evrp-common-hard-constraints-v1`, current formulation version, local solver config, and local output schema. It has no direct superseded run_id, V17 hash, legacy config path, or old BLOCKED-run reference. Its transitive R15/R09 dependencies are nevertheless not authority-clean.

### Current recorded dependency chain

`03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/building_delivery_stops_scoped.csv` (`fcfca5cb87bc482f1d98306c98823773e872f200c58ecb9090aa12985e3e80e0`) → R04 `candidate_demand_weights.csv` (`e7694dd7461ae048d1de9289408faa91f6d3924defaf06b15b09341e38842ad8`) → R05 `customer_ids.csv` (`a3307ac024c639b2690b120d11cd163abbbf83820428d090abb09fa18b0e4d0e`) → R06 `customer_demand.csv` (`9c321d63d5c611d0f348f8e9eb6c5581e4db9dbefa3e4db9e9c747ebde746825`) → R07 `customer_time_windows.csv` (`4915372ccc64131631cc1bcd0850b823e2c916663d869e93dd76622e7d4aa6c3`) → R08 `customer_service_times.csv` (`3d0ac325e0c5bf7686fc8501d9bfaa207a77a4ddc77527b6ea4b014508a2d6e2`) → current payload-fixed R15 `common_instance.json` (`cbbe1c70e3a227ae0a17104f184c7d24f9676f4beaac6a5a38c9277a6d35eb3c`) → R16 `constraint_spec.json` (`1b1c3132b44a542605b19f354a5d9c7464a093aa4cb23b04583ca92e0841ec67`) → current R17 formulation / solver config → R18 contract (`6439a080bc318a157958e60a41fdd4e1787973b71a5e7fcfbb0a5937569b5d98`).

The chain is recorded for audit, but it is not yet an authority-clean R18 chain because R09/R15 require closure against V18/current R16. No downstream artifact was regenerated in this turn.

### R18 readiness and remaining decisions

**Superseded by the 2026-09-09 R09 V18 authority closure and R15→R17 propagation record above.** The following `NOT READY` text is retained only as the pre-closure audit record.

**R18 execution readiness: `NOT READY`.** The blocker is stale/transitive authority dependency, not the adopted fixture PPS policy. Required pre-R18 work is: (1) authorized R09 V18 depot remapping/revalidation; (2) authorized R15 common-instance rebuild with the accepted R16 constraint version; and (3) propagation/revalidation through R16/R17/R18 hashes. These actions are not performed here.

The fixture PPS adoption itself is no longer a user-decision item. Remaining user authorization is limited to whether to authorize the required R09 V18 remapping and R15→R18 dependency closure. Production demand-model choices remain future research decisions and are not prerequisites for treating the current n=10 setup as a fixture baseline.

## R18_ORTOOLS_EXECUTION — OR-Tools Execution

- **Stage ID:** R18_ORTOOLS_EXECUTION
- **Objective:** 予算内で古典候補解を得る
- **Inputs:** 検証済古典model・I_s・solver設定
- **Preconditions:** 前工程 `R17_ORTOOLS_FORMULATION` のPASS（明示された正常結果遷移は例外）と、Inputsの存在・hash・根拠を確認する。
- **Method:** version/seed/time/memory制限を固定しincumbentと終了理由を保存
- **Validation:** 正常終了を分類しraw route/objective/bound/予算を保存ことを独立検査し、実行記録に診断を残す。
- **Acceptance Criteria:** 正常終了を分類しraw route/objective/bound/予算を保存
- **Stop Conditions:** Global Stop Rulesと当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義はBLOCKED、検証不一致・実行異常はFAIL。事前resource ceiling到達はLIMIT_REACHED、正常な解未発見はRESULT_INFEASIBLE。
- **Outputs:** 古典raw solution・execution metadata
- **Status:** FAIL
- **Started At:** 2026-09-10T00:55:00+09:00
- **Completed At:** 2026-09-10T00:58:00+09:00
- **Commands:** Installed-runtime API audit; parameter compatibility smoke and R18 gate command will use new run `reproducibility/outputs/traffic_simulation/demand/evrp_r18_ortools_execution/20260910_r18_ortools_execution_fixture_n10_v18_retry_02`.
- **Input Hashes:** R15 `7ca39facf83de619db7ec37daa90409834d89b4b75bfeb4e7c501ddef94b2ac4`; R16 `evrp-common-hard-constraints-v1`, `1b1c3132b44a542605b19f354a5d9c7464a093aa4cb23b04583ca92e0841ec67`; Network V18 `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`; R17 formulation `656cdf23ab85fed1d04e2e20f9840da161d2c3aac5f4ac61e6bad6219ff84143`; solver config `b948bbd31edf8576e3ec2420c50bc6996e4e89db8a5f0e8116d42f76bdd7f3b1`.
- **Output Hashes:** retry-02 preflight `465b9626f1795fa4db955c36bc6a48fa6571af0f299a92c85d18fdcb125fd5b6`; index smoke `791ef75c2c29681ad4096ce2a808a98acaeede8b0a0bf3b40ade14b88353ddf7`; parameter compatibility smoke `5b14d9c3d2a080c3820ead215af50b31fe0703e5beae16a6a43333ef7b2a99de`; execution validation `ac9f6b903a22dc45b6c6decb5f80b7507c5fdb7e807d0d9fc813493e8aaec895`; solver output `be2845614c25b1dcc3c42c158c350934cf11321f7b223ad040c38c7905a6e0e0`; manifest `626e6637833b85f77202ce98e521ce08242e45194562ff0fa5e0fb39e1192454`.
- **Software Versions:** Python 3.11.15; OR-Tools 9.12.4544. Solver did not start.
- **Results:** `DefaultRoutingSearchParameters()`生成、strategy/metaheuristic/time/logging/solution_limit設定はsupported。`random_seed`, `num_search_workers`, `deterministic`はfield absent。固定R17 configを完全適用できないためsolver status `NOT_STARTED`、termination reason `PARAMETER_COMPATIBILITY_SMOKE_FAIL`。solverは起動していない。
- **Validation Results:** R18 execution-level validation FAIL。parameter compatibility smoke FAIL。R19独立validatorは未実行。
- **Issues:** `routing_enums_pb2.RoutingSearchParameters()`は使用せず、`pywrapcp.DefaultRoutingSearchParameters()`へ修正。installed 9.12.4544にseed/worker/deterministic fieldがないため、代替設定を採用せず停止。
- **Decision:** FAIL — valid solver solutionなし。R19は開始しない。
- **Next Allowed Stage:** NONE（R18 FAILのため停止）

## R18 OR-Tools applicability diagnosis — 2026-09-10（diagnosis only; no solver execution）

- **Scope:** R15 current common instance `7ca39facf83de619db7ec37daa90409834d89b4b75bfeb4e7c501ddef94b2ac4`、R16 current constraint `evrp-common-hard-constraints-v1` / `1b1c3132b44a542605b19f354a5d9c7464a093aa4cb23b04583ca92e0841ec67`、V18 network authorityを対象に、OR-Tools適用可能性だけを監査した。R18 solver execution、solver implementation completion、R19以降は実施していない。
- **Current problem reconstruction:** single depot `DEP_006`、10 customers、1 delivery vehicle、1 accepted charger `OTA_KEIHIN_TRUCK_TERMINAL_A`、directed accepted OD 132本。各customerは`q_i=1` delivery requestと`m_i=1.1 kg` payloadを分離して持つ。service timeは2.5 min、service-start Time Window、payload capacity 2000 kg、battery 41.0 kWh、initial SOC 1.00、minimum/return SOC 0.20、energy `distance_km * 0.35344827586206895 kWh/km`、effective charging 70 kW、1 event最大30 min、charger再訪問可、consecutive charging visit禁止、HC09 operating-timeはBaseline disabled、未配送customerは許容、unreachable arcはsolverへ有限値で代入しない。
- **Fixture/general distinction:** `n=10 → 11 event slots`はroute gapから導くfixtureの有限上限であり、一般nでは`n+1` slotsを生成するschema-level encodingにすぎない。これはcharger訪問回数をR16の意味より小さく制限してはいけない。RoutingModelのnode copyだけで任意のpartial recharge/stateを一般nへ自動的に表現できることは確認できない。

### HC01〜HC13 applicability matrix

| HC | Constraint | RoutingModel標準 | Custom RoutingModel | CP-SAT | 難易度 | 意味保存可否 |
|---|---|---|---|---|---|---|
| HC01 | Customer visit at most once; zero allowed | DIRECTLY_SUPPORTED（optional disjunction） | 不要 | SUPPORTED_WITH_STANDARD_MODELING | 低 | 可 |
| HC02 | Depot start/return | DIRECTLY_SUPPORTED | 不要 | SUPPORTED_WITH_STANDARD_MODELING | 低 | 可 |
| HC03 | Flow conservation | DIRECTLY_SUPPORTED（successor route） | 不要 | SUPPORTED_WITH_STANDARD_MODELING | 低 | 可 |
| HC04 | Subtour elimination | DIRECTLY_SUPPORTED（RoutingModel route） | 不要 | SUPPORTED_WITH_STANDARD_MODELING（flow + connectivity/order） | 中 | 可 |
| HC05 | Vehicle assignment | DIRECTLY_SUPPORTED | 不要 | SUPPORTED_WITH_STANDARD_MODELING | 低 | 可 |
| HC06 | Payload capacity on every segment | SUPPORTED_WITH_STANDARD_MODELING（capacity dimension、`m_i`を整数scale。`q_i`とは別） | 不要 | SUPPORTED_WITH_STANDARD_MODELING | 低〜中 | 可 |
| HC07 | Service-start TW | SUPPORTED_WITH_STANDARD_MODELING（Time dimension + slack + service transition） | service/arrival conventionの明示が必要 | SUPPORTED_WITH_STANDARD_MODELING | 中 | 条件付きで可 |
| HC08 | Travel + service + waiting + charging on one time axis | REQUIRES_CUSTOM_MODELING（travel/service/waitのみは可、charging decision連動は不可） | REQUIRES_STATE_EXPANSION | REQUIRES_CP_SAT（または同等のjoint state model） | 高 | CP-SATなら可 |
| HC09 | Optional maximum operating time | DIRECTLY_SUPPORTED（dimension upper bound。ただしBaseline disabled） | 不要 | SUPPORTED_WITH_STANDARD_MODELING | 低 | 可 |
| HC10 | Arc energy and SOC lower bound | NOT_PRACTICALLY_SUPPORTED by plain RoutingModel dimension | REQUIRES_STATE_EXPANSION | REQUIRES_CP_SAT | 非常に高 | standalone CP-SATなら可 |
| HC11 | Initial/final SOC | NOT_PRACTICALLY_SUPPORTED by plain RoutingModel dimension | REQUIRES_STATE_EXPANSION | REQUIRES_CP_SAT | 高 | standalone CP-SATなら可 |
| HC12 | Revisit, partial charge, power-time link, 30 min/event, SOC cap, no consecutive charge | NOT_PRACTICALLY_SUPPORTED by standard RoutingModel | REQUIRES_STATE_EXPANSION（finite event copiesでもstate linkが必要） | REQUIRES_CP_SAT | 非常に高 | standalone CP-SATなら可 |
| HC13 | Accepted reachable directed arcs only | SUPPORTED_WITH_STANDARD_MODELING（allowed/forbidden arcを明示。finite penaltyで代替不可） | 不要 | SUPPORTED_WITH_STANDARD_MODELING | 中 | 可 |

**Overall:** HC01〜HC07、HC09、HC13はRoutingModelの得意範囲。ただしHC08は充電なしの時間モデルに限る。HC10〜HC12を含むR16全体はRoutingModel単独では意味保存できない。

### Focused findings

- **Time Window / service / waiting:** RoutingDimensionはarc travel、node service、slackによるwaiting、cumul upper/lower boundを表現できる。ただしR16は`b_i`をservice startと定義するため、cumulがarrivalなのかservice startなのかを一意に固定し、serviceをどのtransitionへ加えるかを証明する必要がある。充電時間がdecision variableになると、標準dimensionだけでは同じ時刻軸への完全な連動にならない。
- **Capacity:** `AddDimensionWithVehicleCapacity`相当で`payload_mass_kg=m_i`をsegment loadとして扱える。`q_i=1`はdelivery request countでありkgへ変換しない。整数scaleとpickup/delivery directionを固定すればHC06は意味保存可能。現行R18試作はこの仕様を完全に実行検証していない。
- **SOC / battery:** RoutingDimensionは通常、routeに沿う単調なcumul/resourceを扱う。移動でenergyが減り、chargerで増える状態を、route選択・charger選択・SOC連続値・return boundと同時に表現する標準dimensionのcontractはない。負のtransitやdimension cumulを用いたworkaroundは、chargerでの増加、capacity上限、event duration連動、partial chargeを完全には表現せず、意味保存の根拠にならない。
- **Charging:** R16のchargingは、(i) charger再訪問、(ii) eventごとの増加、(iii) `charged_energy = power * duration`、(iv) duration≤30 min、(v) SOC≤1、(vi) consecutive event禁止、(vii) route/time/SOCとの同時連動を要求する。duplicated charger nodeや11 finite copiesは候補表現に過ぎず、copy選択をSOC/time stateへjointly linkしない限り不完全。standard RoutingModelの固定arc cost/node visitではpartial recharge decisionを表現できない。

### RoutingModel + CP-SAT reassessment

単純なhybrid（RoutingModelでrouteを決め、CP-SATで後からSOC/chargingを検査）は不適切。route successor variablesはRoutingModel内部に閉じ、CP-SAT state variablesと同一のjoint objective/constraint graphを形成しないため、後検査はfeasible routeの選別に留まり、一次目的・二次travel-time最適性とcompletenessを失う。反復（route生成→state check→cut/no-good→再solve）を追加しても、cutの完全性、終了条件、optimality証明、同一辞書式objectiveの保証が別途必要で、現仕様の標準architectureとしては採択しない。

RoutingModelとCP-SATを本当にjointにするには、RoutingModelのrouteを外部化してCP-SATのarc binary variablesへ移すか、CP-SATをmasterとして全stateを同一モデルへ入れる必要がある。その時点で実質的にはCP-SAT standalone formulationであり、単純hybridの利点は失われる。

### CP-SAT standalone comparison

CP-SAT standaloneなら、arc binary `x_ij`、visit `y_i`、vehicle assignment、order/MTZまたはflow、service-start/wait time、payload/load、SOC/energy、charger event used、charged energy、duration、post-charge SOCを同一modelへ定義できる。`x_ij`とstate transitionをbig-Mまたはreified linear constraintsでlinkし、charger event slotは一般nの`n+1`上限として展開できる。`charged_energy = 70 kW * duration`は整数scaleで線形化し、duration≤30 min、SOC≤1、consecutive charging禁止を同一modelへ入れられる。

CP-SATの欠点は、model builder・整数scale・big-M上限・symmetry・route connectivity・解読・性能設計をすべて実装する必要があり、RoutingModelより複雑なこと。n=10 fixtureではこの複雑性を受入可能で、R16意味保存とQUBOとのvariable/constraint対応を明確にできる。production/scalingでは性能限界を測定し、無制限なn拡大を仮定してはいけない。将来QUBO比較に対しては、CP-SATのbinary decision/state variablesとQUBO encodingの対応を同一に設計しやすい。

### Existing R17/R18 prototype audit

| Area | Current classification | Finding |
|---|---|---|
| R17 formulation files | SPECIFICATION ONLY | `build_formulation_spec.py`はJSON spec/mapping/schemaを生成し、mapping内にもimplementation deferredを記録。solver modelは構築しない。 |
| R17 validation | SPECIFICATION VALIDATION ONLY | `validate_formulation_spec.py`は13 IDs、hash、semantic fields、config presenceを検査するが、solver feasibility・SOC・charging joint modelは検査しない。 |
| RoutingIndexManager | INCOMPLETE PROTOTYPE / API compatibility fixed in prior retry | 3-argument constructor smokeは通過したが、これはmodel completenessを示さない。 |
| Search parameters | INCOMPLETE PROTOTYPE / API compatibility diagnosed | `DefaultRoutingSearchParameters()`はinstalled APIで生成できるが、R17固定の`random_seed`、`num_search_workers`、`deterministic` fieldsは9.12.4544にない。solver executionは未成立。 |
| SOC state | NOT_IMPLEMENTED in executable solver | R17 specはcustom CP-SAT stateを要求するが、R18 runnerはroute後にSOCを手計算しているだけで、solver constraintではない。 |
| Charging events | NOT_IMPLEMENTED in executable solver | R18 outputに11 unused slotsを出す枠だけあり、charger visit、partial charge、duration-energy link、consecutive prohibitionをsolve中に表現していない。 |
| Route/state linking | NOT_IMPLEMENTED | RoutingModel routeとSOC/charging stateをjointly linkするCP-SAT model、cuts、iteration、optimality contractはない。 |
| Objective | INCOMPLETE PROTOTYPE | R17はlexicographic two-phaseをspecifyしたが、試作runnerのphase/objective実装はその保証を実行・検証できる状態ではない。 |
| Output/validation | PARTIAL | schema、trajectory、manifestの枠はあるが、valid solver outputとR19-independent feasibility validationは未生成。 |

### Architecture recommendation

- **Fixture n=10:** **C: CP-SAT standalone**を推奨。HC01〜HC07/HC09/HC13は標準linear constraints、HC08/HC10/HC11/HC12は同一CP-SAT state modelで表現し、route/state/chargingをjointly solveする。RoutingModelは比較用のrelaxed routing smokeまたはarc-data utilityに限定する。
- **Production/scaling:** まず同じCP-SAT semanticsで小〜中規模の性能境界を測る。RoutingModel単独へ戻すのはSOC/chargingを別問題へ分離する場合だけで、現R16 EVRPの同一比較branchには採用しない。CP-SATが規模上限に達した場合は、仕様を変更せず、明示的な decomposition/column-generation等を別設計として診断・承認する。
- **Recommended architecture:** **C: CP-SAT standalone**。Bの単純RoutingModel+CP-SATは採択しない。Dの他solverは今回の対象外。

### Implementation gap analysis for recommended C

| Item | Status | Required work |
|---|---|---|
| model builder | NOT_IMPLEMENTED | current R15/R16 schemaからCP-SAT modelを生成し、units/scaleをlockする |
| variables | NOT_IMPLEMENTED | arc, visit, vehicle, order, time, wait, load, SOC, event, duration, charge-energy variables |
| constraints | NOT_IMPLEMENTED | HC01〜HC13をjoint modelへ一対一対応させる。HC09 disabled flagを保持 |
| objective | PARTIAL | lexicographic priorityはspecのみ。二段階CP-SATまたは厳密なhierarchical solveを実装・検証する |
| charging model | NOT_IMPLEMENTED | 11 fixture slots / general n+1 slots、partial charge、70 kW、30 min、SOC cap、revisit、no consecutiveを実装 |
| state propagation | NOT_IMPLEMENTED | directed arcごとのenergy、service/wait/charge time、initial/final SOCをroute binaryとlinkする |
| solver config | PARTIAL | R17 configは保存済みだがRoutingModel APIとCP-SAT parameter semanticsは未採択。seed/workers/determinismのCP-SAT対応を別に固定する必要がある |
| solution decode | NOT_IMPLEMENTED | CP-SAT assignmentからroute、node trajectory、SOC、payload、charging eventを再構成する |
| output schema | PARTIAL | R18 schema案は存在するがCP-SAT stateに対する確定contractではない |
| independent validation support | PARTIAL | R16 validator contractは存在するが、CP-SAT outputを独立再計算するR19 validatorは未実装 |

### Diagnosis decision

- **OR-Tools applicability:** yes, but not as plain RoutingModel. OR-Tools CP-SAT can represent the current EVRP with meaning preserved after a new standalone formulation is designed and validated.
- **RoutingModel alone:** no for full R16 semantics; acceptable only for a relaxed non-charging/state-free subproblem.
- **RoutingModel + CP-SAT:** no as a post-check hybrid; it is incomplete unless route binaries and all state constraints are moved into one joint model.
- **CP-SAT standalone:** technically appropriate and recommended for fixture; scalability remains an empirical gate.
- **Current implementation completeness:** R17 is specification/validation only; R18 is an incomplete prototype with prior API errors, no executable SOC/charging constraints, no route/state joint linking, and no valid solver output.
- **R17/R18 redesign:** reopen R17 as architecture/formulation selection; replace RoutingModel-centered executable plan with CP-SAT standalone design, then independently validate the new formulation before any R18 execution. Preserve all existing R17/R18 PASS/FAIL history.
- **User decision required:** approve or reject architecture C (CP-SAT standalone), and separately approve the CP-SAT parameter contract for seed, workers, determinism, integer scales, big-M bounds, and solver time limit. Until that decision and a new formulation gate, do not implement or execute R18.
- **Next Allowed Stage:** NONE — architecture decision and formulation re-acceptance required; R19+ remain NOT_STARTED.

## R17 CP-SAT standalone redesign/formulation specification — 2026-09-10

- **Scope:** R17 current architectureを`C: CP-SAT standalone`として再設計したformulation specificationのみ。RoutingModelおよびRoutingModel+CP-SAT hybridはcurrent formulationから除外し、過去R17/R18 prototypeはhistorical/prototypeとして保持した。solver code、R18 execution、R19以降は実施していない。
- **Status:** BLOCKED（specificationは作成済みだが、conditional charger-slot orderingの実装証明、integer model tests、repeated-run reproducibility、independent validatorが未実装）
- **Started At / Completed At:** 2026-09-10T01:10:00+09:00 / 2026-09-10T01:20:00+09:00
- **Commands:** installed runtime audit `.conda/bin/python` with `ortools.sat.python.cp_model.CpSolver().parameters`; no solver/model solve command. R15/R16 JSON read-only reconstruction.
- **Input Hashes:** R15 `7ca39facf83de619db7ec37daa90409834d89b4b75bfeb4e7c501ddef94b2ac4`; R16 `evrp-common-hard-constraints-v1` / `1b1c3132b44a542605b19f354a5d9c7464a093aa4cb23b04583ca92e0841ec67`; V18 network `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`.
- **Outputs:** [CP-SAT formulation spec](reproducibility/outputs/traffic_simulation/demand/evrp_r17_cpsat_standalone/20260910_r17_cpsat_standalone_formulation_fixture_n10_v18/cpsat_formulation_spec.json); [formulation validation report](reproducibility/outputs/traffic_simulation/demand/evrp_r17_cpsat_standalone/20260910_r17_cpsat_standalone_formulation_fixture_n10_v18/r17_cpsat_formulation_validation_report.json).
- **Output Hashes:** specification `d012fe1871c4d63695e6ac294e7b1bc3835481ccd81fe7f41d234d1d5679c4fe`; validation report `2adc02c8801b676d21814b095d16f20cf3adc03559d9c6d15aedda8b8ffc453c`.
- **Formulation summary:** position-indexed route with `x_pij` positional arc binaries and aggregate `x_ij`, `node_at[p,i]`, `active[p]`, `y_i`, exact depot start/return, payload grams, time milliseconds, energy joules, and 11 charger-event slots. General route positions are `2n+3`; charger slots are `n+1` from the R16/R17 route-gap derivation.
- **Integer units:** time ms; energy J; payload g; source distance remains m. Battery `147,600,000 J`, minimum `29,520,000 J`, charging `70 J/ms`, event cap `1,800,000 ms`. Arc travel time uses ceiling to ms. Arc energy uses `ceil(Decimal(distance_m) * Decimal(energy_rate_kWh_per_km) * 3600)` J, so energy is never rounded downward and feasibility is not overestimated.
- **HC01〜HC13:** HC01〜HC07、HC09、HC13はposition/flow/capacity/time/allowed-arc constraintsでmapping。HC08、HC10、HC11、HC12はCP-SATの同一state modelでroute/time/energy/chargingをjointly link。HC09はBaseline disabledを保持。
- **Charging:** `used_e`、`charger_slot_e_p`、`charge_duration_e`、`charge_energy_e`を使用し、`charge_energy_e=70*duration_e`、duration≤1,800,000 ms、post-energy≤battery、同一physical chargerの再訪問、consecutive charger positions禁止を定義。11 slotsはn=10の上限であり、任意の小さい訪問回数制限ではない。
- **Objective:** penalty weightではなく二段階CP-SAT。第1 solveで`n-sum(y_i)`最小化、最適served数を固定、第2 solveでtotal travel time最小化。第2目的が第1目的を逆転しない。
- **Big-M:** 原則OnlyEnforceIfとbounded exact equalityを使用。slot-position orderingだけはconditional orderの実装証明が未完で、必要時のtight boundは`P-1=22`（fixture）と導出済み。恣意的な`1e6`は使用しない。
- **Runtime solver parameter audit:** OR-Tools 9.12.4544 CP-SATで`random_seed`、`num_search_workers`、`max_time_in_seconds`、`log_search_progress`はsupported。deterministic専用fieldは要求しない。solverは未実装・未実行。
- **Validation:** integer units/overflow bounds/HC mapping/11-slot meaning/objective/output decode contractはspec-level PASS。conditional slot ordering proof、integer CP-SAT model tests、repeated-run comparison、R19 independent validatorは未完了のためoverall BLOCKED。
- **Decision:** CP-SAT standalone architectureを正式採択したが、R17 formulation gateは未通過。既存R17/R18のPASS/FAIL historyは変更・削除していない。
- **Next Allowed Stage:** NONE。上記blocking itemsを解消し、新R17 formulationを再validationしてPASSするまで、`R18_CP_SAT_IMPLEMENTATION_AND_EXECUTION`を開始しない。

## R17 charger-slot ordering proof and integer-model smoke-test specification — 2026-09-10

- **Scope:** R17 CP-SAT standalone formulationのconditional charger-slot ordering proofと、R18前に実施すべきinteger-model smoke-test contractの仕様化のみ。CP-SAT solver実行、R18本実行、R19以降は未実施。
- **Status:** BLOCKED（classification: `FORMULATION_COMPLETE_TESTING_PENDING`）。conditional orderingはCP-SAT API/formulation levelでRESOLVED。ただしinteger model smoke tests、repeated-run reproducibility、R19 independent validatorは未実行/未実装。
- **Started At / Completed At:** 2026-09-10T01:25:00+09:00 / 2026-09-10T01:35:00+09:00
- **Commands:** OR-Tools 9.12.4544の`CpModel.AddImplication`、`Add(... > ...).OnlyEnforceIf(...)`、Boolean channelingのmodel-construction API smoke。solver callなし。
- **Inputs:** R15 `7ca39facf83de619db7ec37daa90409834d89b4b75bfeb4e7c501ddef94b2ac4`; R16 `evrp-common-hard-constraints-v1` / `1b1c3132b44a542605b19f354a5d9c7464a093aa4cb23b04583ca92e0841ec67`; V18 network `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`.
- **Outputs:** [ordering proof](reproducibility/outputs/traffic_simulation/demand/evrp_r17_cpsat_standalone/20260910_r17_cpsat_standalone_formulation_fixture_n10_v18_slot_order_proof/charger_slot_ordering_proof.json); [integer-model smoke contract](reproducibility/outputs/traffic_simulation/demand/evrp_r17_cpsat_standalone/20260910_r17_cpsat_standalone_formulation_fixture_n10_v18_slot_order_proof/integer_model_smoke_test_contract.json); [validation report](reproducibility/outputs/traffic_simulation/demand/evrp_r17_cpsat_standalone/20260910_r17_cpsat_standalone_formulation_fixture_n10_v18_slot_order_proof/r17_slot_order_validation_report.json).
- **Output Hashes:** ordering proof `92d9bccce409aba6ad44cccd9d8e5493a1c4c9db55cb5bd6246e234dec818e0d`; smoke contract `a68c3ec63b922eb24a5cbea59c695bec57bb79ca9fdec59843904321921de3d5`; validation report `8ad2dec265505136379e9f73f8cf5be05dabbf3a116cee16f9724b2a2a69518b`.
- **Slot ordering proof:** `slot_used[c+1] => slot_used[c]` via `AddImplication`; used-slot order via `Add(slot_position[c+1] > slot_position[c]).OnlyEnforceIf(slot_used[c+1])`; unused slot position is fixed to 0 and no ordering is imposed on it. This uses no Big-M.
- **Route-slot link:** `sum_p slot_at[c,p]=slot_used[c]`; `sum_c slot_at[c,p]=charger_at[p]`; `slot_at[c,p] => slot_position[c]=p`; at most one slot per route position. Thus a slot cannot be metadata-independent from route state, a used slot requires a charger node, and every charger visit has exactly one slot.
- **Charging semantics:** used slot duration is `1..1,800,000 ms`; unused slot duration and energy are exactly 0; `slot_energy=70*duration` is an unconditional exact integer equality; post-charge energy is linked and capped at `147,600,000 J`; charger positions cannot be consecutive, independent of duration, so zero-duration dummy visits cannot bypass HC12.
- **Time/state link:** slot duration is channelled to charger-position charge duration; charger departure includes that duration; next arrival uses the selected directed arc. Non-charger positions have zero charge duration/energy.
- **n+1 proof:** with k served customers there are k+2 non-charger route events including depot start/return, hence k+1 gaps. No consecutive charger visits permits at most one charger event per gap, so events≤k+1≤n+1. For n=10, 11 slots cover every allowed route without imposing a smaller visit cap.
- **Smoke contract:** 8 cases specified: no charger, one charger, multiple revisit, consecutive charger infeasible, duration-over-cap infeasible, post-charge capacity-overflow infeasible, minimum-energy violation infeasible, and unused-slot neutrality. Expected route, slot, energy, and time behavior are machine-readable; none were solved in this step.
- **Decision:** conditional charger-slot ordering blocker is RESOLVED at formulation/API level. R17 remains BLOCKED until the listed integer-model smoke tests and later reproducibility/independent-validation gates pass. R18 solver execution is not authorized.
- **Next Allowed Action:** Execute only the specified R17 integer-model smoke tests after explicit implementation authorization; do not start R18. Current `Next Allowed Stage: NONE`.

## R17 integer-model smoke tests — 2026-09-10

- **Scope:** R17 CP-SAT standalone integer-model smoke tests 8件のみ。R18本番n=10 solver、R19以降は未実施。
- **Status:** PASS（8/8 expected status、decoded state checks、feasible-test repeated-run comparison PASS）。R17 overall remains `FORMULATION_COMPLETE_TESTING_PENDING`/BLOCKED until the independent validator and full formulation gate are completed.
- **Commands:** `.conda/bin/python 05_src/traffic_simulation/evrp_r17_cpsat_standalone/run_integer_model_smoke_tests_v2.py --output-dir reproducibility/outputs/traffic_simulation/demand/evrp_r17_cpsat_standalone/20260910_r17_integer_model_smoke_fixture_n10_v18_retry_01`.
- **Configuration:** OR-Tools 9.12.4544; random_seed `20260909`; num_search_workers `1`; deterministic intent via single worker; max_time_in_seconds `2.0` per test; log_search_progress `false`.
- **Input:** current smoke contract; R15 `7ca39facf83de619db7ec37daa90409834d89b4b75bfeb4e7c501ddef94b2ac4`; R16 `evrp-common-hard-constraints-v1` / `1b1c3132b44a542605b19f354a5d9c7464a093aa4cb23b04583ca92e0841ec67`.
- **Results:** T01 `OPTIMAL/OPTIMAL PASS`; T02 `OPTIMAL/OPTIMAL PASS`, 1 slot, duration `1715 ms`, energy `120050 J`; T03 `OPTIMAL/OPTIMAL PASS`, 2 slots, positions strictly increasing, prefix PASS, no consecutive charger; T04 `INFEASIBLE PASS`; T05 `INFEASIBLE PASS`; T06 `INFEASIBLE PASS`; T07 `INFEASIBLE PASS`; T08 `OPTIMAL/OPTIMAL PASS`, 1 used slot and 10 neutral unused slots.
- **State validation:** feasible tests independently checked prefix/order, positive used duration, zero unused duration/energy, exact `E_charge=70*t_ms`, energy bounds, and time propagation. T02/T03/T08 decoded energy/time trajectories were stored per test.
- **Repeated-run:** T01, T02, T03, T08 repeated with the same seed/config; status, route, slot usage/position/duration/energy, time state, energy state, and objective matched.
- **Infeasibility diagnostics:** relaxation records were generated for T04–T07; main expected outcomes are valid. Some relaxed diagnostic variants require follow-up tightening of the smoke harness domains before treating the relaxation as sole-cause proof.
- **Artifacts:** `reproducibility/outputs/traffic_simulation/demand/evrp_r17_cpsat_standalone/20260910_r17_integer_model_smoke_fixture_n10_v18_retry_01/`; aggregate report SHA-256 `65cc606b2847370dcb2f9c7fd5bf0de5855acfafa4c97a12f741ba5633e38fc5`.
- **Decision:** integer-model smoke behavior and reproducibility PASS, but R17 remains BLOCKED because relaxed-cause diagnostics are not fully clean and R19 independent validator remains pending. No R18 execution authorized.
- **Next Allowed Action:** tighten/re-run only the R17 smoke-harness relaxation diagnostics and then perform formulation gate review; `Next Allowed Stage: NONE` for R18.

## R17 relaxed diagnostic harness and formulation gate review — 2026-09-10

- **Scope:** R17 CP-SAT standalone T04〜T07 relaxed diagnostics and formulation gate review only. R18 production n=10 solver and R19+ were not started.
- **Started At / Completed At:** 2026-09-10 / 2026-09-10
- **Status:** BLOCKED. T04, T06, T07 causal controls passed; T05 target-only control remained INFEASIBLE for an independently derived battery/minimum-energy reason.
- **Command:** `.conda/bin/python 05_src/traffic_simulation/evrp_r17_cpsat_standalone/run_relaxed_diagnostics_and_gate_review.py --output-dir reproducibility/outputs/traffic_simulation/demand/evrp_r17_cpsat_standalone/20260910_r17_relaxed_diagnostics_formulation_gate_fixture_n10_v18_retry_02`
- **Input Hashes:** smoke-test contract `a68c3ec63b922eb24a5cbea59c695bec57bb79ca9fdec59843904321921de3d5`; prior T01〜T08 aggregate `65cc606b2847370dcb2f9c7fd5bf0de5855acfafa4c97a12f741ba5633e38fc5`.
- **Output Hashes:** relaxed aggregate `c94b50f282e0b5452d98a20f00b10c809259abab52ba71c2962c2fb4b64aced6`; gate review `aba514751bc2d06641311cfca536a6edaab55beb077701223a8d500846f49d6f`.
- **Software / Solver:** OR-Tools 9.12.4544; CP-SAT; random seed 20260909; one worker; diagnostic limit 2 s/test; no production solver execution.
- **T04:** original `INFEASIBLE`; control `OPTIMAL`. Only consecutive-charger prohibition was removed. T04 route was corrected to include movement energy, avoiding a separate full-battery charging conflict.
- **T05:** original `INFEASIBLE`; target-only control `INFEASIBLE`. Duration domain was extended from 1,800,000 to 1,800,001 ms and the explicit duration cap was removed; exact 70 J/ms linkage and battery/minimum-energy constraints remained. The control is mathematically infeasible because `29,520,000 + 70×1,800,001 = 155,520,070 J > 147,600,000 J`. Thus the current fixture cannot isolate the duration cap under unchanged remaining constraints.
- **T06:** original `INFEASIBLE`; control `OPTIMAL`. Only the post-charge battery upper-bound constraint was relaxed; energy domain was extended consistently for diagnosis.
- **T07:** original `INFEASIBLE`; control `OPTIMAL`. Only minimum-energy inequalities were removed; energy propagation and domains remained unchanged.
- **Formulation gate:** route/slot linkage PASS; prefix/order PASS; charger revisit PASS; consecutive charging PASS; time/payload/energy propagation PASS; charging duration-energy exactness PASS; battery bounds BLOCKED by T05 causal isolation; unused-slot neutrality PASS; integer consistency PASS; repeated-run reproducibility PASS; HC01〜HC13 mapping review PASS.
- **Artifacts:** `reproducibility/outputs/traffic_simulation/demand/evrp_r17_cpsat_standalone/20260910_r17_relaxed_diagnostics_formulation_gate_fixture_n10_v18_retry_02/` contains per-test diagnostics, aggregate, manifest, and `r17_formulation_gate_review.json`.
- **Issues:** T05 requires a semantically valid causal diagnostic redesign or formal retirement as a redundant-bound test. R19 independent validator remains not started.
- **Decision:** Keep current R17 BLOCKED; do not promote to PASS and do not start R18/R19.
- **Next Allowed Action:** Redesign or formally retire the T05 causal diagnostic, then rerun only the R17 gate review.

## R17 T05 charging-duration-cap causal diagnostic redesign — 2026-09-10

- **Scope:** T05 causal diagnostic preflight/re-design only. No CP-SAT solver execution, R18 production execution, or R19 execution.
- **Status:** BLOCKED before solver execution because the requested control case is mathematically impossible under unchanged R16/R17 semantics.
- **Required values:** charging duration `1,800,001 ms`; charging power `70 J/ms`; battery capacity `147,600,000 J`; minimum energy `29,520,000 J`.
- **Isolation calculation:** control feasibility requires `E_arr <= 147,600,000 - 70×1,800,001 = 21,599,930 J`, while minimum-energy requires `E_arr >= 29,520,000 J`. The interval is empty. At the minimum permitted arrival energy, departure energy is `155,520,070 J`, exceeding capacity by `7,920,070 J`.
- **Derived bound:** unchanged battery and minimum-energy constraints imply a maximum charging duration of `floor((147,600,000−29,520,000)/70) = 1,686,857 ms`, with 10 J residual. Therefore the existing 1,800,000 ms cap is already redundant for this diagnostic configuration.
- **Original / control:** original remains `INFEASIBLE`; a valid duration-cap-only relaxed control cannot be constructed. The solver was intentionally not run with an invalid fixture.
- **Artifact:** `reproducibility/outputs/traffic_simulation/demand/evrp_r17_cpsat_standalone/20260910_r17_t05_duration_cap_causal_retry_03/T05_causal_diagnostic_preflight.json` (SHA-256 `5a3bc0f74acc770b74a02245f3ea9fbf3b6a1322f75c4a61fec1bd1f7b076246`).
- **Conclusion:** T05 causal confirmation is not established. Making the control feasible would require changing battery capacity, charging power, or minimum-energy semantics, which is outside this request and would invalidate the causal isolation.
- **R17 gate:** remains `BLOCKED`; prior T01〜T08 and T04/T06/T07 results are retained unchanged. R19 independent validator remains a later-stage implementation issue, but the T05 formulation-gate blocker is unresolved.
- **Next Allowed Action:** redesign the diagnostic with an allowed semantic change or formally retire T05 as a redundant-bound causal test; do not start R18/R19.

## R17 T05 redundant-bound proof and formulation gate reclassification — 2026-09-10

- **Scope:** T05 classification and R17 formulation gate review only. R18/R19 were not executed.
- **T05 classification:** `DURATION_CAP_REDUNDANCY_PROOF`（旧 `DURATION_CAP_CAUSAL_INFEASIBILITY_TEST` から変更）。
- **Baseline:** `E_max=147,600,000 J`; `E_min=29,520,000 J`; `P=70 J/ms`; `t_session,max=1,800,000 ms`.
- **Proof:** `t_max^battery=(E_max−E_min)/P=118,080,000/70=1,686,857.142857 ms`; floorは `1,686,857 ms`、余りは `10 J`。従って `1,686,857.142857 < 1,800,000 ms`、差は `113,142.857143 ms`（約1分53.143秒）。
- **Conclusion:** arrival energyが`E_min`以上である限り、battery upper boundを守れる1 charging eventの最大時間は約1,686,857.14 ms。HC12の30分上限はcurrent Baseline state-spaceではbattery/SOC boundsより緩く、独立にはbindingしない。これはformulation errorではない。
- **HC12:** `t_c^charge <= 1,800,000 ms`をCP-SAT general formulationから削除せず保持。annotationは `REDUNDANT_UNDER_CURRENT_BASELINE_PARAMETERS`。将来、minimum SOC、battery capacity、charging power、charger specificationが変わればbindingになり得る。
- **T05 expected result:** 30分超のeventはcurrent Baselineのbattery/SOC boundsで先に排除される。duration-cap-only FEASIBLE controlは構成不能であり、redundancy proofをPASSとする。
- **Gate acceptance:** constraint実装、causal test可能な制約の因果診断、mathematically redundantな制約の証明、誤実装でないことを確認する基準へ修正。T01/T02/T03/T08 positive tests、T04/T06/T07 causal diagnostics、slot/state/reproducibility、HC01〜HC13 mappingはすべてPASS。unresolved formulation issuesは`0`。
- **Artifact:** `reproducibility/outputs/traffic_simulation/demand/evrp_r17_cpsat_standalone/20260910_r17_t05_redundant_bound_proof_20260910/T05_redundant_bound_proof.json`（SHA-256 `9365f36041a358217b67418a7e0430012f770dda15327f9ebc40ed3fd45072ab`）。
- **Decision:** `R17_ORTOOLS_FORMULATION = PASS`。R19 independent validatorは未実装だが、R17 formulationの未解決issueには含めず、R19 stageの課題として保持。
- **Next Allowed Stage:** `R18_CP_SAT_IMPLEMENTATION_AND_EXECUTION`（今回は開始しない）。

## R18_CP_SAT_IMPLEMENTATION_AND_EXECUTION — CP-SAT Standalone Implementation and Execution

- **Status:** `PASS`
- **Started / Completed:** 2026-09-10 / 2026-09-10
- **Commands:** `.conda/bin/python -m py_compile 05_src/traffic_simulation/evrp_r18_execution/run_ortools_execution.py`; `.conda/bin/python 05_src/traffic_simulation/evrp_r18_execution/run_ortools_execution.py --instance reproducibility/outputs/traffic_simulation/demand/evrp_r15_common_instance/20260909_r15_common_instance_fixture_n10_v18_r09_v18_authority_closed --constraints reproducibility/outputs/traffic_simulation/demand/evrp_r16_constraints/20260909_r16_common_hard_constraints_v1_fixture_n10_charger_revisit_resolved_payload_fixed --formulation reproducibility/outputs/traffic_simulation/demand/evrp_r17_cpsat_standalone/20260910_r17_cpsat_standalone_formulation_fixture_n10_v18 --output-dir reproducibility/outputs/traffic_simulation/demand/evrp_r18_cpsat_execution/20260910_r18_cpsat_standalone_fixture_n10_v18_retry_02`
- **Input Hashes:** R15 `7ca39facf83de619db7ec37daa90409834d89b4b75bfeb4e7c501ddef94b2ac4` PASS; current R16 `1b1c3132b44a542605b19f354a5d9c7464a093aa4cb23b04583ca92e0841ec67` PASS after reference unification; network V18 hash `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2` PASS.
- **Output Hashes:** final execution manifest records hashes for all generated files; artifact path is `reproducibility/outputs/traffic_simulation/demand/evrp_r18_cpsat_execution/20260910_r18_cpsat_standalone_fixture_n10_v18_execution_03/`.
- **OR-Tools version:** `9.12.4544`.
- **Solver config:** CP-SAT standalone, random_seed `20260909`, num_search_workers `1`, max_time_in_seconds `300`, log_search_progress `true`; Stage 1 `150 s`, Stage 2 `150 s`, total `300 s`, dynamic transfer `disabled`.
- **Implementation:** position-indexed `x_pij`, aggregate arcs, node-at-position, active positions, served variables, depot/flow/subtour chain, payload grams, time milliseconds, waiting/service/departure, battery joules, 11 prefix charger slots, strict slot positions, one-to-one slot linkage, charge duration/energy, post-charge cap, and no consecutive charger positions. Arc travel and energy use R17 ceiling conversion. HC09 remains disabled; HC12 retains `REDUNDANT_UNDER_CURRENT_BASELINE_PARAMETERS`.
- **R16 hash audit:** classification `SEMANTICALLY_IDENTICAL_BUT_REPACKAGED`. Artifact: `reproducibility/outputs/traffic_simulation/demand/evrp_r16_constraints/20260909_r16_common_hard_constraints_v1_fixture_n10_charger_revisit_resolved_payload_fixed/constraint_spec.json`; manifest: same directory `r16_manifest.json`; declared version `evrp-common-hard-constraints-v1`; recomputed content hash equals `1b1c3132b44a542605b19f354a5d9c7464a093aa4cb23b04583ca92e0841ec67`. The prior reference had a transcription mismatch. HC01〜HC13 enabled flags/tolerances, HC12 repeated charger semantics, event upper-bound reference, and solver-independent validator contract have semantic diff `0`; only R15 input instance path/hash provenance differs from the payload-free R16 package.
- **Dependency propagation:** R15 reference remains `7ca39fac...`; R17 CP-SAT formulation and R18 execution contract/config now reference current R16 hash `1b1c3132b44a542605b19f354a5d9c7464a093aa4cb23b04583ca92e0841ec67`; constraint values and semantics unchanged.
- **Preflight:** `PASS` with positions `23`, nodes `12`, slots `11`, accepted arcs `132`, integer domains valid, Stage 1 `150 s`, Stage 2 `150 s`, total `300 s`; solver execution then started under this contract.
- **Stage 1 result:** `OPTIMAL`; objective unserved `0`, served `10`, best bound `0`, gap `0`, wall time `4.05624195 s`, conflicts `49`, branches `37034`, booleans `6964`.
- **Stage 2 result:** `OPTIMAL`; objective travel time `11527966 ms`, best bound `11527966 ms`, gap `0`, wall time `3.074861516 s`, conflicts `7`, branches `34331`, booleans `6311`.
- **Decoded solution:** served `10`, unserved `0`, fulfillment `1.0`; route distance `144529.80971 m`, travel `11527966 ms`, service `1500000 ms`, waiting `73051530 ms`, charging `1049104 ms`, total route time `87128600 ms`, minimum SOC `0.2515958333`, charging events `11`.
- **Validation:** R18 execution-level sanity checks `PASS` (depot start/end, no duplicate customers, 10=served+unserved, accepted arcs, finite decode, energy/SOC, slot linkage, objective consistency, source hashes). HC01〜HC13 independent recomputation remains R19 scope.
- **Reproducibility:** second identical run matched Stage 1/2 status/objective, served/unserved, route sequence, and charging slot usage; `PASS`.
- **Issues:** initial execution run `...execution_01` stopped with an unavailable optional statistics API; it was retained as FAIL evidence. The corrected new run `...execution_03` passed. No current unresolved R18 issue.
- **Decision:** `R18_CP_SAT_IMPLEMENTATION_AND_EXECUTION = PASS`.
- **Next Allowed Stage:** `R19_ORTOOLS_VALIDATION`; R19 was not started.

## R19_ORTOOLS_VALIDATION — OR-Tools Validation

- **Stage ID:** R19_ORTOOLS_VALIDATION
- **Objective:** 古典解のfeasibilityを独立確認する
- **Inputs:** 古典raw solution・同一I_s・共通validator
- **Preconditions:** 前工程 `R18_ORTOOLS_EXECUTION` のPASS（明示された正常結果遷移は例外）と、Inputsの存在・hash・根拠を確認する。
- **Method:** 経路から時間/荷量/SOC/訪問を再計算しsolver判定と照合
- **Validation:** feasible宣言解の全Hard Constraints合格、判定矛盾0ことを独立検査し、実行記録に診断を残す。
- **Acceptance Criteria:** feasible宣言解の全Hard Constraints合格、判定矛盾0
- **Stop Conditions:** Global Stop Rulesと当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義はBLOCKED、検証不一致・実行異常はFAIL。
- **Outputs:** 古典validation・validated incumbent
- **Status:** `PASS`
- **Started At / Completed At:** 2026-09-10 / 2026-09-10
- **Commands:** `.conda/bin/python 05_src/traffic_simulation/evrp_r19_validation/validate_cpsat_solution.py --r18 reproducibility/outputs/traffic_simulation/demand/evrp_r18_cpsat_execution/20260910_r18_cpsat_standalone_fixture_n10_v18_execution_03 --r15 reproducibility/outputs/traffic_simulation/demand/evrp_r15_common_instance/20260909_r15_common_instance_fixture_n10_v18_r09_v18_authority_closed --r16 reproducibility/outputs/traffic_simulation/demand/evrp_r16_constraints/20260909_r16_common_hard_constraints_v1_fixture_n10_charger_revisit_resolved_payload_fixed --out reproducibility/outputs/traffic_simulation/demand/evrp_r19_validation/20260910_r19_cpsat_solution_validation_fixture_n10_v18_retry_03`
- **Input Hashes:** R15 `7ca39facf83de619db7ec37daa90409834d89b4b75bfeb4e7c501ddef94b2ac4`; R16 `1b1c3132b44a542605b19f354a5d9c7464a093aa4cb23b04583ca92e0841ec67`; V18 network `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`; R18 input artifact `...execution_03`.
- **Output Hashes:** manifest at `reproducibility/outputs/traffic_simulation/demand/evrp_r19_validation/20260910_r19_cpsat_solution_validation_fixture_n10_v18_retry_03/manifest.json` records all output hashes.
- **Software / Validator:** Python 3.11 environment; independent validator `R19 independent validator v1`; R18 model builder/solver constraints were not reused.
- **HC01〜HC13:** HC01 `PASS`, HC02 `PASS`, HC03 `PASS`, HC04 `PASS`, HC05 `PASS`, HC06 `PASS`, HC07 `PASS`, HC08 `PASS`, HC09 `DISABLED`, HC10 `PASS`, HC11 `PASS`, HC12 `PASS`, HC13 `PASS`.
- **Independent reconstruction:** fulfillment `10/10 = 100%`; route distance `144529.80971 m`; travel `11527966 ms`; service `1500000 ms`; waiting `73051530 ms`; charging `1049104 ms`; total `87128600 ms`; minimum SOC `0.25159583333333335`; final SOC `0.25159583333333335`.
- **HC12:** all 11 events PASS; each accepted charger, positive duration, duration≤`1800000 ms`, `70*duration` energy, no consecutive charger visit, post-charge energy≤battery, continuity PASS. `E_max(10)=11`; use of 11 events is valid. Annotation `REDUNDANT_UNDER_CURRENT_BASELINE_PARAMETERS` retained.
- **Objective reconciliation:** Stage 1 unserved `0` and Stage 2 travel `11527966 ms` exactly match independent reconstruction. Distance/time reconciliation PASS. Minimum SOC independently matches reported R18 value exactly.
- **Mismatch:** none. Earlier validator attempts were retained as separate failed/retry artifacts; final retry_03 is the accepted result after correcting validator-only repeated-charger occurrence handling and charging-state ordering.
- **R20:** not started.
- **Decision:** `R19_ORTOOLS_VALIDATION = PASS`.
- **Next Allowed Stage:** `R20_QUBO_FORMULATION`.
- **Validation Results:** NOT_RUN
- **Issues:** 未実行。Acceptance Criteriaの未固定項目を実行開始時に解消し、解消不能ならBLOCKED
- **Decision:** NOT_RUN
- **Next Allowed Stage:** R20_QUBO_FORMULATION（Gate通過時のみ）

## R20_QUBO_FORMULATION — QUBO Formulation

- **Stage ID:** R20_QUBO_FORMULATION
- **Objective:** 同じI_sと制約をbinary encodingする
- **Inputs:** I_s・共通制約・小規模古典fixture
- **Preconditions:** 前工程 `R19_ORTOOLS_VALIDATION` のPASS（明示された正常結果遷移は例外）と、Inputsの存在・hash・根拠を確認する。
- **Method:** logical/binary/aux変数、penalty、離散化、decode、目的優先を記録
- **Validation:** 全13制約の表現が明示、係数/変数mapping/量子幅/単位が定義済ことを独立検査し、実行記録に診断を残す。
- **Acceptance Criteria:** 全13制約の表現が明示、係数/変数mapping/量子幅/単位が定義済
- **Stop Conditions:** Global Stop Rulesと当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義はBLOCKED、検証不一致・実行異常はFAIL。
- **Outputs:** QUBO仕様・matrix・encoding manifest
- **Status:** `BLOCKED`
- **Started At / Completed At:** 2026-09-10 / 2026-09-10
- **Commands:** `.conda/bin/python 05_src/traffic_simulation/evrp_r20_qubo_formulation/build_r20_spec.py --r15 reproducibility/outputs/traffic_simulation/demand/evrp_r15_common_instance/20260909_r15_common_instance_fixture_n10_v18_r09_v18_authority_closed --r16 reproducibility/outputs/traffic_simulation/demand/evrp_r16_constraints/20260909_r16_common_hard_constraints_v1_fixture_n10_charger_revisit_resolved_payload_fixed --r19 reproducibility/outputs/traffic_simulation/demand/evrp_r19_validation/20260910_r19_cpsat_solution_validation_fixture_n10_v18_retry_03 --out reproducibility/outputs/traffic_simulation/demand/evrp_r20_qubo_formulation/20260910_r20_qubo_formulation_fixture_n10_v18`
- **Input Hashes:** R15 `7ca39facf83de619db7ec37daa90409834d89b4b75bfeb4e7c501ddef94b2ac4`; R16 `1b1c3132b44a542605b19f354a5d9c7464a093aa4cb23b04583ca92e0841ec67`; R19 independent validation `PASS`; V18 network `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`.
- **Output Hashes:** manifest at `reproducibility/outputs/traffic_simulation/demand/evrp_r20_qubo_formulation/20260910_r20_qubo_formulation_fixture_n10_v18/manifest.json` records all artifacts.
- **Adopted encoding:** position-indexed, with exact binary expansion for CP-SAT integer ranges. Alternatives compared: arc-based, time/state-expanded, hybrid. No superseded RoutingModel or old R18 artifact used as authority.
- **HC mapping:** all HC01〜HC13 listed; HC09 `DISABLED`; HC07/HC10/HC11/HC12 require exact state discretization/bit encoding; no HC silently dropped. HC12 preserves 11 events, partial charge, 70 J/ms, event cap, post-charge battery cap, revisit, and no consecutive charger visit.
- **Resource estimate:** n=10 primary `8469`, Rosenberg auxiliary `5313`, total logical binary variables `13782`; estimated quadratic terms/couplers `17953`, density `0.00018905`. Scaling total logical variables: n=5 `5152`, n=10 `13782`, n=20 `49642`, n=50 `414022`.
- **Penalty strategy:** two-stage/hierarchical concept retained; numeric penalty coefficients are not invented before a complete coefficient-bound certificate. No QUBO matrix, Ising transform, QAOA/Aer, or R21 validation was run.
- **Feasibility:** exact full-EVRP formulation is specified but full n=10 is impractical for Aer/QAOA at the estimated logical width. Coarser time/energy discretization and any reduced quantum problem require explicit user decisions because they can change R16 semantics.
- **Validation Results:** variable registry, HC mapping completeness, no silent drop, quadratization registry, reproducible resource counts, and authority hashes `PASS`; formulation overall `BLOCKED` by unresolved discretization/reduction/penalty-certificate decisions.
- **Issues:** decide whether to adopt coarser state discretization, a reduced quantum subproblem, and a fully expanded penalty-bound certificate. R21 and later stages must not start.
- **Decision:** `R20_QUBO_FORMULATION = BLOCKED`.
- **Next Allowed Stage:** `NONE`.

## R20 QUBO application audit / gap analysis — 2026-09-10

- **Scope:** R20 artifact・R15/R16/R19 authority・repository sourceのread-only監査のみ。R20 formulationの作り直し、R21、Ising、QAOA/Aer、reduced problem採択は行わない。
- **Current maturity:** `FORMULATION_ONLY`。R20にはposition-indexed candidate、variable registry、HC mapping、exact bit-width案、penalty framework、Rosenberg auxiliary registry、resource/scaling estimateがある。一方、実装済みのcoefficient builder、sparse QUBO matrix、numeric penalty certificate、completed quadratization、QUBO decoder、R21 validatorはない。
- **Authority reconstruction:** R15 `7ca39facf83de619db7ec37daa90409834d89b4b75bfeb4e7c501ddef94b2ac4`; R16 `evrp-common-hard-constraints-v1` / `1b1c3132b44a542605b19f354a5d9c7464a093aa4cb23b04583ca92e0841ec67`; R19 `PASS`; fixture n=10, depot=1, charger=1, vehicle=1, accepted directed OD=132, charger upper bound=11, HC09 disabled. R17 RoutingModel prototype and old R18 artifact are not QUBO authority.

### HC01〜HC13 completeness audit

| HC | Current QUBO expression / dependency | Penalty readiness | Classification | Remaining gap |
|---|---|---|---|---|
| HC01 | `(Σ_p node_at[p,i] - served[i])^2`; node_at, served | concept only | `FORMALLY_DEFINED` | numeric coefficient and full expansion |
| HC02 | fixed depot start + one return position; node_at, active, return | concept only | `FORMALLY_DEFINED` | exact return/depot coefficient expansion |
| HC03 | positional incoming/outgoing equalities on `arc_transition[p,i,j]` | concept only | `FORMALLY_DEFINED` | complete coefficient builder |
| HC04 | ordered position chain; no disconnected cycle in position representation | concept only | `FORMALLY_DEFINED` | prove/encode inactive suffix and all gated links in QUBO |
| HC05 | single-vehicle `served`/position assignment | concept only | `FORMALLY_DEFINED` | coefficient expansion |
| HC06 | binary payload state equality and capacity inequality with slack | concept only | `REQUIRES_AUXILIARY` | slack family and exact inequality encoding not registered |
| HC07 | `e_i <= b_i <= l_i` using time bits | none | `REQUIRES_DISCRETIZATION` | exact quantum time representation policy unresolved |
| HC08 | arrival/service/wait/charge/departure state equalities | concept only | `REQUIRES_HIGHER_ORDER_REDUCTION` | gated state products and auxiliaries not fully enumerated |
| HC09 | no term | none | `FORMALLY_DEFINED` / `DISABLED` | preserve disabled flag |
| HC10 | energy propagation and minimum-energy inequality | none | `REQUIRES_DISCRETIZATION` | exact J bit model and gated products unresolved |
| HC11 | initial energy fixed; final energy lower bound | none | `REQUIRES_DISCRETIZATION` | exact final-state inequality/slack unresolved |
| HC12 | slot activation/position, duration, `70*t`, battery cap, no consecutive charger | concept only | `REQUIRES_HIGHER_ORDER_REDUCTION` + `REQUIRES_DISCRETIZATION` | full event-state product and coefficientization unresolved |
| HC13 | transition variables exist only for accepted reachable arcs | concept only | `FORMALLY_DEFINED` | sparse coefficient construction not implemented |

No HC is silently dropped, but HC07, HC10, HC11, HC12 are not meaning-preserving executable QUBO terms yet. “Specified” in the R20 JSON is not equivalent to “implemented.”

### Variable explosion audit, n=10

| Family | Variables | Share of 13,782 |
|---|---:|---:|
| Route/order (`node_at` 276 + active 23 + arcs 2,904 + return 23) | 3,226 | 23.407% |
| Served/unserved | 10 | 0.073% |
| Time state bits | 2,484 | 18.024% |
| Payload state bits | 966 | 7.009% |
| SOC/energy state bits | 1,288 | 9.346% |
| Charging duration bits | 231 | 1.676% |
| Charger event (`slot_at` 253 + used 11) | 264 | 1.916% |
| Slack | 0 | 0% |
| Quadratization auxiliary (`slot_at * duration_bit`) | 5,313 | 38.550% |
| **Total** | **13,782** | **100%** |

The largest reducible source is the 5,313 Rosenberg auxiliary estimate. Next are arc-transition variables (2,904) and time bits (2,484). Eliminating charger/state auxiliaries or arc variables without a replacement changes the problem; no simplification is adopted in this audit.

### Exact encoding necessity audit

| State | Current range | Exact bits | Coarser candidate | Maximum quantization error / semantic risk |
|---|---:|---:|---|---|
| Time | 0–124,669,348 ms | 27 | 1 s, 10 s, 1 min | up to 999 ms, 9,999 ms, 59,999 ms; can change TW and propagation feasibility |
| Energy | 0–147,600,000 J | 28 | 1 kJ, 10 kJ, 0.1 MJ | up to 999 J, 9,999 J, 99,999 J; can change SOC lower bound and post-charge cap |
| Payload | 0–2,000,000 g | 21 | 1 kg / 100 g | up to 999 g / 99 g; current 1,100 g and 2,000,000 g semantics can change at boundary |
| Charging duration | 0–1,800,000 ms | 21 | 1 s / 1 min | up to 999 ms / 59,999 ms; can change HC12 event cap and `70 J/ms` relation |

R20 does not adopt coarser units. Exact binary expansion is formally possible but resource-heavy; the actual precision requirement versus acceptable coarsening is a `USER_RESEARCH_DECISION`, not an implementation assumption.

### Position-indexed re-evaluation

Position indexing is strong for fixture-level subtour handling, route order, charger revisit slots, and accepted-arc restriction. It is not proven globally best: arc-based can reduce route variables but needs order/state/subtour auxiliaries; time-expanded/state-expanded gives direct feasibility but has state-space explosion; hybrid reduces some width only by introducing a semantic discretization boundary. Position indexing is therefore “best current exact-semantics candidate for the fixture,” not a proven scalable optimum. Its route transition growth is approximately `O(n^3)` for complete directed OD, while state bits grow approximately `O(n log range)` and slot-duration quadratization approximately `O(n^2 log duration)`.

### Penalty readiness

All R20 penalty entries are `concept only` or `lower-bound framework only`; no constraint has a completed numeric penalty certificate. The proposed rule `lambda > max objective improvement / minimum nonzero violation` is not yet instantiated with complete coefficient bounds. Missing items are: maximum Stage-1 travel/objective contribution, Stage-2 travel range after fixed fulfillment, every inequality slack domain, every equality violation minimum, interaction/cross-term bounds, Rosenberg penalty lower bounds, and a hierarchy proof ensuring no HC violation beats a valid objective improvement. No arbitrary 1000/1e6 weight is accepted.

### Quadratization readiness

| Term source | Degree | Planned method | Current state |
|---|---:|---|---|
| slot position × duration bit | 2 | Rosenberg `z=xy` | auxiliary family estimated (5,313), penalty coupling not coefficientized |
| arc/state gated propagation | 3 or higher after state-bit gating | Rosenberg / chained reductions | not fully enumerated |
| charger activation × duration/energy state | 3 or higher in expanded form | auxiliary products | not implemented |
| inequality slack and conditional state bounds | 2–higher | binary slack plus reduction | slack variables absent from registry |

“Rosenberg planned” is not implementation. Reduction order, auxiliary uniqueness, penalty coupling, and count certificate remain incomplete.

### QUBO coefficient-generation readiness

Current status: `BLOCKED_BY_DECISIONS` (not `READY_TO_GENERATE_QUBO`). Variable registry exists; coefficient builder, linear/quadratic term emitter, constant offset, symmetry normalization, coefficient range audit, reproducible sparse matrix, and matrix hash do not exist. No QUBO coefficients have been generated. QUBO symmetry/coefficient sanity is therefore not testable yet.

### R21 validation readiness

Not ready. Required unimplemented components are: binary assignment→route decoder, independent HC checker for QUBO samples, QUBO energy recomputation, penalty decomposition, objective decomposition, encoding of the known R19-feasible CP-SAT solution, known infeasible-vector separation, and exact coefficient/matrix reproducibility checks. R19’s accepted solution is usable as a known-feasible vector only after exact variable assignment, all state-bit assignment, auxiliary assignment, and objective/penalty energy are defined without discretization drift.

### Aer/QAOA applicability and reduced-problem gate

13,782 logical binary variables imply a 13,782-qubit logical QAOA width before hardware mapping. Statevector memory is exponential in width; shot-based simulation still incurs circuit-width and shot cost; QAOA parameter count grows with depth and mixer/cost design; the interaction graph has estimated 17,953 nonzero couplers, and higher-order reduction adds coupling/depth overhead. The dominant blockers are width, state-vector impossibility, circuit depth from penalty gadgets, and coefficient dynamic range—not merely matrix density. Full exact n=10 is not ready for Aer/QAOA.

Before any reduced quantum problem, user decisions are required on: quantum-optimized object, HC retained classically, permitted time/energy/payload coarsening, target problem size, classical benchmark, feasibility repair policy, and how a reduced result maps back to the full EVRP/system metric. No reduced problem is adopted.

### Gap classification and recommended dependency order

| Gap | Class | Priority |
|---|---|---|
| QUBO scope / full-vs-reduced decision | `USER_RESEARCH_DECISION` | `CRITICAL` |
| time/energy/payload precision decision | `USER_RESEARCH_DECISION` | `CRITICAL` |
| exact HC07/10/11/12 state encoding | `IMPLEMENTATION_TASK` | `CRITICAL` |
| complete penalty lower-bound certificate | `MUST_RESOLVE_BEFORE_R21` | `CRITICAL` |
| full higher-order term inventory and quadratization | `IMPLEMENTATION_TASK` | `CRITICAL` |
| coefficient builder, sparse matrix, hash | `IMPLEMENTATION_TASK` | `HIGH` |
| known-feasible/infeasible QUBO vectors and validator | `MUST_RESOLVE_BEFORE_R21` | `HIGH` |
| Aer/QAOA width/depth decision | `MUST_RESOLVE_BEFORE_QAOA` | `HIGH` |
| n-scaling empirical measurement | `CAN_DEFER_TO_R28_SCALING` | `MEDIUM` |

Recommended order: `QUBO scope decision → state precision decision → encoding lock → exact HC07/10/11/12 state design → complete higher-order inventory → penalty certificate → quadratization implementation → coefficient builder and sparse matrix/hash → R19 known-solution exact encoding → R21 QUBO validation → only then Ising/QAOA decision`. R20 remains blocked and R21+ are not started.

- **Audit decision:** R20 status is not changed automatically by this audit; current R20 remains `BLOCKED`.
- **Next Allowed Stage:** `NONE`.

## Temporary diagnostic: Qiskit/Aer and hybrid feasibility — 2026-09-10

- **Position:** `TEMPORARY_DIAGNOSTIC` / exploratory evidence only. This is separate from the R20 formal decision and does not revise R20 formulation, encoding, problem size, reduced problem, architecture, provider, or QAOA parameters.
- **Authority:** R15 current accepted hash `7ca39facf83de619db7ec37daa90409834d89b4b75bfeb4e7c501ddef94b2ac4`; R16 current `evrp-common-hard-constraints-v1` / `1b1c3132b44a542605b19f354a5d9c7464a093aa4cb23b04583ca92e0841ec67`; R19 `PASS`; R20 formal `FORMULATION_ONLY/BLOCKED`; n=10 full estimate `13782` logical variables. No superseded RoutingModel or stale artifact was used as authority.
- **Artifact:** `reproducibility/outputs/traffic_simulation/temporary_quantum_diagnostic/20260910_temporary_qiskit_aer_hybrid_feasibility_diagnostic_n10/`. Metadata marks `purpose=temporary_qiskit_aer_and_hybrid_feasibility_diagnostic`, `status=TEMPORARY_DIAGNOSTIC`, and non-authoritative status for R20 formulation, problem-size selection, reduced problem, quantum architecture, and provider selection. Existing accepted/formal artifacts were not overwritten.
- **Environment:** Hayate, AMD EPYC 9684X 96-Core Processor, 192 physical cores / 384 threads, 1.5 TiB RAM, 1.4 TiB available at audit, 8 GiB swap, NVIDIA H100 NVL 95,830 MiB, driver 550.163.01. Python 3.11.15, NumPy 2.4.6, SciPy 1.15.3. Qiskit, Qiskit Aer, qiskit-optimization, IBM Runtime, Braket and CUDA-Q were not installed. No package/driver/CUDA/environment change was made.
- **Aer audit:** statevector, statevector GPU, matrix_product_state, tensor_network, density_matrix, stabilizer, extended_stabilizer and unitary were unavailable in this environment. No Aer scaling case was run; maximum successfully simulated qubits and maximum practical qubits are `UNKNOWN_NOT_MEASURED`. Stabilizer methods would not generally be exact substitutes for non-Clifford QAOA-like circuits.
- **Theoretical statevector memory:** using `16*2^q` bytes, q=20 is about `1.6e6` bytes, q=30 `1.6e9`, q=40 `1.6e12`, q=50 `1.6e15`, q=100 `1.6e30`, and q=13782 has `log10(bytes)≈4149.9995` (`~1.6e4149` bytes). These are theory only, not measured boundaries. Full 13,782-variable statevector simulation is `IMPOSSIBLE_UNDER_CURRENT_ENVIRONMENT_AND_THEORETICAL_WIDTH`.
- **Full QUBO:** breakdown rechecked against R20: route/order 3,226; served/unserved 10; time 2,484; payload 966; SOC/energy 1,288; charging duration 231; charger event 264; quadratization auxiliary 5,313; total 13,782. The dominant growth sources are quadratization auxiliaries (38.55%), route transitions (2,904 within route/order), and time bits (18.024%).
- **Temporary route/order candidates:** for n=10 including depot+charger, basic position-indexed candidate estimate is primary/total `3,236/3,236` with no state auxiliary; arc/order candidate is `203/203` under a basic order-bit estimate. These are not reduced-problem adoption or formal QUBO variables. Position-indexed versus arc/order totals for n=3/4/5/6/8/10/15/20 are saved in `route_order_scaling.json`; position estimate grows `O(n^3)`, arc/order estimate `O(n^2 log n)` under the temporary assumptions.
- **Hybrid candidate:** classical Hayate preprocessing/state layer may handle reachability, necessary-condition `F_ij`, TW/payload/SOC/charging bounds and transition filtering; a quantum candidate may handle route/order only; classical postprocessing must reconstruct state, validate HC01〜HC13 and metrics. `F_ij` is only a necessary-condition filter, not sufficient for history-dependent route feasibility. This is `PLAUSIBLE_BUT_UNSUPPORTED`, not an architecture decision.
- **Responsibility matrix:** HC01 shared; HC02〜HC05 candidate quantum route/order; HC06〜HC08 classical state propagation; HC09 not applicable/disabled; HC10/HC12 classical state propagation; HC11 classical preprocessing; HC13 classical preprocessing. This is temporary responsibility allocation and does not delete any HC.
- **Runtime framework:** temporary `T_total=T_pre+T_QUBO+T_map_or_transpile+T_solve+T_post`; cloud `T_wall=T_total+T_queue`; QAOA repeated cost includes `N_iterations*N_expectation_evaluations*shots*per-shot/job cost`. Queue time remains separate from algorithmic compute time. No actual runtime scaling was measured because Qiskit/Aer was unavailable.
- **Option assessment:** Option 1 full classical `SUPPORTED_BY_CURRENT_EVIDENCE`; Option 2 Hayate+Aer `UNCERTAIN` (package unavailable); Option 3 Hayate+cloud QPU `PLAUSIBLE_BUT_UNSUPPORTED` (no provider, connectivity, queue, cost, error or execution evidence). No provider was selected and no paid/cloud job was run.
- **Hypotheses:** A `PARTIALLY_SUPPORTED_BY_THEORY` (width/memory/repeated expectation cost dominate; no Aer measurement); B `PLAUSIBLE_BUT_UNTESTED` (classical state handling may reduce quantum width); C `PARTIALLY_SUPPORTED_CONCEPTUALLY` (hybrid is technically discussable but unverified).
- **Required user decisions before any formal reduced design:** QUBO scope, allowed state precision/discretization, quantum-side objective, classical HC boundary, target size, benchmark and stopping rules, mapping back to full-EVRP/system metrics, and provider evaluation criteria.
- **Formal status protection:** R20 remains `BLOCKED`; `Next Allowed Stage: NONE`. No R20 status change, next-stage authorization, reduced-problem adoption, provider adoption, formal experiment parameter adoption, R21, Ising or QAOA/Aer execution resulted from this diagnostic.

## R21_QUBO_VALIDATION — QUBO Validation

- **Stage ID:** R21_QUBO_VALIDATION
- **Objective:** QUBOと共通問題の同値性を検証する
- **Inputs:** QUBO・decoder・厳密小規模fixture
- **Preconditions:** 前工程 `R20_QUBO_FORMULATION` のPASS（明示された正常結果遷移は例外）と、Inputsの存在・hash・根拠を確認する。
- **Method:** 限定小規模の列挙等で目的/feasibility/penaltyを比較
- **Validation:** 小規模同値性PASS・NaN/Infなし・制約欠落なし・decode往復一致ことを独立検査し、実行記録に診断を残す。
- **Acceptance Criteria:** 小規模同値性PASS・NaN/Infなし・制約欠落なし・decode往復一致
- **Stop Conditions:** Global Stop Rulesと当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義はBLOCKED、検証不一致・実行異常はFAIL。
- **Outputs:** QUBO validation report
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **Commands:** NOT_RUN — 実行前に採択command・cwd・出力pathを記録
- **Input Hashes:** NOT_FIXED — 実行前にlock
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **Issues:** 未実行。Acceptance Criteriaの未固定項目を実行開始時に解消し、解消不能ならBLOCKED
- **Decision:** NOT_RUN
- **Next Allowed Stage:** R22_ISING_CONVERSION（Gate通過時のみ）

## R21_REDUCED_QUBO_VALIDATION — Initial Reduced Route-Ordering QUBO Validation

### Governance decision — 2026-09-10

`R21_QUBO_VALIDATION SHALL BE APPLIED TO INITIAL_R20_REDUCED_ROUTE_ORDERING_SCOPE_ONLY`.

This is an explicitly scoped branch of the execution plan. It does not replace, relax, or mark PASS the full-EVRP `R20_QUBO_FORMULATION`; it creates a separate validation path for the already scoped-PASS reduced formulation before any scoped Ising conversion is considered.

The two paths remain separate:

```text
Full-EVRP path:
  Full R20 PASS -> R21_QUBO_VALIDATION -> R22_ISING_CONVERSION

Initial reduced path:
  FORMULATION_VERIFIED = PASS
  Scope = INITIAL_R20_REDUCED_ROUTE_ORDERING_SCOPE_ONLY
    -> R21_REDUCED_QUBO_VALIDATION
    -> scoped R22 eligibility for the same reduced QUBO only
```

- **Stage ID:** `R21_REDUCED_QUBO_VALIDATION`
- **Scope:** `INITIAL_R20_REDUCED_ROUTE_ORDERING_SCOPE_ONLY`
- **Purpose:** frozen reduced route-ordering QUBOが、同じ frozen classical route-ordering problem と同値であり、次の scoped transformation stageへ渡せることを検証する。
- **Full-EVRP boundary:** full-EVRP R20/R21のPASS、capacity、time window、battery/SOC、charging、fleet、またはfull-EVRP QUBOの検証を意味しない。

### Prerequisites

All of the following are required:

- `FORMULATION_VERIFIED = PASS`;
- scope exactly `INITIAL_R20_REDUCED_ROUTE_ORDERING_SCOPE_ONLY`;
- formulation source freeze and gate commit are identifiable;
- reduced QUBO implementation, decoder, independent validator, and exact-small fixtures exist;
- a Routing Baseline-derived complete-reachability input is available;
- the theoretical penalty bound is available;
- applied `lambda` is finite and strictly satisfies `lambda > B`.

The following are not prerequisites for this reduced branch:

- full-EVRP R20 PASS;
- capacity, time-window, battery/SOC, charging, fleet-sizing QUBO;
- unreachable-transition QUBO extension;
- QAOA, Ising conversion, or performance benchmarking.

### Input contract

Mandatory fields:

- schema/version;
- instance ID, depot ID, ordered customer IDs, and `n_customers`;
- row-major variable ordering and `n^2` logical-variable count;
- raw directed travel-time representation in seconds;
- normalized directed travel-time representation and `tau_max`;
- complete-reachability result;
- Routing Baseline artifact ID/hash and source metadata;
- R20 formulation source commit and R20 gate commit;
- expanded QUBO constant, linear, and canonical quadratic coefficients;
- QUBO coefficient hash;
- finite `lambda`, bound type, `B`, and applied margin;
- numerical tolerance metadata;
- exact classical-reference configuration.

Optional fields include distance metadata, selected edge records, and diagnostic coefficient-scale summaries. Distance must not enter the formal QUBO objective.

### Mandatory invariants

The following V1--V8 are formal reduced-R21 invariants. One failed invariant fails the reduced R21 gate.

1. **V1 Feasibility:** `argmin H_QUBO subseteq F`.
2. **V2 Objective equivalence:** the best feasible QUBO route cost equals the classical route-ordering optimum.
3. **V3 Route-set equivalence:** all optimal route identities, including ties, match the exact reference.
4. **V4 Energy consistency:** direct squared and expanded QUBO energies agree within the specified energy tolerance.
5. **V5 Decode/re-encode:** every valid QUBO minimum decodes deterministically and re-encodes to the same assignment.
6. **V6 Input/provenance integrity:** source hashes and selected-instance metadata match.
7. **V7 Lambda validity:** `isfinite(lambda)` and strict `lambda > B`; equality is not PASS.
8. **V8 Normalization consistency:** raw and normalized travel-time route ranking and optimal-route set are preserved.

### Validation ladder and fixtures

Only exact-small validation is permitted:

- synthetic n=2;
- synthetic n=3, including unique and tie cases;
- synthetic n=4 when the existing exact-enumeration guard permits it;
- deterministic real-data-derived depot + 2 customers;
- deterministic real-data-derived depot + 3 customers.

The binary state count is `2^(n^2)`. Any enumeration guard is an implementation validation limit only, not a QAOA, QPU, quantum-scalability, or formal research problem-size limit.

Fixtures must cover unique optimum, multiple optimum/tie, asymmetric directed travel time, adversarial penalty behavior, and complete-reachability real-data-derived input. Negative input-contract behavior may reference the existing R20 adapter regression tests when provenance is explicit.

### Classical reference and validation procedure

The classical reference enumerates all `n!` customer permutations with fixed depot, depot departure, consecutive customer transitions, depot return, the same directed travel-time matrix, and all ties retained. It is the reduced route-ordering problem only; full-EVRP solver comparison is out of scope.

The formal execution sequence is:

1. load and schema-validate the reduced R21 input;
2. validate provenance, complete reachability, and normalization metadata;
3. validate finite `lambda` and strict `lambda > B`;
4. construct/freeze the expanded QUBO and calculate its coefficient hash;
5. calculate the exact classical reference;
6. enumerate QUBO states within the guard;
7. independently classify feasibility and decode states;
8. identify all global minima;
9. compare direct/expanded energy and classical/QUBO route sets;
10. verify decode/re-encode and raw/normalized consistency;
11. write the standalone evidence artifact and evaluate V1--V8.

### Numerical comparison policy

- direct/expanded energy uses the repository `ENERGY_ABS_TOLERANCE`;
- classical route-cost equality uses an explicitly named route-cost tolerance;
- the lambda condition uses strict finite numeric comparison, not `isclose`;
- normalization comparison uses an explicit route-ranking/tie tolerance;
- reproducibility comparison excludes only schema-approved runtime/timestamp fields.

The candidate rule `lambda = B + max(10*e_noise, 1e-6*B)` remains an implementation-policy candidate. Reduced R21 does not require formal adoption of `kappa=10` or `delta_min=1e-6`; it must record the actual applied lambda, bound, and margin metadata.

### PASS and failure criteria

Reduced R21 PASS requires input/provenance, complete reachability, lambda bound, classical reference, QUBO construction, V1--V8, deterministic semantic artifact generation, and no CRITICAL/HIGH issue to pass. Partial PASS is not allowed.

Failure reason codes are:

`INPUT_CONTRACT_FAILURE`, `PROVENANCE_FAILURE`, `LAMBDA_BOUND_FAILURE`, `INFEASIBLE_GLOBAL_MINIMUM`, `QUBO_ROUTE_OBJECTIVE_MISMATCH`, `OPTIMAL_ROUTE_SET_MISMATCH`, `DIRECT_EXPANDED_MISMATCH`, `DECODE_FAILURE`, `NORMALIZATION_MISMATCH`, `EXACT_ENUMERATION_GUARD`, `NUMERICAL_TOLERANCE_FAILURE`, and `NONDETERMINISTIC_RESULT`.

### Evidence artifact and status

The artifact shall use the established output convention:

`reproducibility/outputs/traffic_simulation/r21_qubo_validation/<run_id>/`

with at least `validation_results.json` and `manifest.json`. The manifest records source commit, R20 formulation source commit, R20 gate commit, reduced R21 specification/version, input and coefficient hashes, routing provenance, n, `n^2`, state/permutation counts, lambda/bound/margin metadata, classical and QUBO optima, all global minima, feasibility, direct/expanded diagnostics, decode and normalization results, runtime, reason codes, and final status.

- **Status:** `READY_FOR_EXECUTION` (runner/tests prepared; validation not executed)
- **Execution authorization:** `NONE` in this planning record
- **Decision:** reduced R21 governance defined; no validation result is claimed
- **Next scoped stage after PASS:** `R22_ISING_CONVERSION` eligibility for the same reduced QUBO only

This reduced branch does not alter the full-EVRP `R21_QUBO_VALIDATION`, whose prerequisite remains full-EVRP `R20_QUBO_FORMULATION = PASS`.

### Formal reduced-R21 validation result — 2026-09-10

- **Run:** `reproducibility/outputs/traffic_simulation/r21_qubo_validation/20260910_formal_reduced_v1/`
- **Classification:** `FORMAL_R21_REDUCED_QUBO_VALIDATION`
- **Result:** all 7 required instances PASS; V1--V8 PASS for every instance; deterministic semantic rerun PASS.
- **Instances:** synthetic n=2 unique; synthetic n=3 unique, tie, and asymmetric; synthetic n=4 adversarial/asymmetric; Routing Baseline-derived depot + 2 customers; Routing Baseline-derived depot + 3 customers.
- **Decision:** `R21_REDUCED_QUBO_VALIDATION = PASS` for `INITIAL_R20_REDUCED_ROUTE_ORDERING_SCOPE_ONLY`.
- **R22 boundary:** scoped eligibility is recorded for the same reduced QUBO only. R22 execution remains blocked/not executed; full-EVRP R22 eligibility is not granted.
- **Status transition:** `READY_FOR_EXECUTION -> PASS` for this reduced branch only. The full-EVRP `R21_QUBO_VALIDATION` remains `NOT_STARTED`.

## R22_ISING_CONVERSION — Ising Conversion

- **Stage ID:** R22_ISING_CONVERSION
- **Objective:** QUBOを同値なIsingへ変換する
- **Inputs:** 検証済QUBO・変数順
- **Preconditions:** 前工程 `R21_QUBO_VALIDATION` のPASS（明示された正常結果遷移は例外）と、Inputsの存在・hash・根拠を確認する。
- **Method:** binary-spin対応と定数offsetを記録しenergyを比較
- **Validation:** 小規模全状態でoffset込みenergy一致・qubit対応が一意ことを独立検査し、実行記録に診断を残す。
- **Acceptance Criteria:** 小規模全状態でoffset込みenergy一致・qubit対応が一意
- **Stop Conditions:** Global Stop Rulesと当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義はBLOCKED、検証不一致・実行異常はFAIL。
- **Outputs:** Ising operator・conversion validation
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **Commands:** NOT_RUN — 実行前に採択command・cwd・出力pathを記録
- **Input Hashes:** NOT_FIXED — 実行前にlock
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **Issues:** 未実行。Acceptance Criteriaの未固定項目を実行開始時に解消し、解消不能ならBLOCKED
- **Decision:** NOT_RUN
- **Next Allowed Stage:** R23_QAOA_AER_EXECUTION（Gate通過時のみ）

### Reduced-scope dependency boundary

`R21_REDUCED_QUBO_VALIDATION = PASS` may establish eligibility only for a correspondingly scoped `R22_ISING_CONVERSION` of the same initial reduced route-ordering QUBO. It does not authorize full-EVRP Ising conversion, QAOA execution, or completion of the full R22 stage.

## R23_QAOA_AER_EXECUTION — QAOA / Qiskit Aer Execution

- **Stage ID:** R23_QAOA_AER_EXECUTION
- **Objective:** resource preflight後にAerで候補sampleを得る
- **Inputs:** Ising・p/shots/optimizer設定・導入検証済環境
- **Preconditions:** 前工程 `R22_ISING_CONVERSION` のPASS（明示された正常結果遷移は例外）と、Inputsの存在・hash・根拠を確認する。
- **Method:** resource見積と上限照合後に1run実行、bitstring/counts/終了理由を記録
- **Validation:** preflight合格・正常termination・回路/seed/実行時間保存ことを独立検査し、実行記録に診断を残す。
- **Acceptance Criteria:** preflight合格・正常termination・回路/seed/実行時間保存
- **Stop Conditions:** Global Stop Rulesと当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義はBLOCKED、検証不一致・実行異常はFAIL。事前resource ceiling到達はLIMIT_REACHED、正常な解未発見はRESULT_INFEASIBLE。
- **Outputs:** 回路・raw samples・resource/optimizer log
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **Commands:** NOT_RUN — 実行前に採択command・cwd・出力pathを記録
- **Input Hashes:** NOT_FIXED — 実行前にlock
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **Issues:** 未実行。Acceptance Criteriaの未固定項目を実行開始時に解消し、解消不能ならBLOCKED
- **Decision:** NOT_RUN
- **Next Allowed Stage:** R24_QUANTUM_SOLUTION_DECODE（Gate通過時のみ）

## R24_QUANTUM_SOLUTION_DECODE — Quantum Solution Decode

- **Stage ID:** R24_QUANTUM_SOLUTION_DECODE
- **Objective:** bitstringを共通route表現へ変換する
- **Inputs:** raw samples・encoding/decoder版・I_s
- **Preconditions:** 前工程 `R23_QAOA_AER_EXECUTION` のPASS（明示された正常結果遷移は例外）と、Inputsの存在・hash・根拠を確認する。
- **Method:** bit順序/aux/離散化を照合しraw decode、repairは別保存
- **Validation:** 全sampleのdecode結果または理由を記録、黙示修復なしことを独立検査し、実行記録に診断を残す。
- **Acceptance Criteria:** 全sampleのdecode結果または理由を記録、黙示修復なし
- **Stop Conditions:** Global Stop Rulesと当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義はBLOCKED、検証不一致・実行異常はFAIL。
- **Outputs:** decoded quantum routes・decode report
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **Commands:** NOT_RUN — 実行前に採択command・cwd・出力pathを記録
- **Input Hashes:** NOT_FIXED — 実行前にlock
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **Issues:** 未実行。Acceptance Criteriaの未固定項目を実行開始時に解消し、解消不能ならBLOCKED
- **Decision:** NOT_RUN
- **Next Allowed Stage:** R25_COMMON_INDEPENDENT_VALIDATION（Gate通過時のみ）

## R25_COMMON_INDEPENDENT_VALIDATION — Common Independent Validation

- **Stage ID:** R25_COMMON_INDEPENDENT_VALIDATION
- **Objective:** 両手法を同一validatorで独立比較可能にする
- **Inputs:** 古典解・量子decode・同じI_sとvalidator版
- **Preconditions:** 前工程 `R24_QUANTUM_SOLUTION_DECODE` のPASS（明示された正常結果遷移は例外）と、Inputsの存在・hash・根拠を確認する。
- **Method:** 両解で13制約を再計算、invalid sampleとvalidator errorを分離
- **Validation:** validator正常・制約別判定とfeasible件数・終了理由が保存済ことを独立検査し、実行記録に診断を残す。
- **Acceptance Criteria:** validator正常・制約別判定とfeasible件数・終了理由が保存済
- **Stop Conditions:** Global Stop Rulesと当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義はBLOCKED、検証不一致・実行異常はFAIL。
- **Outputs:** 共通validation report
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **Commands:** NOT_RUN — 実行前に採択command・cwd・出力pathを記録
- **Input Hashes:** NOT_FIXED — 実行前にlock
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **Issues:** 未実行。Acceptance Criteriaの未固定項目を実行開始時に解消し、解消不能ならBLOCKED
- **Decision:** NOT_RUN
- **Next Allowed Stage:** R26_DEMAND_FULFILLMENT_EVALUATION（Gate通過時のみ）

## R26_DEMAND_FULFILLMENT_EVALUATION — Demand Fulfillment Evaluation

- **Stage ID:** R26_DEMAND_FULFILLMENT_EVALUATION
- **Objective:** 配送件数DFRと追加荷量DFRを計算する
- **Inputs:** 共通validation・I_s全要求
- **Preconditions:** 前工程 `R25_COMMON_INDEPENDENT_VALIDATION` のPASS（明示された正常結果遷移は例外）と、Inputsの存在・hash・根拠を確認する。
- **Method:** validated完了だけを分子とし未充足を含む固定分母で算出
- **Validation:** 0<=DFR<=1・重複なし・分母一致・invalid解をfeasible扱いしないことを独立検査し、実行記録に診断を残す。
- **Acceptance Criteria:** 0<=DFR<=1・重複なし・分母一致・invalid解をfeasible扱いしない
- **Stop Conditions:** Global Stop Rulesと当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義はBLOCKED、検証不一致・実行異常はFAIL。
- **Outputs:** DFR・完了/未充足・energy等指標
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **Commands:** NOT_RUN — 実行前に採択command・cwd・出力pathを記録
- **Input Hashes:** NOT_FIXED — 実行前にlock
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **Issues:** 未実行。Acceptance Criteriaの未固定項目を実行開始時に解消し、解消不能ならBLOCKED
- **Decision:** NOT_RUN
- **Next Allowed Stage:** R27_CLASSICAL_QUANTUM_COMPARISON（Gate通過時のみ）

## R27_CLASSICAL_QUANTUM_COMPARISON — Classical–Quantum Comparison

- **Stage ID:** R27_CLASSICAL_QUANTUM_COMPARISON
- **Objective:** 同一条件の品質と計算資源を比較する
- **Inputs:** 両branch結果・I_s/hash・共通指標
- **Preconditions:** 前工程 `R26_DEMAND_FULFILLMENT_EVALUATION` のPASS（明示された正常結果遷移は例外）と、Inputsの存在・hash・根拠を確認する。
- **Method:** 同一instance/seed/入力を照合し予算境界を明示して比較
- **Validation:** 入力一致・限界/欠測/非実行を隠さない・全比較指標と量子資源を記録ことを独立検査し、実行記録に診断を残す。
- **Acceptance Criteria:** 入力一致・限界/欠測/非実行を隠さない・全比較指標と量子資源を記録
- **Stop Conditions:** Global Stop Rulesと当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義はBLOCKED、検証不一致・実行異常はFAIL。
- **Outputs:** paired comparison report
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **Commands:** NOT_RUN — 実行前に採択command・cwd・出力pathを記録
- **Input Hashes:** NOT_FIXED — 実行前にlock
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **Issues:** 未実行。Acceptance Criteriaの未固定項目を実行開始時に解消し、解消不能ならBLOCKED
- **Decision:** NOT_RUN
- **Next Allowed Stage:** R28_PROBLEM_SIZE_SCALING（Gate通過時のみ）

## R28_PROBLEM_SIZE_SCALING — Problem-Size Scaling

- **Stage ID:** R28_PROBLEM_SIZE_SCALING
- **Objective:** n増加に伴うbranch別限界を記録する
- **Inputs:** 検証済比較手順・n列/seed列・resource ceiling
- **Preconditions:** 前工程 `R27_CLASSICAL_QUANTUM_COMPARISON` のPASS（明示された正常結果遷移は例外）と、Inputsの存在・hash・根拠を確認する。
- **Method:** 事前登録した増加列で13〜27の子runを直列実行・逐次記録
- **Validation:** branch停止理由・最大成功n・停止n・共通比較範囲を区別ことを独立検査し、実行記録に診断を残す。
- **Acceptance Criteria:** branch停止理由・最大成功n・停止n・共通比較範囲を区別
- **Stop Conditions:** Global Stop Rulesと当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義はBLOCKED、検証不一致・実行異常はFAIL。事前resource ceiling到達はLIMIT_REACHED、正常な解未発見はRESULT_INFEASIBLE。
- **Outputs:** scaling matrix・n_max記録
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **Commands:** NOT_RUN — 実行前に採択command・cwd・出力pathを記録
- **Input Hashes:** NOT_FIXED — 実行前にlock
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **Issues:** 未実行。Acceptance Criteriaの未固定項目を実行開始時に解消し、解消不能ならBLOCKED
- **Decision:** NOT_RUN
- **Next Allowed Stage:** R29_EV_TECHNOLOGY_SCENARIO_EVALUATION（Gate通過時のみ）

## R29_EV_TECHNOLOGY_SCENARIO_EVALUATION — EV Technology Scenario Evaluation

- **Stage ID:** R29_EV_TECHNOLOGY_SCENARIO_EVALUATION
- **Objective:** EV技術変化のDFR効果を評価する
- **Inputs:** 固定customer/需要/窓/道路と技術parameter表
- **Preconditions:** 前工程 `R28_PROBLEM_SIZE_SCALING` のPASS（明示された正常結果遷移は例外）と、Inputsの存在・hash・根拠を確認する。
- **Method:** battery/効率/charging power/usable SOCのみ計画通り変更し子runを直列実行
- **Validation:** 固定入力hash一致・変更値の根拠・古典量子同条件・failure可視化ことを独立検査し、実行記録に診断を残す。
- **Acceptance Criteria:** 固定入力hash一致・変更値の根拠・古典量子同条件・failure可視化
- **Stop Conditions:** Global Stop Rulesと当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義はBLOCKED、検証不一致・実行異常はFAIL。事前resource ceiling到達はLIMIT_REACHED、正常な解未発見はRESULT_INFEASIBLE。
- **Outputs:** 技術scenario比較
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **Commands:** NOT_RUN — 実行前に採択command・cwd・出力pathを記録
- **Input Hashes:** NOT_FIXED — 実行前にlock
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **Issues:** 未実行。Acceptance Criteriaの未固定項目を実行開始時に解消し、解消不能ならBLOCKED
- **Decision:** NOT_RUN
- **Next Allowed Stage:** R30_FINAL_REPRODUCIBILITY_VALIDATION（Gate通過時のみ）

## R30_FINAL_REPRODUCIBILITY_VALIDATION — Final Reproducibility Validation

- **Stage ID:** R30_FINAL_REPRODUCIBILITY_VALIDATION
- **Objective:** 全結果を第三者が追跡・再現可能にする
- **Inputs:** 本書の全run記録・source/schema/config/code/environment・成果物
- **Preconditions:** 前工程 `R29_EV_TECHNOLOGY_SCENARIO_EVALUATION` のPASS（明示された正常結果遷移は例外）と、Inputsの存在・hash・根拠を確認する。
- **Method:** hash/link/schema監査・同seed再現・浮動誤差とstochastic範囲の確認
- **Validation:** 全claimに証拠・再現command・version・判定、未実行/限界を明示ことを独立検査し、実行記録に診断を残す。
- **Acceptance Criteria:** 全claimに証拠・再現command・version・判定、未実行/限界を明示
- **Stop Conditions:** Global Stop Rulesと当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義はBLOCKED、検証不一致・実行異常はFAIL。
- **Outputs:** 最終manifest・再現性validation
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **Commands:** NOT_RUN — 実行前に採択command・cwd・出力pathを記録
- **Input Hashes:** NOT_FIXED — 実行前にlock
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **Issues:** 未実行。Acceptance Criteriaの未固定項目を実行開始時に解消し、解消不能ならBLOCKED
- **Decision:** NOT_RUN
- **Next Allowed Stage:** NONE — 最終凍結・終了（Gate通過時のみ）

# Environment

監査時Python 3.11.15、NumPy 2.2.5、pandas 2.2.3、pyarrow 19.0.1、OR-Tools 9.12.4544、pytest 8.3.3。SUMO/duarouter binaryは.local/sumo-1.24.0/bin。Qiskit/Aerとsumolib/traci distribution metadataなし。GPUは未調査・不使用。Git commitは`ae0c3906a94fce00353d9f61b33462e9d1a50344`、監査開始時DIRTY。既存の利用者変更を保持した。

# Audit Commands

監査中に実行したread-only検査（cwdはrepository root）:

```bash
git status --short
./research portal check
./research demand validate
.local/sumo-1.24.0/bin/sumo --version
free -b
lscpu
cat /proc/self/cgroup
```

追加監査ではPython csv/zipfile/json/hashlibで候補行数・ID・WKT座標・統計manifest全file hash・census ZIP hashを照合し、importlib.metadataでpackage versionとcgroupのmemory.max/high・cpu.maxを調べた。原本の再生成・書換えは行っていない。再確認用の自己完結command:

```bash
.conda/bin/python - <<'PY_AUDIT'
from pathlib import Path
import csv, json, hashlib, re
r=Path.cwd()
h=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
p=r/'03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/building_delivery_stops_scoped.csv'
rows=list(csv.DictReader(p.open()))
assert len(rows)==39956
for col in ('stop_id','building_id'):
 assert all(x[col] for x in rows) and len({x[col] for x in rows})==39956
for x in rows:
 xy=tuple(map(float,re.findall(r'[-+]?\d+(?:\.\d+)?',x['building_representative_point'])))
 assert len(xy)==2 and -180<=xy[0]<=180 and -90<=xy[1]<=90
m=r/'03_data/raw/traffic_simulation/demand_proxy/mlit_tokyo_metropolitan_goods_movement_survey_2024_20260823/manifest.json'
items=json.loads(m.read_text())['files']
assert all(h(m.parent/x['filename'])==x['sha256'] for x in items)
print('candidate audit PASS; manifest',len(items),'entries /',len({x['filename'] for x in items}),'unique PASS')
PY_AUDIT
```

候補の座標範囲はlon 139.65317823652003〜139.75249792175939、lat 35.54015044054699〜35.61236590455608。CRS・住宅分類・mesh全件対応の正式受入はR03で別途行う。

監査logは作業用/tmpにあり永続的な唯一の証拠とはしない。本書の検査結果・command・hashを実行記録とする。

- `/tmp/evrp_initial_portal.log` SHA-256: `14c01ca818965ba33ea16826576c0f3ed3975db0a7ce7a644baad9c35e16fece`
- `/tmp/evrp_initial_demand.log` SHA-256: `380d2d662c03c8374abb0b98b007c7a666d4c7675f2a31525f961264dfeb3f81`

# Input Hash Ledger

以下は今回の監査入力の実ファイルhash（SHA-256）。既存成果物はこのhashを維持する。

| Path | SHA-256 |
|---|---|
| `RESEARCH_PIPELINE_REFERENCE.md` | `2abee53ac768dc32ecddf20efbb0d778b6ed0ff7f992c2b709333b1a99511290` |
| `reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml` | `5774598068e3f8008a661c0f519a48f0f312925856adad458fe99ede04082f86` |
| `reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/network_acceptance.json` | `3a1ea4f81715eb1966394522799ec8beac332c87fddefdc1d5d0993d435948f0` |
| `03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/building_delivery_stops_scoped.csv` | `fcfca5cb87bc482f1d98306c98823773e872f200c58ecb9090aa12985e3e80e0` |
| `03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/stop_generation_run_summary.json` | `9d4b087462f17897524878d15a6db842efb34f583e02c2f9b120517e1be6c47a` |
| `03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/pipeline_run_summary.json` | `7cbcc67664e1b9c3bf3c20e418fe4e6875335da1491555dc05aec56bd32d50c4` |
| `03_data/raw/traffic_simulation/demand_proxy/mlit_tokyo_metropolitan_goods_movement_survey_2024_20260823/manifest.json` | `b218db3c37faeb0ba21ac9b0b6a92ea4fc0d07feef423db9c9c97db82da38a5e` |
| `03_data/metadata/traffic_simulation_sources.csv` | `8b370e6feaaceea385ee669d4a770e531cb3925c5eaa6dd83f7ccb7195aad6dc` |
| `reproducibility/config/traffic_simulation/baseline_demand.yml` | `544417c4e8b2c906c6431516f5e355524cfeacd95aecf3bd4945e501d360b58b` |
| `reproducibility/config/traffic_simulation/scenario_profiles/managed_urban_ev_delivery_v1.yml` | `8f837f7a1b4fa7274e86e5d8ac09260738d2c0dac9cbeb7143300e82b92bc2b5` |
| `reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/request_stop_mapping.json` | `edc75989b1d4a43d6172661a993789c0c9e58fd6d9c0c5cde267355255bbea89` |
| `03_data/raw/traffic_simulation/population/estat_2020_500m_jgd2011/tblT001141H5339.zip` | `8a8b47563ffe88ec1afb5a17b8d29ac987b40df65498bec4c2fcf1829777f67d` |
| `reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/three_tier.net.xml` | `4625dbbc150cbcf72964bed0e90a8b33fe03f190ff4264aecaaf89e3aab0e40f` |
| `reproducibility/config/traffic_simulation/current_network_completion_authority_v18_geometry_reaccepted.yml` | `29ee5fe979c85eb1d11b0f5a55f33782b7b5b08fcf09b48d2fad3e47c0ae33ee` |
| `reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_3_geometry_reacceptance/three_tier.net.xml` | `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2` |
| `reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_3_geometry_reacceptance/network_acceptance.json` | `078bc16ccef865ba18e3f6c8010c7929b3b9e77f3740ee992a62de15c716cbc4` |
| `reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_3_geometry_reacceptance/network_reacceptance_manifest.json` | `8b85d46b21926b154ddee81439fa07d043e4fac621c726eaa6892d263adfb0a1` |
| `reproducibility/outputs/traffic_simulation/demand/evrp_r12_routing/20260909_r12_routing_spec_fixture_n10_v18_geometry_reaccepted/endpoint_manifest.csv` | `9f0d0cdd289fad73c696e7a3efe56af7bb4385fa5f268cb5db6e6d8844335913` |
| `reproducibility/outputs/traffic_simulation/demand/evrp_r12_routing/20260909_r12_routing_spec_fixture_n10_v18_geometry_reaccepted/od_manifest.csv` | `bee697860ab422d0eacdc8ac4d3019bb3caf1673bcbd2f31ae903e977f530b74` |
| `reproducibility/outputs/traffic_simulation/demand/evrp_r12_routing/20260909_r12_routing_spec_fixture_n10_v18_geometry_reaccepted/r12_routing_config.json` | `12c32ada0b3d615e8acdc32c033138fb309ccf434d3b3f3aaaea3c05b40fb5c8` |
| `reproducibility/outputs/traffic_simulation/demand/evrp_r12_routing/20260909_r12_routing_spec_fixture_n10_v18_geometry_reaccepted/routing_output_schema.json` | `7ef7a66cd221376b7f3e7588934439cd00164721283d2eaca540cc4b9428544b` |
| `reproducibility/outputs/traffic_simulation/demand/evrp_r12_routing/20260909_r12_routing_spec_fixture_n10_v18_geometry_reaccepted/r12_v18_independent_validation.json` | `fe645a7a432e87072e67d56e48c87b6623ba8c30e6d126f6fe7a5b1cdca30e52` |
| `reproducibility/outputs/traffic_simulation/demand/evrp_r12_routing/20260909_r12_routing_spec_fixture_n10_v18_geometry_reaccepted/r12_manifest.json` | `f6194ec010e1cd97fbcfd9e97b080bfe9a7bb46fdfcc5112cbc8c1d1eb55fc3e` |

# MD Validation

2026-09-09 R03再実行後検証: PASS。30工程の順序、R01/R02のPASS、R03のBLOCKED継続、R04以降未実行、13 Hard Constraints、Stage Recordの21欄、Global/Data/Routing/Instance/Solver停止条件、resource ceiling、入力hash台帳、内部Markdownリンクを検査した。R03の新規接続表はrun-scoped pathへ出力し、既存raw・候補CSV・受入network/mappingは変更していない。本書の自己hashは文書内に埋め込まない。
2026-09-09 R13 runner restoration and execution validation: PASS。既存SUMO/sumolibのみでrunnerを固定pathへ実装し、同一edge順方向・逆offset・異なるedge部分区間・directed unreachableのfixture validationをPASSした。preflight後、132 directed ODを計算し、生成132、reachable132、unreachable0、OD完全性、offset合算、network hash、vehicle class、travel-time objective、異常値、別run output hash一致を確認した。R14以降は実行していない。
2026-09-09 R14 independent routing validation: FAIL。R13 output hashは一致し、132/132 OD、endpoint coverage、schema/numeric、delivery connectivity、offset再構成、代表route、travel-time objective、vehicle classはPASSした。一方、raw endpoint座標のstraight-line distanceをroad distanceが下回るODが44件（最大差約587.76m）あり、mapping距離約5.26mでは説明できないため、network geometry/edge lengthまたはendpoint mapping整合性の問題候補として停止した。R13 outputは変更せず、R15以降は実行していない。
2026-09-09 R14 spatial gate re-audit: FAIL継続。Critical Gateをmapped SUMO positions間の`road_distance >= straight(mapped)-1e-6m`へ変更し、original-coordinate比較をdiagnosticへ移した。132 ODを再検証した結果、true critical inconsistency 44件、explainable by mapping/geometry 0件、diagnostic warning only 0件。original-coordinate warningは44件。したがって旧判定の過剰性は修正されたが、mapped-position基準でもCritical anomalyが残りR14 FAILを維持した。R13 output/network/mappingは変更せず、R15以降は実行していない。
2026-09-09 R14 root-cause investigation: ROOT_CAUSE_IDENTIFIED。44件と正常比較10件を同一分解手順で再計算した。R13 distanceと独立declared edge length合計は全件一致、offset不整合0、lane length不整合0、internal edge欠落0、CRS単位不整合なし。44件全てでedge shape/edge connection gapsが確認され、gapを含むshape polylineはmapped-position直線距離以上となった。root causeはaccepted network geometry/length inconsistency 44件。R13 output/network/mappingは変更せず、R15以降は実行していない。
2026-09-09 network geometry/length re-acceptance: PASS。run_3_geometry_reacceptanceで既存accepted networkを上書きせず、edge/lane shapeをfrom/to junction XYへ接続し、lane declared lengthを接続後polyline長へ更新した。node/edge/lane差分0、weak connectivity差分0、delivery edge数差分0、topology/one-way/permission signature一致、SUMO load PASS、39,956/39,956 mapping保持、edge-node gap 0、connection shape gap 0、lane declared-vs-shape差0、44 OD diagnosticのmapped-position下回り0。新authority V18を記録し、R12/R13/R14は再実行していない。
2026-09-09 R12 V18 re-specification: PASS。V18 authority/hashを読み込み、endpoint 12件（depot 1、customer 10、charger 1）、directed OD 132本、edge ID/delivery access/offset範囲、units/null semantics、travel_time_minimizing、R13 command contractを新runへ固定した。独立validation PASS、R13 routing artifactなしを確認。旧R12 artifactは変更せず、R13以降は実行していない。
2026-09-09 R13 V18 routing computation: PASS。R12 V18固定contractを変更せず、V18専用runで132 directed ODを計算した。generated 132、reachable 132、unreachable 0、routing exception 0。R13 basic validationはschema、OD完全性、network hash、vehicle class、path edge存在/permission、finite/nonnegativeをPASSした。R14独立検証は未実行。
2026-09-09 R14 V18 routing validation: PASS。最新R13 output hashとV18 network hashを確認し、132/132 ODを独立検証した。mapped-position Critical anomaly 0件、original-coordinate diagnostic warning 0件、path/distance/time再計算、offset、delivery access、travel-time objective、lane declared length/shape、lane connection geometryをPASSした。旧V17の44件はV18で解消。R15以降は実行していない。
2026-09-09 R15 common instance integration: PASS。R05〜R14 artifactを読み取り専用で統合し、fixture n=10、node/index order、12 endpoint、132 accepted OD、EV/SOC/charging、field provenanceをcommon instanceへ固定した。同一入力の再生成hash一致を確認。R16以降は実行していない。
2026-09-09 R16 common hard constraints: BLOCKED。13制約のschema・tolerance・validator contractを生成・検証したが、charger再訪問policyが既存仕様で未確定のため停止。R17以降は実行していない。
2026-09-09 R16 charger revisit resolution: PASS。charger複数回訪問を許可し、各訪問を独立charging event、連続eventによる30分上限回避は禁止、R16の恣意的回数上限なしとしてHC12/validator contractを更新した。unresolved semantics 0、13制約schema、R15整合、共通constraint version参照を再validationした。R17以降は実行していない。
2026-09-09 R17 OR-Tools formulation: BLOCKED。R15/R16 authorityからHC01〜HC13 mapping、RoutingModel/CP-SAT候補、辞書式objective、R18 execution contract/output schemaを新runへ生成し、構造検証はPASSした。R16の無制限charger再訪問を有限event modelへ写す上限、q_i（配送要求件数）とpayload kgの変換、solver詳細設定が未採択のためR18へ進めず停止した。OR-Tools solverは実行していない。

2026-09-10 temporary CPU Aer scaling diagnostic: `TEMPORARY_DIAGNOSTIC`。作成済みの `evrp-quantum-temp` を変更せず使用し、固定パラメータの疎な QAOA-like statevector circuit を q=8,10,12,14,16,18,20,22,24,26,28,30 で実行した。全ケース PASS、最大完了 q=30、停止条件未発生。GPU、optimizer、正式QAOA、R21、正式Ising変換、cloud QPU、reduced problem正式採択は実施していない。今回のCPU Aer境界はtemporary diagnosticのみであり、R20 Status=`BLOCKED`、Next Allowed Stage=`NONE`を変更しない。成果物は `reproducibility/outputs/traffic_simulation/temporary_quantum_diagnostic/20260910_temporary_cpu_aer_scaling_n10/TEMPORARY_CPU_AER_SCALING_BENCHMARK.md`。

2026-09-10 temporary QAOA simulation study design: `TEMPORARY_DIAGNOSTIC`。QAOA/Aerを将来量子ハードウェアそのものではなく、量子最適化アルゴリズムの挙動・計算時間・solution qualityを評価し、将来の量子技術発展scenarioへ接続するsoftware simulation layerとして設計した。既存CPU Aer scaling benchmarkは`TEMPORARY_IMPLEMENTATION_FEASIBILITY_DIAGNOSTIC`へ再位置づけし、`Aer simulation limit != quantum computing technology limit`を明記した。今回、formal QUBO、reduced problem、formal Ising、formal QAOA、production simulation、GPU、R21、provider、future scenario parameterは採択・実行していない。R20 Status=`BLOCKED`、Next Allowed Stage=`NONE`は変更しない。成果物は `reproducibility/outputs/traffic_simulation/temporary_quantum_diagnostic/20260910_temporary_qaoa_simulation_study_design_n10/TEMPORARY_QAOA_SIMULATION_STUDY_DESIGN.md`。

2026-09-10 temporary Qiskit/Aer environment planning: `TEMPORARY_DIAGNOSTIC`。R15 current accepted instance、R16 `evrp-common-hard-constraints-v1`、R19 PASS、R20 `FORMULATION_ONLY/BLOCKED` をauthorityとして確認した。既存conda/base environmentは変更せず、environment作成・package install・Aer benchmark・job投入は行っていない。HayateのCPU/RAM/GPU/CUDA/conda、既存envのQiskit/Aer状態、保存容量、schedulerコマンドを読み取り専用で確認し、CPU-onlyとGPU-enabledの隔離environment候補、version compatibilityの未確定点、readiness/failure criteriaを記録した。新規artifactは `reproducibility/outputs/traffic_simulation/temporary_quantum_diagnostic/20260910_temporary_qiskit_aer_environment_plan_n10/` に保存し、既存artifactを上書きしていない。R20 Statusは`BLOCKED`のまま、Next Allowed Stageは`NONE`のまま変更しない。今回のtemporary planはR20 formal formulation、reduced problem、problem size、quantum architecture、provider、QAOA parameterの採択ではない。
## Temporary diagnostic: Qiskit/Aer environment creation and smoke test — 2026-09-10

- Scope: temporary diagnostic environment creation and small CPU Qiskit/Aer smoke tests only.
- CPU environment `evrp-quantum-temp` was created in isolation at `/home/takuma/.conda/envs/evrp-quantum-temp`.
- CPU import, Aer capability, CPU statevector, and CPU QAOA-like smoke tests PASSed.
- GPU package pip dry-run resolved a candidate, but GPU environment creation and GPU tests were deferred as `GPU_TEST_DEFERRED_RESOURCE_CONTENTION` because the H100 had approximately 3.3 GiB free and existing `sglang` processes occupied approximately 91.9 GiB. No process was terminated.
- No existing environment was modified.
- No scaling benchmark, formal QAOA experiment, R21, Ising conversion, formal reduced-problem adoption, provider adoption, or R20 formal judgment was performed.
- R20 Status: `BLOCKED` (unchanged). Next Allowed Stage: `NONE` (unchanged).
- Artifact: `reproducibility/outputs/traffic_simulation/temporary_quantum_diagnostic/20260910_temporary_qiskit_aer_environment_smoke_test_n10/TEMPORARY_QISKIT_AER_ENVIRONMENT_SMOKE_TEST.md`
