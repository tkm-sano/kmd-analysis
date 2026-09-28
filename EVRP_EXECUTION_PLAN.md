<a id="evrp-execution-plan"></a>

# 電気自動車配送経路問題実行計画

Document ID: `EVRP-EXECUTION-PLAN-001`
Role: `CURRENT_NORMATIVE`
Lifecycle: `CURRENT`
Created: `2026-09-10`
Last Updated: `2026-09-10`
現行 Authority: `本研究の唯一の進行管理・実行記録文書。工程status・次工程・実行判断を管理する。`
計画版: 1.0

初回監査・計画作成を完了した後、利用者の継続指示により、計画順に1工程ずつ実行する。各工程の完了記録と停止判定を本書へ先に反映する。

<a id="objective"></a>

# 目的

東京の住宅向けlast-mile 電気自動車配送を対象に、公的統計・実道路ネットワーク・電気自動車性能条件から共通配送インスタンスを構築する。古典最適化と量子最適化を同一条件で比較し、配送需要充足率と計算資源要求を評価する。

<a id="scope"></a>

# 範囲

Residential / B2C last-mile 荷物 配送。基準 problemはE-時間窓付き配送経路問題を基礎とする電気自動車 経路計算 problem。現在の地理基盤は大田区。古典手法はOR-Tools、量子手法は制約なし二値二次最適化 → Ising ハミルトニアン → 量子近似最適化アルゴリズム → Qiskit Aer。

39,956地点は候補母集団 $C_{\mathrm{all}}$ であり、全件を1つの電気自動車配送経路問題として解かない。$C_s\subset C_{\mathrm{all}}$、$n=|C_s|$ をproblem-規模実験パラメータとする。25/50/100等を固定想定条件として採択しない。基準は単一配送拠点を原則固定する。

[最新B2C仕様](RESEARCH_PIPELINE_REFERENCE.md#b2c-pipeline-20260909)を参照するが、今回の指示で時間窓を**作業開始**に適用し、Operating 時間は**最大運行時間を設定した場合に適用**すると具体化した。本書がこれらと実行順序・停止条件の最新記録である。旧ロードマップ、コマンド操作やポータルの「Routing 次の工程」「需要 完了」は既存実装の表示であり、本書の次工程や合格を上書きしない。

<a id="existing-state-audit"></a>

# 既存状態監査

既存成果物分類と工程状況は別の軸である。`ACCEPTED`は確認した受入範囲内、`IMPLEMENTED_NOT_VALIDATED`は実装があるが対象検証未完、`PARTIAL`は一部のみ、`NOT_IMPLEMENTED`は現行source/runnerなし、`UNKNOWN`は証拠不足を意味する。

| 対象 | 分類 | 監査証拠と範囲 |
|---|---|---|
| 現行B2C仕様 | 受入済み | 2026-09-09の利用者採択。研究実装の受入ではない。 |
| Formal SUMO network | 受入済み | 現行の正本 → run_2/network_acceptance.json、FORMAL_NETWORK_ACCEPTED=真。今回ハッシュ値照合・既存正本 検証器 合格。 |
| Stop-road mapping | 受入済み | 39,956/39,956、配送許可道路区間。道路区間中点索引・上書き指定という既存方式の受入範囲。 |
| 39,956 候補 母集団の新用途 | 一部完了 | コンマ区切り形式は39,956行、stop_id/building_idとも重複・空欄0、WKT座標は経緯度範囲内。新しい住宅候補母集団の代表性・メッシュ対応・再生成契約はR03で検証する。 |
| Candidate生成方法 | 一部完了 | stop_generation_run_summary.jsonに世帯→建物割当乱数の種 20260830、85,690割当建物のうち39,956 有効建物。正式再生成source/runnerは現行checkoutにない。 |
| 国勢調査2020 500m | 一部完了 | ZIP ハッシュ値は台帳一致。人口列の既存利用あり、世帯列採用と秘匿・合算の解釈は未確定。ZIPは指定構成要素だけを読む。 |
| 個人のモノの受取調査2024 | 一部完了 | 成果物一覧 20 entries / 19 unique files、全ハッシュ値一致。ss515重複入口は同一ハッシュ値で原本を変更しない。新しい需要/時間窓の採用契約は未完。 |
| 既存人口・荷物換算単位生成 | 受入済み | prepare_baseline_demand.pyの既存試験 13 合格。旧代理指標の範囲に限り、新しい配送件数生成の合格ではない。 |
| 新B2C weight/sampling/demand/TW/service生成 | NOT_IMPLEMENTED | 旧コンマ区切り形式・仕様はあるが新契約の本番生成器・検証器はない。 |
| OSM/SUMO runtime | 一部完了 | SUMO/duarouter 1.24.0の二値あり。Python環境でsumolib/traciのdistribution 付随情報なし。スーモ付属toolsの取込みは未検証。 |
| Routing code | 一部完了 | research_cli/routing.pyは入口・未実装通知。道路網 到達可能性検査コードはあるが本番必要出発地・到着地 実行器はない。 |
| Routing validation | 一部完了 | 受入主標本 100/100、追加sanity 91/100。全必要出発地・到着地の証明ではなく、将来R14を代替しない。 |
| 配送拠点 | 一部完了 | 旧版の公的物流施設代理指標候補コンマ区切り形式あり。基準拠点・受入網接続は未採択。 |
| EV specification | 一部完了 | managed_urban_ev_delivery_v1は明示モデル 仮定（配送、積載量 2000kg）。電気自動車 catalog派生表もあるがbattery/energy/SOCの問題例採択は未完。 |
| Charging stations | 一部完了 | 現行未加工 充電は.gitkeep、旧版のOCM候補あり。public 接続不明の行があり、利用可能性・互換性・網接続は未受入。 |
| OR-Tools package | IMPLEMENTED_NOT_VALIDATED | 9.12.4544導入済み。13制約付き本番model/runner/解検証はNOT_IMPLEMENTED。 |
| Common instance / independent EVRP validator | NOT_IMPLEMENTED | 05_src/optimizationには古い__pycache__のみ。出典不在を実装済みとしない。 |
| Reduced QUBO / Ising | ACCEPTED_SCOPED | `INITIAL_R20_REDUCED_ROUTE_ORDERING_SCOPE_ONLY`についてR20 定式化、R21 厳密 制約なし二値二次最適化 検証、R22 全体-状態 Ising equivalenceが合格。完全な電気自動車配送経路問題 QUBO/Isingは未完。 |
| Reduced QAOA authority | SEE_CURRENT_INDEX | Reduced R23の参照先の補完・最終結果・制約・R24 判定基準は[R23_STATUS.md](05_src/traffic_simulation/R23_STATUS.md)を参照する。完全な電気自動車配送経路問題の未完状態とは分離する。 |
| Qiskit / Aer | IMPLEMENTED_SCOPED_ENVIRONMENT | isolated `evrp-quantum-temp`でPython 3.11.16、Qiskit 2.5.2、Aer 0.17.2、qiskit-最適化 0.7.0、qiskit-algorithms 0.4.0を確認。GPU/QPU 根拠ではない。縮約した 中央処理装置 simulation ベンチマークの正本はR23_STATUS.mdを参照する。 |
| 運用パラメータの実測根拠 | UNKNOWN | 住宅作業時間、採択電気自動車の消費率、充電設備利用条件等は未確定。 |
| Tests / manifests / generated reports | 一部完了 | 既存ポータル 6検査合格・旧需要13 試験 合格。下流電気自動車配送経路問題実験の受入成果物一覧と報告はない。 |

主な証拠:

- [道路網正本](reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml)
- [geometry/length再受入authority](reproducibility/config/traffic_simulation/current_network_completion_authority_v18_geometry_reaccepted.yml)
- [候補生成要約](03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/stop_generation_run_summary.json)
- [旧処理工程要約](03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/pipeline_run_summary.json)
- [宅配統計取得記録](03_data/metadata/acquisition/20260825_tokyo_metropolitan_goods_movement_delivery_receipt_tables.md)
- [需要コード](05_src/traffic_simulation/demand/prepare_baseline_demand.py)
- [経路計算入口](05_src/research_cli/routing.py)
- [比較規約](05_src/traffic_simulation/optimization_comparison_protocol.md)
- [EV profile](reproducibility/config/traffic_simulation/scenario_profiles/managed_urban_ev_delivery_v1.yml)
- [Depot proxy](legacy/non_sumo_route_proxy_analysis/data/processed/evrp_constraint_gap_inputs/depot_candidates_public_proxy_snapshot.csv)
- [Charging proxy](legacy/non_sumo_route_proxy_analysis/data/processed/charger_access/eligible_charger_candidates.csv)

旧処理工程 まとめの配送地点=0/未割当と、後続配送地点 まとめ・道路網 受入の39,956は異なる生成段階を示す。旧まとめのblocked snap 規則を現在の道路網受入へ適用しない。一方、候補再生成の完全な連鎖は未確認なのでR03のGateで説明を要求する。39,956が旧日の有効建物に限られる選択偏りは、新しい母集団の研究上の限界として残す。より大きい建物母集団へ黙って置換しない。

# 処理工程 Overview

工程順序は以下に固定する。Definition工程に必要な小規模検証用データ検査はその工程内で行い、本番計算の先行実行はしない。

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
22. `R22_ISING_CONVERSION` — Ising Conversion (full-EVRP path; reduced branch: `R22_REDUCED_ISING_CONVERSION`)
23. `R23_QAOA_AER_EXECUTION` — QAOA / Qiskit Aer Execution
24. `R24_QUANTUM_SOLUTION_DECODE` — Quantum Solution Decode
25. `R25_COMMON_INDEPENDENT_VALIDATION` — Common Independent Validation
26. `R26_DEMAND_FULFILLMENT_EVALUATION` — Demand Fulfillment Evaluation
27. `R27_CLASSICAL_QUANTUM_COMPARISON` — Classical–Quantum Comparison
28. `R28_PROBLEM_SIZE_SCALING` — Problem-Size Scaling
29. `R29_EV_TECHNOLOGY_SCENARIO_EVALUATION` — EV Technology Scenario Evaluation
30. `R30_FINAL_REPRODUCIBILITY_VALIDATION` — Final Reproducibility Validation

<a id="common-hard-constraints"></a>

# Common 必須制約

| # | 制約 | 共通の正式な意味 |
|---|---|---|
| 1 | Customer Visit Constraint | 配送する顧客は高々1回訪問する。未充足は許容する。 |
| 2 | Depot Departure and Return Constraint | 使用車両は同一配送拠点から出発し帰着する。 |
| 3 | Flow Conservation Constraint | ノードに入った車両は同じ車両で出る。 |
| 4 | Subtour Elimination Constraint | 配送拠点から切り離された独立cycleを禁止する。 |
| 5 | Vehicle Assignment Constraint | 顧客を複数車両へ重複割当しない。 |
| 6 | Capacity Constraint | 積載上限を絶対に超えない。 |
| 7 | Time Window Constraint | $e_i\le b_i\le l_i$、$b_i$は作業開始時刻。 |
| 8 | Time Propagation Constraint | 移動、作業、待機、充電を同じ時刻軸で正しく累積する。 |
| 9 | Operating-Time Constraint | 最大運行時間を設定した場合、その上限を超えない。無効の場合も共通適用フラグに記録。 |
| 10 | Battery / SOC Constraint | 経路全体で充電率が最低許容値を下回らない。 |
| 11 | Initial / Final SOC Constraint | 出発時充電率を定義し、必要な場合は帰着時最低充電率を満たす。 |
| 12 | Charging Constraint | 充電可能地点のみ、電池 容量以下、充電量と充電設備 powerに対応した時間を計上する。 |
| 13 | Reachability Constraint | OSM/SUMOで実際に到達可能な区間のみ使用する。 |

R16で各意味・許容誤差・離散化と適用フラグを凍結する。両手法で制約を変更しない。充電局の再訪問を顧客高々1回制約と混同しない。全顧客訪問を必須にしないため、無配送の空計画が実行可能なら配送需要充足率=0は正当な解であり、問題全体のinfeasibilityとは異なる。

<a id="data-classification-rules"></a>

# データ分類規則

全入力値に`classification`, `source`, `source_hash`, `unit`, `transformation`, `assumption_reason`（該当時）を付ける。分類はOBSERVED / PUBLIC_STATISTICS_DERIVED / PROXY / SYNTHETIC_CALIBRATED / ASSUMED / COMPUTEDの6種。

公表人口・世帯値はOBSERVED、集計・配賦値はPUBLIC_STATISTICS_DERIVED、住宅需要を代理する使い方はPROXYとして派生来歴をつなぐ。顧客発生と時間窓は統計較正後にSYNTHETIC_CALIBRATED、道路d/t/aはCOMPUTED、仮定作業時間は理由付きASSUMED。未較正の合成値をSYNTHETIC_CALIBRATEDと偽らない。

依頼文のcatalog 電池「OBSERVED / PUBLIC_SPECIFICATION」は、分類をOBSERVED、出典種別をPUBLIC_SPECIFICATIONとする（実測値という意味ではない）。分類集合を黙って増やさない。根拠不明値はUNKNOWNの課題として実行不可にし、silently ASSUMEDにしない。

<a id="demand-weight-definition"></a>

# 需要重み定義

$w_i$は相対標本抽出 重みで、配送量$q_i$とは別概念である（$w_i\neq q_i$は意味の区別であり、偶然の数値一致を禁止しない）。住宅では利用可能な世帯数を人口より優先的代理指標として検討する。

候補式は $w_i=H_m/N_m$、地域宅配発生率が利用可能なら $w_i=H_m r_m/N_m$。$H_m$はメッシュ世帯数、$N_m$は同メッシュ内候補数。全候補に$H_m$をそのまま付与しない。メッシュ内重み和が$H_m$（または$H_mr_m$）となることを検証する。N_m=0の需要は未配賦として記録し、隣接メッシュへ黙って移さない。採用式・秘匿/合算・境界処理はR02〜R04で確定し、初回は未採択。

<a id="customer-sampling-rules"></a>

# 顧客標本抽出規則

Spatial stratification + weighted 標本抽出 + without replacement。層と割当数、アルゴリズム、候補順序、RNG種類・版・random 乱数の種を保存する。nは入力パラメータ。OR-Tools/QAOA直接比較はsame instance_id / 顧客 IDs / 問題例 乱数の種 / demand / 時間窓 / 経路計算 costs / 車両 条件。求解器固有の乱数の種は役割別に別途保存する。

<a id="time-window-rules"></a>

# 時間窓規則

個別住宅の実配送ログではなく、東京都市圏の日時指定・受取統計で較正した合成 $[e_i,l_i]$。出典、変換、窓幅、指定なし、時刻原点・単位・乱数の種を保存する。受取時刻分布をそのまま許容窓とはしない。判定は作業開始時刻。

<a id="routing-baseline-rules"></a>

# 経路計算の基準規則

$d_{ij}$=道路網 距離、$t_{ij}$=移動 時間、$a_{ij}$=到達可能性。全39,956完全出発地・到着地を無条件に生成しない。depot/customer/chargerの必要出発地・到着地と端点位置を固定する。正当な$a_{ij}=0$自体は不合格ではない。経路なしを実装失敗と区別できなければ不合格。未到達のd/tはnull等の明示表現にし、0として求解器へ投入しない。

R12〜R14ではR05〜R11の生成契約から経路計算端点を固定する。R15は検証済費用と他入力の最終統合・データ構造 固定を行うため循環依存はない。既存対応付けのmidpoint近似と道路位置補正値の扱い、異なる地点が同一道路区間にある場合のzero 距離の妥当性はR12で定義する。

<a id="common-delivery-instance"></a>

# 共通配送問題

$I_s$はinstance_id、顧客 IDs、配送拠点、車両、充電 stations、demand、時間窓、作業 times、road 距離、移動 時間、到達可能性、車両 容量、電池 容量、電力量 consumption、充電率 assumptions、充電 assumptions、出典 ハッシュ値、random seeds、データ構造 版を最低限含む。

加えて単位、ノード順、constraint 版、目的優先順、生成config/code ハッシュ値を固定する。R15以降の変更は新instance_idと変更記録が必要で、同じ比較対の片側だけ変更しない。電力量行列は電気自動車依存なので技術想定条件で再計算してよいが、道路距離・旅行時間は原則固定する。

<a id="classical-branch"></a>

# 古典計算 分岐

OR-Toolsを用い、基準は各抽出顧客=1配送要求として $\max\sum_i y_i$。この1件対応は配送件数と顧客数を一致させるための明示したモデル規約（実測主張ではない）で、複数件を導入するなら件数$c_i$と分母を再定義する。荷量を主目的に採用する実験は $\max\sum_i q_i y_i$ として両手法を同時に変更・記録する。同一充足なら第二目的の距離等を最小化する。二段階求解または優先順位を保証する重みの根拠をR17で示す。OR-Tools内部判定だけで実行可能性を認定しない。

<a id="quantum-branch"></a>

# 量子計算 分岐

同一$I_s$から制約なし二値二次最適化を生成し、論理上の 変数、二値 変数、auxiliary 変数、符号化、罰則項 formulation/coefficients、discretization、制約なし二値二次最適化 行列、二値 変数数、論理上の 量子ビット 件数を保存する。未表現のHard Constraintは対応表に明示し、共同比較分岐を実行不可にする。制約を削除した問題を同一比較と称しない。

連続時間/充電率の離散化が実行可能集合を変える場合、OR-Toolsにも同じ離散化を適用した新共通問題例で比較するか、同値性が確立するまで停止する。小規模厳密検証用データはOR-Toolsの「良い暫定最良解」を厳密最適値と見なさず、列挙や証明済値を使う。罰則項が低電力量の違反解を許しても独立検証器で除外する。

<a id="common-independent-validator"></a>

# Common 独立検証器

両手法で同じ検証器・版・入力ハッシュ値を使用する。顧客 duplication、配送拠点発着、流れ、subtour、車両 割当、容量、時間窓、時間 propagation、operating 時間、充電率、initial/final 充電率、充電、到達可能性を経路から再計算する。Hard Constraint違反解は実行可能扱いしない。検査器自体の異常は不合格、正常検査器が量子標本を違反と判定することは研究結果として区別する。

<a id="execution-status"></a>

# 実行 状態

| 状態 | 意味と遷移 |
|---|---|
| NOT_STARTED | 未実行。開始・終了日時を捏造しない。 |
| IN_PROGRESS | 記録した1工程だけを実行中。 |
| 合格 | 工程と検証がAcceptance Gateを満たした。 |
| RESULT_INFEASIBLE | 正常処理だが実行可能解なし。証明済infeasibleと求解器未発見を理由で区別する。 |
| LIMIT_REACHED | 事前上限に到達。対象branch/scalingのみ停止。暫定最良解は保存・検証する。 |
| 実行不可 | 必須データ・仕様・根拠不足。次工程へ進まない。 |
| 不合格 | 実装異常・破損・検証不整合・再現不能。次工程へ進まない。 |

UNKNOWNは監査項目の分類でありstage 状況には使用しない。未実行の下流は未着手のまま、課題へ潜在阻害要因を記録する。

<a id="global-stop-rules"></a>

# 共通停止規則

必須入力なし、期待ハッシュ値不一致、データ構造不合格、必須パラメーターの出典・来歴不明、データ分類不明、Acceptance不達、検証器実行不能、再現性試験不合格、同seed/configで非再現、受入成果物との不整合を説明不能、のいずれかで停止する。欠落・未定義は実行不可、破損・誤実装・検証矛盾は不合格。受入済network/mappingを再生成・上書きして解消しない。

<a id="data-stop-rules"></a>

# データ停止規則

候補 識別子 重複、不正 coordinates、負 重み、合計 重み=0、母集団不足、非復元抽出で重複 顧客、負 demand、不正 window/e_i>l_i、負 作業時間、未対応 単位、必須 statistical 出典 unavailable、transformation undefinedで停止する。数値は有限も確認する。既知欠損の規則未定義は実行不可、規則違反出力は不合格。

# 経路計算停止規則

説明のない必須 出発地・到着地欠落、到達可能=true/pathなし、負 distance/time、異なる端点の説明不能zero 距離、one-way/access/vehicle-class違反、保存先とd/t不整合、道路網 ハッシュ値不一致、経路計算 設定未記録は不合格。正当な到達不能は正常結果として保存する。

<a id="common-instance-stop-rules"></a>

# Common 問題例停止規則

顧客必須なのに0、配送拠点なし、車両0、payload/battery容量非正、customer/chargerの経路計算 対応付け欠落、識別子不整合、必須パラメーター不足は停止。出典未解決は実行不可、データ構造/生成違反は不合格。

# OR-Tools 終了規則

実行可能解かつ独立検証器合格で合格。正常model/runで解なしはRESULT_INFEASIBLE（証明有無を記録）。time/memory上限はLIMIT_REACHEDで暫定最良解を保存。exception、不正 モデル、crash、実行可能性矛盾、実行可能宣言解のHard Constraint違反は不合格。

<a id="qubo-stop-rules"></a>

# 制約なし二値二次最適化停止規則

binary/decoder 対応付け未定義、罰則項未定義、未対応 constraint未記録、NaN/Inf、malformed 制約なし二値二次最適化、小規模同値性失敗、logical/binary対応不能で実行不可または不合格。未表現制約を記録するだけではGate通過にならない。R21 合格なしでR22/R23へ進まない。

<a id="quantum-resource-preflight"></a>

# 量子計算資源事前確認

監査環境: AMD EPYC 9684X、384 論理上の CPUs、physical RAM 1,622,707,548,160 バイト（約1511 GiB）。監査時MemAvailable 1,555,386,302,464 バイト。sessionとuser階層のcgroup memory.max/highはmax、cpu.maxはmax 100000。共有hostの全資源を占有可能と解釈しない。

以下は**実測性能限界ではなくASSUMEDの保守的実行予算**として初期採択する。各実行直前に空きメモリ・cgroupを再確認し、より低い実上限を優先する。

| 項目 | 初期ceiling / 設定 |
|---|---|
| 分岐同時実行 | 1、中央処理装置 threads上限8、画像処理装置使用なし |
| OR-Tools memory / wall-clock | 8 GiB / 300秒 per 問題例 |
| Aer memory / wall-clock | 8 GiB / 600秒 per 問題例 |
| Aer logical qubits | 最大26（符号化から計算しnで代用しない） |
| transpiled circuit depth / gate count | 最大10,000 / 100,000（パラメーター binding後の代表回路を計測） |
| QAOA p / shots | 初期p=1、回測定=1024 per 目的 evaluation。変更は事前記録 |
| 最適化処理 | 初期候補COBYLA、max iterations=100、目的相対変化tolerance=1e-6、いいえ-improvement=20 evaluations |
| 最適化処理終端 | tolerance/no-improvementは正常収束、iteration/wall ceilingはLIMIT_REACHED。最良標本を保存 |
| 小規模厳密検証 | 二値 変数<=20、実経過時間<=60秒、メモリー<=1 GiB。超過時は検証検証用データを縮小する変更を記録 |

初期計算方式方式は中央処理装置 double-precision 状態ベクトルを計画し、採用可否とAer 版はR23で確認する。状態要素数$2^Q$、状態 バイト=$16\times2^Q$、保守的estimated peak=$4\times16\times2^Q+1$ GiB（作業領域用の明示仮定）。Q=26で未加工 1 GiB、推定5 GiB。推定が8 GiB、または直前有効空き量の25%を超える場合は起動せずLIMIT_REACHED。dense 制約なし二値二次最適化行列や回路構築のメモリも加算する。density-行列等へ変更したら式から再審査する。

論理上の 量子ビット、状態 規模、estimated メモリー、回路 深さ、判定基準 件数を必ず保存する。package/実行環境未準備は実行不可。OOM/crashまで試さず、監視と終了処理をR23で検証してから本実行を開始する。

<a id="qaoa-termination-rules"></a>

# 量子近似最適化アルゴリズム終了規則

max iterations、実経過時間、convergence tolerance、いいえ-improvement 件数、回測定は上表で事前定義する。実装最適化処理のiterationと目的 evaluationの数え方を別記する。実行可能 標本=0はRESULT_INFEASIBLE、理由=NO_FEASIBLE_QAOA_SAMPLE（上限に達した実行はLIMIT_REACHEDを優先し標本結果を併記）。これは実装不合格ではない。

# 問題規模規模拡大停止規則

R28開始前に増加するn列・乱数の種列・合計実行予算を本書へ記録する。初期nや増分を未検討の固定想定条件から流用しない。OR-Toolsは300秒/8GiB、または同分岐の連続3 実行で実行可能解未発見を停止閾値とする。量子近似最適化アルゴリズムはqubit/memory/depth/gate/wall ceiling到達でその分岐の拡大を停止する。

依頼の$n_{\max}^{classical}$、$n_{\max}^{quantum}$は各分岐の停止境界nとして保存し、last_attempted_n、largest_validated_feasible_n、first_limit_n、stop_reasonも併記する。最初の失敗nを最大成功nと誤記しない。両分岐成功の同一I_sだけを直接比較する。

# 有効な研究結果 That Must NOT 停止その Whole 処理工程

一部未配送、低配送需要充足率、配送需要充足率=0、正当な到達不能、optimality未証明の実行可能 暫定最良解、量子近似最適化アルゴリズムが古典より悪い、量子近似最適化アルゴリズム 実行可能 標本なし、Aer 資源 limit、技術想定条件で100%未達は不合格ではない。不正解しかない場合の配送需要充足率は実行可能 計画の配送需要充足率=0と区別してN/Aにし、いいえ-実行可能件数を報告する。

非合格の許可遷移: R18 RESULT_INFEASIBLE/LIMIT_REACHED → R19で証拠・暫定最良解を検証 → R20。R19で有効解なしを正常記録できればRESULT_INFEASIBLEとしてR20へ進めるが、R21は独立の厳密小規模検証用データが必要。R23 LIMIT_REACHED/RESULT_INFEASIBLE → R24で標本または非実行理由を記録 → R25 → R26 → R27。取得できなかった解の復号や配送需要充足率を創作しない。R24/R25の正常な結果不在はRESULT_INFEASIBLE、R26/R27は欠測理由の正常集計で合格可能。R28/R29は許可された分岐・子実行のみ継続。BLOCKED/FAILは例外なく先へ進まない。

<a id="execution-protocol-after-creating-the-md"></a>

# 実行手順後の作成その MD

最初の未着手かつpreconditions充足stageを1つ選びIN_PROGRESSへ記録 → 手法実行 → 検証 → 停止条件評価 → command/hash/version/resultsを記録 → status/Decision確定 → 次に許可される段階。合格以外は上記の明示例外のみ遷移可能。R03が実行不可になったため、R04以降は開始しない。

<a id="execution-order-rule"></a>

# 実行順序規則

Plan → Execute → Validate → 記録 → Decide → Nextを厳守し、複数stageを先行実行しない。監査中の複数ファイル確認はR01内部であり、R02以降の採択・生成を行ったとは扱わない。

R28/R29では必須の反復を子実行として扱い、本書内にR13〜R27の必要工程を同じ順序で記録する。変化しないGateはハッシュ値一致の再利用根拠を残す。各子実行も本書の段階 記録 Templateを使い、並列に先行しない。新データ定義が必要なら先に変更管理を行い、該当上流Gateを開き直す。

# 変更-管理規則

変更前・変更後・理由・影響stage・既存結果への影響・再実行stageを本書へ先に記載してからコードを変更する。既受入物はハッシュ値付きで保存し、新出力は実行識別子別の分離保存先とする。

| 記録 | 変更前 | 変更後 | 理由・影響・再実行 |
|---|---|---|---|
| 2026-09-09 initial plan | 旧段階 1 Routing 次の工程、時間窓開始/完了未確定、最大運行時間必須の表現 | 本書R01→R30、時間窓=作業開始、operating上限は設定時適用 | 最新利用者指示。R02〜R30の今後設計へ適用、旧受入道路網再実行不要。 |
| 2026-09-09 governance | 複数文書に研究進行記録 | 本書だけで進行・実行を管理 | 旧仕様・機械成果物は参照証拠。本書以外の状況から次工程を選ばない。 |
| 2026-09-09 R03 unblock attempt | R03は候補生成runner/configと候補別道路接続表が不足し実行不可 | 受入済候補コンマ区切り形式・受入済道路網を入力として、候補コンマ区切り形式を変更せず候補別スーモ 道路区間接続表と検証成果物一覧を新実行 保存先へ生成する。既存受入成果物は再生成・上書きしない | R03の道路接続証拠を補完する。候補生成実行器自体は新たに発見できない限り未解決のため、R03は再判定後も実行不可の可能性がある。再実行stage: R03のみ |
| 2026-09-09 R13 runner restoration | R13はR12固定取り決めの実行器欠損で実行不可 | 既存SUMO/sumolibを使用し、R12の`travel_time_minimizing`、配送 道路区間 通行許可、directed グラフ、端点 位置補正値、到達不能 null 意味を実装する`compute_routing.py`を固定保存先へ追加する。検証用データ 検証を新実行識別子へ保存し、合格後にR13本計算を再開する | R12仕様を変更せず欠損実行器 阻害要因を解消するため。R12 成果物は変更しない。影響stage: R13のみ。R14以降は実行しない。 |
| 2026-09-09 R14 independent routing validation | R13 経路計算 出力は実行器内検証済みだが、独立したmatrix/graph/geometry 検証は未実装 | R13 出力をimmutable 入力として、独立検証器で出発地・到着地 completeness、端点 網羅率、schema/numeric、配送 connectivity、位置補正値 component、代表経路再構成、移動時間 目的、speed/asymmetry/detour diagnosticsを別実行 保存先へ保存する。R13 出力は再生成・上書きしない | R13 経路計算 行列を電気自動車配送経路問題入力として採択可能か独立に判定するため。影響stage: R14のみ。R15以降は実行しない。 |
| 2026-09-09 R14 spatial gate revision | 旧判定はoriginal 端点座標間のstraight-line 距離違反を即Critical 不合格としていた | 新判定は実際のmapped スーモ positions間の`road_distance >= straight(mapped)-epsilon`をCritical Gateとし、original coordinate比較は対応付け距離を考慮したdiagnostic 注意事項へ変更。`epsilon=1e-6 m`を数値丸め用に固定 | 経路計算 端点と比較対象を一致させるため。R13 出力、受入済み道路網、端点 対応付けは変更しない。影響stage: R14のみ。R15以降は実行しない。 |
| 2026-09-09 R14 root-cause decomposition | R14のmapped-位置 Critical anomaly 44件は原因未確定 | R13 経路 道路区間 sequenceを読み取り専用で分解し、スーモ declared 道路区間 長さ、車線 長さ、形状 polyline、道路区間 接続 隔たり、位置補正値 部分的、internal 道路区間、座標参照系を正常出発地・到着地と比較する最上位-cause investigation 成果物を追加 | 44件の不合格原因を分類するため。R13 出力、受入済み道路網、端点 対応付けは変更しない。影響stage: R14のみ。修正はR14で行わず、R13/R12の再実行要否を記録する。 |
| 2026-09-09 network geometry/length re-acceptance scope | 受入済み道路網のtopology/connectivity、配送地点 対応付け、配送 接続、経路計算 geometry/lengthを単一の受入範囲として扱っていた | topology/connectivity、39,956 配送地点 対応付け、配送 接続、one-way/permissionは既存受入を保持し、経路計算 距離用geometry/declared-length consistencyだけを新実行で再検証・修正する。旧受入済み道路網とR13 出力は不変。 | R14 最上位-causeで44件が道路網 geometry/length inconsistencyと分類されたため。新道路網が全受入条件を満たした場合だけ正本を更新し、R12/R13/R14の再実行は今回行わない。 |
| 2026-09-09 R12 V18 re-specification | R12 endpoint/OD/configはV17 受入済み道路網 ハッシュ値 `4625...40f`を参照 | V18 authority/hash `460554...51b2`で端点 対応付け・位置補正値範囲・132 directed 出発地・到着地・データ構造・R13 コマンド 取り決めを新実行へ再固定。旧R12 成果物は保持し、R13本番計算は未実行。 | geometry/length再受入後の経路計算入力を固定するため。影響stage: R12のみ。R13以降は今回実行しない。 |
| 2026-09-09 R16 charger revisit resolution | 充電設備は顧客 訪問制約の対象外だが、複数回訪問の許可/禁止が未定義でR16 実行不可 | 充電設備複数回訪問を許可し、各訪問を独立充電 eventとして扱う。effective power 70 kW、各event 30分以下、連続eventによるsession上限回避は禁止。R16では恣意的回数上限を置かず、制約なし二値二次最適化 コピー上限はR20/R21へ延期。 | 利用者の明示採択により唯一のR16 阻害要因を解消。HC12と検証器 取り決めを更新しR16のみ再検証。影響stage: R16。R17以降は今回実行しない。 |
| 2026-09-09 R17 formulation boundary | R16 意味をOR-Toolsへ写す定式化とR18設定は未固定 | RoutingModelをnode/flow/depot/visitの骨格、CP-SAT/custom 状態を充電率・充電 eventの候補として仕様化し、HC 対応付け・R18 取り決め・出力 データ構造を新実行 保存先へ保存。充電設備 event コピー数、q_i（件数）と積載量（kg）の変換、求解器詳細設定は未採択のまま実行不可。 | R16意味論を黙って近似せず、R18実行前に未解決点を可視化するため。影響stage: R17のみ。R18以降は実行しない。 |

<a id="2026-09-09-r09-v18-authority-closure-attempt"></a>

# 2026-09-09 R09 V18 正本参照先の補完試行

- **Change control:** R09 artifact is V17/legacy-network based; current R15 also points to the old R09 run and a constraint placeholder. Re-map the unchanged `DEP_006` identity/coordinates/PROXY to the V18 accepted network in a new run, validate all requested mapping/topology/hash/reproducibility fields, and compare with R12/R13/R14.
- **Stop rule:** If edge ID, offset, or mapping distance differs from the currently accepted R12/R13/R14 endpoint mapping, stop with R12→R14 re-execution required; do not propagate to R15–R18. Old artifacts remain immutable and R18 is not executed.

<a id="execution-status-snapshot"></a>

# 実行状態保存時点の記録

2026-09-09 preparation record: payload model, charger event upper bound, and fixture solver configuration were fixed for R17 revalidation. R18 and later stages remain NOT_STARTED and are not executed in this turn.

R01 Existing State 監査〜R15 共通配送問題 Definitionを合格として記録した。R03では、既存候補別道路接続表の検証結果を再利用し、git history内の候補生成source/configと入力ハッシュ値を追跡して一時保存先で厳密 regenerationを実行し、39,956候補の完全一致を確認した。R12では検証用データ端点12件と必要OD132本を固定し、R13ではその全出発地・到着地を実道路経路計算した。今回のR09 V18 正本 参照先の補完により、R15 現行とR17 現行も新実行として合格し、R16 意味は変更せず参照ハッシュ値を更新した。R18は未実行、現在実行中stageなし。旧network/mapping/旧需要試験の受入を下流stageへ自動昇格させない。

正本 参照先の補完前の停止工程は**R17_ORTOOLS_FORMULATION**だった。R09 V18 対応付けとR12–R14比較、R15/R17 propagation、independent 検証が合格したため、現在の正本 参照先の補完 状況は合格である。R18〜R30は未実行であり、本番用nは未採択のまま保持する。

<a id="2026-09-09-r09-v18-authority-closure-and-r15r17-propagation-record"></a>

# 2026-09-09 R09 V18 正本参照先の補完 ・ R15→R17 伝播記録

- **Scope:** R09 V18 re-mapping/revalidation and downstream hash/reference propagation only. `R18_ORTOOLS_EXECUTION` was not executed.
- **R09 V18 run:** `20260909_r09_depot_fixture_n10_v18_geometry_reaccepted`; repeat run `20260909_r09_depot_fixture_n10_v18_geometry_reaccepted_repeat` was used for deterministic reproducibility. Old V17 R09 artifacts were not overwritten.
- **R09 結果:** `PASS`. DEP_006 / 京浜トラックターミナル, coordinates `139.745306, 35.586971`, `PROXY`, 配送 接続 合格, 採用済み 道路区間 `617631294`, 道路区間 長さ `38.346827 m`, 位置補正値 `12.507432581420328 m`, 対応付け 距離 `1.4616751655855091 m`, 接続構造 合格, 道路網 ハッシュ値 `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`, 成果物一覧 入力 ハッシュ値 合格, deterministic 反復 合格. The V18 検証 報告 is `reproducibility/outputs/traffic_simulation/demand/evrp_r09_depot/20260909_r09_depot_fixture_n10_v18_geometry_reaccepted/r09_v18_validation_report.json`.
- **V17→V18 difference:** identity, facility, coordinates, classification, edge ID, and mapping distance were preserved. Offset changed `7.496943583328211 m → 12.507432581420328 m` (`+5.010488998092117 m`); declared edge length changed `28.41 m → 38.346827 m`; network hash changed V17 `4625dbbc150cbcf72964bed0e90a8b33fe03f190ff4264aecaaf89e3aab0e40f → V18 460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`.
- **R12–R14 rerun decision:** no rerun required. Current accepted V18 R12/R13/R14 endpoint manifests already have the same edge `617631294`, offset `12.507432581420328 m`, mapping distance `1.4616751655855091 m`, coordinates, and V18 network hash. Therefore the V18 R09 mapping is substantively identical to the mapping used by accepted R12–R14.
- **R15 current run:** `20260909_r15_common_instance_fixture_n10_v18_r09_v18_authority_closed`. Existing values and semantics were preserved; R09 source changed to the V18 artifact, the formal `evrp-common-hard-constraints-v1` reference replaced the stale placeholder, and the new instance validation PASSed. New R15 `common_instance.json` SHA-256: `7ca39facf83de619db7ec37daa90409834d89b4b75bfeb4e7c501ddef94b2ac4`.
- **R16 propagation:** current constraint artifact retained without semantic modification. R16 constraint hash propagated to R17: `1b1c3132b44a542605b19f354a5d9c7464a093aa4cb23b04583ca92e0841ec67`; version remains `evrp-common-hard-constraints-v1`.
- **R17 current run:** `20260909_r17_ortools_formulation_fixture_n10_v18_r09_v18_authority_closed`. Independent validation PASSed. R15 instance hash and R16 artifact hash match exactly; HC01–HC13 mapping, HC12 `E_max(n)=n+1` with n=10 → 11 event slots, formulation semantics, payload separation, charger semantics, and solver config show no semantic drift. R18 contract remains `READY_PENDING_R18` / `R18_ONLY_NOT_EXECUTED`.
- **Current-chain stale audit:** current R09 V18, R15, R16, R17, and R18 contract contain no V17 network hash, V17 current-authority reference, superseded R09 reference, old R15 constraint placeholder, BLOCKED R16/R17 reference, stale HC12 text, or legacy payload path. Historical artifacts may retain those values but are not referenced by the current chain.
- **Closed dependency chain:** `candidate → R04 → R05 → R06 → R07 → R08 → R09 V18 → R10 → R11 → R13/R14 V18 → R15 current → R16 current → R17 current → R18 contract` is uniquely closed. R12 is the accepted V18 routing authority specification used by R13/R14; no alternate current R09/R15/R16/R17 reference remains in the chain.
- **R18 readiness:** `READY` for the next allowed execution stage, with the explicit restriction that the R18 solver has not been executed in this turn.
- **Next Allowed Stage:** `R18_ORTOOLS_EXECUTION` (only after separate explicit execution instruction; do not infer execution from this closure record).

<a id="stage-records"></a>

# 段階記録

全工程で以下の21欄を使う。未実行command/hash/versionはNOT_RUN / NOT_FIXEDであり仮の実行結果ではない。出力は予定成果物名、正式保存先は実行前に本書へ固定する。

<a id="r01_existing_state_audit--existing-state-audit"></a>

## R01_EXISTING_STATE_AUDIT — 既存状態監査

- **Stage ID:** R01_EXISTING_STATE_AUDIT
- **目的:** 既存成果物と受入範囲を確定する
- **入力:** 仕様・コード・未加工・試験・成果物一覧・環境
- **事前条件:** リポジトリを読取り専用で確認できること。既存受入物を変更しない。
- **手法:** 読取り専用棚卸し、ハッシュ値照合、既存検証を実行
- **検証:** 5分類・来歴・欠落・環境を記録し受入物が不変ことを独立検査し、実行記録に診断を残す。
- **受入基準:** 5分類・来歴・欠落・環境を記録し受入物が不変
- **停止条件:** 共通停止規則と当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義は実行不可、検証不一致・実行異常は不合格。
- **出力:** 監査一覧・環境・ハッシュ値台帳
- **Status:** PASS
- **Started At:** 2026-09-09T10:53:52+09:00
- **Completed At:** 2026-09-09T10:53:52+09:00
- **コマンド:** 本書監査 コマンド参照（実行済み）
- **入力のハッシュ値:** 本書入力 Hash Ledger参照
- **出力のハッシュ値:** 本書自体は自己ハッシュ値対象外。監査記録のハッシュ値は監査 コマンド参照
- **ソフトウェアの版:** 本書Environment参照
- **結果:** 既存受入を確認し、監査時点ではR02以降未実行だった。継続後にR02は合格、R03は実行不可となった。分類と潜在阻害要因を記録。
- **検証結果:** ポータル 6検査合格、旧需要13 試験 合格、統計19原本ハッシュ値一致、候補識別子/座標監査合格
- **課題:** 候補再生成と住宅母集団代表性は未確認。旧まとめは生成段階が異なる。既存working treeはDIRTY
- **決定記録:** 監査工程の範囲を満たすため合格。下流の実装受入は主張しない。後続工程はR02/R03の記録に従う。
- **次に許可される段階:** R02_PUBLIC_STATISTICS_DEFINITION（初回タスクでは実行しない）

## R02_PUBLIC_STATISTICS_DEFINITION — 公的統計定義

- **Stage ID:** R02_PUBLIC_STATISTICS_DEFINITION
- **目的:** 人口／世帯・宅配受取統計の採用契約を固定する
- **入力:** 国勢調査ZIP・定義書・受取調査19原本と成果物一覧
- **事前条件:** 前工程 `R01_EXISTING_STATE_AUDIT` の合格と、入力の存在・ハッシュ値・根拠を確認する。R01の監査記録により充足。
- **手法:** 列・分母・単位・地域・年次・秘匿処理・日時指定集計を照合
- **検証:** 採用列と変換・欠損処理・データ分類・出典ハッシュ値を、定義文書ファイル・未加工 成果物一覧・XLSX/XML・ZIPで独立照合し、実行記録に診断を残す。
- **受入基準:** 採用列と変換・欠損処理・データ分類・出典ハッシュ値が全て確定
- **停止条件:** 共通停止規則と当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義は実行不可、検証不一致・実行異常は不合格。
- **出力:** 統計入力仕様・採用列台帳
- **Status:** PASS
- **Started At:** 2026-09-09T11:02:00+09:00
- **Completed At:** 2026-09-09T11:05:00+09:00
- **Commands:** `python` read-only ZIP/XLSX/XML/hash audit; `pdftotext -layout 03_data/raw/traffic_simulation/population/estat_2020_500m_jgd2011/T001141_definition.pdf -`
- **Input Hashes:** Census ZIP `8a8b47563ffe88ec1afb5a17b8d29ac987b40df65498bec4c2fcf1829777f67d`; receipt manifest `b218db3c37faeb0ba21ac9b0b6a92ea4fc0d07feef423db9c9c97db82da38a5e`; all 20 manifest entries hash-match (19 unique filenames; duplicate `ss515_r06a.xlsx` entry is byte-identical).
- **Output Hashes:** No separate generated file. This stage's adopted definition and column ledger are recorded in this section of `EVRP_EXECUTION_PLAN.md`; the plan file is not self-hashed.
- **Software Versions:** Python 3.11.15; standard-library `zipfile`, `xml.etree.ElementTree`, `hashlib`; `pdftotext` available.
- **結果:** 採用原本を固定した。国勢調査500mメッシュ（JGD2011）は `T001141001`（人口総数）と `T001141034`（世帯総数）を採用候補列として固定し、`T001141034`を住宅標本抽出 重みの第一候補とする。両列は定義文書ファイルで単位（人／世帯）を確認した。秘密処理は`HTKSYORI`/`HTKSAKI`/`GASSAN`を保持し、一般世帯の内訳列を合算先へ再配賦しない。宅配受取調査は `ss508_r06a.xlsx`（受取曜日×時間帯、単位: 件）、`ss515_r06a.xlsx`（日時指定区分、単位: 件）、`ss519_r06a.xlsx`（地域別受取頻度・再配達頻度、単位: 回/週・割合）を採用入力として固定した。ss508/ss515は時間窓較正、ss519は地域差の補助較正に使用し、個人調査の回答を大田区の実測注文へ直接同一視しない。
- **検証結果:** Census header/XMLと定義文書ファイルの列番号・単位一致、受取調査表計算ファイルのタイトル・単位・カテゴリ存在を確認。選択原本は成果物一覧 ハッシュ値一致。採用値はOBSERVED（未加工表）、PUBLIC_STATISTICS_DERIVED（後続の集計・変換）、PROXY（住宅需要への利用）、SYNTHETIC_CALIBRATED（後続customer/TW生成）を工程ごとに分離する。未取得の表は必須入力にしていない。合格。
- **課題:** 世帯数から候補へのメッシュ配賦式、境界・秘密処理の実装、宅配統計からの時間窓幅変換、地域差の適用はR04/R07で固定する。これはR02の列・出典定義未完了ではなく、後続変換の未実装事項である。
- **決定記録:** 採用列、単位、調査範囲、秘密処理、データ分類、入力ハッシュ値が確定したため合格。新しい需要値・顧客・時間窓は生成していない。
- **次に許可される段階:** R03_CANDIDATE_DELIVERY_LOCATIONS_VALIDATION（Gate通過時のみ）

<a id="r03_candidate_delivery_locations_validation--candidate-delivery-locations-validation"></a>

## R03_CANDIDATE_DELIVERY_LOCATIONS_VALIDATION — 候補配送位置検証

- **Stage ID:** R03_CANDIDATE_DELIVERY_LOCATIONS_VALIDATION
- **目的:** 39,956候補の固定と住宅代理指標としての範囲を検証する
- **入力:** 候補コンマ区切り形式・旧生成要約・PLATEAU来歴・受入対応付け
- **事前条件:** 前工程 `R02_PUBLIC_STATISTICS_DEFINITION` の合格（明示された正常結果遷移は例外）と、入力の存在・ハッシュ値・根拠を確認する。
- **手法:** 識別子/座標/座標参照系/道路接続を全件照合、過去有効建物選択の偏りと生成手順を監査
- **検証:** 39,956の一意識別子、妥当座標、全件対応付け、選択偏り・再生成可否の根拠を明記ことを独立検査し、実行記録に診断を残す。
- **受入基準:** 39,956の一意識別子、妥当座標、全件対応付け、選択偏り・再生成可否の根拠を明記
- **停止条件:** 共通停止規則と当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義は実行不可、検証不一致・実行異常は不合格。
- **出力:** 候補集合固定・候補 検証
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
- **次に許可される段階:** R04_DEMAND_WEIGHT_DEFINITION（Gate通過時のみ）

<a id="r04_demand_weight_definition--demand-weight-definition"></a>

## R04_DEMAND_WEIGHT_DEFINITION — 需要重み定義

- **Stage ID:** R04_DEMAND_WEIGHT_DEFINITION
- **目的:** w_iをq_iから分離し保存則を定義する
- **入力:** 採用世帯／人口列・候補メッシュ対応
- **事前条件:** 前工程 `R03_CANDIDATE_DELIVERY_LOCATIONS_VALIDATION` の合格（明示された正常結果遷移は例外）と、入力の存在・ハッシュ値・根拠を確認する。
- **手法:** H_m/N_mを第一候補にメッシュ配賦し必要ならr_mを検討
- **検証:** 非負・総和正、メッシュ別配賦保存、N_m=0/秘匿/境界処理の規則確定ことを独立検査し、実行記録に診断を残す。
- **受入基準:** 非負・総和正、メッシュ別配賦保存、N_m=0/秘匿/境界処理の規則確定
- **停止条件:** 共通停止規則と当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義は実行不可、検証不一致・実行異常は不合格。
- **出力:** 重み仕様・重み台帳
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
- **次に許可される段階:** R05_CUSTOMER_SAMPLING_DEFINITION（Gate通過時のみ）

<a id="r05_customer_sampling_definition--customer-sampling-definition"></a>

## R05_CUSTOMER_SAMPLING_DEFINITION — 顧客標本抽出定義

- **Stage ID:** R05_CUSTOMER_SAMPLING_DEFINITION
- **目的:** 層化・重み付き非復元抽出を定義する
- **入力:** 候補固定・weights・空間層
- **事前条件:** 前工程 `R04_DEMAND_WEIGHT_DEFINITION` の合格（明示された正常結果遷移は例外）と、入力の存在・ハッシュ値・根拠を確認する。
- **手法:** 層別割当・抽出アルゴリズム・乱数の種・n引数を固定し小規模再現検査
- **検証:** n件・重複なし・母集団内・同一seed/configで一致・層の保持ことを独立検査し、実行記録に診断を残す。
- **受入基準:** n件・重複なし・母集団内・同一seed/configで一致・層の保持
- **停止条件:** 共通停止規則と当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義は実行不可、検証不一致・実行異常は不合格。
- **出力:** 標本抽出仕様・検証用設定
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **コマンド:** NOT_RUN — 実行前に採択コマンド・cwd・出力保存先を記録
- **入力のハッシュ値:** NOT_FIXED — 実行前に固定
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **課題:** 未実行。受入基準の未固定項目を実行開始時に解消し、解消不能なら実行不可
- **Decision:** NOT_RUN
- **次に許可される段階:** R06_CUSTOMER_DEMAND_DEFINITION（Gate通過時のみ）

<a id="r06_customer_demand_definition--customer-demand-definition"></a>

## R06_CUSTOMER_DEMAND_DEFINITION — 顧客需要定義

- **Stage ID:** R06_CUSTOMER_DEMAND_DEFINITION
- **目的:** 抽出顧客の配送要求を定義する
- **入力:** 標本抽出仕様・宅配受取統計
- **事前条件:** 前工程 `R05_CUSTOMER_SAMPLING_DEFINITION` の合格（明示された正常結果遷移は例外）と、入力の存在・ハッシュ値・根拠を確認する。
- **手法:** 基準は1customerに1配送要求を置く単位契約を明示し追加q_iを別管理
- **検証:** 配送件数と荷物量とw_iを区別、非負、全顧客に要求、分母を固定ことを独立検査し、実行記録に診断を残す。
- **受入基準:** 配送件数と荷物量とw_iを区別、非負、全顧客に要求、分母を固定
- **停止条件:** 共通停止規則と当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義は実行不可、検証不一致・実行異常は不合格。
- **出力:** demand仕様・生成契約
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **コマンド:** NOT_RUN — 実行前に採択コマンド・cwd・出力保存先を記録
- **入力のハッシュ値:** NOT_FIXED — 実行前に固定
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **課題:** 未実行。受入基準の未固定項目を実行開始時に解消し、解消不能なら実行不可
- **Decision:** NOT_RUN
- **次に許可される段階:** R07_TIME_WINDOW_DEFINITION（Gate通過時のみ）

<a id="r07_time_window_definition--time-window-definition"></a>

## R07_TIME_WINDOW_DEFINITION — 時間窓定義

- **Stage ID:** R07_TIME_WINDOW_DEFINITION
- **目的:** 統計較正した合成時間窓を定義する
- **入力:** 受取時間帯・日時指定統計・顧客生成契約
- **事前条件:** 前工程 `R06_CUSTOMER_DEMAND_DEFINITION` の合格（明示された正常結果遷移は例外）と、入力の存在・ハッシュ値・根拠を確認する。
- **手法:** 指定割合と時間帯から窓を生成する変換・窓幅・指定なし・乱数の種を固定
- **検証:** e_i<=l_i、作業開始を判定、単位・時刻原点・分布較正診断と再現性ことを独立検査し、実行記録に診断を残す。
- **受入基準:** e_i<=l_i、作業開始を判定、単位・時刻原点・分布較正診断と再現性
- **停止条件:** 共通停止規則と当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義は実行不可、検証不一致・実行異常は不合格。
- **出力:** 時間-window仕様・較正検証
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **コマンド:** NOT_RUN — 実行前に採択コマンド・cwd・出力保存先を記録
- **入力のハッシュ値:** NOT_FIXED — 実行前に固定
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **課題:** 未実行。受入基準の未固定項目を実行開始時に解消し、解消不能なら実行不可
- **Decision:** NOT_RUN
- **次に許可される段階:** R08_SERVICE_TIME_DEFINITION（Gate通過時のみ）

## R08_SERVICE_TIME_DEFINITION — 作業時間定義

- **Stage ID:** R08_SERVICE_TIME_DEFINITION
- **目的:** 住宅での配送作業時間を定義する
- **入力:** 作業時間の根拠または明示仮定
- **事前条件:** 前工程 `R07_TIME_WINDOW_DEFINITION` の合格（明示された正常結果遷移は例外）と、入力の存在・ハッシュ値・根拠を確認する。
- **手法:** s_iの単位・値/分布・分類・乱数の種を設定
- **検証:** 有限かつ非負、出典またはASSUMED採択理由、再現可能ことを独立検査し、実行記録に診断を残す。
- **受入基準:** 有限かつ非負、出典またはASSUMED採択理由、再現可能
- **停止条件:** 共通停止規則と当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義は実行不可、検証不一致・実行異常は不合格。
- **出力:** 作業-時間仕様
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **コマンド:** NOT_RUN — 実行前に採択コマンド・cwd・出力保存先を記録
- **入力のハッシュ値:** NOT_FIXED — 実行前に固定
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **課題:** 未実行。受入基準の未固定項目を実行開始時に解消し、解消不能なら実行不可
- **Decision:** NOT_RUN
- **次に許可される段階:** R09_DEPOT_DEFINITION（Gate通過時のみ）

<a id="r09_depot_definition--depot-definition"></a>

## R09_DEPOT_DEFINITION — 配送拠点定義

- **Stage ID:** R09_DEPOT_DEFINITION
- **目的:** 単一配送拠点を固定する
- **入力:** 物流施設代理指標候補・受入道路網
- **事前条件:** 前工程 `R08_SERVICE_TIME_DEFINITION` の合格（明示された正常結果遷移は例外）と、入力の存在・ハッシュ値・根拠を確認する。
- **手法:** 候補範囲・位置・通行可否を検討し1拠点を選択
- **検証:** 位置と道路接続が有効、同じn/seed比較で原則同一、代理指標明記ことを独立検査し、実行記録に診断を残す。
- **受入基準:** 位置と道路接続が有効、同じn/seed比較で原則同一、代理指標明記
- **停止条件:** 共通停止規則と当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義は実行不可、検証不一致・実行異常は不合格。
- **Outputs:** depot lock
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **コマンド:** NOT_RUN — 実行前に採択コマンド・cwd・出力保存先を記録
- **入力のハッシュ値:** NOT_FIXED — 実行前に固定
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **課題:** 未実行。受入基準の未固定項目を実行開始時に解消し、解消不能なら実行不可
- **Decision:** NOT_RUN
- **次に許可される段階:** R10_EV_DEFINITION（Gate通過時のみ）

<a id="r10_ev_definition--ev-definition"></a>

## R10_EV_DEFINITION — 電気自動車定義

- **Stage ID:** R10_EV_DEFINITION
- **目的:** 車両・容量・電力量・充電率を定義する
- **入力:** 管理された 車両 設定プロファイル・電気自動車仕様表・出典
- **事前条件:** 前工程 `R09_DEPOT_DEFINITION` の合格（明示された正常結果遷移は例外）と、入力の存在・ハッシュ値・根拠を確認する。
- **手法:** 車両群・積載量・電池・消費率・usable/initial/final 充電率・運行時間適用を固定
- **検証:** 正容量、単位整合、充電率境界と電力量計算法・全値の根拠、車種権限を固定ことを独立検査し、実行記録に診断を残す。
- **受入基準:** 正容量、単位整合、充電率境界と電力量計算法・全値の根拠、車種権限を固定
- **停止条件:** 共通停止規則と当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義は実行不可、検証不一致・実行異常は不合格。
- **出力:** 車両仕様・電力量契約
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **コマンド:** NOT_RUN — 実行前に採択コマンド・cwd・出力保存先を記録
- **入力のハッシュ値:** NOT_FIXED — 実行前に固定
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **課題:** 未実行。受入基準の未固定項目を実行開始時に解消し、解消不能なら実行不可
- **Decision:** NOT_RUN
- **次に許可される段階:** R11_CHARGING_STATION_DEFINITION（Gate通過時のみ）

<a id="r11_charging_station_definition--charging-station-definition"></a>

## R11_CHARGING_STATION_DEFINITION — 充電設備定義

- **Stage ID:** R11_CHARGING_STATION_DEFINITION
- **目的:** 利用可能な充電条件を定義する
- **入力:** 充電代理指標資料・電気自動車互換性・道路網
- **事前条件:** 前工程 `R10_EV_DEFINITION` の合格（明示された正常結果遷移は例外）と、入力の存在・ハッシュ値・根拠を確認する。
- **手法:** 位置/出力/connector/利用時間/アクセスと充電量→時間の式を確認
- **検証:** 採用局の必須項目と対応付けが完全、不明を利用可能と見なさないことを独立検査し、実行記録に診断を残す。
- **受入基準:** 採用局の必須項目と対応付けが完全、不明を利用可能と見なさない
- **停止条件:** 共通停止規則と当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義は実行不可、検証不一致・実行異常は不合格。
- **出力:** 充電設備集合・充電モデル
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **コマンド:** NOT_RUN — 実行前に採択コマンド・cwd・出力保存先を記録
- **入力のハッシュ値:** NOT_FIXED — 実行前に固定
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **課題:** 未実行。受入基準の未固定項目を実行開始時に解消し、解消不能なら実行不可
- **Decision:** NOT_RUN
- **次に許可される段階:** R12_ROUTING_SPECIFICATION（Gate通過時のみ）

<a id="r12_routing_specification--routing-specification"></a>

## R12_ROUTING_SPECIFICATION — 経路計算仕様

- **Stage ID:** R12_ROUTING_SPECIFICATION
- **目的:** 必要出発地・到着地と経路意味論を先に固定する
- **入力:** candidate/customer生成契約・配送拠点・電気自動車・充電設備・受入道路網
- **事前条件:** 前工程 `R11_CHARGING_STATION_DEFINITION` の合格（明示された正常結果遷移は例外）と、入力の存在・ハッシュ値・根拠を確認する。
- **手法:** 選択端点集合・有向区間・出発/到着位置補正値・車種・費用・異常閾値を定義
- **検証:** d/t/aの単位・必要出発地・到着地一覧・到達不能判別・hash/version/command契約が完備ことを独立検査し、実行記録に診断を残す。
- **受入基準:** d/t/aの単位・必要出発地・到着地一覧・到達不能判別・hash/version/command契約が完備
- **停止条件:** 共通停止規則と当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義は実行不可、検証不一致・実行異常は不合格。
- **出力:** 経路計算仕様・出発地・到着地 成果物一覧
- **Status:** PASS
- **Started At:** 2026-09-09T17:45:00+09:00
- **Completed At:** 2026-09-09T17:49:00+09:00
- **コマンド:** `.conda/bin/python 05_src/traffic_simulation/evrp_r12_routing/define_routing_specification.py --run-id 20260909_r12_routing_spec_fixture_n10_v18_geometry_reaccepted --network-authority reproducibility/config/traffic_simulation/current_network_completion_authority_v18_geometry_reaccepted.yml --network reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_3_geometry_reacceptance/three_tier.net.xml --expected-network-hash 460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`。独立検証: `.conda/bin/python 05_src/traffic_simulation/evrp_r12_routing/validate_routing_specification_v18.py --run-dir reproducibility/outputs/traffic_simulation/demand/evrp_r12_routing/20260909_r12_routing_spec_fixture_n10_v18_geometry_reaccepted --authority reproducibility/config/traffic_simulation/current_network_completion_authority_v18_geometry_reaccepted.yml`。R13本番計算は実行していない。
- **Input Hashes:** V18 network `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`; V18 authority `29ee5fe979c85eb1d11b0f5a55f33782b7b5b08fcf09b48d2fad3e47c0ae33ee`; R09 depot `3b7b168f1ae9159234f812cb476c0721364554e03db7ebadfd2b155295b40eeb`; R05 customer IDs `a3307ac024c639b2690b120d11cd163abbbf83820428d090abb09fa18b0e4d0e`; R04 weights `e7694dd7461ae048d1de9289408faa91f6d3924defaf06b15b09341e38842ad8`; R11 revision manifest `f60bad51c7a6ad8936ce5094f7821da2df965cdc050fc9bba3c9ce07f2592bf9`。
- **Output Hashes:** endpoint manifest `9f0d0cdd289fad73c696e7a3efe56af7bb4385fa5f268cb5db6e6d8844335913`; OD manifest `bee697860ab422d0eacdc8ac4d3019bb3caf1673bcbd2f31ae903e977f530b74`; config `12c32ada0b3d615e8acdc32c033138fb309ccf434d3b3f3aaaea3c05b40fb5c8`; schema `7ef7a66cd221376b7f3e7588934439cd00164721283d2eaca540cc4b9428544b`; generator validation `a38c1fec8b106ceb620511534a7afdd359d8e3407e1db9d170ae34c796e5be70`; independent V18 validation `fe645a7a432e87072e67d56e48c87b6623ba8c30e6d126f6fe7a5b1cdca30e52`; manifest `f6194ec010e1cd97fbcfd9e97b080bfe9a7bb46fdfcc5112cbc8c1d1eb55fc3e`。
- **ソフトウェアの版:** Python 3.11.15、SUMO/sumolib 1.24.0。R12は仕様固定のみで、本番経路計算計算を実行していない。
- **結果:** V18 正本に整合する新実行を生成した。端点 12件（配送拠点 1、顧客 10、充電設備 1）、必要出発地・到着地 132本、self-loop除外、directed、`travel_time_minimizing`、距離[m]、移動 時間[s]、到達可能[真偽値]、到達不能 null 意味、位置補正値 意味、V18 道路網 ハッシュ値、R13 コマンド 取り決めを再固定した。V18では全端点の道路区間 識別子が有効で配送 通行許可を持ち、全位置補正値が道路区間 長さ範囲内だった。
- **検証結果:** 独立検証器で正本 状況、道路網 ハッシュ値、端点 uniqueness/role、V18 道路区間 対応付け、配送 接続、位置補正値範囲、有限値、出発地・到着地 completeness、出発地あたり11本、units/null 意味、位置補正値 意味、目的、unreachable/failure distinction、R13 取り決めを全て合格。R13本番成果物 `routing_arcs.csv`は存在せず、R13未実行を確認した。
- **課題:** なし。旧V17 R12 成果物は保持し、V18 実行を新保存先へ分離した。本番problem-規模 nは未採択のまま。R13は次工程として未実行。
- **決定記録:** V18 正本との整合、成果物一覧、データ構造、コマンド 取り決め、独立検証が全て合格したため、V18向けR12を合格とする。
- **次に許可される段階:** R13_ROUTING_COMPUTATION（V18 正本でのGate通過時のみ）

## R13_ROUTING_COMPUTATION — 経路計算計算

- **Stage ID:** R13_ROUTING_COMPUTATION
- **目的:** 必要出発地・到着地の実道路費用を計算する
- **入力:** 採択経路計算仕様・端点・道路網 固定
- **事前条件:** 前工程 `R12_ROUTING_SPECIFICATION` の合格（明示された正常結果遷移は例外）と、入力の存在・ハッシュ値・根拠を確認する。
- **手法:** 分離出力で必要出発地・到着地のみ計算し保存先と診断を保存
- **検証:** 全必要出発地・到着地に保存先または根拠ある到達不能、実行例外なしことを独立検査し、実行記録に診断を残す。
- **受入基準:** 全必要出発地・到着地に保存先または根拠ある到達不能、実行例外なし
- **停止条件:** 共通停止規則と当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義は実行不可、検証不一致・実行異常は不合格。
- **Outputs:** d_ij/t_ij/a_ij・paths・run manifest
- **Status:** PASS
- **Started At:** 2026-09-09T18:01:49+09:00
- **Completed At:** 2026-09-09T18:04:30+09:00
- **コマンド:** 事前確認（R12 V18 成果物、manifest/hash、道路網 ハッシュ値、endpoint/OD、役割、車種、目的を読取り専用検査）; 検証用データ: `.conda/bin/python 05_src/traffic_simulation/evrp_r13_routing/validate_routing_fixture.py --output reproducibility/outputs/traffic_simulation/demand/evrp_r13_routing/20260909_r13_routing_fixture_n10_v18_geometry_reaccepted/runner_fixture_validation.json`; 正式運用: `.conda/bin/python 05_src/traffic_simulation/evrp_r13_routing/compute_routing.py --config reproducibility/outputs/traffic_simulation/demand/evrp_r12_routing/20260909_r12_routing_spec_fixture_n10_v18_geometry_reaccepted/r12_routing_config.json --output-dir reproducibility/outputs/traffic_simulation/demand/evrp_r13_routing/20260909_r13_routing_fixture_n10_v18_geometry_reaccepted`; basic: `.conda/bin/python 05_src/traffic_simulation/evrp_r13_routing/validate_routing_basic.py --r12-dir reproducibility/outputs/traffic_simulation/demand/evrp_r12_routing/20260909_r12_routing_spec_fixture_n10_v18_geometry_reaccepted --r13-dir reproducibility/outputs/traffic_simulation/demand/evrp_r13_routing/20260909_r13_routing_fixture_n10_v18_geometry_reaccepted`。
- **Input Hashes:** endpoint manifest `9f0d0cdd289fad73c696e7a3efe56af7bb4385fa5f268cb5db6e6d8844335913`; OD manifest `bee697860ab422d0eacdc8ac4d3019bb3caf1673bcbd2f31ae903e977f530b74`; R12 config `12c32ada0b3d615e8acdc32c033138fb309ccf434d3b3f3aaaea3c05b40fb5c8`; output schema `7ef7a66cd221376b7f3e7588934439cd00164721283d2eaca540cc4b9428544b`; V18 network `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`; V18 authority `29ee5fe979c85eb1d11b0f5a55f33782b7b5b08fcf09b48d2fad3e47c0ae33ee`。
- **Output Hashes:** routing arcs `29c1a68a71838bb44629cbf4bf7230a0492e9484c0a97d0c2fb2e370f2ca2ec1`; execution log `8ce3c0747d7e793d5d813f9c6ee0db417772acfd134342691ecab188f6763e77`; basic validation `c084785bdf642ab02e3050453752625a4f9a2c34a80bf8aa8b1611ee97424a15`; summary `1ee5873dbdcdc08da568b3f86981acbf0cbef0cb3ae5f2c0c1e77992e8642294`; manifest `b3367f49e8fee9f9971cdf88eb426b58df7f04b477d2c77e78b4f5a7224b601e`; fixture `d9739978b2b15d2e75f5635c7c3771c474c6bb42d3add6d1914a475fc19504ed`。
- **ソフトウェアの版:** Python 3.11.15、SUMO/sumolib 1.24.0。新規外部依存関係は導入していない。実行器 `compute_routing.py` ハッシュ値 `13c89a026363256f60900488b9c77808a207f2b4d9546d4158d266ea50d10f54`、basic 検証器 ハッシュ値 `1540b6f3bddcbb0ff047bfe8171f8e027a4214c154c53bdac5abd3da6264588b`。
- **結果:** V18専用実行で、R12固定の12 端点・132 directed 出発地・到着地のみを実行。生成済み 132、到達可能 132、到達不能 0、経路計算 exception 0。距離はm、移動 時間はs、selected 保存先は`travel_time_minimizing`、位置補正値 componentsと保存先 参照を保存した。距離統計: min 603.8403355348、max 11361.9776978131、平均 5503.4970219848、中央値 5666.0612792584 m。移動 時間統計: min 93.8332519304、max 771.3335528117、平均 429.4312502215、中央値 426.7058239354 s。
- **検証結果:** endpoint/role、出発地・到着地完全性、self-loop 0、重複 0、missing/unexpected 0、データ構造、道路網 ハッシュ値、車種、目的、到達可能値、保存先 道路区間存在・配送 通行許可、finite/nonnegativeをR13基本検証として合格。R14の形状下限・保存先再計算・位置補正値独立検証は未実行。
- **課題:** なし。R13は`n=10` 検証用データで実行。本番problem-規模 nは未採択であり、R13 検証用データ 実行と区別して管理する。
- **決定記録:** 事前確認、検証用データ 検証、実道路経路計算、R13基本検証、成果物保存を全て合格したためR13 合格。旧R13 成果物は変更していない。
- **次に許可される段階:** R14_ROUTING_VALIDATION（今回未実行）

<a id="r14_routing_validation--routing-validation"></a>

## R14_ROUTING_VALIDATION — 経路計算検証

- **Stage ID:** R14_ROUTING_VALIDATION
- **目的:** 経路計算を独立検証する
- **Inputs:** OD manifest・paths・d/t/a・SUMO network
- **事前条件:** 前工程 `R13_ROUTING_COMPUTATION` の合格（明示された正常結果遷移は例外）と、入力の存在・ハッシュ値・根拠を確認する。
- **手法:** 出発地・到着地完全性、方向/進入/車種、位置補正値、距離時間再計算・異常値・再現を照合
- **検証:** 経路計算停止条件が0件、到達不能と実装不具合を識別ことを独立検査し、実行記録に診断を残す。
- **受入基準:** 経路計算停止条件が0件、到達不能と実装不具合を識別
- **停止条件:** 共通停止規則と当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義は実行不可、検証不一致・実行異常は不合格。
- **Outputs:** routing validation・accepted routing lock
- **Status:** PASS
- **Started At:** 2026-09-09T18:18:00+09:00
- **Completed At:** 2026-09-09T18:24:00+09:00
- **コマンド:** independent 検証: `.conda/bin/python 05_src/traffic_simulation/evrp_r14_routing_validation/validate_routing.py --r12-dir reproducibility/outputs/traffic_simulation/demand/evrp_r12_routing/20260909_r12_routing_spec_fixture_n10_v18_geometry_reaccepted --r13-dir reproducibility/outputs/traffic_simulation/demand/evrp_r13_routing/20260909_r13_routing_fixture_n10_v18_geometry_reaccepted --output-dir reproducibility/outputs/traffic_simulation/demand/evrp_r14_routing_validation/20260909_r14_routing_validation_fixture_n10_v18_geometry_reaccepted`; 経路 geometry/length: `.conda/bin/python 05_src/traffic_simulation/evrp_r14_routing_validation/validate_v18_route_geometry.py --network reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_3_geometry_reacceptance/three_tier.net.xml --r13-dir reproducibility/outputs/traffic_simulation/demand/evrp_r13_routing/20260909_r13_routing_fixture_n10_v18_geometry_reaccepted --output reproducibility/outputs/traffic_simulation/demand/evrp_r14_routing_validation/20260909_r14_routing_validation_fixture_n10_v18_geometry_reaccepted/v18_route_geometry_length_validation.json`。R13 出力、V18 道路網、端点 対応付けは読み取り専用。
- **Input Hashes:** R13 routing output `29c1a68a71838bb44629cbf4bf7230a0492e9484c0a97d0c2fb2e370f2ca2ec1`; R12 endpoint manifest `9f0d0cdd289fad73c696e7a3efe56af7bb4385fa5f268cb5db6e6d8844335913`; R12 OD manifest `bee697860ab422d0eacdc8ac4d3019bb3caf1673bcbd2f31ae903e977f530b74`; V18 network `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`; V18 authority `29ee5fe979c85eb1d11b0f5a55f33782b7b5b08fcf09b48d2fad3e47c0ae33ee`。
- **Output Hashes:** validation report `489516593b6c125bfd32a8b5c10572d59c1d1da11bd7d6adf4796e6e7bb57ea2`; statistics `469387eee1afb79cd28d198be4063a6bacbb86f6cf885b6bcca35fb101c448ea`; anomaly report `b21182697b7f6b9447cea4e0d6b7ccc84cdffd0c9bc3d426192a54c60f7aec38`; spatial diagnostics `548f56bf17d334c6fe5e45774e72c89ad2a204943d874eadd44bb04abdc4d1c6`; geometry/length `d50799973ceb576be6139f1af46ef92cc3e988b6599839b1233635081fabcc17`; manifest `9218f4bfc8139ef910a67a7bc62486d0a184497b8f047a0c6f8642a2ea6fa2cf`。
- **ソフトウェアの版:** Python 3.11.15、SUMO/sumolib 1.24.0。R14 検証器 `validate_routing.py` ハッシュ値 `88e7092f003667287e581ee8cdaf2decef61de4c75870202cc2821935aec4beb`、形状 検証器 `validate_v18_route_geometry.py` ハッシュ値 `51ddb9e15f4d71580251eefa752487abff93b7b3e2dc64dd0a8896eeabde2f7a`。R13 実行器は変更していない。
- **結果:** V18 R13の132/132 出発地・到着地を独立検証。端点 網羅率は各端点がorigin/destination各11件、到達可能 132、到達不能 0。R13 出力 ハッシュ値、道路網 ハッシュ値、配送 接続、one-道路地物 道路区間 グラフ、データ構造、numeric、位置補正値、path/distance/time、移動時間 目的を合格した。
- **検証結果:** mapped-位置 Critical Gate `road_distance >= straight(mapped)-1e-6m`は132件中132件合格、Critical anomaly 0件。original-coordinate diagnostic 注意事項 0件。R13 保存先の独立distance/time再計算差は全件許容誤差内、部分的 道路区間二重計上0件、same-道路区間処理とspot 経路再構成合格。V18 経路上の4,507 車線についてdeclared 長さと形状 polylineの不整合0件、車線 接続 形状 隔たり 0件。代表道路区間 形状 端点 隔たりは5件（最大2.359984m）だが、multi-車線代表形状と車線 接続 形状の差による診断値でCritical Gateには使用しない。速度・detour・非対称性は診断として保存し、重大な anomalyなし。
- **課題:** 車線 接続 記録がない道路区間-level遷移18件を診断記録した。これはR13固定取り決めの道路区間-level グラフで生成された遷移で、実接続形状 隔たりや配送 通行許可違反としては検出されなかった。R13 出力、V18 道路網、端点 対応付けは変更していない。
- **決定記録:** 旧V17の44件はV18でmapped-位置 Critical anomaly 0件、original-coordinate 注意事項 0件へ解消。R14の全受入基準を満たしたため合格。
- **次に許可される段階:** R15_COMMON_DELIVERY_INSTANCE_DEFINITION（今回未実行）

<a id="r15_common_delivery_instance_definition--common-delivery-instance-definition"></a>

## R15_COMMON_DELIVERY_INSTANCE_DEFINITION — 共通配送問題定義

- **Stage ID:** R15_COMMON_DELIVERY_INSTANCE_DEFINITION
- **目的:** 求解器非依存I_sを定義・生成・凍結する
- **入力:** 採択需要/窓/service/depot/EV/charger・検証済経路計算
- **事前条件:** 前工程 `R14_ROUTING_VALIDATION` の合格（明示された正常結果遷移は例外）と、入力の存在・ハッシュ値・根拠を確認する。
- **手法:** データ構造、識別子順序、生成設定、出典 ハッシュ値、乱数の種を統合
- **検証:** 必須項目充足・データ構造合格・全識別子対応・同一乱数の種再生成一致ことを独立検査し、実行記録に診断を残す。
- **受入基準:** 必須項目充足・データ構造合格・全識別子対応・同一乱数の種再生成一致
- **停止条件:** 共通停止規則と当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義は実行不可、検証不一致・実行異常は不合格。
- **Outputs:** instance schema・I_s・hash lock
- **Status:** PASS
- **Started At:** 2026-09-09T18:25:00+09:00
- **Completed At:** 2026-09-09T18:28:40+09:00
- **コマンド:** `.conda/bin/python 05_src/traffic_simulation/evrp_r15_instance/build_common_instance.py --output-dir reproducibility/outputs/traffic_simulation/demand/evrp_r15_common_instance/20260909_r15_common_instance_fixture_n10_v18`; `.conda/bin/python 05_src/traffic_simulation/evrp_r15_instance/validate_common_instance.py --instance-dir reproducibility/outputs/traffic_simulation/demand/evrp_r15_common_instance/20260909_r15_common_instance_fixture_n10_v18`; 同一入力で `/tmp/evrp_r15_repro_check_20260909`へ再生成し`common_instance.json` ハッシュ値を比較。
- **Input Hashes:** R05 customer IDs `a3307ac024c639b2690b120d11cd163abbbf83820428d090abb09fa18b0e4d0e`; R06 demand `9c321d63d5c611d0f348f8e9eb6c5581e4db9dbefa3e4db9e9c747ebde746825`; R07 windows `4915372ccc64131631cc1bcd0850b823e2c916663d869e93dd76622e7d4aa6c3`; R08 service `3d0ac325e0c5bf7686fc8501d9bfaa207a77a4ddc77527b6ea4b014508a2d6e2`; R09 depot `3b7b168f1ae9159234f812cb476c0721364554e03db7ebadfd2b155295b40eeb`; R10 vehicle `53b1122a76f2f65661991d9f4b0b9091efa93108b8a8763b4e079c140a56f96c`; R11 station `3077eb1ed6d41ae16c5c7262706755a3dd042f4cb822a76b445cb7a1484a0c72`; R12 endpoint `9f0d0cdd289fad73c696e7a3efe56af7bb4385fa5f268cb5db6e6d8844335913`; R12 OD `bee697860ab422d0eacdc8ac4d3019bb3caf1673bcbd2f31ae903e977f530b74`; R13 routing `29c1a68a71838bb44629cbf4bf7230a0492e9484c0a97d0c2fb2e370f2ca2ec1`; R14 validation `489516593b6c125bfd32a8b5c10572d59c1d1da11bd7d6adf4796e6e7bb57ea2`; V18 network `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`。
- **Output Hashes:** common instance `1d01afb5b871dc0cfdbeda701f5853827e0d24bb126d86d958644cb36ec5f1ca`; node mapping `a9ab24fab2129b2c7fb8203adcfb9c123c9d697605292f0493265c420143954c`; provenance ledger `9f8d3206991dd6eaeb08ad1b21f62926dd09f4ece85c6ae8857a21c0bb2f0493`; config `6a57af71934a9db4f6718f3ae2cd59ec791f9ae3eb8c33eb0a361ae8a74971de`; validation `5a615f02814cf4c15e81a14fa7201eebf66dcba82fbecabe57abd8ded6a359e7`; manifest `33aba4e492fa96103b7516472ec9d1f8b7433f5752c632096d903cc705cda19c`。
- **ソフトウェアの版:** Python 3.11.15。builder `build_common_instance.py`、検証器 `validate_common_instance.py`、NumPy/solver/QUBOは未使用。builder コード ハッシュ値は成果物一覧に保存。
- **結果:** `instance_id=evrp_fixture_n10_v18_common_20260909`として検証用データ n=10を固定。ノードは12件（配送拠点 1、顧客 10、充電設備 1）、車両 1、required/validated 経路計算 出発地・到着地 132/132。R13 受入済み 経路計算を再計算せず取り込み、V18 authority/hashを保持した。R10の初期 充電率 1.00、最小 充電率 0.20、operational available 電力量 32.8 kWh、R11 effective 充電 power 70 kW、session limit 30分、外部 演算子 接続のASSUMEDを保持した。
- **検証結果:** 顧客 識別子重複0、全顧客のdemand/TW/service存在、node/index一意、端点 対応付け存在、出発地・到着地 132/132、distance/time/reachability整合、EV/SOC/charging値、出典 hash/provenance、単位を合格。同一入力の一時再生成でcommon 問題例 ハッシュ値一致（`1d01afb5b871dc0cfdbeda701f5853827e0d24bb126d86d958644cb36ec5f1ca`）。
- **課題:** 本番problem-規模 nは未採択。`constraint_version`はR16参照仮置き、`objective_priority`はR17参照仮置きとして保存した。R16以降は実行していない。
- **決定記録:** R05〜R14の確定成果物を同一node/index/orderと出典・来歴で統合し、common 問題例の受入基準を満たしたためR15 合格。既存R05〜R14 成果物は変更していない。
- **次に許可される段階:** R16_COMMON_HARD_CONSTRAINT_DEFINITION（今回未実行）

## R16_COMMON_HARD_CONSTRAINT_DEFINITION — Common 必須制約定義

- **Stage ID:** R16_COMMON_HARD_CONSTRAINT_DEFINITION
- **目的:** 13制約の共通意味論と独立検査器を固定する
- **入力:** I_s・本書の13制約
- **事前条件:** 前工程 `R15_COMMON_DELIVERY_INSTANCE_DEFINITION` の合格（明示された正常結果遷移は例外）と、入力の存在・ハッシュ値・根拠を確認する。
- **手法:** 時間/充電率遷移・許容誤差・適用フラグを定式化し検証器と手計算検証用データを用意
- **検証:** 各制約の正常/違反検証用データ、複数車両/充電/subtourの検査、求解器非依存ことを独立検査し、実行記録に診断を残す。
- **受入基準:** 各制約の正常/違反検証用データ、複数車両/充電/subtourの検査、求解器非依存
- **停止条件:** 共通停止規則と当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義は実行不可、検証不一致・実行異常は不合格。
- **出力:** 制約仕様・共通検証器・検証用データ結果
- **Status:** PASS
- **Started At:** 2026-09-09T18:39:00+09:00
- **Completed At:** 2026-09-09T18:40:00+09:00
- **Commands:** `.conda/bin/python 05_src/traffic_simulation/evrp_r16_constraints/build_constraint_spec.py --instance reproducibility/outputs/traffic_simulation/demand/evrp_r15_common_instance/20260909_r15_common_instance_fixture_n10_v18 --output-dir reproducibility/outputs/traffic_simulation/demand/evrp_r16_constraints/20260909_r16_common_hard_constraints_v1_fixture_n10_charger_revisit_resolved`; `.conda/bin/python 05_src/traffic_simulation/evrp_r16_constraints/validate_constraint_spec.py --spec-dir reproducibility/outputs/traffic_simulation/demand/evrp_r16_constraints/20260909_r16_common_hard_constraints_v1_fixture_n10_charger_revisit_resolved`。
- **Input Hashes:** R15 common instance `1d01afb5b871dc0cfdbeda701f5853827e0d24bb126d86d958644cb36ec5f1ca`。
- **Output Hashes:** constraint spec `f5532f521b00855eeda7e74286c76e169ad4b5ac890ea093402d92f5c5a90313`; constraint config `809fa1bd989a279c2a64169b8278258145728c319e1dabac4178962d3eb1bd83`; validator contract `176656214dbc42fb91dd298911e28a7da39567d43d7945f13f1dc2d6ac858fe4`; validation report `f93dc13bb7e40b4e6e32bf4c182704ce89546f9593bc218c99976c2586030924`; manifest `bf390f8f1018855a39ee659481e6d54d13d2ef23fa33a5f86e4353edc375d2b7`。
- **ソフトウェアの版:** Python 3.11.15。求解器・制約なし二値二次最適化・量子環境は未使用。
- **結果:** `constraint_version=evrp-common-hard-constraints-v1`として13制約を一意識別子で定義。HC01〜HC08、HC10〜HC13をenabled、HC09 Operating-Timeは基準の`maximum_operating_time_enabled=false`に対応してdisabledとした。顧客未配送許容、DFR/objective分離、充電率 1.00/0.20、充電 70 kW/30分/post-充電率<=1.00、R15 reachability/null 意味、OR-Tools/QUBO共通検証器 取り決めを維持した。toleranceは厳密 discrete、距離 1e-6 m、時間 1e-9 s、電力量 1e-9 kWh、充電率 1e-9、積載量 1e-9 kgを変更していない。充電設備複数回訪問を許可し、各訪問を独立eventとした。
- **検証結果:** 未解決 意味 0、13 IDs、必須 fields、R15 問題例 ハッシュ値、units/tolerances、目的 separation、共通版参照、検証器 取り決めを合格。HC12は各充電設備 eventの70 kW・30分・post-充電率<=1.00、連続eventによる上限回避禁止、顧客 訪問制約非適用、R16の回数上限なしを検査対象とする。制約なし二値二次最適化 コピー上限はR20/R21へ延期する。
- **課題:** なし。R16では制約なし二値二次最適化 符号化を実装していない。
- **決定記録:** 利用者採択の充電設備再訪問意味により唯一の実行不可要因を解消し、R16 合格。
- **次に許可される段階:** R17_ORTOOLS_FORMULATION（今回未実行）

<a id="r17_ortools_formulation--or-tools-formulation-initial-blocked-record-superseded-by-revalidation-record-below"></a>

## R17_ORTOOLS_FORMULATION — OR-Tools 定式化 (初期実行不可記録; 後続版に置換済み別再検証記録以下)

- **Stage ID:** R17_ORTOOLS_FORMULATION
- **目的:** 同一制約と辞書式目的をOR-Toolsへ写す
- **入力:** I_s・制約仕様・共通検証器
- **事前条件:** 前工程 `R16_COMMON_HARD_CONSTRAINT_DEFINITION` の合格（明示された正常結果遷移は例外）と、入力の存在・ハッシュ値・根拠を確認する。
- **手法:** 訪問選択・車両割当・充電を表現し小規模手計算と照合
- **検証:** 13制約の対応表・目的優先の保証・整数化と単位整合・モデル妥当ことを独立検査し、実行記録に診断を残す。
- **受入基準:** 13制約の対応表・目的優先の保証・整数化と単位整合・モデル妥当
- **停止条件:** 共通停止規則と当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義は実行不可、検証不一致・実行異常は不合格。
- **Outputs:** OR-Tools formulation・model tests
- **Status:** BLOCKED
- **Started At:** 2026-09-09T18:55:00+09:00
- **Completed At:** 2026-09-09T18:56:32+09:00
- **コマンド:** `python -m py_compile 05_src/traffic_simulation/evrp_r17_ortools/build_formulation_spec.py 05_src/traffic_simulation/evrp_r17_ortools/validate_formulation_spec.py`; `.conda/bin/python 05_src/traffic_simulation/evrp_r17_ortools/build_formulation_spec.py --instance reproducibility/outputs/traffic_simulation/demand/evrp_r15_common_instance/20260909_r15_common_instance_fixture_n10_v18 --constraints reproducibility/outputs/traffic_simulation/demand/evrp_r16_constraints/20260909_r16_common_hard_constraints_v1_fixture_n10_charger_revisit_resolved --output-dir reproducibility/outputs/traffic_simulation/demand/evrp_r17_ortools/20260909_r17_ortools_formulation_fixture_n10_v18`; `.conda/bin/python 05_src/traffic_simulation/evrp_r17_ortools/validate_formulation_spec.py --spec-dir reproducibility/outputs/traffic_simulation/demand/evrp_r17_ortools/20260909_r17_ortools_formulation_fixture_n10_v18`; OR-Tools 求解器本番実行は未実施。
- **Input Hashes:** R15 `common_instance.json` `1d01afb5b871dc0cfdbeda701f5853827e0d24bb126d86d958644cb36ec5f1ca`; R16 `constraint_spec.json` `f5532f521b00855eeda7e74286c76e169ad4b5ac890ea093402d92f5c5a90313`; R16 validator contract `176656214dbc42fb91dd298911e28a7da39567d43d7945f13f1dc2d6ac858fe4`。
- **Output Hashes:** formulation spec `370bdd0369411a81328346f98733ee93938f0777b4fc7cda1b661775b16fdef0`; HC mapping `2f338d925535344c54be732ed54c6ccd37bb4c038e93340cfb37a00767c917ac`; validation report `41949fe54e76dfd5eb5152be7b078741085bdcb9ff2372eb2713c07a3c8fa94a`; R18 contract `64d57d32e3ef890af1c232033e7b525968a5cfcd313b89a6aba8f4b66f20216a`; output schema `b9ae2a2b695a45b4536ba707d9ed813b9f87f8185a4ccc6cbbe1c84a4f715571`; solver config `9da8d141314022e6ab1a6128341207ca77a681a605cb8e965ab1a08d19c6d57d`; manifest `871d9afda8fab42d672e93f4aaa2c32836fbf1f5b1064eb2c25a346af6378c18`。
- **ソフトウェアの版:** Python 3.11.15; OR-Tools 9.12.4544。新規依存関係なし。求解器未実行。
- **結果:** R15を唯一の問題例 正本、R16をconstraint 正本として、RoutingModelのnode/order、配送拠点 start/end、directed transit、optional 顧客、capacity/time callback、到達不能 区間 制限を定義した。充電率はplain RoutingDimensionではなくCP-SAT/custom 電力量-状態候補、充電はevent-expanded候補としてR18 出力 データ構造まで固定した。目的は第1段階で未充足最小、第2段階で合計 移動 時間最小。HC01〜HC13 対応付けを生成し、HC09は基準 disabledとして保持した。
- **検証結果:** 13 unique IDs、instance/constraint 版、未充足、到達可能性、充電率、充電 意味、R18 データ構造の構造検証は合格。定式化 受入は実行不可。R16の「充電設備再訪問回数上限なし」を有限RoutingModelで表すevent copy/slot数が未採択、R15の`q_i`（配送要求件数）をR10 積載量 容量（kg）へ変換する根拠がなく容量を意味保存できない、first solution/metaheuristic/seed/workers/logging/solution limitが未採択。
- **課題:** 上記3点。特に充電設備 コピー数を推測で固定したり、q_iをkgへ黙って同一視したり、求解器設定を恣意採択してR18へ進めない。
- **決定記録:** 実行不可。R16 意味を近似・変更せずにR18を開始できる定式化 受入に未達。必要な変更は、充電設備 event表現の有限化根拠またはR16と整合する別求解器 定式化、q_iと積載量の明示的変換規約、求解器設定の採択。
- **Next Allowed Stage:** NONE

<a id="r17-preparation-and-revalidation-record--2026-09-09"></a>

## R17 準備 ・ 再検証記録 — 2026-09-09

- **範囲:** A 積載量 モデル → B 充電設備 event upper 境界 → C 検証用データ 求解器 設定 の順に準備。R18 求解器 実行は未実行。
- **Repo 監査:** 現行R06 `reproducibility/outputs/traffic_simulation/demand/evrp_r06_customer_demand/20260909_r06_customer_demand_final/customer_demand.csv` は `q_i=1`（配送 request/customer）と `w_i`（世帯-equivalent 標本抽出 重み）のみで、parcel/customer重量は未定義。旧版 `legacy/non_sumo_route_proxy_analysis/src/scenario_generation/scenario_utils.py:31-32,148-175` と `legacy/.../monte_carlo_utils.py:552-559` に `demand_kg` の整数一様5–30 kg 合成 仮定があるが、旧代理指標・非観測・本R06 取り決め外。車両 `payload_kg` はR10の車両容量であり顧客 積載量ではない。現行B2C 基準へ直接再利用しない。
- **External 候補 監査:** (1) MLIT `平成19年度 貨物純流動調査`（2008公表、全国貨物、宅配便の1件重量10.8 kg）は件数/個数の定義がB2C 荷物 要求と一致せず、分布・中央値なし、直接基準不採用。 (2) Japan Post Yu-Pack（現行作業 仕様）は25–30 kg階級と上限30 kgを示すが、母集団 distributionではなくサービス上限、直接基準不採用。 (3) Dalla Chiara et al. (2020,査読、Singapore/UPS-linked observed 配送 weights) は観測配送重量の中央値1.1 kgを報告し、B2C/urban 荷物に近いが日本代表ではない。 (4) Nuzzolo et al./European Transport Research Review (2021, Munich urban 荷物 simulation) は平均約7.5 kgを使い、10 kg超をcargo bike対象外とし、地域・carrier差が大きい。 (5) Sustainability São Paulo 事例（2022, retailer 過去の記録 distribution）は9 kg未満の荷物 重み distributionを使うが、図ベースで再現用パラメータが本repoにない。候補間でmean/medianが大きく異なるため、日本のB2C母集団推定としては採択しない。
- **Payload 判断:** 検証用データ 実装 検証には、再現性・`q_i=1`との互換性・解釈性を優先し、Dalla Chiara et al. (2020) の観測中央値を外部代理指標としてconstant モデルに採択。これは日本の実測推定ではなく `ASSUMED_FIXTURE_BASELINE_EXTERNAL_PROXY`。`m_i=1.1 kg` を全selected 顧客へコピーし、random 乱数の種は `not_applicable_constant`。経験分布の categorical/continuous distributionは根拠の母集団・階級/パラメータが揃わないため検証用データ 基準には採択せず、将来の日本演算子データ置換点として残す。
- **Final 積載量 fields:** `delivery_request_count=q_i=1`（count/customer、R06 モデル convention）と `payload_mass_kg=m_i=1.1`（kg/customer、R17 検証用データ 積載量 モデル）を完全分離。HC06は各segmentの `sum(m_i)` [kg] ≤ `vehicle.payload_capacity_kg=2000` [kg] のみで判定し、`q_i`をkgとして扱わない。SOC/chargingはR16の単位・意味を変更しない。
- **Charger 境界 proof:** 配送済み 顧客数を `k` とする。non-充電 visitsは `depot_departure + k customers + depot_return = k+2`。その間の隔たりは `depot→customer_1`、顧客間 `k-1`、`customer_k→depot` の合計 `k+1`。同一充電設備への連続充電 訪問を禁止するため、各隔たりには高々1 eventしか置けず、`E_max(k)=k+1`。検証用データ全顧客数 `n=10` では安全上限 `E_max(n)=n+1=11`。general 検証用データは `n+1` copies/slots、実際にk<nを訪問した経路では未使用枠を空にする。索引は `charger_event_slot_01..charger_event_slot_(n+1)`、対応コピーは `charger_copy_01..charger_copy_(n+1)`、求解器 索引はR15 ノード 索引とは別namespace。これは恣意的な2/3回制限ではなく、R16の経路構造から導出した有限 符号化であり、R16の複数回訪問許可・連続event禁止・30分/event上限を切り詰めない。
- **検証用データ 求解器 設定:** OR-Tools `9.12.4544`; first solution `PATH_CHEAPEST_ARC`; local search `GUIDED_LOCAL_SEARCH`; 時間 limit `300 s`; random 乱数の種 `20260909`; `num_workers=1`; deterministic `true`; logging `true`; solution limit `1000`; 範囲 `fixture_implementation_validation_only; not production_tuning`。本番想定条件 tuningは未採択・未実行。
- **R17 成果物:** new 実行 `reproducibility/outputs/traffic_simulation/demand/evrp_r17_ortools/20260909_r17_ortools_formulation_fixture_n10_v18_payload_charger_solver_fixed`。R15 積載量-固定済み 問題例 検証 合格 (`common_instance.json` SHA-256 `cbbe1c70e3a227ae0a17104f184c7d24f9676f4beaac6a5a38c9277a6d35eb3c`)、R16 検証 合格、R17 定式化 検証 合格 (`ortools_formulation_spec.json` SHA-256 `52ece569821b69260de37545d8a53d1df9c8abfaaf4fcb1bed8af3d00bc55cd2`)。HC01〜HC13 対応付け count/uniqueness 合格、HC12 意味保持 合格、SOC/charging/reachability/output データ構造 合格。
- **R18 実行 取り決め:** `r18_execution_contract.json` is `READY_PENDING_R18`; 実行器 remains `NOT_IMPLEMENTED_R17_ONLY`; `R18_ONLY_NOT_EXECUTED`。求解器実行、経路生成、R19 検証は行っていない。
- **Final R17 判断:** `R17_ORTOOLS_FORMULATION = PASS`。未解決 issuesは、(i) 1.1 kgは日本実測ではない検証用データ-only 外部 代理指標であり本番分布ではない、(ii) 正式運用 n/scenario tuningは未採択、(iii) R18 実行器実装・実行は未実施。これらはR17 阻害要因ではなく、R18以降の実行前提として明示保存した。**次に許可される段階: R18_ORTOOLS_EXECUTION**。ただし本右左折ではR18を開始しない。

<a id="r18-pre-execution-repository-authority--dependency--demand-usage-audit--2026-09-09"></a>

## R18 pre-実行リポジトリ正本 / 依存関係 / 需要-利用監査 — 2026-09-09

**Scope and stop rule:** read-only audit plus this record only. R18 solver/runner was not executed. Existing R05–R17 PASS statuses were not changed.

<a id="1-authority-and-dependency-classification"></a>

### 1. 正本 ・ 依存関係分類

| Artifact / script | 分類 | Audit result |
|---|---|---|
| `reproducibility/config/traffic_simulation/current_network_completion_authority_v18_geometry_reaccepted.yml` | CURRENT_AUTHORITY | V18 network hash `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`; current R12/R13 V18 fixture artifacts use it. `source_authority: V17` is provenance, not the active network. |
| V17 authority, V17 R12/R13 outputs, V17 R14 outputs | 後続版に置換済み | retained, but must not feed current R18. V17 authority file itself still says `status: CURRENT`, creating repository-level ambiguity. |
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

<a id="2-reconstructed-current-demand-generation-pipeline"></a>

### 2. 再構成した現行需要-生成処理工程

`candidate delivery locations → 500m census household count → R04 weight → R05 successive PPS sample → R06 q_i=1 request convention → R07 synthetic service-start window → R08 fixed service-time assumption → R17 fixture payload m_i=1.1 kg → R15/R17 solver input`

| 段階 | Input / transformation / output | Source, classification, seed/parameter | Represents | Does not represent |
|---|---|---|---|---|
| Candidate locations | `building_delivery_stops_scoped.csv` (39,956 rows): active building-level stop candidates from scoped historical household/parcel pipeline; representative point retained. | PLATEAU/chocho residential candidate tables plus synthetic household/request artifacts; current accepted processed artifact, not observed orders. `housing_seed=20260830`; evaluation date `2026-01-01`. | Potential building-level delivery point population. | Not 39,956 observed homes, customers, orders, or unique households. One row is one active building stop; rows can aggregate multiple households/requests. |
| Census household input | Decode 500m JGD2011 mesh, use e-Stat `T001141034` as `H_m`; map candidate points to mesh and count `N_m`. | Public e-Stat 2020 Census; `H_m` observed household count, unit households; no random seed. | Household-count proxy for spatial residential exposure. | Does not observe parcel orders, order frequency, or delivery probability. |
| R04 weight | `w_i=H_m/N_m`; `N_m=0` recorded with no reallocation; mesh is an input unit, not a sampling stratum. Weight sums conserve candidate-linked household totals; recorded total is 438,455. | R04 computed artifact; `classification_H_m=OBSERVED`, `classification_w_i=COMPUTED`; no seed. | Household-equivalents assigned equally to candidate points within each mesh. | Not household existence probability, delivery demand, order frequency, or observed customer probability by itself. |
| R05 customer sampling | Successive PPS without replacement: `p_i^(k)=w_i/sum(w_j)` over remaining units; n=10, seed=20260909, Python `random.Random`. | R04 weight artifact → R05 sample; conditional draw probability recorded; first-order inclusion probability not calculated; `sampling_stratification=false`. | A reproducible household-weighted candidate sample. | Not spatially balanced sampling and not an observed delivery-demand sample. |
| R06 request count | Left-preserving join to selected R05 IDs; set `q_i=1` for every selected customer. | `ASSUMED`; model convention; no random seed. | One sampled customer equals one model delivery request. | Not empirical parcel count, observed order count, or household delivery frequency. |
| Payload | Set `m_i=1.1 kg` for fixture customers. | Dalla Chiara et al. median as external proxy; `ASSUMED_FIXTURE_BASELINE_EXTERNAL_PROXY`; constant, no seed. | Fixture payload mass for capacity testing. | Not Japan-specific B2C distribution or production scenario payload model. Legacy 5–30 kg path is not in current R17 payload model. |
| R07 time window | Draw receipt-specification category from `ss515`; draw hour anchor from `ss508`; transform to service-start interval (`[0,24]`, clipped bands, or one-hour clock proxy). | `SYNTHETIC_CALIBRATED`; seed=20260909; public Tokyo Metropolitan Goods Movement Survey 2024. | Reproducible synthetic allowable service-start window calibrated to aggregate receipt statistics. | Not customer-level records, Ota-ku order history, or literal requested delivery intervals. |
| R08 service time | Copy `s_i=2.5 minutes/customer` to each R07 customer; travel/waiting/charging excluded. | `ASSUMED (external empirical reference)`; deterministic; 4–15 min is sensitivity candidate, not executed. | Fixture service-time assumption. | Not Ota observed service time or a result of current customer-level measurement. |

<a id="3-candidate-population-and-household-interpretation"></a>

### 3. 候補母集団 ・ 世帯解釈

The 39,956 candidates are active building-level stops after the historical scoped mapping process: `active_households=73,200`, `active_buildings=39,956`, `stop_count=39,956`; `requests_per_stop` ranges 1–12 and `parcel_equivalent_per_stop` ranges 1–14. The upstream `384,353 synthetic_households` artifact is a synthetic household frame, not the candidate count. Households were assigned to buildings using a uniform assignment rule and `housing_seed=20260830`; multiple households can map to one building. Therefore `1 candidate != 1 household` and `1 candidate != 1 observed delivery`; current candidate semantics are one active building-level potential delivery point with aggregated upstream synthetic activity.

The R04 equality `sum_i w_i = 438,455` is a conservation result for candidate-linked census households, not evidence that 438,455 orders or deliveries exist. `N_m=0` meshes are retained as no-candidate records and are not reallocated.

<a id="4-data-usage-field-boundary-table"></a>

### 4. データ-利用項目境界表

| Variable / field | Current value / rule | Source type | 分類 | Geography / unit | Transformation | Current status |
|---|---|---|---|---|---|---|
| `H_m` / `T001141034` | census household count per 500m mesh | public statistic | OBSERVED | Japan Census mesh / households | point-in-mesh join; confidentiality fields preserved | current R04 input |
| `N_m` | candidate count per mesh | computed from candidate artifact | COMPUTED | Ota candidate mesh / count | group candidate points by mesh | current R04 input |
| `w_i` | `H_m/N_m` | public-statistic-derived | COMPUTED | Ota candidate / household-equivalents per candidate | equal allocation inside mesh | current sampling weight; interpretation requires decision |
| `customer_selected` | R05 inclusion | synthetic sampling | COMPUTED | Ota fixture / boolean | successive PPS without replacement | fixture-only sample |
| `q_i` / `delivery_request_count` | 1 per selected customer | model assumption | ASSUMED | customer / requests per customer | constant convention | current fixture model; not observed |
| `m_i` / `payload_mass_kg` | 1.1 per selected customer | external research proxy | ASSUMED_FIXTURE_BASELINE_EXTERNAL_PROXY | customer / kg | constant copy; no q-to-kg conversion | fixture-only; production decision pending |
| `time_window_category`, `e_i`, `l_i` | seeded category/hour and transformed interval | public statistic calibrated synthetic | SYNTHETIC_CALIBRATED | Tokyo aggregate → customer / hours from local midnight | `ss515` category + `ss508` hour; interval rules | fixture-only; production decision pending |
| `s_i` / `service_time_min` | 2.5 | external empirical reference | ASSUMED | urban parcel reference → customer / minutes/customer | fixed copy; excludes travel/wait/charge | fixture-only baseline; 4–15 not executed |

<a id="5-time-window-source-usage-audit"></a>

### 5. 時間-window 出典利用監査

`ss508_r06a.xlsx` is used for receipt weekday/time-band hour distribution; `ss515_r06a.xlsx` is used for date/time-specification category distribution. The current R07 generator does not read `ss519_r06a.xlsx`; it is not a current R07 dependency. `ss519` contains regional receipt/re-delivery frequency information and may be useful for future regional calibration, but the plan's earlier statement that it is used as supplemental calibration is not reflected in the current generator or R07 manifest. This source/documentation mismatch is recorded; no automatic change was made. Weekday, date designation, and redelivery statistics are not currently separate solver variables.

### 6. 適合性評価

| Dimension | Assessment |
|---|---|
| population / household representation | ACCEPTABLE_AS_CURRENT_BASELINE for a synthetic fixture input; REQUIRES_FUTURE_REFINEMENT for observed-population claims |
| spatial representation | ACCEPTABLE_FOR_FIXTURE_ONLY; building representative points and historical mapping are proxies |
| customer sampling | ACCEPTABLE_FOR_FIXTURE_ONLY; reproducible PPS sample, not spatially balanced or observed demand |
| delivery frequency | REQUIRES_USER_DECISION_BEFORE_R18; `q_i=1` is a convention and suppresses frequency variation |
| parcel count | REQUIRES_FUTURE_REFINEMENT; parcel_count/delivery_count are explicitly not defined in R06 |
| 積載量 | ACCEPTABLE_FOR_FIXTURE_ONLY; 1.1 kg is external proxy, not Japan production distribution |
| 時間窓 | ACCEPTABLE_FOR_FIXTURE_ONLY; aggregate-statistic-calibrated synthetic intervals |
| 作業時間 | ACCEPTABLE_FOR_FIXTURE_ONLY; explicit external-reference assumption |
| 再現性 | ACCEPTABLE_AS_CURRENT_BASELINE for fixed fixture artifacts, hashes, and seeds |
| production/scenario analysis | REQUIRES_USER_DECISION_BEFORE_R18; current fixture assumptions must not be silently promoted |

<a id="7-research-decisions-required-before-r18"></a>

### 7. 研究判断必須 R18より前

| 決定記録 | Current policy | Rationale | Limitation | Alternative | Fixture impact | Production impact |
|---|---|---|---|---|---|---|
| household weight as customer probability | use `w_i` in PPS | preserves spatial household exposure proxy | not demand probability | uniform/spatially balanced/explicit inclusion-probability design | はい | はい |
| successive PPS baseline | use R05 PPS without replacement | reproducible household-weighted sample | no spatial balance; conditional probabilities only | stratified/spatially balanced sampling | はい | はい |
| one customer = one request | `q_i=1` | simple fixture objective | no frequency variation | household/order-frequency model | はい | はい |
| constant payload 1.1 kg | fixture-only `m_i` | reproducible external proxy | not Japanese distribution | categorical/continuous Japanese/operator data | はい | yes, if promoted |
| R07 synthetic TW | use ss508+ss515 calibration | public aggregate data available | no customer-level interval; ss519 unused | integrate ss519 or order/operator data | はい | はい |
| service time 2.5 min | fixed assumed baseline | explicit external urban reference | not Ota measurement | 4–15 sensitivity or empirical stop-time data | はい | はい |
| V17/V18 authority closure | use V18 artifact, retain V17 provenance | current output is V18 | V17 file/default/R09 remain ambiguous | regenerate R09/R12/R13 closure against V18 | no current contract, but preflight yes | はい |

**Required confirmation format:** each item must be answered `YES`, `NO`, or `CHOOSE` before any R18 execution. No code, artifact, or execution decision is changed based on an unanswered item.

<a id="8-dependency-chain-and-r18-readiness"></a>

### 8. 依存関係 ・ R18 準備状況

**Superseded by the 2026-09-09 R09 V18 authority closure and R15→R17 propagation record above.** The hashes and readiness statement in this historical pre-closure audit are retained as audit history only; the current chain is the new R09 V18 / R15 current / R16 current / R17 current chain recorded above.

Current recorded chain and hashes:

`03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/building_delivery_stops_scoped.csv` (`fcfca5cb87bc482f1d98306c98823773e872f200c58ecb9090aa12985e3e80e0`) → `03_data/raw/traffic_simulation/population/estat_2020_500m_jgd2011/tblT001141H5339.zip` (`8a8b47563ffe88ec1afb5a17b8d29ac987b40df65498bec4c2fcf1829777f67d`) + `reproducibility/outputs/traffic_simulation/demand/evrp_r04_demand_weight/20260909_r04_demand_weight_v3/candidate_demand_weights.csv` (`e7694dd7461ae048d1de9289408faa91f6d3924defaf06b15b09341e38842ad8`) → `reproducibility/outputs/traffic_simulation/demand/evrp_r05_pps_sampling/20260909_r05_pps_n10_seed20260909_final/customer_ids.csv` (`a3307ac024c639b2690b120d11cd163abbbf83820428d090abb09fa18b0e4d0e`, seed `20260909`) → `reproducibility/outputs/traffic_simulation/demand/evrp_r06_customer_demand/20260909_r06_customer_demand_final/customer_demand.csv` (`9c321d63d5c611d0f348f8e9eb6c5581e4db9dbefa3e4db9e9c747ebde746825`) → `reproducibility/outputs/traffic_simulation/demand/evrp_r07_time_window/20260909_r07_time_window_fixture_n10_v2/customer_time_windows.csv` (`4915372ccc64131631cc1bcd0850b823e2c916663d869e93dd76622e7d4aa6c3`) → `reproducibility/outputs/traffic_simulation/demand/evrp_r08_service_time/20260909_r08_service_time_fixture_n10_final/customer_service_times.csv` (`3d0ac325e0c5bf7686fc8501d9bfaa207a77a4ddc77527b6ea4b014508a2d6e2`) → `reproducibility/outputs/traffic_simulation/demand/evrp_r15_common_instance/20260909_r15_common_instance_fixture_n10_v18_payload_fixed/common_instance.json` (`cbbe1c70e3a227ae0a17104f184c7d24f9676f4beaac6a5a38c9277a6d35eb3c`) → `reproducibility/outputs/traffic_simulation/demand/evrp_r16_constraints/20260909_r16_common_hard_constraints_v1_fixture_n10_charger_revisit_resolved_payload_fixed/constraint_spec.json` (`1b1c3132b44a542605b19f354a5d9c7464a093aa4cb23b04583ca92e0841ec67`) → `reproducibility/outputs/traffic_simulation/demand/evrp_r17_ortools/20260909_r17_ortools_formulation_fixture_n10_v18_payload_charger_solver_fixed/ortools_formulation_spec.json` (`52ece569821b69260de37545d8a53d1df9c8abfaaf4fcb1bed8af3d00bc55cd2`) / `r18_execution_contract.json` (`6439a080bc318a157958e60a41fdd4e1787973b71a5e7fcfbb0a5937569b5d98`). Network side dependency is `reproducibility/config/traffic_simulation/current_network_completion_authority_v18_geometry_reaccepted.yml` (`29ee5fe979c85eb1d11b0f5a55f33782b7b5b08fcf09b48d2fad3e47c0ae33ee`) and V18 network hash `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`.

**Historical pre-closure result: `NOT READY`.** This statement is superseded by the later authority-closure record above. The fixture research decisions remain documented, but they were not changed by the closure.

<a id="r04r05-candidate-generation-and-household-weight-double-correction-audit--2026-09-09"></a>

## R04/R05 候補-生成 ・ 世帯-重み double-correction 監査 — 2026-09-09

**Scope and stop rule:** read-only audit and this record only. R04/R05 were not regenerated, parameters were not changed, and R18 was not executed. Existing R04–R17 statuses were not changed.

<a id="1-39956-candidate-generation-reconstruction"></a>

### 1. 39,956 候補生成再構成

The current candidate artifact is `03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/building_delivery_stops_scoped.csv` (39,956 data rows; SHA-256 `fcfca5cb87bc482f1d98306c98823773e872f200c58ecb9090aa12985e3e80e0`). Its upstream chain is:

`census_000032163278_ota.csv` small-area household margins → `synthetic_households.csv` (384,353 synthetic household rows) → household-size delivery propensity and top-down parcel-equivalent calibration → `daily_requests.csv` (73,547 generated requests; Poisson, seed `20260829`) → multinomial housing-type assignment (Ota municipal housing distribution, seed `20260830`) → uniform compatible-building assignment from accepted PLATEAU/chocho residential building candidates → request-to-building mapping → group by `(evaluation_date, building_id)` → `building_delivery_stops_scoped.csv`.

The historical pipeline implementation is recorded in git commit `d441953`, `05_src/household_parcel/pipelines.py`; the materialized scoped-stop run summary is `03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/stop_generation_run_summary.json`. The current stop-generation summary records: `assigned_households=382,369`, `active_requests=73,547`, `mapped_requests=73,200`, `active_households=73,200`, `active_buildings=39,956`, `requests_per_stop` 1–12, and `parcel_equivalent_per_stop` 1–14. The accepted building candidate inputs are `residential_building_candidates.parquet` and `plateau_buildings_all_with_chocho_points.geo.parquet`; the stop-generation gate accepts only `matched` and `matched_cross_boundary` mappings.

The candidate-generation code does use household and request information upstream, but not the R04 500m `H_m` field: synthetic household rows are expanded from small-area Census household margins; requests are generated by a household-size propensity and top-down parcel-equivalent model; households are randomly assigned to compatible buildings; only buildings with at least one mapped request become active stops. It does not use observed household coordinates, dwelling-unit counts, entrances, a building capacity constraint, or observed orders. `384,353` is the synthetic household frame, not the candidate population. Multiple synthetic households and requests can aggregate into one building candidate.

**Candidate meaning:** one row is one active building-level potential delivery point with aggregated synthetic activity. It is not one real house, one real household, one real order, or one synthetic request. It is also not a household-equivalent count by itself. Candidate count is affected indirectly by synthetic household/request activity and building assignment, but the generation code does not use the later R04 500m household count `H_m` to allocate candidates.

<a id="2-quantitative-mesh-audit"></a>

### 2. 定量的なメッシュ監査

Read-only aggregation joined the 39,956 candidate buildings to the R04 mesh assignment and joined assigned synthetic households by building. There are 172 candidate-containing meshes:

| Quantity | 結果 |
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

<a id="3-meaning-of-current-w_ih_mn_m"></a>

### 3. 意味 of 現行 `w_i=H_m/N_m`

`w_i` assigns the mesh's observed Census household total equally to each active building candidate in that mesh. R05 then treats this household-equivalent as the conditional PPS draw weight. It is not an order rate, parcel count, delivery probability, or first-order inclusion probability.

| Candidate interpretation | Meaning of adding `H_m/N_m` |
|---|---|
| Candidate population already household-distribution-representative | Reweights an already household-informed active-building population toward the same mesh household totals; potential double correction. |
| Candidate population is only building locations | A defensible post-stratification/household-equivalent correction, assuming every candidate is an exchangeable potential point inside the mesh. |
| Candidate population partially reflects households/activity | A correction may be useful, but its magnitude and estimand are not identified without a calibrated joint model; it can overcorrect in meshes where activity filtering already tracks households. |

<a id="4-double-counting-classification"></a>

### 4. 二重計上分類

**判定: `POSSIBLE_DOUBLE_COUNTING`.** It is not `NO_DOUBLE_COUNTING` because the 候補-生成 保存先 already expands 世帯 margins, generates 世帯-level demand, and assigns households to buildings before 有効 buildings are formed. It is not `CONFIRMED_DOUBLE_COUNTING` because the 上流 合成 frame is built at chocho/small-area level and the R04 `H_m` is a separate 500m メッシュ statistic; the リポジトリ does not contain a proof that the same 世帯 合計 is applied once in 候補 selection and again with the same estimand. The 厳密 overlap between the small-area 世帯 margins/top-down demand and `T001141034` is not documented as an 同一性 対応付け.

Evidence: `05_src/household_parcel/pipelines.py` (`build_synthetic_household_frame`, `generate_daily_requests`, `assign_housing`, uniform compatible-building assignment, building aggregation); `reproducibility/config/traffic_simulation/household_parcel_v1/pipeline.yml` (`multinomial` housing assignment, Poisson requests, uniform building assignment); `stop_generation_run_summary.json`; current R04 config and `candidate_demand_weights.csv` (`H_m/N_m`).

### 5. 標本抽出代替案

| 選択肢 | Statistical meaning | Candidate consistency / household reproduction | Double-counting risk | Interpretability / reproducibility | 検証用データ | Production |
|---|---|---|---|---|---|---|
| A. Uniform `1/N` | Equal probability per active building stop | Treats all 39,956 active buildings as the population; does not impose Census household exposure | low additional risk, but preserves upstream synthetic-selection effects | very clear and reproducible | suitable | only if building-stop estimand is intended |
| B. Current PPS `H_m/N_m` | Household-equivalent PPS over active building stops | Reproduces the R04 mesh household proxy under equal within-mesh allocation | possible, because candidate formation already used household/activity information | clear formula and fixed seed; conditional draw probabilities only | currently implemented | only after estimand decision |
| C. Existing candidate-level household/request weight | Sample by `household_count`, `request_count`, or `parcel_equivalent` already aggregated in each candidate | Directly uses the upstream synthetic activity represented by each building; not observed household/order probability | avoids adding a second Census correction, but can overweight activity if used as demand truth | interpretable as synthetic activity-weighted sampling, reproducible; not empirical demand | requires new contract | requires model validation |

No option is automatically adopted. Option C is not currently a valid substitute merely because fields exist: `household_count`, `request_count`, and `parcel_equivalent` are aggregated synthetic pipeline outputs and have different meanings. Selecting among A–C is a research estimand decision.

<a id="6-re-execution-impact-if-w_i-changes"></a>

### 6. Re-実行影響 if `w_i` 変化

If the research decision removes or changes `w_i`, the minimum demand dependency chain is: R04 weight definition/output → R05 customer sample → R06 `q_i=1` rows → R07 time windows → R08 service times. Because the selected customer IDs change, fixture-specific customer endpoints/OD/routing artifacts R12–R14 and their validation must also be regenerated or explicitly revalidated; R15 common instance, R16 constraint input hash, R17 formulation, and the pending R18 contract must then be rebuilt/revalidated. R09 depot authority, R10 vehicle capacity, R11 charger authority, and the V18 network authority do not become invalid merely because demand sampling changes; only demand-dependent joins and downstream fixture artifacts require propagation. No such propagation was performed in this audit.

<a id="7-research-decision-status"></a>

### 7. 研究判断状態

Recommendation: **`INSUFFICIENT_EVIDENCE`** for automatic adoption. The repository supports both interpretations: active building-stop sampling and household-equivalent correction. The strong `N_m`–synthetic-household association makes `KEEP_CURRENT_WI_PPS` non-neutral, but it does not alone prove that `USE_UNIFORM_SAMPLING` is correct. The appropriate choice depends on whether the intended fixture estimand is (i) an active building-stop route sample, (ii) a Census-household-exposure sample, or (iii) a synthetic activity-weighted sample. Do not change R04/R05 or run R18 until the researcher selects the estimand and sampling option.

<a id="8-confirmation-required-before-r18"></a>

### 8. 確認必須 R18より前

| Question | YES / NO / CHOOSE |
|---|---|
| Should the fixture target equal active building-level potential delivery points rather than household exposure? | `CHOOSE: A Uniform / B Current PPS / C Existing candidate-level field` |
| Is `H_m/N_m` intended as a household-exposure post-stratification correction even though candidate creation already used synthetic household/request activity? | `YES / NO` |
| If NO, should R04/R05 be redesigned before R18? | `YES / NO` |
| If C is selected, which field is the estimand: `household_count`, `request_count`, or `parcel_equivalent`? | `CHOOSE` |
| May the current R04/R05 sample remain unchanged for the fixture while the production sampling policy is deferred? | `YES / NO` |

**Audit conclusion:** current statuses R04–R17 are unchanged; no regeneration or execution occurred. R18 execution readiness remains **`REQUIRES_USER_DECISION`**. `EVRP_EXECUTION_PLAN.md` remains the sole progress/execution record.

<a id="r04r05-candidate-population-double-correction-re-audit--2026-09-09"></a>

## R04/R05 候補母集団 double-correction re-監査 — 2026-09-09

**Scope:** audit only. R04/R05 were not regenerated, parameters were not changed, and R18 was not executed. Existing R04–R17 statuses remain unchanged.

<a id="1-candidate-generation-authority-and-meaning"></a>

### 1. 候補-生成正本 ・ 意味

The current artifact is `03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/building_delivery_stops_scoped.csv` (39,956 data rows, 39,956 unique `building_id`; SHA-256 `fcfca5cb87bc482f1d98306c98823773e872f200c58ecb9090aa12985e3e80e0`). The upstream generator is recorded in git commit `d441953`, `05_src/household_parcel/pipelines.py`; the materialized run is documented by `stop_generation_run_summary.json` and the historical config `reproducibility/config/traffic_simulation/household_parcel_v1/pipeline.yml`.

The actual path is:

`census_000032163278_ota.csv` small-area household margins → `synthetic_households.csv` (384,353 synthetic rows) → household-size delivery propensity and top-down parcel-equivalent calibration → `daily_requests.csv` (73,547 Poisson-generated requests, seed `20260829`) → Ota housing-type multinomial assignment (seed `20260830`) → uniform compatible-building assignment from accepted PLATEAU/chocho residential building data → request/building mapping → aggregation by `(evaluation_date, building_id)` → `building_delivery_stops_scoped.csv`.

The generation uses household attributes (`chocho_code`, size class), synthetic household/request activity, housing-type attributes, building usage/residential compatibility, and building representative points. It does not use observed household coordinates, observed orders, dwelling-unit counts, entrances, building capacity, or the later R04 500m `H_m` value. Accepted mapping statuses are `matched` and `matched_cross_boundary`; unmapped/ambiguous states are excluded and not nearest-filled.

The stop summary records `synthetic_households=384,353`, `assigned_households=382,369`, `active_requests=73,547`, `mapped_requests=73,200`, `active_households=73,200`, `active_buildings=39,956`, and `stop_count=39,956`. Therefore one candidate is one active building-level potential delivery point with aggregated synthetic activity. It is not one real building-as-household, one real household, one observed order, or one synthetic request. Multiple synthetic households and requests can be aggregated into one candidate. Candidate count is indirectly affected by household/request generation and building assignment, but not by R04 `H_m` during the candidate-generation step.

### 2. メッシュ再測定

The current candidate and R04 weight artifacts were joined read-only for all 172 candidate-containing 500m meshes:

| Metric | 結果 |
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

<a id="3-interpretation-of-w_ih_mn_m"></a>

### 3. 解釈 of `w_i=H_m/N_m`

R04 assigns the mesh's observed e-Stat household count equally to each active building candidate. R05 then uses this household-equivalent value in successive PPS. It is not an observed delivery probability, order frequency, parcel count, or first-order inclusion probability.

| Candidate population interpretation | Effect of adding `H_m/N_m` |
|---|---|
| Already reflects household distribution | Adds another household-based spatial correction; possible double correction. |
| Pure building locations | Acts as a defensible mesh post-stratification weight if the estimand is household exposure. |
| Partially household-informed | May correct residual spatial mismatch, but the correct magnitude/estimand is not identified. |

<a id="4-double-counting-result"></a>

### 4. 二重計上結果

**判定: `POSSIBLE_DOUBLE_COUNTING`.**

Evidence for possibility: `build_synthetic_household_frame` expands household margins; `generate_daily_requests` generates household-level activity; `assign_buildings` assigns households to compatible buildings; active stops are then formed only from buildings with mapped requests. R04 subsequently applies the separate 500m Census quantity `H_m/N_m`. This is not `NO_DOUBLE_COUNTING` because household information enters both stages. It is not `CONFIRMED_DOUBLE_COUNTING` because the upstream household margins/top-down demand are small-area/derived inputs and the repository does not establish that they are identical to `T001141034` at the same mesh-level estimand. The appropriate research interpretation remains unresolved.

### 5. 標本抽出代替案

| 選択肢 | Meaning / spatial reproduction | Double-counting risk | Interpretability / reproducibility | 検証用データ | Production |
|---|---|---|---|---|---|
| A. Uniform `1/N` | Equal active building-stop probability; preserves the candidate population as generated | Low additional risk, but retains upstream synthetic-selection effects | Highest simplicity and reproducibility | Suitable | Suitable only for a building-stop estimand |
| B. Current PPS `H_m/N_m` | Household-equivalent PPS; explicitly restores R04 mesh household exposure | Possible, because candidate creation already used synthetic household/request activity | Formula and seed are clear; conditional draw probabilities only | Current implementation suitable | Requires estimand decision |
| C. Existing candidate-level `household_count` / `request_count` / `parcel_equivalent` | Directly weights by upstream synthetic activity aggregated at building | Avoids a second Census correction, but risks treating synthetic activity as observed demand | Reproducible but the three fields have different meanings and are not interchangeable | Requires new contract | Requires model validation |

No option is auto-adopted. In particular, candidate-level fields cannot be selected without deciding whether the target is household count, request count, or parcel-equivalent activity.

### 6. 依存関係影響 if `w_i` is 削除済み or 変更済み

The demand dependency is `R04 → R05 → R06 → R07 → R08`. A changed R05 sample changes customer IDs, so customer-dependent R12–R14 fixture endpoint/OD/routing artifacts and then R15, R16, R17 and the pending R18 contract require regeneration or revalidation. R09 depot, R10 EV, R11 charger, and V18 network authority do not need to be invalidated merely because sampling changes; only their demand-dependent joins, if any, must be checked. No propagation was performed.

<a id="7-recommendation-and-decision-gate"></a>

### 7. 推奨 ・ 判断判定基準

Recommended status: **`INSUFFICIENT_EVIDENCE`**. The repository supports a building-stop estimand, a household-exposure estimand, and a synthetic-activity estimand, but does not uniquely select one. Do not change `w_i`, R04/R05, or R18 execution automatically.

User decisions required:

1. Sampling estimand: `CHOOSE A Uniform / B Current PPS / C Candidate-level field`.
2. If B is retained, confirm that household exposure should be applied after a candidate population already formed from synthetic household/request activity: `YES / NO`.
3. If C is selected, choose field: `CHOOSE household_count / request_count / parcel_equivalent`.
4. May the current R04/R05 fixture sample remain frozen while production sampling is deferred: `YES / NO`.

**Final audit status:** R18 execution readiness remains **`REQUIRES_USER_DECISION`**. `EVRP_EXECUTION_PLAN.md` remains the sole execution record.

<a id="r04r05-pps-role-separation-audit--2026-09-09"></a>

## R04/R05 PPS 役割-separation 監査 — 2026-09-09

**Scope and stop rule:** audit only. R04/R05 were not regenerated, no parameter or downstream artifact was changed, and R18 was not executed. Existing R04/R05/R17 statuses remain unchanged.

<a id="1-candidate-generation-role"></a>

### 1. 候補-生成役割

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

<a id="2-r04r05-role"></a>

### 2. R04/R05 役割

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

### 3. 二重計上 re-評価

**判定: `PARTIAL_OVERLAP_BUT_INTERPRETABLE`.**

The implementation is closer to the user's two-role hypothesis (B) than to confirmed same-purpose double counting (A):

1. Synthetic household/request information determines activity-conditioned candidate support: which compatible buildings have at least one mapped synthetic request and therefore enter the 39,956-row population.
2. R04 Census weighting determines a separate mesh-level sampling-mass calibration over that support.
3. R05 performs the actual customer-location sample selection; no candidate-level request/household intensity is passed into R05.

The overlap is real but partial: candidate inclusion is not independent of synthetic household/request activity, so R04 is not correcting a pure building-only frame. However, the same candidate-level intensity is not applied a second time: R04 uses independent mesh-level `H_m/N_m`, and within each mesh makes candidates equal. The repository does not prove that the synthetic small-area margins/top-down request calibration and e-Stat 500m `H_m` have identical estimands. Accordingly, `CONFIRMED_DOUBLE_COUNTING` is not supported; `NO_DOUBLE_COUNTING_DIFFERENT_ROLES` is too strong because the support itself is activity-conditioned.

<a id="4-semantics-of-one-sampled-customer"></a>

### 4. 意味の one 抽出された顧客

The proposed description is **正しい**, with one qualification:

> 39,956 有効 potential 配送 buildingsを候補 母集団とし、500m メッシュのCensus 世帯 件数に比例するようメッシュ-level 顧客-位置 標本抽出 質量を較正し、同一メッシュ内では有効 候補 buildingsを等しく扱ってsuccessive PPS without replacementで抽出する。

The qualification is that the 39,956 support is already conditioned on synthetic household/request activity and accepted building mapping. The resulting sampled customer is a selected active building-level potential delivery point under a synthetic, Census-calibrated sampling design. It must not be described as an actual order probability, an actual household, or an empirical customer probability.

<a id="5-current-pps-versus-uniform"></a>

### 5. 現行 PPS 対一様

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

<a id="6-current-pps-assessment-and-decision-gate"></a>

### 6. 現行 PPS 評価 ・ 判断判定基準

**Assessment: `JUSTIFIED_FOR_FIXTURE_ONLY`.**

The role separation is sufficiently interpretable for a reproducible fixture: synthetic activity creates the active-building support, while Census household counts calibrate mesh-level sampling mass and equalize active buildings within each mesh. It is not justified as an empirical B2C customer-probability model or as a production demand model because the candidate support is synthetic/activity-conditioned and the overlap between small-area synthetic household inputs and 500m Census calibration is not formally decomposed.

No automatic keep/change decision is made. Before R18, the researcher must answer: **`KEEP CURRENT PPS` / `REDESIGN` / `CHOOSE`**. If `KEEP CURRENT PPS` is chosen, the above fixture-only semantics must be accepted. If `REDESIGN` is chosen, R04/R05 and dependent customer-demand artifacts require a separate authorized change; no such change was made here.

**Audit conclusion:** candidate generation, R04 Census weighting, and R05 PPS have distinguishable primary roles, with partial estimand overlap. R04/R05/R17 statuses are unchanged, and R18 remains unexecuted.

<a id="fixture-baseline-formalization-and-r18-pre-readiness-recheck--2026-09-09"></a>

## 検証用データ基準 formalization ・ R18 pre-準備状況再確認 — 2026-09-09

**Scope and stop rule:** The current R04/R05 PPS is formally recorded as a fixture baseline. No R04/R05 regeneration, parameter change, downstream-stage execution, or R18 execution was performed. Existing R04/R05/R17 status fields were not changed.

<a id="fixture-baseline-definition"></a>

### 検証用データ 基準 定義

In this repository, **fixture** means a small, fixed validation instance used to verify implementation, constraints, solver formulation, and reproducibility. **Baseline** means the fixed configuration used as the comparison and reproducibility reference within that fixture. This is explicitly distinct from a **production baseline**: the fixture baseline is not the final empirical demand model or final production/scenario-analysis model.

The adopted fixture baseline is therefore:

- candidate population: 39,956 active potential delivery buildings;
- R04: `w_i=H_m/N_m`, where `H_m` is the 500m Census household count and `N_m` is the active candidate-building count in that mesh;
- same-mesh candidates receive equal `w_i`, so `sum(i in m) w_i = H_m` and mesh sampling mass is calibrated to Census household count;
- R05: successive PPS without replacement, with conditional draw probability `p_i^(k)=w_i/sum(j in U_k) w_j`;
- purpose: synthetic residential B2C customer-location generation for fixture validation, not actual order probability, observed customer probability, an actual household sample, or empirical delivery demand.

Candidate-generation synthetic household/request information and R04 Census weighting remain documented as different roles: candidate support/eligibility formation versus mesh-level sampling-mass calibration. The prior audit classification **`PARTIAL_OVERLAP_BUT_INTERPRETABLE`** is retained. Current PPS is formally assessed as **`JUSTIFIED_FOR_FIXTURE_ONLY`**, not as a production demand-model decision.

<a id="fixture-specific-inputs-and-classifications"></a>

### 検証用データ-specific 入力 ・ 分類

The current R18 input closure identifies these fixture-specific assumptions: `n=10`; R05 current PPS; R06 `q_i=1` delivery-request convention; R17 `m_i=1.1 kg/customer` (`ASSUMED_FIXTURE_BASELINE_EXTERNAL_PROXY`); R08 `2.5 min/customer` (`ASSUMED`); one vehicle; one depot; one charger; and the fixed OR-Tools 9.12.4544 fixture solver configuration. R07 time windows are `SYNTHETIC_CALIBRATED` from aggregate public statistics, not customer-level observations. These labels are fixture/synthetic/assumed classifications and are not production claims.

The following remain explicitly outside the production specification and require future reconsideration: production customer count; production customer-location sampling design; delivery frequency/parcel-count model; payload distribution; service-time distribution; demand scenario generation; and production solver tuning.

<a id="authority-and-stale-reference-recheck"></a>

### 正本 ・ 古い-参照再確認

- The V17 network authority file was corrected from `status: CURRENT` to `status: SUPERSEDED`. Its historical V17 run and provenance remain retained.
- R09 remains unresolved for current authority closure. `evrp_r09_depot_v1.yml` and `r09_depot_manifest.json` point to the V17 network hash `4625dbbc...` and the legacy depot candidate path. The current accepted network is V18 hash `460554c7...`; V18 depot remapping/revalidation is **required before R18**, but R09 was not regenerated.
- The payload-fixed R15 common instance still contains `constraint_version: R16_NOT_STARTED_REFERENCE_EV_RP_COMMON_HARD_CONSTRAINTS`. This is a stale placeholder and cannot be silently relabeled because changing the accepted R15 bytes would require downstream hash propagation. R15 must be rebuilt against the accepted R16 constraint artifact before R18.
- The R17 HC12 text `BLOCKED pending finite event encoding` was corrected to state the fixed route-derived `n+1` finite event-slot encoding; the corresponding formulation and HC mapping hashes are now `f572b338ed14aa0ab87301bf4f10ce4195e405d017f15e205903ea1d59055c73` and `c0716140d93b5fa2f54fddd61cb852c6bc9bec9dd2837ad0d3f8ec15465c0493`. This changes stale wording only; the event bound and semantics are unchanged.
- The current R18 execution contract directly references the current R15 instance hash `cbbe1c70...`, current constraint version `evrp-common-hard-constraints-v1`, current formulation version, local solver config, and local output schema. It has no direct superseded run_id, V17 hash, legacy config path, or old BLOCKED-run reference. Its transitive R15/R09 dependencies are nevertheless not authority-clean.

<a id="current-recorded-dependency-chain"></a>

### 現行記録済み依存関係

`03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/building_delivery_stops_scoped.csv` (`fcfca5cb87bc482f1d98306c98823773e872f200c58ecb9090aa12985e3e80e0`) → R04 `candidate_demand_weights.csv` (`e7694dd7461ae048d1de9289408faa91f6d3924defaf06b15b09341e38842ad8`) → R05 `customer_ids.csv` (`a3307ac024c639b2690b120d11cd163abbbf83820428d090abb09fa18b0e4d0e`) → R06 `customer_demand.csv` (`9c321d63d5c611d0f348f8e9eb6c5581e4db9dbefa3e4db9e9c747ebde746825`) → R07 `customer_time_windows.csv` (`4915372ccc64131631cc1bcd0850b823e2c916663d869e93dd76622e7d4aa6c3`) → R08 `customer_service_times.csv` (`3d0ac325e0c5bf7686fc8501d9bfaa207a77a4ddc77527b6ea4b014508a2d6e2`) → current payload-fixed R15 `common_instance.json` (`cbbe1c70e3a227ae0a17104f184c7d24f9676f4beaac6a5a38c9277a6d35eb3c`) → R16 `constraint_spec.json` (`1b1c3132b44a542605b19f354a5d9c7464a093aa4cb23b04583ca92e0841ec67`) → current R17 formulation / solver config → R18 contract (`6439a080bc318a157958e60a41fdd4e1787973b71a5e7fcfbb0a5937569b5d98`).

The chain is recorded for audit, but it is not yet an authority-clean R18 chain because R09/R15 require closure against V18/current R16. No downstream artifact was regenerated in this turn.

<a id="r18-readiness-and-remaining-decisions"></a>

### R18 準備状況 ・ 残る判断

**Superseded by the 2026-09-09 R09 V18 authority closure and R15→R17 propagation record above.** The following `NOT READY` text is retained only as the pre-closure audit record.

**R18 execution readiness: `NOT READY`.** The blocker is stale/transitive authority dependency, not the adopted fixture PPS policy. Required pre-R18 work is: (1) authorized R09 V18 depot remapping/revalidation; (2) authorized R15 common-instance rebuild with the accepted R16 constraint version; and (3) propagation/revalidation through R16/R17/R18 hashes. These actions are not performed here.

The fixture PPS adoption itself is no longer a user-decision item. Remaining user authorization is limited to whether to authorize the required R09 V18 remapping and R15→R18 dependency closure. Production demand-model choices remain future research decisions and are not prerequisites for treating the current n=10 setup as a fixture baseline.

<a id="r18_ortools_execution--or-tools-execution"></a>

## R18_ORTOOLS_EXECUTION — OR-Tools 実行

- **Stage ID:** R18_ORTOOLS_EXECUTION
- **目的:** 予算内で古典候補解を得る
- **入力:** 検証済古典モデル・I_s・求解器設定
- **事前条件:** 前工程 `R17_ORTOOLS_FORMULATION` の合格（明示された正常結果遷移は例外）と、入力の存在・ハッシュ値・根拠を確認する。
- **手法:** version/seed/time/memory制限を固定し暫定最良解と終了理由を保存
- **検証:** 正常終了を分類し未加工 route/objective/bound/予算を保存ことを独立検査し、実行記録に診断を残す。
- **受入基準:** 正常終了を分類し未加工 route/objective/bound/予算を保存
- **停止条件:** 共通停止規則と当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義は実行不可、検証不一致・実行異常は不合格。事前資源 ceiling到達はLIMIT_REACHED、正常な解未発見はRESULT_INFEASIBLE。
- **出力:** 古典未加工 solution・実行 付随情報
- **Status:** FAIL
- **Started At:** 2026-09-10T00:55:00+09:00
- **Completed At:** 2026-09-10T00:58:00+09:00
- **Commands:** Installed-runtime API audit; parameter compatibility smoke and R18 gate command will use new run `reproducibility/outputs/traffic_simulation/demand/evrp_r18_ortools_execution/20260910_r18_ortools_execution_fixture_n10_v18_retry_02`.
- **Input Hashes:** R15 `7ca39facf83de619db7ec37daa90409834d89b4b75bfeb4e7c501ddef94b2ac4`; R16 `evrp-common-hard-constraints-v1`, `1b1c3132b44a542605b19f354a5d9c7464a093aa4cb23b04583ca92e0841ec67`; Network V18 `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`; R17 formulation `656cdf23ab85fed1d04e2e20f9840da161d2c3aac5f4ac61e6bad6219ff84143`; solver config `b948bbd31edf8576e3ec2420c50bc6996e4e89db8a5f0e8116d42f76bdd7f3b1`.
- **Output Hashes:** retry-02 preflight `465b9626f1795fa4db955c36bc6a48fa6571af0f299a92c85d18fdcb125fd5b6`; index smoke `791ef75c2c29681ad4096ce2a808a98acaeede8b0a0bf3b40ade14b88353ddf7`; parameter compatibility smoke `5b14d9c3d2a080c3820ead215af50b31fe0703e5beae16a6a43333ef7b2a99de`; execution validation `ac9f6b903a22dc45b6c6decb5f80b7507c5fdb7e807d0d9fc813493e8aaec895`; solver output `be2845614c25b1dcc3c42c158c350934cf11321f7b223ad040c38c7905a6e0e0`; manifest `626e6637833b85f77202ce98e521ce08242e45194562ff0fa5e0fb39e1192454`.
- **Software Versions:** Python 3.11.15; OR-Tools 9.12.4544. Solver did not start.
- **結果:** `DefaultRoutingSearchParameters()`生成、strategy/metaheuristic/time/logging/solution_limit設定はsupported。`random_seed`, `num_search_workers`, `deterministic`は項目 absent。固定R17 設定を完全適用できないため求解器 状況 `NOT_STARTED`、終了 理由 `PARAMETER_COMPATIBILITY_SMOKE_FAIL`。求解器は起動していない。
- **検証結果:** R18 実行-level 検証 不合格。パラメーター compatibility 動作確認 不合格。R19独立検証器は未実行。
- **課題:** `routing_enums_pb2.RoutingSearchParameters()`は使用せず、`pywrapcp.DefaultRoutingSearchParameters()`へ修正。installed 9.12.4544にseed/worker/deterministic 項目がないため、代替設定を採用せず停止。
- **決定記録:** 不合格 — 有効 求解器 solutionなし。R19は開始しない。
- **次に許可される段階:** なし（R18 不合格のため停止）

<a id="r18-or-tools-applicability-diagnosis--2026-09-10diagnosis-only-no-solver-execution"></a>

## R18 OR-Tools 適用可能性診断 — 2026-09-10（診断のみ; いいえ求解器実行）

- **範囲:** R15 現行 common 問題例 `7ca39facf83de619db7ec37daa90409834d89b4b75bfeb4e7c501ddef94b2ac4`、R16 現行 constraint `evrp-common-hard-constraints-v1` / `1b1c3132b44a542605b19f354a5d9c7464a093aa4cb23b04583ca92e0841ec67`、V18 道路網 正本を対象に、OR-Tools適用可能性だけを監査した。R18 求解器 実行、求解器 実装 完了判定、R19以降は実施していない。
- **現行 problem reconstruction:** single 配送拠点 `DEP_006`、10 顧客、1 配送 車両、1 受入済み 充電設備 `OTA_KEIHIN_TRUCK_TERMINAL_A`、directed 受入済み 出発地・到着地 132本。各顧客は`q_i=1` 配送 要求と`m_i=1.1 kg` 積載量を分離して持つ。作業時間は2.5 min、作業開始 時間窓、積載量 容量 2000 kg、電池 41.0 kWh、初期 充電率 1.00、minimum/return 充電率 0.20、電力量 `distance_km * 0.35344827586206895 kWh/km`、effective 充電 70 kW、1 event最大30 min、充電設備再訪問可、consecutive 充電 訪問禁止、HC09 operating-時間は基準 disabled、未配送顧客は許容、到達不能 区間は求解器へ有限値で代入しない。
- **Fixture/general distinction:** `n=10 → 11 event slots`は経路 隔たりから導く検証用データの有限上限であり、一般nでは`n+1` 枠を生成するデータ構造-level 符号化にすぎない。これは充電設備訪問回数をR16の意味より小さく制限してはいけない。RoutingModelのノード コピーだけで任意の部分的 recharge/stateを一般nへ自動的に表現できることは確認できない。

<a id="hc01hc13-applicability-matrix"></a>

### HC01〜HC13 適用可能性行列

| HC | Constraint | RoutingModel標準 | Custom RoutingModel | CP-SAT | 難易度 | 意味保存可否 |
|---|---|---|---|---|---|---|
| HC01 | Customer visit at most once; zero allowed | DIRECTLY_SUPPORTED（optional disjunction） | 不要 | SUPPORTED_WITH_STANDARD_MODELING | 低 | 可 |
| HC02 | Depot start/return | DIRECTLY_SUPPORTED | 不要 | SUPPORTED_WITH_STANDARD_MODELING | 低 | 可 |
| HC03 | Flow conservation | DIRECTLY_SUPPORTED（successor route） | 不要 | SUPPORTED_WITH_STANDARD_MODELING | 低 | 可 |
| HC04 | Subtour elimination | DIRECTLY_SUPPORTED（RoutingModel route） | 不要 | SUPPORTED_WITH_STANDARD_MODELING（flow + connectivity/order） | 中 | 可 |
| HC05 | Vehicle assignment | DIRECTLY_SUPPORTED | 不要 | SUPPORTED_WITH_STANDARD_MODELING | 低 | 可 |
| HC06 | Payload capacity on every segment | SUPPORTED_WITH_STANDARD_MODELING（容量 dimension、`m_i`を整数規模。`q_i`とは別） | 不要 | SUPPORTED_WITH_STANDARD_MODELING | 低〜中 | 可 |
| HC07 | Service-start TW | SUPPORTED_WITH_STANDARD_MODELING（Time dimension + slack + service transition） | service/arrival conventionの明示が必要 | SUPPORTED_WITH_STANDARD_MODELING | 中 | 条件付きで可 |
| HC08 | Travel + service + waiting + charging on one time axis | REQUIRES_CUSTOM_MODELING（travel/service/waitのみは可、充電 判断連動は不可） | REQUIRES_STATE_EXPANSION | REQUIRES_CP_SAT（または同等のjoint 状態 モデル） | 高 | CP-SATなら可 |
| HC09 | Optional maximum operating time | DIRECTLY_SUPPORTED（dimension upper 境界。ただし基準 disabled） | 不要 | SUPPORTED_WITH_STANDARD_MODELING | 低 | 可 |
| HC10 | Arc energy and SOC lower bound | NOT_PRACTICALLY_SUPPORTED by plain RoutingModel dimension | REQUIRES_STATE_EXPANSION | REQUIRES_CP_SAT | 非常に高 | standalone CP-SATなら可 |
| HC11 | Initial/final SOC | NOT_PRACTICALLY_SUPPORTED by plain RoutingModel dimension | REQUIRES_STATE_EXPANSION | REQUIRES_CP_SAT | 高 | standalone CP-SATなら可 |
| HC12 | Revisit, partial charge, power-time link, 30 min/event, SOC cap, no consecutive charge | NOT_PRACTICALLY_SUPPORTED by standard RoutingModel | REQUIRES_STATE_EXPANSION（有限 event copiesでも状態 リンクが必要） | REQUIRES_CP_SAT | 非常に高 | standalone CP-SATなら可 |
| HC13 | Accepted reachable directed arcs only | SUPPORTED_WITH_STANDARD_MODELING（allowed/forbidden 区間を明示。有限 罰則項で代替不可） | 不要 | SUPPORTED_WITH_STANDARD_MODELING | 中 | 可 |

**Overall:** HC01〜HC07、HC09、HC13はRoutingModelの得意範囲。ただしHC08は充電なしの時間モデルに限る。HC10〜HC12を含むR16全体はRoutingModel単独では意味保存できない。

### 焦点を絞った確認事項

- **時間窓 / 作業 / 待機:** RoutingDimensionは区間 移動、ノード 作業、余裕変数による待機、cumul upper/lower 境界を表現できる。ただしR16は`b_i`を作業 startと定義するため、cumulがarrivalなのか作業 startなのかを一意に固定し、作業をどの移行へ加えるかを証明する必要がある。充電時間が判断 変数になると、標準dimensionだけでは同じ時刻軸への完全な連動にならない。
- **容量:** `AddDimensionWithVehicleCapacity`相当で`payload_mass_kg=m_i`をsegment 負荷として扱える。`q_i=1`は配送 要求 件数でありkgへ変換しない。整数規模とpickup/delivery 方向を固定すればHC06は意味保存可能。現行R18試作はこの仕様を完全に実行検証していない。
- **充電率 / 電池:** RoutingDimensionは通常、経路に沿う単調なcumul/resourceを扱う。移動で電力量が減り、充電設備で増える状態を、経路選択・充電設備選択・充電率連続値・帰着 境界と同時に表現する標準dimensionの取り決めはない。負のtransitやdimension cumulを用いたworkaroundは、充電設備での増加、容量上限、event 所要時間連動、部分的 充電を完全には表現せず、意味保存の根拠にならない。
- **充電:** R16の充電は、(i) 充電設備再訪問、(ii) eventごとの増加、(iii) `charged_energy = power * duration`、(iv) 所要時間≤30 min、(v) 充電率≤1、(vi) consecutive event禁止、(vii) route/time/SOCとの同時連動を要求する。duplicated 充電設備 ノードや11 有限 copiesは候補表現に過ぎず、コピー選択をSOC/time 状態へjointly リンクしない限り不完全。standard RoutingModelの固定区間 cost/node 訪問では部分的 recharge 判断を表現できない。

### RoutingModel + CP-SAT 再評価

単純な混合型（RoutingModelで経路を決め、CP-SATで後からSOC/chargingを検査）は不適切。経路 successor 変数はRoutingModel内部に閉じ、CP-SAT 状態 変数と同一のjoint objective/constraint グラフを形成しないため、後検査は実行可能 経路の選別に留まり、一次目的・二次移動時間最適性とcompletenessを失う。反復（経路生成→状態 check→cut/no-good→再求解）を追加しても、cutの完全性、終了条件、optimality証明、同一辞書式目的の保証が別途必要で、現仕様の標準architectureとしては採択しない。

RoutingModelとCP-SATを本当にjointにするには、RoutingModelの経路を外部化してCP-SATの区間 二値 変数へ移すか、CP-SATをmasterとして全状態を同一モデルへ入れる必要がある。その時点で実質的にはCP-SAT standalone 定式化であり、単純混合型の利点は失われる。

<a id="cp-sat-standalone-comparison"></a>

### CP-SAT 単独構成比較

CP-SAT standaloneなら、区間 二値 `x_ij`、訪問 `y_i`、車両 割当、order/MTZまたは流れ、service-start/wait 時間、payload/load、SOC/energy、充電設備 event 使用済み、charged 電力量、所要時間、post-充電 充電率を同一モデルへ定義できる。`x_ij`と状態 移行をbig-Mまたはreified linear constraintsでリンクし、充電設備 event 枠は一般nの`n+1`上限として展開できる。`charged_energy = 70 kW * duration`は整数規模で線形化し、所要時間≤30 min、充電率≤1、consecutive 充電禁止を同一モデルへ入れられる。

CP-SATの欠点は、モデル builder・整数規模・big-M上限・symmetry・経路 connectivity・解読・性能設計をすべて実装する必要があり、RoutingModelより複雑なこと。n=10 検証用データではこの複雑性を受入可能で、R16意味保存と制約なし二値二次最適化とのvariable/constraint対応を明確にできる。production/scalingでは性能限界を測定し、無制限なn拡大を仮定してはいけない。将来制約なし二値二次最適化比較に対しては、CP-SATの二値 decision/state 変数と制約なし二値二次最適化 符号化の対応を同一に設計しやすい。

<a id="existing-r17r18-prototype-audit"></a>

### 既存 R17/R18 試作監査

| Area | Current classification | 確認事項 |
|---|---|---|
| R17 formulation files | SPECIFICATION ONLY | `build_formulation_spec.py`はジェイソン形式 spec/mapping/schemaを生成し、対応付け内にも実装 deferredを記録。求解器 モデルは構築しない。 |
| R17 validation | SPECIFICATION VALIDATION ONLY | `validate_formulation_spec.py`は13 IDs、ハッシュ値、意味上の fields、設定 presenceを検査するが、求解器 実行可能性・充電率・充電 joint モデルは検査しない。 |
| RoutingIndexManager | INCOMPLETE PROTOTYPE / API compatibility fixed in prior retry | 3-argument constructor 動作確認は通過したが、これはモデル completenessを示さない。 |
| Search parameters | INCOMPLETE PROTOTYPE / API compatibility diagnosed | `DefaultRoutingSearchParameters()`はinstalled プログラム用インターフェースで生成できるが、R17固定の`random_seed`、`num_search_workers`、`deterministic` fieldsは9.12.4544にない。求解器 実行は未成立。 |
| SOC state | NOT_IMPLEMENTED in executable solver | R17 仕様はcustom CP-SAT 状態を要求するが、R18 実行器は経路後に充電率を手計算しているだけで、求解器 constraintではない。 |
| Charging events | NOT_IMPLEMENTED in executable solver | R18 出力に11 unused 枠を出す枠だけあり、充電設備 訪問、部分的 充電、所要時間-電力量 リンク、consecutive prohibitionを求解中に表現していない。 |
| Route/state linking | NOT_IMPLEMENTED | RoutingModel 経路とSOC/charging 状態をjointly リンクするCP-SAT モデル、cuts、iteration、optimality 取り決めはない。 |
| 目的 | INCOMPLETE PROTOTYPE | R17はlexicographic two-段階をspecifyしたが、試作実行器のphase/objective実装はその保証を実行・検証できる状態ではない。 |
| Output/validation | 一部完了 | データ構造、trajectory、成果物一覧の枠はあるが、有効 求解器 出力とR19-independent 実行可能性 検証は未生成。 |

### 構成推奨

- **検証用データ n=10:** **C: CP-SAT standalone**を推奨。HC01〜HC07/HC09/HC13は標準linear constraints、HC08/HC10/HC11/HC12は同一CP-SAT 状態 モデルで表現し、route/state/chargingをjointly 求解する。RoutingModelは比較用のrelaxed 経路計算 動作確認または区間-data utilityに限定する。
- **Production/scaling:** まず同じCP-SAT 意味で小〜中規模の性能境界を測る。RoutingModel単独へ戻すのはSOC/chargingを別問題へ分離する場合だけで、現R16 電気自動車配送経路問題の同一比較分岐には採用しない。CP-SATが規模上限に達した場合は、仕様を変更せず、明示的な decomposition/column-generation等を別設計として診断・承認する。
- **Recommended architecture:** **C: CP-SAT standalone**。Bの単純RoutingModel+CP-SATは採択しない。Dの他求解器は今回の対象外。

<a id="implementation-gap-analysis-for-recommended-c"></a>

### 実装差分分析の対象： 推奨する C

| Item | 状態 | Required work |
|---|---|---|
| model builder | NOT_IMPLEMENTED | 現行 R15/R16 データ構造からCP-SAT モデルを生成し、units/scaleを固定する |
| 変数 | NOT_IMPLEMENTED | arc, visit, vehicle, order, time, wait, load, SOC, event, duration, charge-energy variables |
| constraints | NOT_IMPLEMENTED | HC01〜HC13をjoint モデルへ一対一対応させる。HC09 disabled フラグを保持 |
| 目的 | 一部完了 | lexicographic 優先順位は仕様のみ。二段階CP-SATまたは厳密なhierarchical 求解を実装・検証する |
| charging model | NOT_IMPLEMENTED | 11 検証用データ 枠 / general n+1 枠、部分的 充電、70 kW、30 min、充電率 cap、revisit、いいえ consecutiveを実装 |
| state propagation | NOT_IMPLEMENTED | directed 区間ごとの電力量、service/wait/charge 時間、initial/final 充電率を経路 二値とリンクする |
| solver config | 一部完了 | R17 設定は保存済みだがRoutingModel プログラム用インターフェースとCP-SAT パラメーター 意味は未採択。seed/workers/determinismのCP-SAT対応を別に固定する必要がある |
| solution decode | NOT_IMPLEMENTED | CP-SAT 割当から経路、ノード trajectory、充電率、積載量、充電 eventを再構成する |
| output schema | 一部完了 | R18 データ構造案は存在するがCP-SAT 状態に対する確定取り決めではない |
| independent validation support | 一部完了 | R16 検証器 取り決めは存在するが、CP-SAT 出力を独立再計算するR19 検証器は未実装 |

<a id="diagnosis-decision"></a>

### 診断判断

- **OR-Tools applicability:** yes, but not as plain RoutingModel. OR-Tools CP-SAT can represent the current EVRP with meaning preserved after a new standalone formulation is designed and validated.
- **RoutingModel alone:** no for full R16 semantics; acceptable only for a relaxed non-charging/state-free subproblem.
- **RoutingModel + CP-SAT:** no as a post-check hybrid; it is incomplete unless route binaries and all state constraints are moved into one joint model.
- **CP-SAT standalone:** technically appropriate and recommended for fixture; scalability remains an empirical gate.
- **Current implementation completeness:** R17 is specification/validation only; R18 is an incomplete prototype with prior API errors, no executable SOC/charging constraints, no route/state joint linking, and no valid solver output.
- **R17/R18 redesign:** reopen R17 as architecture/formulation selection; replace RoutingModel-centered executable plan with CP-SAT standalone design, then independently validate the new formulation before any R18 execution. Preserve all existing R17/R18 PASS/FAIL history.
- **User decision required:** approve or reject architecture C (CP-SAT standalone), and separately approve the CP-SAT parameter contract for seed, workers, determinism, integer scales, big-M bounds, and solver time limit. Until that decision and a new formulation gate, do not implement or execute R18.
- **Next Allowed Stage:** NONE — architecture decision and formulation re-acceptance required; R19+ remain NOT_STARTED.

<a id="r17-cp-sat-standalone-redesignformulation-specification--2026-09-10"></a>

## R17 CP-SAT 単独構成 redesign/formulation 仕様 — 2026-09-10

- **範囲:** R17 現行 architectureを`C: CP-SAT standalone`として再設計した定式化 仕様のみ。RoutingModelおよびRoutingModel+CP-SAT 混合型は現行 定式化から除外し、過去R17/R18 prototypeはhistorical/prototypeとして保持した。求解器 コード、R18 実行、R19以降は実施していない。
- **状態:** 実行不可（仕様は作成済みだが、条件付き 充電設備-枠 orderingの実装証明、整数 モデル 試験、repeated-実行 再現性、独立検証器が未実装）
- **Started At / Completed At:** 2026-09-10T01:10:00+09:00 / 2026-09-10T01:20:00+09:00
- **Commands:** installed runtime audit `.conda/bin/python` with `ortools.sat.python.cp_model.CpSolver().parameters`; no solver/model solve command. R15/R16 JSON read-only reconstruction.
- **Input Hashes:** R15 `7ca39facf83de619db7ec37daa90409834d89b4b75bfeb4e7c501ddef94b2ac4`; R16 `evrp-common-hard-constraints-v1` / `1b1c3132b44a542605b19f354a5d9c7464a093aa4cb23b04583ca92e0841ec67`; V18 network `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`.
- **Outputs:** [CP-SAT formulation spec](reproducibility/outputs/traffic_simulation/demand/evrp_r17_cpsat_standalone/20260910_r17_cpsat_standalone_formulation_fixture_n10_v18/cpsat_formulation_spec.json); [formulation validation report](reproducibility/outputs/traffic_simulation/demand/evrp_r17_cpsat_standalone/20260910_r17_cpsat_standalone_formulation_fixture_n10_v18/r17_cpsat_formulation_validation_report.json).
- **Output Hashes:** specification `d012fe1871c4d63695e6ac294e7b1bc3835481ccd81fe7f41d234d1d5679c4fe`; validation report `2adc02c8801b676d21814b095d16f20cf3adc03559d9c6d15aedda8b8ffc453c`.
- **Formulation summary:** position-indexed route with `x_pij` positional arc binaries and aggregate `x_ij`, `node_at[p,i]`, `active[p]`, `y_i`, exact depot start/return, payload grams, time milliseconds, energy joules, and 11 charger-event slots. General route positions are `2n+3`; charger slots are `n+1` from the R16/R17 route-gap derivation.
- **Integer units:** time ms; energy J; payload g; source distance remains m. Battery `147,600,000 J`, minimum `29,520,000 J`, charging `70 J/ms`, event cap `1,800,000 ms`. Arc travel time uses ceiling to ms. Arc energy uses `ceil(Decimal(distance_m) * Decimal(energy_rate_kWh_per_km) * 3600)` J, so energy is never rounded downward and feasibility is not overestimated.
- **HC01〜HC13:** HC01〜HC07、HC09、HC13はposition/flow/capacity/time/allowed-arc constraintsで対応付け。HC08、HC10、HC11、HC12はCP-SATの同一状態 モデルでroute/time/energy/chargingをjointly リンク。HC09は基準 disabledを保持。
- **充電:** `used_e`、`charger_slot_e_p`、`charge_duration_e`、`charge_energy_e`を使用し、`charge_energy_e=70*duration_e`、所要時間≤1,800,000 ms、post-電力量≤電池、同一physical 充電設備の再訪問、consecutive 充電設備 positions禁止を定義。11 枠はn=10の上限であり、任意の小さい訪問回数制限ではない。
- **目的:** 罰則項 重みではなく二段階CP-SAT。第1 求解で`n-sum(y_i)`最小化、最適配送済み数を固定、第2 求解で合計 移動 時間最小化。第2目的が第1目的を逆転しない。
- **Big-M:** 原則OnlyEnforceIfとbounded 厳密 equalityを使用。枠-位置 orderingだけは条件付き 順序の実装証明が未完で、必要時のtight 境界は`P-1=22`（検証用データ）と導出済み。恣意的な`1e6`は使用しない。
- **Runtime 求解器 パラメーター 監査:** OR-Tools 9.12.4544 CP-SATで`random_seed`、`num_search_workers`、`max_time_in_seconds`、`log_search_progress`はsupported。deterministic専用項目は要求しない。求解器は未実装・未実行。
- **検証:** 整数 units/overflow bounds/HC mapping/11-slot meaning/objective/output 復号 取り決めは仕様-level 合格。条件付き 枠 ordering proof、整数 CP-SAT モデル 試験、repeated-実行 比較、R19 独立検証器は未完了のためoverall 実行不可。
- **決定記録:** CP-SAT standalone architectureを正式採択したが、R17 定式化 判定基準は未通過。既存R17/R18のPASS/FAIL historyは変更・削除していない。
- **次に許可される段階:** なし。上記進行を妨げる itemsを解消し、新R17 定式化を再検証して合格するまで、`R18_CP_SAT_IMPLEMENTATION_AND_EXECUTION`を開始しない。

<a id="r17-charger-slot-ordering-proof-and-integer-model-smoke-test-specification--2026-09-10"></a>

## R17 充電設備-枠順序証明 ・ 整数-モデル動作確認-試験仕様 — 2026-09-10

- **範囲:** R17 CP-SAT standalone 定式化の条件付き 充電設備-枠 ordering proofと、R18前に実施すべき整数-モデル 動作確認-試験 取り決めの仕様化のみ。CP-SAT 求解器実行、R18本実行、R19以降は未実施。
- **状態:** 実行不可（分類: `FORMULATION_COMPLETE_TESTING_PENDING`）。条件付き orderingはCP-SAT API/formulation levelでRESOLVED。ただし整数 モデル 動作確認 試験、repeated-実行 再現性、R19 独立検証器は未実行/未実装。
- **Started At / Completed At:** 2026-09-10T01:25:00+09:00 / 2026-09-10T01:35:00+09:00
- **コマンド:** OR-Tools 9.12.4544の`CpModel.AddImplication`、`Add(... > ...).OnlyEnforceIf(...)`、Boolean channelingのモデル-construction プログラム用インターフェース 動作確認。求解器 callなし。
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

<a id="r17-integer-model-smoke-tests--2026-09-10"></a>

## R17 整数-モデル 動作確認 試験 — 2026-09-10

- **範囲:** R17 CP-SAT standalone 整数-モデル 動作確認 試験 8件のみ。R18本番n=10 求解器、R19以降は未実施。
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

<a id="r17-relaxed-diagnostic-harness-and-formulation-gate-review--2026-09-10"></a>

## R17 緩和した diagnostic harness ・ 定式化判定基準確認 — 2026-09-10

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

<a id="r17-t05-charging-duration-cap-causal-diagnostic-redesign--2026-09-10"></a>

## R17 T05 充電-所要時間-cap causal diagnostic 再設計 — 2026-09-10

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

<a id="r17-t05-redundant-bound-proof-and-formulation-gate-reclassification--2026-09-10"></a>

## R17 T05 redundant-境界証明 ・ 定式化判定基準 reclassification — 2026-09-10

- **Scope:** T05 classification and R17 formulation gate review only. R18/R19 were not executed.
- **T05 分類:** `DURATION_CAP_REDUNDANCY_PROOF`（旧 `DURATION_CAP_CAUSAL_INFEASIBILITY_TEST` から変更）。
- **Baseline:** `E_max=147,600,000 J`; `E_min=29,520,000 J`; `P=70 J/ms`; `t_session,max=1,800,000 ms`.
- **Proof:** `t_max^battery=(E_max−E_min)/P=118,080,000/70=1,686,857.142857 ms`; floorは `1,686,857 ms`、余りは `10 J`。従って `1,686,857.142857 < 1,800,000 ms`、差は `113,142.857143 ms`（約1分53.143秒）。
- **Conclusion:** arrival 電力量が`E_min`以上である限り、電池 upper 境界を守れる1 充電 eventの最大時間は約1,686,857.14 ms。HC12の30分上限は現行 基準 状態-spaceではbattery/SOC boundsより緩く、独立にはbindingしない。これは定式化 誤りではない。
- **HC12:** `t_c^charge <= 1,800,000 ms`をCP-SAT general 定式化から削除せず保持。annotationは `REDUNDANT_UNDER_CURRENT_BASELINE_PARAMETERS`。将来、最小 充電率、電池 容量、充電 power、充電設備 仕様が変わればbindingになり得る。
- **T05 expected 結果:** 30分超のeventは現行 基準のbattery/SOC boundsで先に排除される。所要時間-cap-only FEASIBLE controlは構成不能であり、redundancy proofを合格とする。
- **Gate 受入:** constraint実装、causal 試験可能な制約の因果診断、mathematically redundantな制約の証明、誤実装でないことを確認する基準へ修正。T01/T02/T03/T08 正 試験、T04/T06/T07 causal diagnostics、slot/state/reproducibility、HC01〜HC13 対応付けはすべて合格。未解決 定式化 issuesは`0`。
- **Artifact:** `reproducibility/outputs/traffic_simulation/demand/evrp_r17_cpsat_standalone/20260910_r17_t05_redundant_bound_proof_20260910/T05_redundant_bound_proof.json`（SHA-256 `9365f36041a358217b67418a7e0430012f770dda15327f9ebc40ed3fd45072ab`）。
- **決定記録:** `R17_ORTOOLS_FORMULATION = PASS`。R19 独立検証器は未実装だが、R17 定式化の未解決課題には含めず、R19 stageの課題として保持。
- **次に許可される段階:** `R18_CP_SAT_IMPLEMENTATION_AND_EXECUTION`（今回は開始しない）。

<a id="r18_cp_sat_implementation_and_execution--cp-sat-standalone-implementation-and-execution"></a>

## R18_CP_SAT_IMPLEMENTATION_AND_EXECUTION — CP-SAT 単独構成実装 ・ 実行

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

<a id="r19_ortools_validation--or-tools-validation"></a>

## R19_ORTOOLS_VALIDATION — OR-Tools 検証

- **Stage ID:** R19_ORTOOLS_VALIDATION
- **目的:** 古典解の実行可能性を独立確認する
- **入力:** 古典未加工 solution・同一I_s・共通検証器
- **事前条件:** 前工程 `R18_ORTOOLS_EXECUTION` の合格（明示された正常結果遷移は例外）と、入力の存在・ハッシュ値・根拠を確認する。
- **手法:** 経路から時間/荷量/充電率/訪問を再計算し求解器判定と照合
- **検証:** 実行可能宣言解の全必須制約合格、判定矛盾0ことを独立検査し、実行記録に診断を残す。
- **受入基準:** 実行可能宣言解の全必須制約合格、判定矛盾0
- **停止条件:** 共通停止規則と当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義は実行不可、検証不一致・実行異常は不合格。
- **出力:** 古典検証・検証済み 暫定最良解
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
- **課題:** 未実行。受入基準の未固定項目を実行開始時に解消し、解消不能なら実行不可
- **Decision:** NOT_RUN
- **次に許可される段階:** R20_QUBO_FORMULATION（Gate通過時のみ）

<a id="r20_qubo_formulation--qubo-formulation"></a>

## R20_QUBO_FORMULATION — 制約なし二値二次最適化定式化

- **Stage ID:** R20_QUBO_FORMULATION
- **目的:** 同じI_sと制約を二値 符号化する
- **入力:** I_s・共通制約・小規模古典検証用データ
- **事前条件:** 前工程 `R19_ORTOOLS_VALIDATION` の合格（明示された正常結果遷移は例外）と、入力の存在・ハッシュ値・根拠を確認する。
- **手法:** logical/binary/aux変数、罰則項、離散化、復号、目的優先を記録
- **検証:** 全13制約の表現が明示、係数/変数対応付け/量子幅/単位が定義済ことを独立検査し、実行記録に診断を残す。
- **受入基準:** 全13制約の表現が明示、係数/変数対応付け/量子幅/単位が定義済
- **停止条件:** 共通停止規則と当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義は実行不可、検証不一致・実行異常は不合格。
- **出力:** 制約なし二値二次最適化仕様・行列・符号化 成果物一覧
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

<a id="r20-qubo-application-audit--gap-analysis--2026-09-10"></a>

## R20 制約なし二値二次最適化 application 監査 / 差分分析 — 2026-09-10

- **範囲:** R20 成果物・R15/R16/R19 正本・リポジトリ 出典の読取り専用監査のみ。R20 定式化の作り直し、R21、Ising、QAOA/Aer、縮約した problem採択は行わない。
- **現行 maturity:** `FORMULATION_ONLY`。R20には位置-indexed 候補、変数 登録簿、HC 対応付け、厳密 ビット-幅案、罰則項 framework、Rosenberg auxiliary 登録簿、resource/scaling estimateがある。一方、実装済みのcoefficient builder、sparse 制約なし二値二次最適化 行列、numeric 罰則項 certificate、completed quadratization、制約なし二値二次最適化 復号器、R21 検証器はない。
- **Authority reconstruction:** R15 `7ca39facf83de619db7ec37daa90409834d89b4b75bfeb4e7c501ddef94b2ac4`; R16 `evrp-common-hard-constraints-v1` / `1b1c3132b44a542605b19f354a5d9c7464a093aa4cb23b04583ca92e0841ec67`; R19 `PASS`; fixture n=10, depot=1, charger=1, vehicle=1, accepted directed OD=132, charger upper bound=11, HC09 disabled. R17 RoutingModel prototype and old R18 artifact are not QUBO authority.

<a id="hc01hc13-completeness-audit"></a>

### HC01〜HC13 完全性監査

| HC | Current QUBO expression / dependency | Penalty readiness | 分類 | Remaining gap |
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

<a id="variable-explosion-audit-n10"></a>

### 変数 explosion 監査, n=10

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

<a id="exact-encoding-necessity-audit"></a>

### 厳密符号化 necessity 監査

| State | Current range | Exact bits | Coarser candidate | Maximum quantization error / semantic risk |
|---|---:|---:|---|---|
| Time | 0–124,669,348 ms | 27 | 1 s, 10 s, 1 min | up to 999 ms, 9,999 ms, 59,999 ms; can change TW and propagation feasibility |
| 電力量 | 0–147,600,000 J | 28 | 1 kJ, 10 kJ, 0.1 MJ | up to 999 J, 9,999 J, 99,999 J; can change SOC lower bound and post-charge cap |
| Payload | 0–2,000,000 g | 21 | 1 kg / 100 g | up to 999 g / 99 g; current 1,100 g and 2,000,000 g semantics can change at boundary |
| Charging duration | 0–1,800,000 ms | 21 | 1 s / 1 min | up to 999 ms / 59,999 ms; can change HC12 event cap and `70 J/ms` relation |

R20 does not adopt coarser units. Exact binary expansion is formally possible but resource-heavy; the actual precision requirement versus acceptable coarsening is a `USER_RESEARCH_DECISION`, not an implementation assumption.

### 位置-indexed re-評価

Position indexing is strong for fixture-level subtour handling, route order, charger revisit slots, and accepted-arc restriction. It is not proven globally best: arc-based can reduce route variables but needs order/state/subtour auxiliaries; time-expanded/state-expanded gives direct feasibility but has state-space explosion; hybrid reduces some width only by introducing a semantic discretization boundary. Position indexing is therefore “best current exact-semantics candidate for the fixture,” not a proven scalable optimum. Its route transition growth is approximately `O(n^3)` for complete directed OD, while state bits grow approximately `O(n log range)` and slot-duration quadratization approximately `O(n^2 log duration)`.

<a id="penalty-readiness"></a>

### 罰則項準備状況

All R20 penalty entries are `concept only` or `lower-bound framework only`; no constraint has a completed numeric penalty certificate. The proposed rule `lambda > max objective improvement / minimum nonzero violation` is not yet instantiated with complete coefficient bounds. Missing items are: maximum Stage-1 travel/objective contribution, Stage-2 travel range after fixed fulfillment, every inequality slack domain, every equality violation minimum, interaction/cross-term bounds, Rosenberg penalty lower bounds, and a hierarchy proof ensuring no HC violation beats a valid objective improvement. No arbitrary 1000/1e6 weight is accepted.

<a id="quadratization-readiness"></a>

### Quadratization 準備状況

| Term source | Degree | Planned method | Current state |
|---|---:|---|---|
| slot position × duration bit | 2 | Rosenberg `z=xy` | auxiliary family estimated (5,313), penalty coupling not coefficientized |
| arc/state gated propagation | 3 or higher after state-bit gating | Rosenberg / chained reductions | not fully enumerated |
| charger activation × duration/energy state | 3 or higher in expanded form | auxiliary products | not implemented |
| inequality slack and conditional state bounds | 2–higher | binary slack plus reduction | slack variables absent from registry |

“Rosenberg planned” is not implementation. Reduction order, auxiliary uniqueness, penalty coupling, and count certificate remain incomplete.

<a id="qubo-coefficient-generation-readiness"></a>

### 制約なし二値二次最適化係数-生成準備状況

Current status: `BLOCKED_BY_DECISIONS` (not `READY_TO_GENERATE_QUBO`). Variable registry exists; coefficient builder, linear/quadratic term emitter, constant offset, symmetry normalization, coefficient range audit, reproducible sparse matrix, and matrix hash do not exist. No QUBO coefficients have been generated. QUBO symmetry/coefficient sanity is therefore not testable yet.

<a id="r21-validation-readiness"></a>

### R21 検証 準備状況

Not ready. Required unimplemented components are: binary assignment→route decoder, independent HC checker for QUBO samples, QUBO energy recomputation, penalty decomposition, objective decomposition, encoding of the known R19-feasible CP-SAT solution, known infeasible-vector separation, and exact coefficient/matrix reproducibility checks. R19’s accepted solution is usable as a known-feasible vector only after exact variable assignment, all state-bit assignment, auxiliary assignment, and objective/penalty energy are defined without discretization drift.

<a id="aerqaoa-applicability-and-reduced-problem-gate"></a>

### Aer/QAOA 適用可能性 ・ 縮約した-問題判定基準

13,782 logical binary variables imply a 13,782-qubit logical QAOA width before hardware mapping. Statevector memory is exponential in width; shot-based simulation still incurs circuit-width and shot cost; QAOA parameter count grows with depth and mixer/cost design; the interaction graph has estimated 17,953 nonzero couplers, and higher-order reduction adds coupling/depth overhead. The dominant blockers are width, state-vector impossibility, circuit depth from penalty gadgets, and coefficient dynamic range—not merely matrix density. Full exact n=10 is not ready for Aer/QAOA.

Before any reduced quantum problem, user decisions are required on: quantum-optimized object, HC retained classically, permitted time/energy/payload coarsening, target problem size, classical benchmark, feasibility repair policy, and how a reduced result maps back to the full EVRP/system metric. No reduced problem is adopted.

<a id="gap-classification-and-recommended-dependency-order"></a>

### 隔たり分類 ・ 推奨する依存関係順序

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

<a id="temporary-diagnostic-qiskitaer-and-hybrid-feasibility--2026-09-10"></a>

## 一時的 diagnostic: Qiskit/Aer ・ 混合型実行可能性 — 2026-09-10

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

<a id="r21_qubo_validation--qubo-validation"></a>

## R21_QUBO_VALIDATION — 制約なし二値二次最適化検証

- **Stage ID:** R21_QUBO_VALIDATION
- **目的:** 制約なし二値二次最適化と共通問題の同値性を検証する
- **入力:** 制約なし二値二次最適化・復号器・厳密小規模検証用データ
- **事前条件:** 前工程 `R20_QUBO_FORMULATION` の合格（明示された正常結果遷移は例外）と、入力の存在・ハッシュ値・根拠を確認する。
- **手法:** 限定小規模の列挙等で目的/feasibility/penaltyを比較
- **検証:** 小規模同値性合格・NaN/Infなし・制約欠落なし・復号往復一致ことを独立検査し、実行記録に診断を残す。
- **受入基準:** 小規模同値性合格・NaN/Infなし・制約欠落なし・復号往復一致
- **停止条件:** 共通停止規則と当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義は実行不可、検証不一致・実行異常は不合格。
- **Outputs:** QUBO validation report
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **コマンド:** NOT_RUN — 実行前に採択コマンド・cwd・出力保存先を記録
- **入力のハッシュ値:** NOT_FIXED — 実行前に固定
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **課題:** 未実行。受入基準の未固定項目を実行開始時に解消し、解消不能なら実行不可
- **Decision:** NOT_RUN
- **次に許可される段階:** R22_ISING_CONVERSION（Gate通過時のみ）

<a id="r21_reduced_qubo_validation--initial-reduced-route-ordering-qubo-validation"></a>

## R21_REDUCED_QUBO_VALIDATION — 初期縮約した訪問順序制約なし二値二次最適化検証

<a id="governance-decision--2026-09-10"></a>

### 管理判断 — 2026-09-10

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
- **目的:** 固定済み 縮約した訪問順序 制約なし二値二次最適化が、同じ 固定済み 古典計算 訪問順序 problem と同値であり、次の scoped transformation stageへ渡せることを検証する。
- **Full-電気自動車配送経路問題 境界:** 完全な電気自動車配送経路問題 R20/R21の合格、容量、時間窓、battery/SOC、充電、車両群、または完全な電気自動車配送経路問題 制約なし二値二次最適化の検証を意味しない。

### 前提条件

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

<a id="input-contract"></a>

### 入力 取り決め

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

### 必須 invariants

The following V1--V8 are formal reduced-R21 invariants. One failed invariant fails the reduced R21 gate.

1. **V1 Feasibility:** `argmin H_QUBO subseteq F`.
2. **V2 Objective equivalence:** the best feasible QUBO route cost equals the classical route-ordering optimum.
3. **V3 Route-set equivalence:** all optimal route identities, including ties, match the exact reference.
4. **V4 Energy consistency:** direct squared and expanded QUBO energies agree within the specified energy tolerance.
5. **V5 Decode/re-encode:** every valid QUBO minimum decodes deterministically and re-encodes to the same assignment.
6. **V6 Input/provenance integrity:** source hashes and selected-instance metadata match.
7. **V7 Lambda validity:** `isfinite(lambda)` and strict `lambda > B`; equality is not PASS.
8. **V8 Normalization consistency:** raw and normalized travel-time route ranking and optimal-route set are preserved.

<a id="validation-ladder-and-fixtures"></a>

### 検証 ladder ・ 検証用データ

Only exact-small validation is permitted:

- synthetic n=2;
- synthetic n=3, including unique and tie cases;
- synthetic n=4 when the existing exact-enumeration guard permits it;
- deterministic real-data-derived depot + 2 customers;
- deterministic real-data-derived depot + 3 customers.

The binary state count is `2^(n^2)`. Any enumeration guard is an implementation validation limit only, not a QAOA, QPU, quantum-scalability, or formal research problem-size limit.

Fixtures must cover unique optimum, multiple optimum/tie, asymmetric directed travel time, adversarial penalty behavior, and complete-reachability real-data-derived input. Negative input-contract behavior may reference the existing R20 adapter regression tests when provenance is explicit.

<a id="classical-reference-and-validation-procedure"></a>

### 古典参照解 ・ 検証手順

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

<a id="numerical-comparison-policy"></a>

### Numerical 比較方針

- direct/expanded energy uses the repository `ENERGY_ABS_TOLERANCE`;
- classical route-cost equality uses an explicitly named route-cost tolerance;
- the lambda condition uses strict finite numeric comparison, not `isclose`;
- normalization comparison uses an explicit route-ranking/tie tolerance;
- reproducibility comparison excludes only schema-approved runtime/timestamp fields.

The candidate rule `lambda = B + max(10*e_noise, 1e-6*B)` remains an implementation-policy candidate. Reduced R21 does not require formal adoption of `kappa=10` or `delta_min=1e-6`; it must record the actual applied lambda, bound, and margin metadata.

<a id="pass-and-failure-criteria"></a>

### 合格 ・ 不具合 criteria

Reduced R21 PASS requires input/provenance, complete reachability, lambda bound, classical reference, QUBO construction, V1--V8, deterministic semantic artifact generation, and no CRITICAL/HIGH issue to pass. Partial PASS is not allowed.

Failure reason codes are:

`INPUT_CONTRACT_FAILURE`, `PROVENANCE_FAILURE`, `LAMBDA_BOUND_FAILURE`, `INFEASIBLE_GLOBAL_MINIMUM`, `QUBO_ROUTE_OBJECTIVE_MISMATCH`, `OPTIMAL_ROUTE_SET_MISMATCH`, `DIRECT_EXPANDED_MISMATCH`, `DECODE_FAILURE`, `NORMALIZATION_MISMATCH`, `EXACT_ENUMERATION_GUARD`, `NUMERICAL_TOLERANCE_FAILURE`, and `NONDETERMINISTIC_RESULT`.

<a id="evidence-artifact-and-status"></a>

### 根拠となる成果物 ・ 状態

The artifact shall use the established output convention:

`reproducibility/outputs/traffic_simulation/r21_qubo_validation/<run_id>/`

with at least `validation_results.json` and `manifest.json`. The manifest records source commit, R20 formulation source commit, R20 gate commit, reduced R21 specification/version, input and coefficient hashes, routing provenance, n, `n^2`, state/permutation counts, lambda/bound/margin metadata, classical and QUBO optima, all global minima, feasibility, direct/expanded diagnostics, decode and normalization results, runtime, reason codes, and final status.

- **Status:** `PASS` (formal validation completed for the declared reduced scope)
- **Execution authorization:** `NONE` in this planning record
- **Decision:** reduced R21 governance defined; formal validation result is recorded below
- **Next scoped stage after PASS:** `R22_ISING_CONVERSION` eligibility for the same reduced QUBO only

This reduced branch does not alter the full-EVRP `R21_QUBO_VALIDATION`, whose prerequisite remains full-EVRP `R20_QUBO_FORMULATION = PASS`.

<a id="formal-reduced-r21-validation-result--2026-09-10"></a>

### 正式 縮約した-R21 検証 結果 — 2026-09-10

- **Run:** `reproducibility/outputs/traffic_simulation/r21_qubo_validation/20260910_formal_reduced_v4/`
- **Classification:** `FORMAL_R21_REDUCED_QUBO_VALIDATION`
- **Result:** all 7 required instances PASS; V1--V8 PASS for every instance; deterministic semantic rerun PASS.
- **Instances:** synthetic n=2 unique; synthetic n=3 unique, tie, and asymmetric; synthetic n=4 adversarial/asymmetric; Routing Baseline-derived depot + 2 customers; Routing Baseline-derived depot + 3 customers.
- **Decision:** `R21_REDUCED_QUBO_VALIDATION = PASS` for `INITIAL_R20_REDUCED_ROUTE_ORDERING_SCOPE_ONLY`.
- **Artifact hashes:** `validation_results.json` SHA-256 `c4baeead366ea2f750cd4ecdd18acc507746dfecd744d0803ed74b5bbb46049f`; `manifest.json` SHA-256 `9a6fc459ef1f5cbf1824b9b0197a2f56f9d67cc88de18bd6bcd8ff7f575691a2`.
- **R22 boundary:** scoped eligibility is recorded for the same reduced QUBO only. R22 execution remains blocked/not executed; full-EVRP R22 eligibility is not granted.
- **Status transition:** `READY_FOR_EXECUTION -> PASS` for this reduced branch only. The full-EVRP `R21_QUBO_VALIDATION` remains `NOT_STARTED`.
- **Scoped next-stage state:** eligible for preparation of the same reduced-QUBO `R22_ISING_CONVERSION`; execution authorization remains `NONE` in this record.

## R22_ISING_CONVERSION — Ising Conversion

- **Stage ID:** R22_ISING_CONVERSION
- **目的:** 制約なし二値二次最適化を同値なIsingへ変換する
- **入力:** 検証済制約なし二値二次最適化・変数順
- **事前条件:** 前工程 `R21_QUBO_VALIDATION` の合格（明示された正常結果遷移は例外）と、入力の存在・ハッシュ値・根拠を確認する。
- **手法:** 二値-spin対応と定数位置補正値を記録し電力量を比較
- **検証:** 小規模全状態で位置補正値込み電力量一致・量子ビット対応が一意ことを独立検査し、実行記録に診断を残す。
- **受入基準:** 小規模全状態で位置補正値込み電力量一致・量子ビット対応が一意
- **停止条件:** 共通停止規則と当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義は実行不可、検証不一致・実行異常は不合格。
- **Outputs:** Ising operator・conversion validation
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **コマンド:** NOT_RUN — 実行前に採択コマンド・cwd・出力保存先を記録
- **入力のハッシュ値:** NOT_FIXED — 実行前に固定
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **課題:** 未実行。受入基準の未固定項目を実行開始時に解消し、解消不能なら実行不可
- **Decision:** NOT_RUN
- **次に許可される段階:** R23_QAOA_AER_EXECUTION（Gate通過時のみ）

<a id="reduced-scope-dependency-boundary"></a>

### 縮約した-範囲依存関係境界

`R21_REDUCED_QUBO_VALIDATION = PASS` may establish eligibility only for a correspondingly scoped `R22_ISING_CONVERSION` of the same initial reduced route-ordering QUBO. It does not authorize full-EVRP Ising conversion, QAOA execution, or completion of the full R22 stage.

<a id="r22_reduced_ising_conversion--initial-reduced-route-ordering-ising-conversion"></a>

## R22_REDUCED_ISING_CONVERSION — 初期縮約した訪問順序 Ising Conversion

<a id="governance-decision--2026-09-10-1"></a>

### 管理判断 — 2026-09-10

The scoped branch after the reduced R21 gate is formally identified as:

`R22_REDUCED_ISING_CONVERSION`

It applies only to the exact frozen QUBO validated by `R21_REDUCED_QUBO_VALIDATION` for `INITIAL_R20_REDUCED_ROUTE_ORDERING_SCOPE_ONLY`. It is a separate branch of the execution plan and does not replace or relax the full-EVRP `R22_ISING_CONVERSION`.

```text
Full-EVRP path:
  Full R20 PASS -> Full R21 PASS -> R22_ISING_CONVERSION

Initial reduced path:
  R21_REDUCED_QUBO_VALIDATION = PASS
    -> R22_REDUCED_ISING_CONVERSION
    -> scoped preparation eligibility for the same reduced Ising Hamiltonian
```

<a id="formal-purpose-and-boundary"></a>

### 正式目的 ・ 境界

The purpose is to convert the R21-validated reduced QUBO into an Ising Hamiltonian and establish, with the constant offset retained, that the two energy landscapes are mathematically equivalent.

This stage is not QAOA performance evaluation and does not validate or authorize:

- full-EVRP Ising conversion;
- QAOA execution or ansatz selection;
- quantum hardware execution;
- quantum advantage or scaling claims;
- any QUBO other than the frozen R21 reduced QUBO.

<a id="prerequisite-and-authoritative-input"></a>

### 前提条件 ・ 正本の入力

All of the following are mandatory:

- `R21_REDUCED_QUBO_VALIDATION = PASS`;
- scope exactly `INITIAL_R20_REDUCED_ROUTE_ORDERING_SCOPE_ONLY`;
- R21 validation-results hash and manifest hash are available;
- the R21 QUBO coefficient hash matches the supplied constant, linear, and quadratic coefficients;
- row-major variable ordering and `n^2` logical-variable count are unchanged;
- lambda, bound, normalization, and source provenance metadata are carried forward from R21.

R22 must not rebuild or symmetrize the QUBO independently. The authoritative input is the frozen R21 coefficient representation:

`E_Q(x) = C + sum_i a_i x_i + sum_(i<j) b_ij x_i x_j`.

### 二値-への-spin 規約

No existing repository Ising converter establishes a conflicting convention. The reduced R22 authority is therefore fixed as:

`x_i = (1 - s_i) / 2`,

where `x_i in {0,1}` and `s_i in {-1,+1}`. The inverse is `s_i = 1 - 2x_i`.

The convention, variable order, and spin index are preserved one-to-one from the R20/R21 row-major order. A later Qiskit utility may be used as an independent check, but it must not redefine this mathematical convention.

### 数理 conversion

Substitution gives:

`E_Q(x(s)) = C_I + sum_i h_i s_i + sum_(i<j) J_ij s_i s_j`,

where:

`C_I = C + (1/2) sum_i a_i + (1/4) sum_(i<j) b_ij`,

`h_i = -(1/2) a_i - (1/4) sum_(j != i) b_(min(i,j),max(i,j))`,

`J_ij = b_ij / 4` for `i < j`.

The derivation uses:

`x_i x_j = (1 - s_i - s_j + s_i s_j) / 4`.

The full Ising energy includes `C_I`. For representations that omit the constant, the artifact must retain the explicit offset and require:

`E_Q(x) = E_Ising_without_offset(s) + C_I`.

Omitting `C_I` from a later operator representation is permitted only after this equality has been validated and recorded.

### 必須 invariants

The reduced R22 gate requires all of the following. One mandatory invariant failure is a gate failure.

1. **I1 Conversion algebra:** coefficients follow the documented substitution and formula.
2. **I2 Variable mapping:** binary-to-spin and spin-to-binary mappings are bijective and roundtrip-safe.
3. **I3 Energy equivalence:** every required mapped state satisfies `E_Q(x) = E_Ising_full(s)` within tolerance.
4. **I4 Global optimum equivalence:** mapped QUBO and Ising global-minimum sets are identical.
5. **I5 Route equivalence:** Ising minima decode to the same route set as the R21 QUBO minima.
6. **I6 Tie preservation:** all degenerate global minima and optimal route ties are retained.
7. **I7 Coefficient/provenance integrity:** Ising coefficients derive from the exact frozen R21 coefficient hash and source lineage.
8. **I8 Deterministic conversion:** identical frozen QUBO input produces identical semantic Ising output.

Feasibility remains defined by the R20 binary validator and decoder. Ising conversion does not introduce a new feasibility definition, repair operation, or unreachable-transition constraint.

<a id="exact-validation-ladder-and-spectrum-policy"></a>

### 厳密検証 ladder ・ spectrum 方針

The R22 validation ladder reuses the R21 formal instances:

- synthetic n=2 unique;
- synthetic n=3 unique;
- synthetic n=3 tie;
- synthetic n=3 asymmetric;
- synthetic n=4 adversarial/asymmetric when the existing guard permits it;
- Routing Baseline-derived n=2;
- Routing Baseline-derived n=3.

For n=2 and n=3, all `2^(n^2)` binary/spin states are mandatory. For n=4, full-state comparison is required when the existing exact-enumeration guard permits it. The state count is a validation-computation quantity only, not a QAOA, QPU, or formal problem-size limit.

For each mapped state, record QUBO energy, full Ising energy, difference, and binary/spin assignment. Exact-small validation must compare global minima, route sets, ties, and state-energy ordering. The required numerical condition is `max_abs_energy_mismatch <= ENERGY_ABS_TOLERANCE` (or a separately approved R22 energy tolerance); a tolerance must not hide sign or factor-of-two errors.

<a id="numerical-and-serialization-policy"></a>

### Numerical ・ 直列化方針

- coefficient transformation uses an explicitly named coefficient tolerance;
- state-energy equality uses an explicitly named energy tolerance;
- global-optimum and tie equality uses the same documented energy comparison policy;
- zero coefficients are not silently rounded or removed before hash/equivalence validation;
- serialization uses canonical ordering and sufficient precision to reproduce coefficients;
- constant offset is always serialized, even if an operator consumer later omits it.

### Mutation-resistant 確認

The implementation test plan must detect:

- wrong sign in `x=(1 +/- s)/2`;
- factor-of-two errors in `J_ij`;
- missing linear contributions from quadratic couplers;
- missing or incorrect `C_I`;
- duplicated or reversed couplers;
- row-major index corruption;
- accidental coefficient symmetrization;
- omitted QUBO constant.

Qiskit `to_ising()` or an equivalent utility may be used only as an independent reference check after the custom mathematical converter is tested. It is not the specification authority.

<a id="artifact-contract"></a>

### 成果物取り決め

Formal reduced R22 output shall use:

`reproducibility/outputs/traffic_simulation/r22_ising_conversion/<run_id>/`

with at least:

- `conversion_results.json`;
- `manifest.json`.

The artifact records R21 artifact/results hashes, QUBO coefficient hash, binary-to-spin convention, QUBO constant, Ising constant `C_I`, explicit transformation offset, `h`, `J`, Ising coefficient hash, logical-spin count, state count, maximum energy mismatch, optimum/tie/route comparisons, I1--I8, failure reasons, runtime, and source/code hashes.

<a id="failure-reasons-and-pass-criteria"></a>

### 不具合 reasons ・ 合格 criteria

Failure reason codes:

`R21_INPUT_NOT_PASS`, `QUBO_HASH_MISMATCH`, `SPIN_MAPPING_FAILURE`, `ISING_COEFFICIENT_MISMATCH`, `CONSTANT_OFFSET_MISMATCH`, `ENERGY_EQUIVALENCE_FAILURE`, `GLOBAL_OPTIMUM_MISMATCH`, `TIE_SET_MISMATCH`, `ROUTE_SET_MISMATCH`, `INDEX_MAPPING_FAILURE`, `NUMERICAL_TOLERANCE_FAILURE`, and `NONDETERMINISTIC_RESULT`.

Scoped R22 PASS requires all of the following:

- R21 reduced PASS and provenance confirmation;
- exact QUBO hash match;
- algebra and convention validation;
- mapping roundtrip PASS;
- coefficient and constant-offset validation PASS;
- full required state energy equivalence PASS;
- global optimum, tie, and route-set equivalence PASS;
- deterministic semantic artifact PASS;
- no CRITICAL/HIGH issue.

Partial PASS is not allowed.

<a id="status-and-next-stage-boundary"></a>

### 状態 ・ 次の-段階境界

- **Status:** `PASS` (formal conversion completed for the declared reduced scope)
- **Execution authorization:** `R22_REDUCED_ISING_CONVERSION` formal validation completed; no QAOA authorization
- **Decision:** reduced R22 formal conversion passed for the exact frozen R21 QUBO only
- **After scoped R22 PASS:** preparation eligibility for a same-reduced-Ising QAOA design may be considered in a separate decision.

<a id="formal-reduced-r22-conversion-result--2026-09-10"></a>

### 正式縮約した-R22 conversion 結果 — 2026-09-10

- **Run:** `reproducibility/outputs/traffic_simulation/r22_ising_conversion/20260910_formal_reduced_v1/`
- **Classification:** `FORMAL_R22_REDUCED_ISING_CONVERSION`
- **Result:** all 7 required instances PASS; I1--I8 PASS for every instance; deterministic semantic rerun PASS.
- **State coverage:** n=2: 16 states; n=3: 512 states; n=4: 65,536 states. Full required state comparison was performed within the existing guard.
- **Energy equivalence:** zero mismatches for all states; maximum absolute mismatch approximately `5.684341886080802e-14`, within the recorded energy tolerance.
- **Minima/ties/routes:** QUBO and Ising global-minimum sets, tie counts, and decoded route sets agree for all required instances.
- **Artifact hashes:** `conversion_results.json` SHA-256 `1b6015bcaf38d58fb98a743f47346be9e68601c0b0f7c09567ca77186ea26cea`; `manifest.json` SHA-256 `2bd1bed556b265cc4b6f555497f78e1e432c8d22dabfcccb722fe0faf0da46d9`.
- **Lineage:** exact R21 artifact `20260910_formal_reduced_v4` and its recorded validation-results/manifest hashes were consumed unchanged; source conversion implementation commit was `8ae79fcf30ada7c1a73cec08d5d70291b7667632`.
- **Boundary:** this PASS applies only to `INITIAL_R20_REDUCED_ROUTE_ORDERING_SCOPE_ONLY`; it is not full-EVRP validation and does not authorize QAOA execution.

This section does not alter the full-EVRP `R22_ISING_CONVERSION`, whose prerequisite remains full-EVRP `R21_QUBO_VALIDATION = PASS`.

<a id="r23_qaoa_aer_execution--qaoa--qiskit-aer-execution"></a>

## R23_QAOA_AER_EXECUTION — 量子近似最適化アルゴリズム / Qiskit Aer 実行

- **Stage ID:** R23_QAOA_AER_EXECUTION
- **目的:** 資源 事前確認後にAerで候補標本を得る
- **入力:** Ising・p/shots/optimizer設定・導入検証済環境
- **事前条件:** 前工程 `R22_ISING_CONVERSION` の合格（明示された正常結果遷移は例外）と、入力の存在・ハッシュ値・根拠を確認する。
- **手法:** 資源見積と上限照合後に1run実行、bitstring/counts/終了理由を記録
- **検証:** 事前確認合格・正常終了・回路/乱数の種/実行時間保存ことを独立検査し、実行記録に診断を残す。
- **受入基準:** 事前確認合格・正常終了・回路/乱数の種/実行時間保存
- **停止条件:** 共通停止規則と当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義は実行不可、検証不一致・実行異常は不合格。事前資源 ceiling到達はLIMIT_REACHED、正常な解未発見はRESULT_INFEASIBLE。
- **出力:** 回路・未加工 標本・resource/optimizer 記録
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **コマンド:** NOT_RUN — 実行前に採択コマンド・cwd・出力保存先を記録
- **入力のハッシュ値:** NOT_FIXED — 実行前に固定
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **課題:** 未実行。受入基準の未固定項目を実行開始時に解消し、解消不能なら実行不可
- **Decision:** NOT_RUN
- **次に許可される段階:** R24_QUANTUM_SOLUTION_DECODE（Gate通過時のみ）

<a id="r23_reduced_qaoa_aer_execution--initial-reduced-route-ordering-qaoaaer-experiment"></a>

## R23_REDUCED_QAOA_AER_EXECUTION — 初期縮約した訪問順序 QAOA/Aer 実験

<a id="governance-decision-and-scope"></a>

### 管理判断 ・ 範囲

The reduced branch is explicitly identified as `R23_REDUCED_QAOA_AER_EXECUTION`. It applies only to the exact Ising Hamiltonians that passed `R22_REDUCED_ISING_CONVERSION` for `INITIAL_R20_REDUCED_ROUTE_ORDERING_SCOPE_ONLY`. It does not replace or relax the full-EVRP `R23_QAOA_AER_EXECUTION`.

`Aer simulation limit != quantum hardware limit` and `Aer runtime != future QPU runtime`. This stage is a software-simulator experiment and does not establish hardware scalability, quantum advantage, or production optimization performance.

<a id="purpose-and-prerequisite"></a>

### 目的 ・ 前提条件

The purpose is to execute a frozen, reproducible baseline QAOA experiment on the validated reduced Ising Hamiltonian and measure solution quality, feasibility, ground-state sampling behavior, and simulator timing. The mandatory prerequisite is reduced R22 PASS with matching artifact/hash, Ising coefficient hash, source lineage, and scope. The exact lambda and Ising coefficients are carried forward unchanged from R22.

<a id="experiment-layers"></a>

### 実験層

- **Implementation smoke:** API, circuit, backend, and metric serialization check; non-authoritative.
- **Pilot:** smallest reduced instances and `p=1` to check termination, runtime, resource guards, and n=4 feasibility; not formal performance evidence.
- **Formal baseline:** only the pre-frozen configuration below; no post-hoc parameter changes.
- **Later sensitivity study:** p, shots, optimizer, initialization, and repetition comparisons are separate and not part of this stage definition.

<a id="authoritative-input"></a>

### 正本の入力

Each run must carry the R22 artifact path and hashes, R22 PASS status/commit, instance ID, `n`, `n^2` logical qubits, row-major variable order, binary-spin convention, full Ising constant, `h`, `J`, Ising coefficient hash, QUBO coefficient hash, frozen lambda and bound metadata, normalization metadata, R20/R21 provenance, and exact R21/R22 ground-state states/routes. The Hamiltonian must not be re-normalized, symmetrized, reordered, or otherwise modified in R23.

<a id="baseline-design-freeze"></a>

### 基準 設計 固定

The initial reduced formal baseline is defined as follows; it is a study-design specification, not an execution record or QAOA parameter-optimization result.

| Item | Frozen baseline design |
|---|---|
| Formal instances | synthetic n=2 unique; synthetic n=3 unique, tie, asymmetric; Routing Baseline-derived n=2 and n=3 |
| Optional n=4 | pilot/resource-gated only; not required for formal baseline PASS |
| QAOA depth | `p in {1,2,3}` |
| Mixer | standard transverse-field X mixer, `H_M = -sum_i X_i` |
| Initial state | `|+>^Q` |
| Parameter order | `[gamma_1,...,gamma_p,beta_1,...,beta_p]` |
| Optimizer | COBYLA, one fixed derivative-free optimizer; comparison with other optimizers is later work |
| maxiter | 100 optimizer iterations per configuration |
| Initialization | deterministic fixed point: all gamma and beta parameters `0.1` |
| Repetitions | 1 per configuration in exact-expectation baseline |
| Expectation mode | exact/statevector expectation on CPU Aer; finite shots are excluded from this baseline |
| Simulator seeds | record `seed_simulator=17` and transpiler seed `17` where the selected API accepts them |
| Formal shots | none; later candidate study may use 256/1024/4096 |

The formal baseline contains 6 instances x 3 depths = **18 optimizer runs**. The n=4 pilot is not included in that count. A technical smoke result is never substituted for a formal baseline result.

The subsequent research design-freeze record `R23_FORMAL_EXPERIMENT_DESIGN_V1`
supersedes the preceding historical 18-run baseline proposal for any future
formal execution. The adopted Experiment A matrix is 5 Routing Baseline-derived
complete-reachability instances for each of `n={2,3,4}` crossed with
`p={1,2,3}`, for **45 runs**. This supersession is a design decision only; no
formal run has been executed.

<a id="backend-and-environment-policy"></a>

### 計算方式 ・ 環境方針

The implemented CPU baseline path uses Qiskit 2.5.2 and Qiskit Aer 0.17.2 in the isolated Python 3.11.16 `evrp-quantum-temp` environment (with qiskit-optimization 0.7.0 and qiskit-algorithms 0.4.0 available). It constructs the validated diagonal cost operator as `SparsePauliOp`, the governed ansatz with `QAOAAnsatz`, exact deterministic expectations/distributions with `Statevector`, CPU-Aer transpilation with `AerSimulator(method="statevector", device="CPU")`, and optimization through SciPy COBYLA. The full R22 constant is restored in reported energies. GPU execution is deferred and is not part of this baseline.

<a id="resource-and-execution-guards"></a>

### 資源 ・ 実行 guards

The following are software-simulation guards only: maximum 16 logical qubits for the initial reduced baseline; maximum `p=3`; maximum 100 optimizer iterations per configuration; maximum 300 objective evaluations per configuration; maximum 600 seconds wall time per run; existing 8 GiB estimated-memory ceiling and available-memory preflight. Guard hits are recorded as `RESOURCE_GUARD_STOP`/`LIMIT_REACHED`; they are not quantum technology or formal problem-size limits. No OOM/crash probing is permitted.

<a id="required-metrics"></a>

### 必須評価指標

The exact R21/R22 reference is recorded per run: ground-state energy, optimal binary/spin states, optimal routes, and exact route objective. Sample bitstrings are classified with the existing binary validator without repair. For finite samples, `P_feasible=N_valid/N_total`; for exact distributions, feasible probability mass is recorded separately. `P_opt` sums probability over all exact optimal states, including ties. Best feasible route, objective, absolute/relative optimality gap, expectation energy/gap, minimum observed energy, ground-state probability, and variance are recorded. Technical records include initial/final parameters, objective history, iterations, function evaluations, termination, logical qubits, p, parameter count, circuit/transpiled depth, gate counts, and decomposed timing where measurable.

Relative gap is `gap_abs/max(|f_exact|, epsilon_ref)`, with an explicitly recorded positive `epsilon_ref`. No feasible sample is represented as null with an explicit status, not as a fabricated objective value.

<a id="run-classification-and-pass-interpretation"></a>

### 実行分類 ・ 合格解釈

Run classes are `OPTIMAL_FOUND`, `FEASIBLE_SUBOPTIMAL`, `NO_FEASIBLE_SOLUTION`, `OPTIMIZER_FAILURE`, `BACKEND_FAILURE`, `NUMERICAL_FAILURE`, `RESOURCE_GUARD_STOP`, and `PROVENANCE_FAILURE`. Low QAOA solution quality is valid scientific data and is not, by itself, an implementation FAIL. Reduced R23 PASS requires the frozen protocol to execute completely, use the exact R22 input, pass provenance/metric/artifact checks, preserve deterministic semantics, and record all required runs. Invalid provenance, missing runs, backend/numerical failure, or non-reproducibility causes FAIL.

<a id="artifact-and-design-freeze-contract"></a>

### 成果物 ・ 設計-固定取り決め

Before execution, a frozen config must be stored under `reproducibility/outputs/traffic_simulation/r23_qaoa_aer/<run_id>/` with `experiment_config.json`, `run_results.json`, `summary.json`, and `manifest.json`. The manifest records all R20--R22 lineage and hashes, Ising coefficients, exact software/environment versions, backend/method/device, seeds, config/code hashes, resource guards, output hashes, and tracked-worktree cleanliness. Runtime/timestamps are non-semantic; configuration, coefficients, states, routes, metrics, classifications, and invariant results are semantic.

<a id="status-and-downstream-boundary"></a>

### 状態 ・ 下流境界

- **Status:** `FORMAL_EXPERIMENT_DESIGN_FROZEN_READY_TO_RUN` (design: `reproducibility/config/traffic_simulation/r23_formal_experiment/20260911_r23_formal_v1.json`; formal 45-run Experiment A not executed)
- **Design authority:** `R23_FORMAL_EXPERIMENT_DESIGN_V1`; historical six-run pilot remains immutable evidence and is not retroactively upgraded.
- **Execution authorization:** `NONE`
- **After reduced R23 PASS:** scoped `R24_QUANTUM_SOLUTION_DECODE` eligibility may be considered for the same reduced branch; the existing full-EVRP path is unchanged.
- **Full-EVRP:** full R20 remains `BLOCKED`, full R21 remains `NOT_STARTED`, and full R23 is not authorized by this reduced definition.

Implementation lineage: governance commit `5f88e6ae242357c784b246d7740a006f483e7798`; runner implementation `3a4066b661faaa554bdb646d84716461b56cb`, with metric/ordering corrections `f99f7fc0840fad38985c094efc5e9bf78214263c` and `09c581b5017563ecef6252604705b8c6534f6f11`. The implementation smoke is non-authoritative and does not satisfy the pilot or formal baseline gate.

The prior CPU Aer and Qiskit environment reports remain `TEMPORARY_DIAGNOSTIC` evidence only. They are not formal R23 results, performance benchmarks, or hardware projections.

<a id="r24_quantum_solution_decode--quantum-solution-decode"></a>

## R24_QUANTUM_SOLUTION_DECODE — 量子計算解復号

- **Stage ID:** R24_QUANTUM_SOLUTION_DECODE
- **目的:** ビット列を共通経路表現へ変換する
- **入力:** 未加工 標本・encoding/decoder版・I_s
- **事前条件:** 前工程 `R23_QAOA_AER_EXECUTION` の合格（明示された正常結果遷移は例外）と、入力の存在・ハッシュ値・根拠を確認する。
- **手法:** ビット順序/aux/離散化を照合し未加工 復号、修復は別保存
- **検証:** 全標本の復号結果または理由を記録、黙示修復なしことを独立検査し、実行記録に診断を残す。
- **受入基準:** 全標本の復号結果または理由を記録、黙示修復なし
- **停止条件:** 共通停止規則と当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義は実行不可、検証不一致・実行異常は不合格。
- **Outputs:** decoded quantum routes・decode report
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **コマンド:** NOT_RUN — 実行前に採択コマンド・cwd・出力保存先を記録
- **入力のハッシュ値:** NOT_FIXED — 実行前に固定
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **課題:** 未実行。受入基準の未固定項目を実行開始時に解消し、解消不能なら実行不可
- **Decision:** NOT_RUN
- **次に許可される段階:** R25_COMMON_INDEPENDENT_VALIDATION（Gate通過時のみ）

<a id="r25_common_independent_validation--common-independent-validation"></a>

## R25_COMMON_INDEPENDENT_VALIDATION — Common 独立検証

- **Stage ID:** R25_COMMON_INDEPENDENT_VALIDATION
- **目的:** 両手法を同一検証器で独立比較可能にする
- **入力:** 古典解・量子復号・同じI_sと検証器版
- **事前条件:** 前工程 `R24_QUANTUM_SOLUTION_DECODE` の合格（明示された正常結果遷移は例外）と、入力の存在・ハッシュ値・根拠を確認する。
- **手法:** 両解で13制約を再計算、不正 標本と検証器 誤りを分離
- **検証:** 検証器正常・制約別判定と実行可能件数・終了理由が保存済ことを独立検査し、実行記録に診断を残す。
- **受入基準:** 検証器正常・制約別判定と実行可能件数・終了理由が保存済
- **停止条件:** 共通停止規則と当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義は実行不可、検証不一致・実行異常は不合格。
- **出力:** 共通検証 報告
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **コマンド:** NOT_RUN — 実行前に採択コマンド・cwd・出力保存先を記録
- **入力のハッシュ値:** NOT_FIXED — 実行前に固定
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **課題:** 未実行。受入基準の未固定項目を実行開始時に解消し、解消不能なら実行不可
- **Decision:** NOT_RUN
- **次に許可される段階:** R26_DEMAND_FULFILLMENT_EVALUATION（Gate通過時のみ）

<a id="r26_demand_fulfillment_evaluation--demand-fulfillment-evaluation"></a>

## R26_DEMAND_FULFILLMENT_EVALUATION — 需要需要充足の評価

- **Stage ID:** R26_DEMAND_FULFILLMENT_EVALUATION
- **目的:** 配送件数配送需要充足率と追加荷量配送需要充足率を計算する
- **入力:** 共通検証・I_s全要求
- **事前条件:** 前工程 `R25_COMMON_INDEPENDENT_VALIDATION` の合格（明示された正常結果遷移は例外）と、入力の存在・ハッシュ値・根拠を確認する。
- **手法:** 検証済み完了だけを分子とし未充足を含む固定分母で算出
- **検証:** 0<=配送需要充足率<=1・重複なし・分母一致・不正解を実行可能扱いしないことを独立検査し、実行記録に診断を残す。
- **受入基準:** 0<=配送需要充足率<=1・重複なし・分母一致・不正解を実行可能扱いしない
- **停止条件:** 共通停止規則と当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義は実行不可、検証不一致・実行異常は不合格。
- **出力:** 配送需要充足率・完了/未充足・電力量等指標
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **コマンド:** NOT_RUN — 実行前に採択コマンド・cwd・出力保存先を記録
- **入力のハッシュ値:** NOT_FIXED — 実行前に固定
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **課題:** 未実行。受入基準の未固定項目を実行開始時に解消し、解消不能なら実行不可
- **Decision:** NOT_RUN
- **次に許可される段階:** R27_CLASSICAL_QUANTUM_COMPARISON（Gate通過時のみ）

<a id="r27_classical_quantum_comparison--classicalquantum-comparison"></a>

## R27_CLASSICAL_QUANTUM_COMPARISON — 古典計算–量子計算比較

- **Stage ID:** R27_CLASSICAL_QUANTUM_COMPARISON
- **目的:** 同一条件の品質と計算資源を比較する
- **入力:** 両分岐結果・I_s/hash・共通指標
- **事前条件:** 前工程 `R26_DEMAND_FULFILLMENT_EVALUATION` の合格（明示された正常結果遷移は例外）と、入力の存在・ハッシュ値・根拠を確認する。
- **手法:** 同一instance/seed/入力を照合し予算境界を明示して比較
- **検証:** 入力一致・限界/欠測/非実行を隠さない・全比較指標と量子資源を記録ことを独立検査し、実行記録に診断を残す。
- **受入基準:** 入力一致・限界/欠測/非実行を隠さない・全比較指標と量子資源を記録
- **停止条件:** 共通停止規則と当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義は実行不可、検証不一致・実行異常は不合格。
- **Outputs:** paired comparison report
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **コマンド:** NOT_RUN — 実行前に採択コマンド・cwd・出力保存先を記録
- **入力のハッシュ値:** NOT_FIXED — 実行前に固定
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **課題:** 未実行。受入基準の未固定項目を実行開始時に解消し、解消不能なら実行不可
- **Decision:** NOT_RUN
- **次に許可される段階:** R28_PROBLEM_SIZE_SCALING（Gate通過時のみ）

## R28_PROBLEM_SIZE_SCALING — 問題規模規模拡大

- **Stage ID:** R28_PROBLEM_SIZE_SCALING
- **目的:** n増加に伴う分岐別限界を記録する
- **入力:** 検証済比較手順・n列/乱数の種列・資源 ceiling
- **事前条件:** 前工程 `R27_CLASSICAL_QUANTUM_COMPARISON` の合格（明示された正常結果遷移は例外）と、入力の存在・ハッシュ値・根拠を確認する。
- **手法:** 事前登録した増加列で13〜27の子実行を直列実行・逐次記録
- **検証:** 分岐停止理由・最大成功n・停止n・共通比較範囲を区別ことを独立検査し、実行記録に診断を残す。
- **受入基準:** 分岐停止理由・最大成功n・停止n・共通比較範囲を区別
- **停止条件:** 共通停止規則と当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義は実行不可、検証不一致・実行異常は不合格。事前資源 ceiling到達はLIMIT_REACHED、正常な解未発見はRESULT_INFEASIBLE。
- **出力:** 規模拡大 行列・n_max記録
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **コマンド:** NOT_RUN — 実行前に採択コマンド・cwd・出力保存先を記録
- **入力のハッシュ値:** NOT_FIXED — 実行前に固定
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **課題:** 未実行。受入基準の未固定項目を実行開始時に解消し、解消不能なら実行不可
- **Decision:** NOT_RUN
- **次に許可される段階:** R29_EV_TECHNOLOGY_SCENARIO_EVALUATION（Gate通過時のみ）

<a id="r29_ev_technology_scenario_evaluation--ev-technology-scenario-evaluation"></a>

## R29_EV_TECHNOLOGY_SCENARIO_EVALUATION — 電気自動車 Technology 想定条件評価

- **Stage ID:** R29_EV_TECHNOLOGY_SCENARIO_EVALUATION
- **目的:** 電気自動車技術変化の配送需要充足率効果を評価する
- **入力:** 固定顧客/需要/窓/道路と技術パラメーター表
- **事前条件:** 前工程 `R28_PROBLEM_SIZE_SCALING` の合格（明示された正常結果遷移は例外）と、入力の存在・ハッシュ値・根拠を確認する。
- **手法:** 電池/効率/充電 power/usable 充電率のみ計画通り変更し子実行を直列実行
- **検証:** 固定入力ハッシュ値一致・変更値の根拠・古典量子同条件・不具合可視化ことを独立検査し、実行記録に診断を残す。
- **受入基準:** 固定入力ハッシュ値一致・変更値の根拠・古典量子同条件・不具合可視化
- **停止条件:** 共通停止規則と当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義は実行不可、検証不一致・実行異常は不合格。事前資源 ceiling到達はLIMIT_REACHED、正常な解未発見はRESULT_INFEASIBLE。
- **出力:** 技術想定条件比較
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **コマンド:** NOT_RUN — 実行前に採択コマンド・cwd・出力保存先を記録
- **入力のハッシュ値:** NOT_FIXED — 実行前に固定
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **課題:** 未実行。受入基準の未固定項目を実行開始時に解消し、解消不能なら実行不可
- **Decision:** NOT_RUN
- **次に許可される段階:** R30_FINAL_REPRODUCIBILITY_VALIDATION（Gate通過時のみ）

<a id="r30_final_reproducibility_validation--final-reproducibility-validation"></a>

## R30_FINAL_REPRODUCIBILITY_VALIDATION — 最終再現性検証

- **Stage ID:** R30_FINAL_REPRODUCIBILITY_VALIDATION
- **目的:** 全結果を第三者が追跡・再現可能にする
- **入力:** 本書の全実行記録・source/schema/config/code/environment・成果物
- **事前条件:** 前工程 `R29_EV_TECHNOLOGY_SCENARIO_EVALUATION` の合格（明示された正常結果遷移は例外）と、入力の存在・ハッシュ値・根拠を確認する。
- **手法:** hash/link/schema監査・同乱数の種再現・浮動誤差とstochastic範囲の確認
- **検証:** 全主張に証拠・再現コマンド・版・判定、未実行/限界を明示ことを独立検査し、実行記録に診断を残す。
- **受入基準:** 全主張に証拠・再現コマンド・版・判定、未実行/限界を明示
- **停止条件:** 共通停止規則と当該Data/Routing/Instance/Solver Gateを適用。必須入力・仕様未定義は実行不可、検証不一致・実行異常は不合格。
- **出力:** 最終成果物一覧・再現性検証
- **Status:** NOT_STARTED
- **Started At:** NOT_STARTED
- **Completed At:** NOT_STARTED
- **コマンド:** NOT_RUN — 実行前に採択コマンド・cwd・出力保存先を記録
- **入力のハッシュ値:** NOT_FIXED — 実行前に固定
- **Output Hashes:** NOT_RUN
- **Software Versions:** NOT_FIXED
- **Results:** NOT_RUN
- **Validation Results:** NOT_RUN
- **課題:** 未実行。受入基準の未固定項目を実行開始時に解消し、解消不能なら実行不可
- **Decision:** NOT_RUN
- **次に許可される段階:** なし — 最終凍結・終了（Gate通過時のみ）

# 環境

監査時Python 3.11.15、NumPy 2.2.5、pandas 2.2.3、pyarrow 19.0.1、OR-Tools 9.12.4544、pytest 8.3.3。SUMO/duarouter 二値は.local/sumo-1.24.0/bin。Qiskit/Aerとsumolib/traci distribution 付随情報なし。画像処理装置は未調査・不使用。Git 変更記録は`ae0c3906a94fce00353d9f61b33462e9d1a50344`、監査開始時DIRTY。既存の利用者変更を保持した。

<a id="audit-commands"></a>

# 監査 コマンド

監査中に実行した読取り専用検査（cwdはリポジトリの最上位）:

```bash
git status --short
./research portal check
./research demand validate
.local/sumo-1.24.0/bin/sumo --version
free -b
lscpu
cat /proc/self/cgroup
```

追加監査ではPython csv/zipfile/json/hashlibで候補行数・識別子・WKT座標・統計成果物一覧全ファイル ハッシュ値・census ZIP ハッシュ値を照合し、importlib.付随情報でpackage 版とcgroupのmemory.max/high・cpu.maxを調べた。原本の再生成・書換えは行っていない。再確認用の自己完結コマンド:

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

候補の座標範囲はlon 139.65317823652003〜139.75249792175939、lat 35.54015044054699〜35.61236590455608。座標参照系・住宅分類・メッシュ全件対応の正式受入はR03で別途行う。

監査記録は作業用/tmpにあり永続的な唯一の証拠とはしない。本書の検査結果・コマンド・ハッシュ値を実行記録とする。

- `/tmp/evrp_initial_portal.log` SHA-256: `14c01ca818965ba33ea16826576c0f3ed3975db0a7ce7a644baad9c35e16fece`
- `/tmp/evrp_initial_demand.log` SHA-256: `380d2d662c03c8374abb0b98b007c7a666d4c7675f2a31525f961264dfeb3f81`

<a id="input-hash-ledger"></a>

# 入力ハッシュ値台帳

以下は今回の監査入力の実ファイルハッシュ値（SHA-256）。既存成果物はこのハッシュ値を維持する。

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

<a id="md-validation"></a>

# MD 検証

2026-09-09 R03再実行後検証: 合格。30工程の順序、R01/R02の合格、R03の実行不可継続、R04以降未実行、13 必須制約、段階 記録の21欄、Global/Data/Routing/Instance/Solver停止条件、資源 ceiling、入力ハッシュ値台帳、内部軽量マークアップ文書リンクを検査した。R03の新規接続表は実行-scoped 保存先へ出力し、既存未加工・候補コンマ区切り形式・受入network/mappingは変更していない。本書の自己ハッシュ値は文書内に埋め込まない。
2026-09-09 R13 実行器 restoration and 実行 検証: 合格。既存SUMO/sumolibのみで実行器を固定保存先へ実装し、同一道路区間順方向・逆位置補正値・異なる道路区間部分区間・directed 到達不能の検証用データ 検証を合格した。事前確認後、132 directed 出発地・到着地を計算し、生成132、reachable132、unreachable0、出発地・到着地完全性、位置補正値合算、道路網 ハッシュ値、車種、移動時間 目的、異常値、別実行 出力 ハッシュ値一致を確認した。R14以降は実行していない。
2026-09-09 R14 independent 経路計算 検証: 不合格。R13 出力 ハッシュ値は一致し、132/132 出発地・到着地、端点 網羅率、schema/numeric、配送 connectivity、位置補正値再構成、代表経路、移動時間 目的、車種は合格した。一方、未加工 端点座標のstraight-line 距離をroad 距離が下回る出発地・到着地が44件（最大差約587.76m）あり、対応付け距離約5.26mでは説明できないため、道路網 geometry/edge 長さまたは端点 対応付け整合性の問題候補として停止した。R13 出力は変更せず、R15以降は実行していない。
2026-09-09 R14 空間的な 判定基準 re-監査: 不合格継続。Critical Gateをmapped スーモ positions間の`road_distance >= straight(mapped)-1e-6m`へ変更し、original-coordinate比較をdiagnosticへ移した。132 出発地・到着地を再検証した結果、真 重大な inconsistency 44件、explainable by mapping/geometry 0件、diagnostic 注意事項 only 0件。original-coordinate 注意事項は44件。したがって旧判定の過剰性は修正されたが、mapped-位置基準でもCritical anomalyが残りR14 不合格を維持した。R13 output/network/mappingは変更せず、R15以降は実行していない。
2026-09-09 R14 最上位-cause investigation: ROOT_CAUSE_IDENTIFIED。44件と正常比較10件を同一分解手順で再計算した。R13 距離と独立declared 道路区間 長さ合計は全件一致、位置補正値不整合0、車線 長さ不整合0、internal 道路区間欠落0、座標参照系単位不整合なし。44件全てで道路区間 shape/edge 接続 gapsが確認され、隔たりを含む形状 polylineはmapped-位置直線距離以上となった。最上位 causeは受入済み道路網 geometry/length inconsistency 44件。R13 output/network/mappingは変更せず、R15以降は実行していない。
2026-09-09 道路網 geometry/length re-受入: 合格。run_3_geometry_reacceptanceで既存受入済み道路網を上書きせず、edge/lane 形状をfrom/to 交差点 XYへ接続し、車線 declared 長さを接続後polyline長へ更新した。node/edge/lane差分0、weak connectivity差分0、配送 道路区間数差分0、topology/one-way/permission signature一致、スーモ 負荷 合格、39,956/39,956 対応付け保持、道路区間-ノード 隔たり 0、接続 形状 隔たり 0、車線 declared-vs-形状差0、44 出発地・到着地 diagnosticのmapped-位置下回り0。新正本 V18を記録し、R12/R13/R14は再実行していない。
2026-09-09 R12 V18 re-仕様: 合格。V18 authority/hashを読み込み、端点 12件（配送拠点 1、顧客 10、充電設備 1）、directed 出発地・到着地 132本、道路区間 ID/delivery access/offset範囲、units/null 意味、travel_time_minimizing、R13 コマンド 取り決めを新実行へ固定した。独立検証 合格、R13 経路計算 成果物なしを確認。旧R12 成果物は変更せず、R13以降は実行していない。
2026-09-09 R13 V18 経路計算 computation: 合格。R12 V18固定取り決めを変更せず、V18専用実行で132 directed 出発地・到着地を計算した。生成済み 132、到達可能 132、到達不能 0、経路計算 exception 0。R13 basic 検証はデータ構造、出発地・到着地完全性、道路網 ハッシュ値、車種、保存先 道路区間存在/通行許可、finite/nonnegativeを合格した。R14独立検証は未実行。
2026-09-09 R14 V18 経路計算 検証: 合格。最新R13 出力 ハッシュ値とV18 道路網 ハッシュ値を確認し、132/132 出発地・到着地を独立検証した。mapped-位置 Critical anomaly 0件、original-coordinate diagnostic 注意事項 0件、path/distance/time再計算、位置補正値、配送 接続、移動時間 目的、車線 declared length/shape、車線 接続 形状を合格した。旧V17の44件はV18で解消。R15以降は実行していない。
2026-09-09 R15 common 問題例 integration: 合格。R05〜R14 成果物を読み取り専用で統合し、検証用データ n=10、node/index 順序、12 端点、132 受入済み 出発地・到着地、EV/SOC/charging、項目 出典・来歴をcommon 問題例へ固定した。同一入力の再生成ハッシュ値一致を確認。R16以降は実行していない。
2026-09-09 R16 common 必須制約: 実行不可。13制約のデータ構造・tolerance・検証器 取り決めを生成・検証したが、充電設備再訪問方針が既存仕様で未確定のため停止。R17以降は実行していない。
2026-09-09 R16 充電設備 revisit 解決: 合格。充電設備複数回訪問を許可し、各訪問を独立充電 event、連続eventによる30分上限回避は禁止、R16の恣意的回数上限なしとしてHC12/validator 取り決めを更新した。未解決 意味 0、13制約データ構造、R15整合、共通constraint 版参照を再検証した。R17以降は実行していない。
2026-09-09 R17 OR-Tools 定式化: 実行不可。R15/R16 正本からHC01〜HC13 対応付け、RoutingModel/CP-SAT候補、辞書式目的、R18 実行 contract/output データ構造を新実行へ生成し、構造検証は合格した。R16の無制限充電設備再訪問を有限event モデルへ写す上限、q_i（配送要求件数）と積載量 kgの変換、求解器詳細設定が未採択のためR18へ進めず停止した。OR-Tools 求解器は実行していない。

2026-09-10 一時的 中央処理装置 Aer 規模拡大 diagnostic: `TEMPORARY_DIAGNOSTIC`。作成済みの `evrp-quantum-temp` を変更せず使用し、固定パラメータの疎な 量子近似最適化アルゴリズム-like 状態ベクトル 回路 を q=8,10,12,14,16,18,20,22,24,26,28,30 で実行した。全ケース 合格、最大完了 q=30、停止条件未発生。画像処理装置、最適化処理、正式量子近似最適化アルゴリズム、R21、正式Ising変換、cloud 量子処理装置、縮約した problem正式採択は実施していない。今回の中央処理装置 Aer境界は一時的 diagnosticのみであり、R20 状態=`BLOCKED`、次に許可される段階=`NONE`を変更しない。成果物は `reproducibility/outputs/traffic_simulation/temporary_quantum_diagnostic/20260910_temporary_cpu_aer_scaling_n10/TEMPORARY_CPU_AER_SCALING_BENCHMARK.md`。

2026-09-10 一時的 量子近似最適化アルゴリズム simulation 調査 設計: `TEMPORARY_DIAGNOSTIC`。QAOA/Aerを将来量子ハードウェアそのものではなく、量子最適化アルゴリズムの挙動・計算時間・solution qualityを評価し、将来の量子技術発展想定条件へ接続するソフトウェア simulation 層として設計した。既存中央処理装置 Aer 規模拡大 ベンチマークは`TEMPORARY_IMPLEMENTATION_FEASIBILITY_DIAGNOSTIC`へ再位置づけし、`Aer simulation limit != quantum computing technology limit`を明記した。今回、正式 制約なし二値二次最適化、縮約した problem、正式 Ising、正式 量子近似最適化アルゴリズム、正式運用 simulation、画像処理装置、R21、provider、将来 想定条件 パラメーターは採択・実行していない。R20 状態=`BLOCKED`、次に許可される段階=`NONE`は変更しない。成果物は `reproducibility/outputs/traffic_simulation/temporary_quantum_diagnostic/20260910_temporary_qaoa_simulation_study_design_n10/TEMPORARY_QAOA_SIMULATION_STUDY_DESIGN.md`。

2026-09-10 一時的 Qiskit/Aer 環境 planning: `TEMPORARY_DIAGNOSTIC`。R15 現行 受入済み 問題例、R16 `evrp-common-hard-constraints-v1`、R19 合格、R20 `FORMULATION_ONLY/BLOCKED` を正本として確認した。既存conda/base 環境は変更せず、環境作成・package install・Aer ベンチマーク・job投入は行っていない。HayateのCPU/RAM/GPU/CUDA/conda、既存envのQiskit/Aer状態、保存容量、schedulerコマンドを読み取り専用で確認し、中央処理装置-onlyと画像処理装置-enabledの隔離環境候補、版 compatibilityの未確定点、readiness/failure criteriaを記録した。新規成果物は `reproducibility/outputs/traffic_simulation/temporary_quantum_diagnostic/20260910_temporary_qiskit_aer_environment_plan_n10/` に保存し、既存成果物を上書きしていない。R20 状態は`BLOCKED`のまま、次に許可される段階は`NONE`のまま変更しない。今回の一時的 計画はR20 正式 定式化、縮約した problem、problem 規模、量子計算 architecture、provider、量子近似最適化アルゴリズム パラメーターの採択ではない。
<a id="temporary-diagnostic-qiskitaer-environment-creation-and-smoke-test--2026-09-10"></a>

## 一時的 diagnostic: Qiskit/Aer 環境 creation ・ 動作確認試験 — 2026-09-10

- Scope: temporary diagnostic environment creation and small CPU Qiskit/Aer smoke tests only.
- CPU environment `evrp-quantum-temp` was created in isolation at `/home/takuma/.conda/envs/evrp-quantum-temp`.
- CPU import, Aer capability, CPU statevector, and CPU QAOA-like smoke tests PASSed.
- GPU package pip dry-run resolved a candidate, but GPU environment creation and GPU tests were deferred as `GPU_TEST_DEFERRED_RESOURCE_CONTENTION` because the H100 had approximately 3.3 GiB free and existing `sglang` processes occupied approximately 91.9 GiB. No process was terminated.
- No existing environment was modified.
- No scaling benchmark, formal QAOA experiment, R21, Ising conversion, formal reduced-problem adoption, provider adoption, or R20 formal judgment was performed.
- R20 Status: `BLOCKED` (unchanged). Next Allowed Stage: `NONE` (unchanged).
- Artifact: `reproducibility/outputs/traffic_simulation/temporary_quantum_diagnostic/20260910_temporary_qiskit_aer_environment_smoke_test_n10/TEMPORARY_QISKIT_AER_ENVIRONMENT_SMOKE_TEST.md`
