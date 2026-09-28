# 現行研究パイプライン 実行・正本・検証リファレンス

<a id="2026-09-27-study-b完了method-scaleはblocked"></a>

## 2026-09-27 調査B完了：手法比較の規模は実行不可

[最小構成の電気自動車配送経路問題量子資源静的監査](reproducibility/outputs/traffic_simulation/r24_minimal_evrp_quantum_resource_audit/20260927_v1/MINIMAL_EVRP_QUANTUM_RESOURCE_AUDIT.md)を完了。現行直接表現表現はn5/m1でも34変数・471coupler・raw256GiBで、凍結計算方式上限256メビバイトを超える。METHOD_COMPARISON_SCALE_AUTHORITY=実行不可、選定nなし、S0_QUANTUM_PROTOCOL_RESOURCE_GATE=実行不可。n3/n4は検証・pilot/referenceのまま。MODEL_VALIDATION_SCALE_AUTHORITY=固定済み、想定条件評価の規模は一部固定済み、本実験の第0段階は未許可。

次は物理問題を変えない代替encoding/decompositionの静的比較。調査Aは別途未実行。凍結予備試験/科学成果物/台帳を保持し、新規最適化・Aer・量子近似最適化アルゴリズム・最適化処理評価・回路・回測定は全て0。以下の評価規模再整理段落は調査B前の履歴であり、手法状態と次作業は本段落が優先する。

<a id="2026-09-27評価規模再整理small-nは検証pilot-scope"></a>

## 2026-09-27（評価規模再整理）：小規模は検証・予備試験の範囲

[評価規模正本](reproducibility/outputs/traffic_simulation/r24_evaluation_scale_authority/20260927_v1/EVALUATION_SCALE_AUTHORITY.md)を現在の規模選定正本とする。既存N002/N003/N004はMODEL_VALIDATION_SCALEとして保持し、N004はS0_PILOT、N003はS0_METHOD_IMPLEMENTATION_REFERENCEへ役割を限定する。既存予備試験 第0段階の物理・比較取り決め・成果物は不変。以下の旧S0_SCALE_AUTHORITY=固定済みはsmall-入力 範囲の値であり、本番評価規模を意味しない。

MODEL_VALIDATION_SCALE_AUTHORITY=固定済み、METHOD_COMPARISON_SCALE_AUTHORITY / SCENARIO_EVALUATION_SCALE_AUTHORITY / 本番のS0_SCALE_AUTHORITY=PARTIALLY_FROZEN。候補は既存n20/R01の無作為・集積型親標本の入れ子構成の先頭部分、n=3,4,5,8,10,15,20（3/4診断、5以上本番候補）。最終二規模は未選定で、同じnを強制しない。量子現行直接表現表現はn5/m1からメモリー下限で不適合、想定条件側は古典EVRP/Batteryの新規模証拠が必要。

次は入力受入→調査A（条件を統制した 古典計算 scaling/Battery 関連性）と調査B（最小構成の電気自動車配送経路問題 QUBO/resource監査）→二規模選定→本実験の第0段階 正本更新。調査設計は固定したが今回は実行していない。本実験の第0段階は未許可、全最適化/量子実行0。人口39,930顧客への直接外挿や39,930/n倍の経済換算は禁止する。

<a id="2026-09-27s0物理条件共通contractの部分freeze"></a>

## 2026-09-27：第0段階物理条件・共通取り決めの部分固定

[第0段階 正本](reproducibility/outputs/traffic_simulation/r24_s0_baseline_authority/20260926_v1/S0_BASELINE_AUTHORITY.md)を更新し、S0_PHYSICAL_AUTHORITY / S0_CLASSICAL_PROTOCOL / 共通条件取り決め / 評価指標を固定済み、S0_QUANTUM_PROTOCOLを実行不可、S0_BASELINE_AUTHORITYを一部固定済みとした。想定条件側は既存n4・最大3台の構造予備試験、手法比較は既存n3・1台で、同一規模とは扱わない。人口39,930顧客への代表性は主張しない。

現行はmodel20 kWh・初期100%・最低10%・r=.127 kWh/km。全単純な配送経路の消費上限がusable18 kWhを下回るため、両層で充電設備訪問判断を除外し充電無効を固定した。実車充電出力は未解決のまま、この限定第0段階の阻害要因にはしない。経済正本は別拡張として未着手。

次作業は凍結第0段階条件に対する最小構成の電気自動車配送経路問題 Quantum/QUBO 符号化・同値性・資源監査。旧Exact/MILP 出典は保存Git treeでハッシュ値一致を確認済みだが、将来実行前の復元・実行器接続は別途必要。S0/全最適化/量子実行は未着手。本段落と第0段階正本が、以下の旧日付の第0段階未定義・経済必須記述に優先する。

<a id="2026-09-26minimal-evrp以降の研究順序改訂"></a>

## 2026-09-26：最小構成の電気自動車配送経路問題以降の研究順序改訂

時間窓付き配送経路問題結果と最小構成の電気自動車配送経路問題設計正本は固定済みである。既存経路電気自動車回帰および制御10kWでの充電あり検証は合格、最小構成の電気自動車配送経路問題 古典計算 モデルもN002 WIDEの検証範囲で固定済みである。10kWはCONTROLLED_VALIDATION_CONDITIONであり実車充電性能ではない。実車の実効充電性能はUNRESOLVED/DEFERRED、第0段階は未実行である。

今後の順序・状態の正本は[研究段階ロードマップ](01_research_design/RESEARCH_STAGE_ROADMAP.md)である。電池根拠・条件固定 → 第0段階 → 同一条件の[Classical/Quantum EVRP比較](01_research_design/CLASSICAL_QUANTUM_EVRP_COMPARISON_PLAN.md) → 第0段階評価/固定 → [劣化・技術向上条件の比較](01_research_design/BATTERY_SCENARIO_COMPARISON_PLAN.md) → 電池差と手法差の分離 → 感度分析 → [量子化学/材料R&Dと二系統の統合](01_research_design/BATTERY_QUANTUM_CHEMISTRY_RESEARCH_PIPELINE.md)へ進む。容量/健全度/技術容量・感度設計正本は固定済みである。直近の次milestoneは完全な第0段階条件正本の定義であり、第0段階実行ではない。実車充電出力は未解決である。

以下の日付付き全体計画・状況は各時点の記録を保持する。最小構成の電気自動車配送経路問題以降の順序・状態が異なる場合は上記全体の研究段階計画を優先する。過去の配送需要充足率目的・未配送許容等を現在の凍結最小構成の電気自動車配送経路問題へ導入しない。凍結科学成果物を変更せず、本改訂で新しい科学実行は行わない。

文書識別子: `DOC-RESEARCH-PIPELINE-REFERENCE`
役割: `CURRENT_REFERENCE`
ライフサイクル: `CURRENT`
作成日: `2026-09-03`
最終更新日: `2026-09-27`
現行正本: `reproducibility/indexes/research_repository_index_v17.yml`

状態: `CURRENT PIPELINE REFERENCE`

本書は、各研究工程の「実行 → 成果物 → 正本 → 検証 → 受入 → 次工程」を追跡する現行運用リファレンスである。研究の問い、概念枠組み、段階 1–11のロードマップ、マイルストーンは[研究概要・ロードマップ](RESEARCH_OVERVIEW.md)を参照する。本書は各決定記録、仕様、設定、データ構造、実行、受入成果物への索引であり、それらを置き換える第二の正本ではない。記載と正本成果物が矛盾する場合は、各節の「正本・信頼源」に示す成果物を優先する。

説明、見出し、表項目は日本語で記載する。実在するコマンド、ファイル名、項目名、識別子、`DONE`や`NOT IMPLEMENTED`などの機械可読な状態値は、リポジトリ内の正本表記を保持する。

<a id="b2c-pipeline-20260909"></a>

## B2C配送パイプライン採択記録（2026-09-09）

採択根拠: 2026-09-09の研究責任者による修正版パイプラインの指示。
状態: `ADOPTED`（2026-09-09の全体設計記録）。最小構成の電気自動車配送経路問題以降の将来順序・目的・状態は冒頭の2026-09-26 全体の研究段階計画を優先する。実装・実行・検証・受入の完了は別途証拠で判定する。

主対象は**住宅向け宅配（B2C last-mile 配送）**。古典最適化と量子最適化は、同一の共通配送問題、必須制約、目的の優先順位、独立検証器を使用する。

### 1. 公的統計の収集

- 国勢調査の人口／世帯メッシュを住宅需要の空間代理指標に使用する。
- 第6回東京都市圏物資流動調査「個人のモノの受取調査」を宅配需要・日時指定・受取時間帯の根拠に使用する。
- 必要に応じて全国貨物純流動調査を補助的に使用する。
- 事業所機能調査・経済センサスをB2B需要の主入力とする案は、今回の主パイプラインには採用しない。
- 採用する統計表、年次、取得元、取得日、単位、入力ハッシュ値と変換規則を記録する。調査項目の存在だけでは必要な集計表の取得完了としない。

### 2. 候補配送位置の固定

39,956地点を住宅向け配送先候補の母集団 $C_{\mathrm{all}}$ と定義する。各地点の識別子、座標、道路接続情報を保持する。現在の `building_delivery_stops_scoped.csv` と受入済み対応付けを候補の来歴として参照し、候補集合のハッシュ値を固定する。

この定義は研究上の住宅配送先候補という位置付けであり、各地点が実在住宅として実地確認されたことや、全地点に実験日の注文があることを意味しない。

<a id="3-地点別demand-weightの設定"></a>

### 3. 地点別需要重みの設定

人口または世帯数を住宅宅配需要の空間代理指標とし、各候補地点に非負の相対重み $w_i$ を設定する。これは39,956地点から顧客を抽出する際の選択確率を定める重みであり、配送量 $q_i$ とは別の変数である。メッシュから地点への配賦規則、欠損・ゼロ重みの扱いは生成設定に記録する。

<a id="4-customer集合の抽出"></a>

### 4. 顧客集合の抽出

地域差を保持する層化を行い、需要 Weightに基づく**重み付き非復元抽出**で $C_s\subset C_{\mathrm{all}}$ を生成する。層の定義、層別割当数、抽出方式を固定・保存する。

顧客数 $n=|C_s|$ は固定想定条件ではなく**実験パラメータ**とする。複数random 乱数の種で異なる顧客 設定を生成し、各設定を古典・量子で共有する。

<a id="5-各customerの配送需要を生成"></a>

### 5. 各顧客の配送需要を生成

抽出された顧客は、その実験日に配送要求が発生した住宅配送先として扱う。基準の基本需要単位は**配送件数**とする。必要に応じて荷物個数・重量 $q_i$ を追加し、単位を明記する。配送要求、荷物、顧客、候補地点を区別する。

<a id="6-time-windowを生成"></a>

### 6. 時間窓を生成

「個人のモノの受取調査」の日時指定・受取時間帯分布を使用し、各顧客に合成な配送可能時間帯 $[e_i,l_i]$ を割り当てる。観測された受取時刻から許容時間窓への変換規則、窓幅、指定なしの扱いを明記する。生成乱数の種と設定を共通入力に固定する。

### 7. 作業時間を設定

各住宅で配送作業に必要な時間 $s_i$ を設定する。単位、値または分布、生成方法を記録する。

<a id="8-depotを設定"></a>

### 8. 配送拠点を設定

基準は**単一配送拠点**とする。顧客集合が変わっても原則として同じ配送拠点を使用する。位置・道路接続と、例外的に変更する場合の理由を記録する。

<a id="9-ev条件を設定"></a>

### 9. 電気自動車条件を設定

車両台数、積載容量、電池 容量、電力量 consumption rate、利用可能な 充電率、出発時充電率を設定する。必要に応じて帰着時最低充電率を設定する。容量・需要・エネルギー・充電率の単位と換算方法を固定する。

<a id="10-charging-station条件を設定"></a>

### 10. 充電設備条件を設定

位置、充電出力、電気自動車との互換性、利用可能条件、充電可能量・充電時間の計算方法を設定する。

<a id="11-routing-baselineを計算"></a>

### 11. 経路計算の基準を計算

OSM/SUMO道路ネットワークを使用し、配送拠点・顧客・充電 station間の**必要出発地・到着地**について、道路距離 $d_{ij}$、移動時間 $t_{ij}$、到達可能性 $a_{ij}$ を生成する。39,956地点の全組合せ計算は前提にしない。

<a id="12-routing-baselineを検証"></a>

### 12. 経路計算の基準を検証

必要出発地・到着地の欠落、到達不能pair、一方通行・進入禁止等の通行制約、車種別通行可否、距離・時間の異常値を確認する。入力ハッシュ値、設定値、ソフトウェア 版、再現コマンド、検証結果を保存する。欠落出発地・到着地と既知の到達不能出発地・到着地を区別する。

<a id="13-common-delivery-instanceを生成"></a>

### 13. 共通配送問題を生成

顧客集合、配送需要、時間窓、Service Time、配送拠点、車両、充電 Station、$d_{ij}$、$t_{ij}$、到達可能性を統合し、古典・量子の共通入力として固定する。地点順序、単位、乱数の種、生成設定、入力ハッシュ値と制約定義も保存する。

<a id="14-共通hard-constraintsを定義"></a>

### 14. 共通必須制約を定義

| 制約 | 両手法に共通する条件 |
|---|---|
| 顧客訪問 | 配送する顧客は高々1回だけ訪問する。未充足顧客を許容する。 |
| 配送拠点発着 | 使用車両は配送拠点から出発し、配送拠点へ帰着する。 |
| Flow Conservation | ある地点に入った車両は、同じ車両でその地点から出る。 |
| Subtour禁止 | 配送拠点と接続されていない独立巡回路を禁止する。 |
| Vehicle Assignment | 1つの顧客を複数車両へ重複割当しない。 |
| 容量 | 車両積載上限を絶対に超えない。 |
| 時間窓 | 指定された時間帯内に配送する。 |
| 時間伝播 | 移動 時間、作業時間、待機 時間、充電 時間を一貫して累積する。 |
| Operating time | 1台あたりの最大運行時間を超えない。 |
| Battery / SOC | 走行中に充電率が最低許容値を下回らない。 |
| 初期・終了充電率 | 出発時充電率を定義し、設定した場合は帰着時最低充電率も満たす。 |
| 充電 | 充電可能地点でのみ充電し、電池 容量を超えず、充電量・充電設備 powerに応じた充電時間を考慮する。 |
| 到達可能性 | OSM/SUMO上で実際に移動可能な区間のみ使用する。 |

時間窓が配送開始・完了のどちらに適用されるか、数値許容誤差などの詳細は、両手法で同一の定義に固定してから実行する。

### 15. 古典最適化分岐 — OR-Tools

共通配送問題を入力し、上記必須制約を満たす配送経路を探索して、配送可能顧客と未充足顧客を決定する。**第一目的は配送需要充足の最大化**とし、同一需要充足量なら総距離・総時間等を最小化する。基準では配送件数を第一目的の単位に使用する。第二目的の選択・優先順は実験設定で固定する。

<a id="16-量子最適化分岐--qubo--qaoa"></a>

### 16. 量子最適化分岐 — 制約なし二値二次最適化 / 量子近似最適化アルゴリズム

OR-Toolsと同じ共通配送問題と目的の優先順位を使用する。経路、顧客訪問、車両 割当等を二値 変数で表現し、共通必須制約を制約なし二値二次最適化 罰則項等として定式化する。

制約なし二値二次最適化をIsing ハミルトニアンへ変換し、必要二値 変数数・量子ビット数を記録する。量子近似最適化アルゴリズム 回路を構築して**Qiskit Aer上でsimulation**し、得られたビット列を配送経路へ復号する。Penaltyの存在や低い電力量だけでは必須制約を満たしたと判定しない。

<a id="17-共通validatorによる独立検証"></a>

### 17. 共通検証器による独立検証

OR-Tools解と量子近似最適化アルゴリズム解の双方について、顧客重複、配送拠点発着、Flow conservation、Subtour、車両 割当、容量、時間窓、時間伝播、Operating 時間、充電率（初期・終了条件を含む）、充電 実行可能性、到達可能性を最適化処理とは独立して再計算する。

**Hard Constraint違反解は実行可能 solutionとして扱わない。** 違反内容を保存し、有効解が得られなかった実行を比較結果から隠さない。

### 18. 需要充足率を計算

配送件数ベースの主指標:

$$
DFR_{\mathrm{orders}}=\frac{\text{配送完了件数}}{\text{総配送要求件数}}
$$

荷物量を導入する場合の追加指標:

$$
DFR_{\mathrm{demand}}=\frac{\sum_i q_i y_i}{\sum_i q_i}
$$

$y_i$ は顧客 $i$ の配送完了を表す0/1変数とする。分母は同じ問題例の全配送要求であり、未充足顧客を除外しない。計画解の独立検証による充足と、追加のスーモ配送simulationで確認する充足は別に報告する。配送完了の判定規則と評価時間範囲を共有する。

### 19. 古典最適化と量子最適化を比較

需要 需要充足 Rate、配送完了件数、総走行距離、総移動時間、総運行時間、電力量 consumption、充電回数・時間、計算時間を比較する。移動時間と、作業・待機・充電を含む運行時間を区別する。

量子近似最適化アルゴリズムではさらに量子ビット数、回路 深さ、量子近似最適化アルゴリズム 深さ $p$、回測定、最適化処理 iterationsを記録する。計算時間の測定範囲と実行環境を保存する。

### 20. 問題規模を変化させる

顧客数 $n$ を固定想定条件にせず、実験パラメータとして増加させる。OR-ToolsとQAOA/Aerの両方で実行可能な範囲では、**完全に同一の問題例を直接比較**する。各 $n$ で複数乱数の種を使用し、片方のみ実行可能な規模の結果は直接比較と区別する。

<a id="21-技術scenarioを設定"></a>

### 21. 技術想定条件を設定

電池 容量、電力量 efficiency、充電 power、利用可能な 充電率等を変更する。顧客、需要、時間窓、道路条件は原則固定し、技術条件の効果を評価する。単一配送拠点も原則固定する。変更した値と固定した入力ハッシュ値を保存する。

<a id="22-技術scenario間を比較"></a>

### 22. 技術想定条件間を比較

電気自動車性能変化によって需要 需要充足 Rateがどの程度変化するかを評価する。同時に、古典・量子の解品質と計算資源要求の違いを評価する。Problem Sizeの変化、顧客 設定の変化、技術条件の変化を区別して集計する。

### 旧記録との整合と実装境界

- 旧82,023 `parcel-equivalent/day`、73,547 要求 行、39,956 配送地点数は生成済み成果物の来歴として保持する。今後の主需要単位・顧客数・配送需要充足率分母をこれらの旧集計値で固定しない。
- この採択当時の需要抽出・時間窓・比較器の背景は本節に保持する。最小構成の電気自動車配送経路問題以降の現在の順序・目的・比較手順は冒頭の全体の研究段階計画を優先する。旧比較器やB2B主入力案を必須工程として追加しない。
- 受入済み道路網・対応付けの証拠とハッシュ値は維持する。既存基準需要・配送地点数の`DONE`は、新しいB2C需要生成の完了を意味しない。
- 統計表の選択、層化・配賦の詳細、実験する $n$ と乱数の種、時間窓・作業時間、配送拠点位置、電気自動車・充電の数値、最大運行時間、罰則項・符号化・計算予算は別途設定に固定する。ここでは値を創作しない。
- 後続A～Q節は現行の実装・成果物・コマンドの台帳を兼ねる。旧設計に由来する記述は本節の採択内容に従って読み替え、未実装実行器を実装済みと扱わない。

## 更新方針

次の場合に本書を更新する。

- 現在の工程、直ちに行う作業、またはマイルストーンが変わる。
- 本番パイプライン、成果物、検証器、受入、コマンド操作コマンドが追加・変更される。
- 正本の入力・出力、正本参照先、データ構造、ゲート、引渡し内容が変わる。
- 工程が受入済みまたは完了になる。

履歴上の診断実行や一時的な実験出力は、現行・正本として採択されない限り本書の現行経路へ追加しない。更新時は本書専用検証器とリポジトリ・ポータル 検証器を実行する。

## 状態の定義

| 状態 | 意味 |
|---|---|
| `CURRENT / IMPLEMENTED` | 現在のcheckoutに実装または参照が存在する。 |
| `ACCEPTED` | 受入成果物によって下流利用が許可されている。 |
| `DONE` | 現行ロードマップ上の完了条件を満たしている。 |
| `NEXT` | 現在着手すべき工程。 |
| `PLANNED` | ロードマップにあるが完了していない。 |
| `FUTURE` | 上流ゲートが閉じている将来工程。 |
| `NOT IMPLEMENTED` | 本番コード、実行器、または検証器が存在しない。 |
| `NOT AVAILABLE` | 必要な成果物または結果が存在しない。 |
| `UNRESOLVED` | 研究判断またはパラメーターの固定が必要。 |
| `HISTORICAL` | 過去の記録で現行ではない。 |
| `SUPERSEDED` | 明示的に後継へ置換された。 |

コマンドインターフェースの存在はパイプライン実装を意味しない。`--dry-run`が成功しても成果物の生成・検証・受入を意味しない。

## 現在の研究位置 — 今何をすべきか

| 項目 | 現在の状態 |
|---|---|
| ネットワーク構築 | `DONE` |
| ネットワーク受入 | `ACCEPTED` / `FORMAL_NETWORK_ACCEPTED = true` |
| 現在のマイルストーン | `M1 Network Ready — DONE` |
| 現在の研究工程 | `Routing Baseline — NEXT` |
| 直ちに行う作業 | 配送インスタンス用の経路計算範囲を定義する。 |
| 受入済みネットワークSHA-256 | `4625dbbc150cbcf72964bed0e90a8b33fe03f190ff4264aecaaf89e3aab0e40f` |
| 最初に決める事項 | インスタンス選択・配送先範囲、デポ、配送車両クラス、経路コスト定義を固定する。 |

最初に次を使用する。

```bash
./research status
./research routing inputs
./research routing status
./research pipeline routing --dry-run
```

`39,956 × 39,956`の全組合せ行列は採択済み前提ではない。対象配送インスタンスと必要出発地・到着地集合を先に定義する。

## パイプライン全体図

```text
公的統計 → 39,956候補地点 C_all → Demand Weight w_i
  → 層化・重み付き非復元抽出 C_s（n・複数seed）
  → 配送需要・Time Window・Service Time
  → 単一Depot・EV・Charging Station条件
  → OSM/SUMO Routing Baseline → Routing検証
  → Common Delivery Instance ＋ 共通Hard Constraints
      ├─ OR-Tools ────────────────────────┐
      └─ QUBO → Ising → QAOA → Qiskit Aer ┤
                                          ↓
                                    共通独立Validator
                                          ↓
                             需要充足評価・古典／量子比較
                                          ↓
                           Problem Size・技術Scenario比較
```

この図は2026-09-09採択の今後の設計である。道路網・対応付けは受入済みだが、新しい需要生成と下流比較は未実装・未受入である。

ロードマップの`PLANNED`とポータル実行マップの`FUTURE`が異なる下流工程では、本書は`PLANNED / FUTURE / NOT IMPLEMENTED`と併記する。`PLANNED`は研究計画上の存在、`FUTURE`は現在の実行位置、`NOT IMPLEMENTED`は本番実装の不在を表す。

## A. 外部・オープンデータ

### 目的

入力出典の同一性、取得元、取得日、ハッシュ値、用途、利用制限を固定し、需要と道路網の派生処理へ渡す。

### 現在の状態

`DONE`（管理対象の 出典 入力）。データセットごとの準備状況と再配布可否は同一ではない。

### 開始条件

出典を台帳登録し、取得記録・local 未加工 保存先・ハッシュ値・利用条件を確認する。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| 出典台帳 | source identity / hash | [traffic_simulation_sources.csv](03_data/metadata/traffic_simulation_sources.csv) | `CURRENT` | 出典ごとの用途・制限を記録。 |
| 来歴方針 | raw/derived provenance | [data_provenance.md](03_data/metadata/data_provenance.md) | `CURRENT` | 未加工原本の一部は再配布されない。 |
| 取得記録 | source-specific acquisition evidence | [acquisition README](03_data/metadata/acquisition/README.md) | `CURRENT` | 個別記録から取得条件を追跡する。 |

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research artifacts` | 現行 input/artifact 保存先確認 | 読取り専用 | データセット内容の再取得・検証は行わない。 |
| `./research demand validate` | 需要 consumer側からsource/config整合性を検証 | Read-only validation | 出典全体の受入ではない。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| 基準値利用処理 | [prepare_baseline_demand.py](05_src/traffic_simulation/demand/prepare_baseline_demand.py) | 登録出典を基準 demandへ変換。 |
| ネットワーク出典処理 | [traffic simulation README](05_src/traffic_simulation/README.md) | 出典道路表現の処理入口説明。 |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| source metadata | identity/hash/license/provenance | `03_data/metadata/` | `AVAILABLE` |
| 未加工 出典データ | acquired originals | `03_data/raw/traffic_simulation/` | dataset-dependent / local |
| 利用側入力 | normalized or derived input | consumer 設定が指定 | dataset-dependent |

### 正本・信頼源

出典 同一性は出典 登録簿、取得事実は個別acquisition 記録、consumer採択は各処理工程 config/acceptanceが正本。本書は出典 受入を新設しない。

### 検証

| 検証器・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| 登録簿・利用側確認 | `./research demand validate` | 需要 試験と必要現行 入力が成功 | `AVAILABLE`; 出典全体判定基準ではない |
| リポジトリ参照 | `./research portal check` | 現行 path/index/link検証成功 | `PASS` |

<a id="受入done条件"></a>

### 受入・完了条件

出典 同一性、ハッシュ値、取得条件、用途、制限が台帳化され、利用処理工程の検証器が出典を確認できること。ポータル 段階計画上は`DONE`。

### 来歴

出典 識別子、取得日、URL、SHA-256は出典 登録簿とacquisition 記録に記録する。

### 既知の制約

未加工原本の一部はgit非追跡で再取得が必要。Open データは実配送運用を直接表さない。

### 未解決の判断

将来 想定条件で採用する追加出典と変換規則は`UNRESOLVED`。

### 次工程への引渡し

登録済み出典 識別子とハッシュ値を需要または道路網 設定へ渡す。

## B. 需要

### 目的

公開統計から大田区500m メッシュの基準 母集団と`parcel_equivalent/day`需要代理指標を生成・検証する。

### 現在の状態

`DONE`（基準）。safe integrated 構築 実行器は`NOT IMPLEMENTED`。`./research demand status`は現行ポータル ノード 識別子不一致により現在exit 1。

### 開始条件

出典 登録簿上の人口・宅配便統計、大田区境界、基準 設定が利用可能であること。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| 需要仕様 | definition / boundary | [baseline demand and comparator](05_src/traffic_simulation/demand/20260718_20260903_baseline_demand_and_comparator.md) | `CURRENT_NORMATIVE` | 実注文・停止ではない。 |
| 需要設定 | parameters / output paths | [baseline_demand.yml](reproducibility/config/traffic_simulation/baseline_demand.yml) | `CURRENT` | `target_days: 1`、単位は`parcel_equivalent`。 |
| 出典台帳 | governed inputs | [traffic_simulation_sources.csv](03_data/metadata/traffic_simulation_sources.csv) | `CURRENT` | 設定内出典 識別子を解決。 |

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research demand validate` | baseline implementation test＋accepted mapping consistency | Read-only validation | 正式運用 demandを再生成しない。 |
| `./research demand build --dry-run` | 不足runner/dependencyを表示 | 読取り専用 | 構築本体は`NOT IMPLEMENTED`。 |
| `./research demand status` | 状況表示 | 読取り専用 | **現在失敗**: ポータル ノード 識別子不一致。 |
| `./research demand future` | 将来 demand利用可否表示 | Read-only refusal | `NOT IMPLEMENTED / UNRESOLVED`。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| 基準値生成器 | [prepare_baseline_demand.py](05_src/traffic_simulation/demand/prepare_baseline_demand.py) | メッシュ人口・荷物換算単位配賦。固定済み 正本 出力のためコマンド操作 構築からは実行しない。 |
| 単体試験 | [test_prepare_baseline_demand.py](05_src/traffic_simulation/validation/test_prepare_baseline_demand.py) | source/config/配賦不変条件を検証。 |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| 基準需要 | 191 メッシュのpopulation/demand 代理指標 | `03_data/processed/traffic_simulation/demand/ota_ward_baseline_demand_2024_500m.parquet` | `AVAILABLE LOCALLY / GIT-IGNORED` |
| 品質要約 | source/config/output ハッシュ値と集計 | `03_data/processed/traffic_simulation/validation/ota_ward_baseline_demand_2024_500m_quality_summary.json` | `AVAILABLE LOCALLY / GIT-IGNORED` |

### 正本・信頼源

定義は需要 仕様、parameter/output 保存先は基準 設定、実行結果のハッシュ値・集計はquality まとめ。独立した需要 受入 フラグはない。

### 検証

| 検証器・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| 基準需要単体検証 | `./research demand validate` | `test_prepare_baseline_demand.py` PASS | `AVAILABLE` |
| 成果物の利用可否 | `./research artifacts` | Parquet/configが存在 | `AVAILABLE LOCALLY` |

<a id="受入done条件-1"></a>

### 受入・完了条件

設定、builder、単位 試験、Parquet、quality まとめが存在し、population/demand conservationとハッシュ値が確認できること。roadmap/Portalは基準を`DONE`とする。

### 来歴

quality まとめに出典 ハッシュ値、設定 ハッシュ値、出力 ハッシュ値、生成済み timestampを記録する。

### 既知の制約

`82,023 parcel-equivalent/day`は顧客数、要求数、配送地点数ではない。成果物はgit-ignoredでportable publicationではない。仕様文書の「未生成」記述と現行 成果物存在にはdocumentation lagがある。

### 未解決の判断

将来 demandの想定条件 year、growth rate、空間的な transformationは`UNRESOLVED`。

### 次工程への引渡し

基準 demand 代理指標を配送要求・配送地点生成契約へ渡す。荷物換算単位を1個1停止へ直接変換しない。

## C. リクエスト・配送先

### 目的

合成需要から要求 記録を作り、建物単位の配送 配送地点へ集約する。要求、荷物換算単位、配送地点の単位を分離する。

### 現在の状態

`DONE`（現行 roadmap/Portal、受入済み道路網 対応付けの入力）。安全な正式運用 regeneration 実行器と専用検証器は`NOT IMPLEMENTED / NOT AVAILABLE`。

### 開始条件

基準 demand、household/building 割当 出典、固定乱数の種、範囲 規則が必要。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| 基準需要 | aggregate demand proxy | `03_data/processed/traffic_simulation/demand/ota_ward_baseline_demand_2024_500m.parquet` | `AVAILABLE LOCALLY` | 荷物換算単位単位。 |
| リクエスト成果物 | synthetic request records | `03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/daily_requests.csv` | `AVAILABLE LOCALLY` | 73,547 data rows。 |
| 配送先生成要約 | generation/accounting | `03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/stop_generation_run_summary.json` | `AVAILABLE LOCALLY` | scoped 荷物 conservationを記録。 |

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research demand validate` | file availability＋accepted mapping consistency | Read-only validation | request/stop 生成器の再現を検証しない。 |
| `./research artifacts` | 正本 local paths表示 | 読取り専用 | availability inspection。 |
| `./research demand build --dry-run` | regeneration 隔たり表示 | 読取り専用 | integrated 生成器不在。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| コマンド操作安全制御 | [demand.py](05_src/research_cli/demand.py) | 生成器不在時に構築を拒否。 |
| 現行生成実装 | — | `NOT AVAILABLE` in current checkout |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| リクエスト | 1行1 合成 要求 | `.../pipelines_v1/daily_requests.csv` | `AVAILABLE LOCALLY / GIT-IGNORED` |
| 配送先 | 建物集約配送 配送地点 | `.../pipelines_v1/building_delivery_stops_scoped.csv` | `AVAILABLE LOCALLY / GIT-IGNORED`; 39,956 stops |
| 生成要約 | count/conservation/seed/hash | `.../pipelines_v1/*run_summary.json` | `AVAILABLE LOCALLY / GIT-IGNORED` |

### 正本・信頼源

現行 pathsはコマンド操作 中核とポータル マップ、下流利用状態は受入済み道路網 authority/acceptanceが参照する。配送要求・配送地点単独のmachine-readable 受入 成果物は`NOT AVAILABLE`。

### 検証

| 検証器・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| 受入済み対応付け整合性 | `./research demand validate` | 正本 検証器 合格、必須 files存在 | `AVAILABLE` |
| リクエスト・配送先再生成検証器 | — | deterministic generation＋conservation | `NOT AVAILABLE` |

<a id="受入done条件-2"></a>

### 受入・完了条件

現行段階計画は成果物存在と受入済み 配送地点 対応付けで`DONE`としている。完全な再現性には生成器、データ構造、専用検証器、portable 成果物 方針が追加で必要。

### 来歴

local 実行 summariesに乱数の種、設定 ハッシュ値、入力 成果物 ハッシュ値、request/stop/parcel 会計を記録。

### 既知の制約

基準 82,023 荷物換算単位、生成済み 要求 73,547 行、39,956 配送地点は異なる単位。scoped 配送地点 荷物換算単位は全体 要求 範囲より小さく、全体 conservationは偽、assigned 範囲 conservationのみ真。

### 未解決の判断

正式運用 regeneration 取り決め、portable publication、将来 想定条件別生成interface。

### 次工程への引渡し

配送要求数、配送地点数、scope/accountingを配送地点の対応付けとRouting 範囲 定義へ渡す。

## D. ネットワーク構築

### 目的

出典道路表現をThree-階層 出典・来歴（DIRECT / 推定 / 代替値）で正式道路網へ完成し、スーモ `net.xml`へ具体化する。

### 現在の状態

`DONE / ACCEPTED`。安全な新規isolated 終了-to-終了 コマンド操作 構築は`NOT IMPLEMENTED`。受入済み 実行を再利用する。

### 開始条件

現行 決定記録、方針、処理工程、registry/schema、source/structural 入力 固定が必要。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| 現行正本参照先 | authority resolver | [current_network_completion_authority_v17.yml](reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml) | `CURRENT` | 唯一の現行 道路網入口。 |
| 判断 | method adoption | [phase13 Formal Completion Decision](reproducibility/config/traffic_simulation/decisions/phase13_formal_completion_three_tier_v1.yml) | `CURRENT` | Decision ID `DEC-P13-FORMAL-COMPLETION-THREE-TIER-001`。 |
| 規範仕様 | Three-tier policy | [formal completion specification](05_src/traffic_simulation/specifications/20260903_20260903_formal_completion_three_tier_policy_v17.md) | `CURRENT_NORMATIVE` | strict/hybridを現行へ混ぜない。 |
| パイプライン仕様 | ordered stages/gates | [network completion pipeline specification](05_src/traffic_simulation/specifications/20260903_20260903_network_completion_pipeline_v17.md) | `CURRENT_NORMATIVE` | SOURCE→…→ACCEPTANCE。 |
| Registry・schema | machine-readable contract | [Three-tier registry](reproducibility/config/traffic_simulation/formal_completion_three_tier_registry_v17.yml) | `CURRENT` | policy/record schemasは正本から解決。 |

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research network status` | 受入済み pointer/hash/status表示 | 読取り専用 | 推奨inspection。 |
| `./research network validate` | 現行の受入済み道路網を全判定基準検証 | Read-only validation | 構築しない。 |
| `./research network acceptance` | 受入 ジェイソン形式表示 | 読取り専用 | flag/gates/mappingを表示。 |
| `./research network build --dry-run` | unsafe 固定済み-出力 limitation表示 | 読取り専用 | 構築本体は拒否される。 |
| `./research pipeline network` | 受入済み道路網を再利用して検証 | Read-only validation | 受入済み 実行を上書きしない。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| Three-階層補完 | [execute_three_tier_completion_streaming.py](05_src/traffic_simulation/network/execute_three_tier_completion_streaming.py) | 受入済み 構築 出典・来歴上の完了判定 実装。 |
| Registry validator | [validate_formal_completion_three_tier_registry.py](05_src/traffic_simulation/network/validate_formal_completion_three_tier_registry.py) | policy/registry/schema整合性。 |
| パイプライン検証器 | [validate_network_completion_pipeline.py](05_src/traffic_simulation/network/validate_network_completion_pipeline.py) | stage ordering/gate contract。 |
| 正本検証器 | [validate_current_network_completion_authority.py](05_src/traffic_simulation/network/validate_current_network_completion_authority.py) | pointer/hash/acceptance integrity。 |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| 受入済み実行 | current run directory | `reproducibility/outputs/.../phase13_20260903_three_tier_completion/run_2` | `ACCEPTED` |
| 受入済み道路網 | 交通シミュレーターの道路網 | [three_tier.net.xml](reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/three_tier.net.xml) | `ACCEPTED` |
| ネットワークグラフ規模 | 経路計算 グラフのノード / directed 道路区間数とスーモ 車線数 | [network_acceptance.json](reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/network_acceptance.json) `/validation/counts` | `ACCEPTED` |
| 来歴集計 | DIRECT/INFERRED/FALLBACK counts | [quality_accounting.json](reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_1/quality_accounting.json) | `CURRENT REFERENCE FROM AUTHORITY` |

### 正本・信頼源

[現行 道路網 正本](reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml)が決定記録、仕様、registry/schema、受入済み run/network/acceptance、ハッシュ値を解決する。階層型混合方式は`SUPERSEDED`、厳密方式 v17と旧実行は`HISTORICAL`。

### 検証

| 検証器・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| Registry・schema | `./research network validate` | registry/schema validator PASS | `PASS` |
| パイプライン定義 | same | 現行 Decision/order/gates一致 | `PASS` |
| スーモ 構築・属性・接続性 | same | build、lane、speed、permission、connectivity PASS | `PASS` |
| ハッシュ値完全性 | same | actual SHA＝authority SHA | `PASS` |

<a id="受入done条件-3"></a>

### 受入・完了条件

all 道路網 gates 合格、受入済み `net.xml`存在、ハッシュ値一致、Stop Mapping/routeability 判定基準 合格、`FORMAL_NETWORK_ACCEPTED=true`。

### 来歴

受入済み 実行 識別子 `three_tier_run_2`、道路網 識別子 `P13-THREE-TIER-RUN-2`、出典 変更記録、input/output ハッシュ値、quality 会計をauthority/acceptanceに記録。

ネットワークグラフ規模は受入成果物の`validation.counts`を正本とする。`network_node_count = 70,050`、`network_edge_count = 147,168`（方向別に定義されたスーモ 道路区間を数える有向道路区間）、`network_lane_count = 154,728`。論文表記は`Traffic network size: |V| nodes, |E| directed edges`とし、車線数はスーモ固有の補助指標とする。

### 既知の制約

スーモ 取込み 注意事項保持、185 components、到達可能性は標本 判定基準。現行 コマンド操作はcaller-supplied unique 実行 識別子を持つ安全なrebuildを提供しない。

### 未解決の判断

道路網 stage自体の現行 受入 阻害要因はない。将来の安全なisolated rebuild 実行器は未実装。

### 次工程への引渡し

受入済み道路網 参照先とハッシュ値を配送地点の対応付け、経路計算の基準、シミュレーションへ渡す。

## E. 配送先マッピング

### 目的

39,956 配送地点数を受入済み 交通シミュレーターの道路網上の配送-permitted 道路区間へ決定的に対応付ける。

### 現在の状態

`DONE / ACCEPTED AS PART OF NETWORK ACCEPTANCE`。

### 開始条件

scoped 配送地点数、交通シミュレーターの道路網、配送 車両 通行許可、deterministic 対応付け 規則が必要。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| 対象範囲内配送先 | mapping targets | `03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/building_delivery_stops_scoped.csv` | `AVAILABLE LOCALLY` | 39,956 stops。 |
| 受入済み道路網 | permitted edges | [three_tier.net.xml](reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/three_tier.net.xml) | `ACCEPTED` | authority-bound SHA。 |
| 到達可能道路区間 上書き指定 | limited mapping fix | [routeable_edge_overrides.json](reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/routeable_edge_overrides.json) | `CURRENT RUN ARTIFACT` | recorded 17-failed-OD cohort fix。 |

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research network acceptance` | 対応付け count/status表示 | 読取り専用 | 39,956 / 39,956。 |
| `./research network validate` | 対応付けを正本 chain内で再検証 | Read-only validation | 受入済み 成果物を書き換えない。 |
| `./research routing inputs` | mapped 配送地点数の引継ぎ確認 | 読取り専用 | Routing input readiness。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| 対応付け受入生成器 | [accept_three_tier_network_run.py](05_src/traffic_simulation/network/accept_three_tier_network_run.py) | 対応付け 成果物と受入 会計を生成した固定実行 スクリプト。日常実行しない。 |
| 到達可能性修正検証器 | [validate_three_tier_routeability_fix.py](05_src/traffic_simulation/network/validate_three_tier_routeability_fix.py) | 対応付け fix後の到達可能性を検証。 |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| 配送先対応付け | 配送地点→道路区間対応 | [request_stop_mapping.json](reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/request_stop_mapping.json) | `ACCEPTED` |
| 対応付け集計 | mapped/unmapped/distance | network acceptance JSON `/mapping` | `ACCEPTED` |

### 正本・信頼源

現行の正本の受入済み 実行と[network_acceptance.json](reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/network_acceptance.json)。

### 検証

| 検証器・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| 対応付け網羅率 | `./research network acceptance` | mapped＝total＝39,956、unmapped＝0 | `PASS` |
| 許可道路区間 対応付け | `./research network validate` | 配送-permitted 対応付けと到達可能性 判定基準 合格 | `PASS` |

<a id="受入done条件-4"></a>

### 受入・完了条件

全配送地点数 mapped、対応付け rate 1.0、配送 通行許可、主要な 到達可能性 標本 100/100、道路網 受入に含まれること。

### 来歴

対応付け 保存先、網羅率、距離 statistics、上書き指定名、標本 件数は受入 ジェイソン形式に記録。

### 既知の制約

nearest-道路区間 索引はdeterministic 道路区間 midpoint方式。到達可能性はall-pairs proofではない。additional non-gating sanity 標本は91/100。

### 未解決の判断

Routing 問題例で使用するStop subsetと到達不能組の方針。

### 次工程への引渡し

受入済み Stop→道路区間 対応付けを経路計算の基準の端点定義へ渡す。

## F. ネットワーク受入

### 目的

道路網 Construction、スーモ validity、配送地点の対応付け、到達可能性を研究利用可能な一つの受入済み 状態へ束ねる。

### 現在の状態

`ACCEPTED / DONE`。

### 開始条件

スーモ 構築、lane/speed/permission/connectivity、対応付け、到達可能性 検証が完了していること。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| 正本参照先 | accepted run resolution | [current authority](reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml) | `CURRENT` | run/network/SHAを固定。 |
| 受入成果物 | formal gate state | [network_acceptance.json](reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/network_acceptance.json) | `ACCEPTED` | `FORMAL_NETWORK_ACCEPTED=true`。 |

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research network acceptance` | 受入済み flags/gates表示 | 読取り専用 | primary inspection。 |
| `./research network validate` | 正本から全受入済み 判定基準再検証 | Read-only validation | 現行 状態を変更しない。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| 正本検証器 | [validate_current_network_completion_authority.py](05_src/traffic_simulation/network/validate_current_network_completion_authority.py) | 保存先、ハッシュ値、フラグ整合性。 |
| Portal・network validator | [validate_research_map_portal.py](05_src/traffic_simulation/network/validate_research_map_portal.py) | 受入済み 評価指標と現行 display整合性。 |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| 受入ジェイソン形式 | formal accepted state | `.../run_2/network_acceptance.json` | `ACCEPTED` |
| 現行正本 | stable pointer | `reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml` | `CURRENT` |

### 正本・信頼源

受入結果は受入 ジェイソン形式、現行選択は正本 参照先。ポータルや本書は受入 正本ではない。

### 検証

| 検証器・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| 正式フラグ | `./research network acceptance` | `FORMAL_NETWORK_ACCEPTED=true` | `PASS` |
| 主要到達可能性 | same | deterministic 100 pairs、100 routeable | `PASS` |
| ハッシュ値紐付け | `./research network validate` | `4625dbbc…e40f`一致 | `PASS` |

<a id="受入done条件-5"></a>

### 受入・完了条件

受入 成果物存在、all 事前分布 gates 合格、正式 フラグ 真、正本 参照先とハッシュ値一致。

### 来歴

決定識別子、道路網 識別子、出典 変更記録、出典 入力 ハッシュ値、道路網 意味上の ハッシュ値、交通シミュレーターの版を受入 ジェイソン形式に記録。

### 既知の制約

到達可能性 受入は標本に基づく。additional sanity 標本は非gatingで91/100。これを現行 不具合へ昇格しないが、all-pairs保証とも表現しない。

### 未解決の判断

なし（現行 受入 範囲内）。

### 次工程への引渡し

受入済み道路網、対応付け、known 限界を経路計算の基準へ渡す。

## G. 経路計算ベースライン

### 目的

選択した配送 問題例に必要な移動時間の費用、距離 費用、到達可能性、経路計算の来歴を固定する。

### 現在の状態

`NEXT / NOT IMPLEMENTED / NOT YET PRODUCTION COMPLETE`。道路網 prerequisiteは`PASS`。

### 開始条件

受入済み道路網、受入済みの配送地点対応付け、配送要求・配送地点、および採択済み経路計算 scope/depot/vehicle class/cost 定義。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| 受入済み道路網 | routing graph | [three_tier.net.xml](reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/three_tier.net.xml) | `READY` | SHA-bound。 |
| ネットワークグラフ規模 | graph traversal substrate scale | [network_acceptance.json](reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/network_acceptance.json) `/validation/counts` | `READY` | Nodes 70,050 / directed edges 147,168 / lanes 154,728。 |
| 受入済み対応付け | route endpoints | [request_stop_mapping.json](reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/request_stop_mapping.json) | `READY` | full Stops mapping。 |
| リクエスト | demand records | `03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/daily_requests.csv` | `READY LOCALLY` | 問題例 範囲未選択。 |
| 配送先 | candidate delivery endpoints | `03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/building_delivery_stops_scoped.csv` | `READY LOCALLY` | 39,956 all-pairsを前提にしない。 |

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research routing inputs` | available 入力と未決定事項表示 | 読取り専用 | 現在の主inspection。 |
| `./research routing status` | stage/runner/artifact状態表示 | 読取り専用 | `NEXT`。 |
| `./research routing build --dry-run` | 欠落 decisions/runner表示 | 読取り専用 | 正式運用 構築は拒否。 |
| `./research routing validate --dry-run` | 欠落 artifact/validator表示 | 読取り専用 | 検証は未実装。 |
| `./research pipeline routing --dry-run` | 入力→構築→検証の判定基準をinspection | 読取り専用 | 成果物を作らない。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| コマンド操作準備状況制御 | [routing.py](05_src/research_cli/routing.py) | input/gate表示、未実装構築拒否。 |
| 本番経路計算 実行器 | — | `NOT IMPLEMENTED` |
| 本番経路計算 検証器 | — | `NOT IMPLEMENTED` |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| 所要時間費用 | required OD travel-time | path `UNRESOLVED` | `EXPECTED / NOT YET AVAILABLE` |
| 距離費用 | required OD distance | path `UNRESOLVED` | `EXPECTED / NOT YET AVAILABLE` |
| 経路到達可能性 | required OD feasibility | path `UNRESOLVED` | `EXPECTED / NOT YET AVAILABLE` |
| 経路計算来歴 | method/version/command/input hashes | path `UNRESOLVED` | `EXPECTED / NOT YET AVAILABLE` |

### 正本・信頼源

現行 stage/decision 境界は[Research Overview 段階 1](RESEARCH_OVERVIEW.md#stage-1--routing-baseline-next)と[ポータル マップ](reproducibility/config/research_portal/research_map_v1.yml)。正式運用 経路計算 正本は`NOT AVAILABLE`。

### 検証

| 検証器・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| ネットワーク前提条件 | `./research routing inputs` | accepted network/mapping READY | `PASS` |
| 経路計算成果物検証器 | `./research routing validate --dry-run` | method fixed、required OD complete、routeability/provenance valid | `NOT AVAILABLE` |

<a id="受入done条件-6"></a>

### 受入・完了条件

経路計算 method/scope 固定済み、必要出発地・到着地集合のみを完全生成、検証器 合格、input/output ハッシュ値と再現コマンドを保存し、downstream利用をacceptすること。

### 来歴

将来成果物に道路網 ハッシュ値、mapping/input ハッシュ値、method/version、車種、出発地・到着地 範囲、コマンド、実行時間を記録する必要がある。現時点では`NOT AVAILABLE`。

### 既知の制約

ネットワークグラフ規模（`|V|`ノード・`|E|`有向道路区間・車線数）と経路計算負荷（出発地・到着地・必要出発地・到着地 pair）、さらに配送インスタンス規模（要求・配送地点・車両・問題例 経路 pair）は、別々の問題規模である。39,956配送先の全組合せは採択しておらず、`routing_origin_count`、`routing_destination_count`、`required_od_pair_count`は`NOT YET AVAILABLE`。標本 到達可能性 受入は本番経路計算 費用成果物ではない。

### 未解決の判断

routing scope、depot、delivery vehicle class、routing cost definition、unreachable pair policy、artifact/schema/provenance contract。

### 次工程への引渡し

検証済み 必須-出発地・到着地 cost/routeability 成果物を共通配送問題へ渡す。

## H. 共通配送インスタンス

### 目的

需要、配送地点数、配送拠点、経路計算 costs、vehicle/battery constraintsを求解器-independentな共通問題へ凍結する。

### 現在の状態

`PLANNED / NOT IMPLEMENTED / NOT AVAILABLE`。ポータル 実行 位置は`PLANNED`。

### 開始条件

検証済み 経路計算の基準、解決済み depot/fleet size/vehicle capacity/battery パラメーター、採用済み データ構造が必要。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| リクエスト・配送先 | common demand | current local paths | `AVAILABLE LOCALLY` | 層化・重み付き非復元抽出を採択済み。層と配賦の詳細は未固定。 |
| 経路計算基準 | matrices/feasibility | 保存先未定 | `NOT AVAILABLE` | blocking input。 |
| 比較手順 | design constraint | [optimization_comparison_protocol.md](05_src/traffic_simulation/optimization_comparison_protocol.md) | `CURRENT DESIGN` | common inputs/evaluatorを要求。 |
| 電気自動車プロファイル | candidate fixed model assumption | [managed_urban_ev_delivery_v1.yml](reproducibility/config/traffic_simulation/scenario_profiles/managed_urban_ev_delivery_v1.yml) | `CURRENT MODEL ASSUMPTION` | fleet/battery 問題例 受入ではない。 |

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research instance status` | 欠落 validator/upstream/artifact表示 | 読取り専用 | 現行 モジュール 保存先は欠落。 |
| `./research instance build --dry-run` | 欠落 inputs/generator表示 | 読取り専用 | no artifact。 |
| `./research instance validate --dry-run` | 欠落 validator/artifact表示 | 読取り専用 | no acceptance。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| コマンド操作安全制御 | [instance.py](05_src/research_cli/instance.py) | 現行 absenceを明示。 |
| `common_delivery_instance.py` | `05_src/optimization/common_delivery_instance.py` | `NOT AVAILABLE` in current checkout |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| インスタンスデータ構造 | solver-independent contract | 保存先未定 | `EXPECTED / NOT AVAILABLE` |
| 本番インスタンス | frozen common problem | 保存先未定 | `EXPECTED / NOT AVAILABLE` |
| 検証・受入 | completeness/feasibility/hash | 保存先未定 | `EXPECTED / NOT AVAILABLE` |

### 正本・信頼源

段階 2 段階計画と比較 手順が設計参照。正式運用 正本、データ構造、受入済み 成果物は存在しない。

### 検証

| 検証器・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| インスタンス検証器 | `./research instance validate --dry-run` | データ構造 固定済み、仮置きなし、hash/feasibility 合格 | `NOT AVAILABLE` |

<a id="受入done条件-7"></a>

### 受入・完了条件

データ構造、生成器、検証器が現行 checkoutに存在し、検証済み 経路計算と解決済み constraintsからreproducible 正式運用 問題例を生成・acceptすること。

### 来歴

将来はRequests/Stops/routing/config ハッシュ値、ノード ordering、vehicle/constraint 版、生成 コマンドを保存する。

### 既知の制約

過去候補は段階計画上の確認 materialであり現行 実装ではない。固定済み 電気自動車 設定プロファイルだけでCommon 問題例成立とはしない。

### 未解決の判断

取り決め復元/改訂/置換、配送拠点、車両群 規模、容量、battery/energy 意味、問題例 範囲。

### 次工程への引渡し

受入済み common 問題例を古典最適化と制約なし二値二次最適化へ同一入力として渡す。

## I. 古典最適化

### 目的

量子手法と比較する古典計算 基準を、共通問題例・共通feasibility/evaluator上で確立する。

### 現在の状態

`PLANNED`（段階計画）/ `FUTURE`（ポータル）/ `NOT IMPLEMENTED`。正式運用 solver/resultなし。

### 開始条件

accepted Common Delivery Instance、fixed formulation/objective/constraints、solver budget、seed、correctness fixtures。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| 共通配送インスタンス | solver input | 保存先未定 | `NOT AVAILABLE` | blocking。 |
| 比較手順 | fairness boundary | [optimization_comparison_protocol.md](05_src/traffic_simulation/optimization_comparison_protocol.md) | `CURRENT DESIGN` | 求解器実装ではない。 |

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research optimization classical status` | upstream/solver状態表示 | 読取り専用 | no result。 |
| `./research optimization classical run --dry-run` | 欠落 solver/upstream表示 | 読取り専用 | 正式運用 実行拒否。 |
| `./research optimization classical validate --dry-run` | 欠落 result/validator表示 | 読取り専用 | no acceptance。 |
| `./research pipeline optimization --dry-run` | instance→classical→validation inspection | 読取り専用 | partial orchestration。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| コマンド操作安全制御 | [optimization.py](05_src/research_cli/optimization.py) | 欠落 正式運用 求解器を明示。 |
| 本番定式化・求解器 | — | `NOT IMPLEMENTED` |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| 数理定式化 | adopted objective/constraints | 保存先未定 | `EXPECTED / NOT AVAILABLE` |
| 古典解 | raw/repaired feasible solution | 保存先未定 | `EXPECTED / NOT AVAILABLE` |
| 検証根拠 | small-instance correctness | 保存先未定 | `EXPECTED / NOT AVAILABLE` |

### 正本・信頼源

段階 3 段階計画と比較 手順のみ。正式運用 Decision/config/result/acceptanceは`NOT AVAILABLE`。

### 検証

| 検証器・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| 古典解法の正当性 | `./research optimization classical validate --dry-run` | fixtures、feasibility、objective、result provenance PASS | `NOT AVAILABLE` |

<a id="受入done条件-8"></a>

### 受入・完了条件

定式化固定、求解器実装、small-問題例 correctness 合格、正式運用 基準生成、common 評価器で検証・accept。

### 来歴

将来は問題例 ハッシュ値、solver/version、予算、乱数の種、raw/repaired 出力、実行時間 boundariesを保存する。

### 既知の制約

OR-Toolsと需要充足最大化の優先順位は採択済み。厳密定式化、車両群 パラメーター、予算と本番実装は未確定。

### 未解決の判断

OR-Tools内の探索設定、mathematical 定式化、予算、乱数の種 set、correctness しきい値。

### 次工程への引渡し

検証済み 古典計算 基準を制約なし二値二次最適化 equivalence、古典計算-vs-量子近似最適化アルゴリズム 比較、配送シミュレーションへ渡す。

<a id="j-qubo"></a>

## J. 制約なし二値二次最適化

### 目的

Full-電気自動車配送経路問題経路とは分離して、固定配送拠点・単一車両の訪問順序 problemを検証可能な制約なし二値二次最適化、encoder、復号器、独立検証器へ写像する。

### 現在の状態

Reduced 保存先は `FORMULATION_VERIFIED = PASS` および `R21_REDUCED_QUBO_VALIDATION = PASS`。完全な電気自動車配送経路問題 R20は`BLOCKED`であり、完全な電気自動車配送経路問題 制約なし二値二次最適化が完成したことを意味しない。

### 開始条件

Reduced 保存先では受入済み 経路計算の基準のcomplete-directed-到達可能性 subset、固定済み 配送拠点、ordered 顧客、静的 directed 移動時間 行列、固定済み source/hashを用いる。一般の全体 共通配送問題と13 必須制約は別の完全な電気自動車配送経路問題開始条件として残る。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| Reduced input | variable/data source | Routing Baseline-derived R20 input | `ACCEPTED SCOPED` | depot + ordered customers、complete directed reachability、travel time seconds。 |
| 古典参照解 | equivalence reference | `r20_route_ordering/core.py` | `VERIFIED SCOPED` | 全`n!` permutation、固定済み 配送拠点、同一移動時間 行列。 |
| 比較手順 | fairness/output accounting | [optimization_comparison_protocol.md](05_src/traffic_simulation/optimization_comparison_protocol.md) | `CURRENT DESIGN` | 制約なし二値二次最適化仕様ではない。 |

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| Stage runner modules | exact build/validation | Read/write artifact | 最上位 コマンド操作への統合とは別。package 実行器が正本。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| Reduced formulation/builder | [r20_route_ordering](05_src/traffic_simulation/r20_route_ordering/) | row-major `n x n` position QUBO、exact reference、adapter、penalty analysis。 |
| Stage-level validator | [r21_qubo_validation](05_src/traffic_simulation/r21_qubo_validation/) | frozen input/provenance、exact QUBO enumeration、V1--V8、artifact/manifest。 |
| Regression tests | [validation](05_src/traffic_simulation/validation/) | R20/R21 exact, adapter, penalty, artifact tests。 |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| 制約なし二値二次最適化定式化 | variables/objective/penalties/scaling | [R20 specification](05_src/traffic_simulation/specifications/R20_QAOA_SUBPROBLEM_SPEC.md) | `FORMULATION_VERIFIED / SCOPED` |
| encoder・decoder contract | instance↔binary mapping | [r20_route_ordering](05_src/traffic_simulation/r20_route_ordering/) | `VERIFIED SCOPED` |
| 等価性報告 | QUBO vs exact classical | `reproducibility/outputs/traffic_simulation/r21_qubo_validation/20260910_formal_reduced_v4/` | `PASS`; 生成済み 出力はGit-ignore 方針に従う。 |

### 正本・信頼源

[R20 仕様](05_src/traffic_simulation/specifications/R20_QAOA_SUBPROBLEM_SPEC.md)、[電気自動車配送経路問題 実行 計画](EVRP_EXECUTION_PLAN.md)、R21 正式 成果物 v4。R21 検証-結果 SHA-256は`c4baeead366ea2f750cd4ecdd18acc507746dfecd744d0803ed74b5bbb46049f`、成果物一覧 SHA-256は`9a6fc459ef1f5cbf1824b9b0197a2f56f9d67cc88de18bd6bcd8ff7f575691a2`。

### 検証

| 検証器・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| Reduced 制約なし二値二次最適化等価性 | R21 package/formal artifact | global minima feasibility、route/tie set、direct/expanded、decode、normalization、lambda、provenance V1--V8 | `PASS` |

<a id="受入done条件-9"></a>

### 受入・完了条件

Reduced 範囲では達成済み。完全な電気自動車配送経路問題では未達。

### 来歴

R21 成果物はinstance/source/coefficient ハッシュ値、lambda/bound/margin、state/permutation 測定度数、optima、decoded 経路、deterministic 成果物一覧を保存する。

### 既知の制約

Reduced 目的は静的 directed 移動 時間であり距離ではない。符号化は顧客-only row-主要な `n x n`、配送拠点は二値 変数ではない。customer-once/position-once以外の完全な電気自動車配送経路問題制約は未収載。complete 到達可能性のみ受理し、non-self zero-時間は不確実な場合は拒否、不正 bitstringsは修復せず破棄する。

### 未解決の判断

数学条件は`lambda>B`。`P_min=2`、universal `B=(n+1)/2`、問題例-aware `B=U_feasible/2`はconservative sufficient 境界。`lambda=B+max(10 e_noise,1e-6 B)`は実装-方針 候補であり定理・正式 optimumではない。一般到達不能-移行 制約なし二値二次最適化と完全な電気自動車配送経路問題 constraintsは未解決。

### 次工程への引渡し

R21 合格の固定済み 制約なし二値二次最適化をR22へ渡し、R22 合格の同一Ising ハミルトニアンだけをR23へ渡す。R20からR22へ直接進めない。

<a id="k-qaoa"></a>

## K. 量子近似最適化アルゴリズム

### 目的

R22で検証済みされた同一縮約した Ising ハミルトニアンを中央処理装置 Aer上の量子近似最適化アルゴリズムへ入力し、solution quality、実行可能性、ground-状態 確率、optimizer/circuit/simulator timingを再現可能に測定する。

### 現在の状態

Current reduced R23/R24 status and accepted evidence: see [R23_STATUS.md](05_src/traffic_simulation/R23_STATUS.md). Full-EVRP and quantum hardware remain separate scopes.

### 開始条件

R22 縮約した 合格 artifact/hash、固定済み Ising coefficients、厳密 R21/R22 state/route 参照、管理対象の 中央処理装置 環境、資源 guards。ハミルトニアンまたはlambdaをR23内で変更しない。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| 検証済みIsing | quantum problem | `reproducibility/outputs/traffic_simulation/r22_ising_conversion/20260910_formal_reduced_v1/` | `PASS / SCOPED` | R22 results/manifest ハッシュ値を固定。 |
| Exact reference | performance reference | R21/R22 artifacts | `AVAILABLE SCOPED` | ground energy、all optimal states/routes、ties。 |
| 比較手順 | fairness | [optimization_comparison_protocol.md](05_src/traffic_simulation/optimization_comparison_protocol.md) | `CURRENT DESIGN` | Aer結果は量子優位性を示さない。 |

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| Governed pilot | API/runtime/resource/artifact確認 | See current evidence index | See R23_STATUS.md; 実装の動作確認とは分離。 |
| Formal baseline | 6 instances x p={1,2,3} | See current evidence index | See R23_STATUS.md; 18 optimizations。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| Reduced QAOA/Aer infrastructure | [r23_qaoa_aer](05_src/traffic_simulation/r23_qaoa_aer/) | R22 loader、SparsePauliOp mapping、QAOAAnsatz、COBYLA、exact Statevector metrics、artifact schema。 |
| Tests | [test_r23_qaoa_aer.py](05_src/traffic_simulation/validation/test_r23_qaoa_aer.py) | endianness、offset、probability/route metrics、guards、determinism。 |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| Pilot evidence | API/runtime/resource/artifact | `reproducibility/outputs/traffic_simulation/r23_qaoa_aer/<pilot_run_id>/` | See R23_STATUS.md |
| Formal baseline | config/run/summary/manifest | same root, distinct formal run ID | See R23_STATUS.md |
| Raw metrics | P_opt、P_feasible、energy/gaps、optimizer/circuit/timing | See current evidence index | いいえ 修復; 厳密 参照を使用。 |

### 正本・信頼源

[電気自動車配送経路問題 実行 計画](EVRP_EXECUTION_PLAN.md)のR23 縮約した governance、governance 変更記録 `5f88e6ae242357c784b246d7740a006f483e7798`、R22 正式 成果物、R23 source/tests。現行 result/benchmark 正本は[R23_STATUS.md](05_src/traffic_simulation/R23_STATUS.md)を参照する。

### 検証

| 検証器・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| Implementation smoke | R23 tests/temp artifact | operator/endianness/metrics/API semantics | `PASS / NON-AUTHORITATIVE` |
| Governed pilot | Archived fixed protocol | n=2/n=3 p=1、runtime/termination/guards/artifact | See R23_STATUS.md |
| Formal baseline | Archived fixed protocol | complete protocol/provenance/reproducibility | See R23_STATUS.md |

<a id="受入done条件-10"></a>

### 受入・完了条件

R23 合格は固定済み 手順が完全かつ再現可能に実行されたことを意味し、量子近似最適化アルゴリズムが常にoptimumを得たことを要求しない。低いP_optやsuboptimal 結果は有効な科学データであり、provenance/backend/numerical/incomplete-run 不具合と区別する。

### 来歴

Pilot/formal 成果物はR20--R22 lineage、Qiskit/Aer/Python versions、中央処理装置 backend/method/device、p、COBYLA設定、乱数の種、initial/final パラメーター、目的 追跡、回路 評価指標、timing、P_opt、P_feasible、energy/route gapsを保存する。runtime/timestamp以外の意味上の 項目を正本 ハッシュ値対象とする。

### 既知の制約

Qiskit Aerは量子計算 実機ではない。`Aer simulation limit != quantum hardware limit`、`Aer runtime != future QPU runtime`。初期 基準は中央処理装置 exact/statevector 期待値のみで、有限 回測定、GPU/H100、cloud 量子処理装置、最適化処理 比較を含まない。

### 未解決の判断

正式 基準 設計は6 instances x `p={1,2,3}`、COBYLA、maxiter 100、evaluation cap 300、初期 パラメーター 0.1、乱数の種 17、repetition 1、中央処理装置 厳密 期待値として固定済み。次の未完了は管理対象の 予備試験実行と正式 設計-固定 成果物であり、結果を見た後の設計変更は別版にする。

### 次工程への引渡し

R23 正式 完了判定後にのみ、同じ縮約した 範囲のR24 復号 eligibilityを検討する。完全な電気自動車配送経路問題 配送シミュレーションや手法 比較へ直接一般化しない。

## L. シナリオ構築

### 目的

基準を上書きせず、将来 demand、電気自動車 technology、optimization/quantum capabilityを分離したversioned 想定条件 入力へする。

### 現在の状態

`PLANNED / NOT IMPLEMENTED`。電気自動車 設定プロファイルは`CURRENT FIXED MODEL ASSUMPTION`だが、受入済み 将来 想定条件 parameterizationではない。

### 開始条件

accepted baseline、evidence-backed parameter sources、scenario scope/year、transformation rules、pre-registered combinations。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| 基準需要設定 | baseline comparator | [baseline_demand.yml](reproducibility/config/traffic_simulation/baseline_demand.yml) | `CURRENT` | 将来 valuesで上書きしない。 |
| 電気自動車車両設定プロファイル | fixed model assumption | [managed_urban_ev_delivery_v1.yml](reproducibility/config/traffic_simulation/scenario_profiles/managed_urban_ev_delivery_v1.yml) | `CURRENT ASSUMPTION` | measured real 車両ではない。 |
| 将来想定条件 段階計画 | planned dimensions/gates | [Research Overview Stage 5](RESEARCH_OVERVIEW.md) | `PLANNED` | year/rates未固定。 |

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research demand future` | 将来 demand availability表示 | Read-only refusal | returns `NOT IMPLEMENTED`。 |
| `./research demand build --dry-run` | baseline/future build boundary inspection | 読取り専用 | 想定条件生成なし。 |
| `./research quantum status` | quantum capability stage state | 読取り専用 | capability 想定条件を生成しない。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| EV profile schema・config | [managed vehicle profile schema](reproducibility/config/traffic_simulation/schemas/managed_vehicle_profile.schema.json) | current vehicle assumption contract。 |
| 将来需要・想定条件生成器 | — | `NOT IMPLEMENTED` |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| 技術想定条件 設定 | EV/optimization capability ranges | 保存先未定 | `EXPECTED / NOT AVAILABLE` |
| 需要想定条件 設定 | year/total/spatial transformation | 保存先未定 | `EXPECTED / NOT AVAILABLE` |
| 組合せ登録簿 | pre-registered comparisons | 保存先未定 | `EXPECTED / NOT AVAILABLE` |

### 正本・信頼源

段階 5 段階計画が設計 正本。採用済み 正式運用 想定条件 正本は`NOT AVAILABLE`。

### 検証

| 検証器・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| EV profile schema test | no dedicated `./research` command | profile schema semantics valid | component exists; not scenario acceptance |
| 将来想定条件 検証器 | — | source/range/transformation/baseline separation PASS | `NOT AVAILABLE` |

<a id="受入done条件-11"></a>

### 受入・完了条件

想定条件 パラメーター、出典、scope/year、transformation、基準 比較、combinationsを版化し検証器 合格。

### 来歴

将来は外部 根拠 IDs、パラメーター 航続距離、transformation code/config ハッシュ値、想定条件 版を保存する。

### 既知の制約

車両 設定プロファイルの積載量等を実際の 車両群値とみなさない。将来 demandや量子計算 capabilityを現在値として扱わない。

### 未解決の判断

scenario year、demand growth/spatial change、EV battery ranges、optimization/quantum capability assumptions。

### 次工程への引渡し

受入済み 想定条件 設定を想定条件-specific Requests/Stops、Common 問題例、最適化、シミュレーションへ渡す。

## M. 配送シミュレーション

### 目的

受入済み network/scenario上で検証済み 配送 plansを実行し、計画とrealized モデル behaviorを分離して記録する。

### 現在の状態

`PLANNED`（roadmap）/ `FUTURE`（Portal）/ `NOT IMPLEMENTED / NOT PRODUCTION COMPLETE`。

### 開始条件

accepted network、Common Instance、validated plans、accepted scenarios/traffic config、seeds、plan-to-SUMO conversion contract。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| 受入済み道路網 | SUMO environment | current authority resolves | `READY` | 道路網 検証 simulationとは別。 |
| 検証済み計画 | delivery execution plan | 保存先未定 | `NOT AVAILABLE` | blocking。 |
| シナリオ設定 | technology/demand conditions | 保存先未定 | `NOT AVAILABLE` | blocking。 |

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research simulation status` | 正式運用 準備状況表示 | 読取り専用 | traffic/network 検証 simulationsを除外。 |
| `./research simulation run --dry-run` | 欠落 runner/plan表示 | 読取り専用 | no simulation。 |
| `./research simulation validate --dry-run` | 欠落 result/validator表示 | 読取り専用 | no acceptance。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| コマンド操作安全制御 | [simulation.py](05_src/research_cli/simulation.py) | 配送 simulation不在を明示。 |
| 本番配送実行器・検証器 | — | `NOT IMPLEMENTED` |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| シミュレーション実行 | realized routes/times/SOC/completions/failures | 保存先未定 | `EXPECTED / NOT AVAILABLE` |
| run manifest | plan/scenario/network/seed hashes | 保存先未定 | `EXPECTED / NOT AVAILABLE` |
| 検証報告 | execution/failure accounting | 保存先未定 | `EXPECTED / NOT AVAILABLE` |

### 正本・信頼源

段階 6 段階計画と[V&V 参照](05_src/traffic_simulation/20260730_20260903_simulation_model_development_and_vv.md)。正式運用 実行 正本なし。

### 検証

| 検証器・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| 配送simulation 検証器 | `./research simulation validate --dry-run` | reproducible plan conversion、run/failure accounting PASS | `NOT AVAILABLE` |

<a id="受入done条件-12"></a>

### 受入・完了条件

受入済み 入力からreproducible 実行を生成し、plan/run 出典・来歴、completion/failure 会計、検証器、受入を満たす。

### 来歴

将来はnetwork/plan/instance/scenario ハッシュ値、SUMO/software versions、乱数の種、コマンド、実行 成果物一覧を保存する。

### 既知の制約

現行 repoのnetwork/traffic 検証 runsは本研究の正式運用 配送 simulation 結果ではない。

### 未解決の判断

plan conversion、traffic scenario、seed set、completion/failure event schema、output/acceptance paths。

### 次工程への引渡し

検証済み simulation outcomesを評価へ渡す。

## N. 評価

### 目的

検証済み simulation 出力から主要な fulfillment 評価指標とauxiliary diagnosticsを共通定義で算出する。

### 現在の状態

`PLANNED`（段階計画）/ `FUTURE`（ポータル）/ `NOT IMPLEMENTED`。式は現行 研究 設計だが正本 評価器と正式 評価指標 成果物はない。

### 開始条件

validated Delivery Simulation、fixed denominator population/time horizon/exclusions、metric schema、fixtures。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| 指標設計 | primary formula | [Research Overview Stage 7](RESEARCH_OVERVIEW.md) | `CURRENT RESEARCH DESIGN / NEEDS FORMALIZATION` | denominator scope unresolved。 |
| 基準需要仕様 | demand/P_eq semantics | [baseline demand and comparator](05_src/traffic_simulation/demand/20260718_20260903_baseline_demand_and_comparator.md) | `CURRENT_NORMATIVE` | 今後の主指標は本書最新採択方針のDFR_orders。旧代理指標の来歴を参照。 |
| シミュレーション結果 | evaluator input | 保存先未定 | `NOT AVAILABLE` | blocking。 |

主要な研究設計：

```text
DFR_orders = completed_orders / total_requested_orders
DFR_demand = sum(q_i * y_i) / sum(q_i)  # 荷物量を導入する場合
```

補助指標には、配送済み・未配送荷物換算単位、車両稼働率、所要時間、距離、電池使用量、到達不能需要を含む。これらを主要指標と混同しない。

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research evaluate status` | formula/evaluator/denominator状態表示 | 読取り専用 | formalization 隔たりを表示。 |
| `./research evaluate fulfillment --dry-run` | 欠落 evaluator/input/scope表示 | 読取り専用 | 評価指標を計算しない。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| コマンド操作安全制御 | [evaluate.py](05_src/research_cli/evaluate.py) | 欠落 評価器を明示。 |
| 正本評価器 | — | `NOT IMPLEMENTED` |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| 主要指標 | delivery fulfillment rate | 保存先未定 | `EXPECTED / NOT AVAILABLE` |
| 補助指標 | cause/resource diagnostics | 保存先未定 | `EXPECTED / NOT AVAILABLE` |
| 評価成果物一覧 | definitions/input hashes/aggregation | 保存先未定 | `EXPECTED / NOT AVAILABLE` |

### 正本・信頼源

現行 段階計画が主要な 設計を示すが、正式 評価指標 schema/evaluator/acceptanceは`NOT AVAILABLE`。本書は式をnormative化しない。

### 検証

| 検証器・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| 充足率評価器 | `./research evaluate fulfillment --dry-run` | formula/unit/scope/denominator/exclusions/aggregation fixtures PASS | `NOT AVAILABLE` |

<a id="受入done条件-13"></a>

### 受入・完了条件

評価指標 取り決め、denominator/time 計画期間、除外 方針を固定し、正本 evaluator/fixtures 合格、結果再現、uncertainty/failure 分解保存。

### 来歴

将来はsimulation ハッシュ値、評価指標 版、範囲、分母、除外項目、aggregation、評価器 版を保存する。

### 既知の制約

fulfillment 結果は未算出。`P_eq`とfulfillment rateの優先順位差が旧版 ポータル 登録簿上の未解決documentation 矛盾として残る。

### 未解決の判断

denominator scope、time horizon、unreachable/excluded demand treatment、primary/auxiliary metric contract。

### 次工程への引渡し

検証済み 評価指標、不確実性、不具合 分解を解釈とSensitivityへ渡す。

## O. エビデンスに基づく解釈

### 目的

直接分析境界`Delivery Fulfillment`の外側を、独立根拠に基づく条件付き解釈として接続する。計算処理工程ではない。

### 現在の状態

根拠 モデルは`CURRENT / IMPLEMENTED`、overall assessmentは`SUPPORTED_WITH_CONDITIONS`。研究結果に適用する段階は`FUTURE / NOT AVAILABLE`。

### 開始条件

一般的解釈設計の閲覧には根拠となる成果物のみ必要。研究結果の解釈には検証済み fulfillment 結果、想定条件、不確実性、感度が必要。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| 解釈根拠 | claims/sources/boundaries | [fleet_capacity_interpretation_v1.yml](reproducibility/evidence/fleet_capacity_interpretation_v1.yml) | `CURRENT` | 道路網 正本とは分離。 |
| エビデンスデータ構造 | status/traceability contract | [fleet_capacity_interpretation_v1.schema.json](reproducibility/evidence/fleet_capacity_interpretation_v1.schema.json) | `CURRENT` | 出典の確認 debtを保持。 |
| 充足率結果 | study-specific direct metric | 保存先未定 | `NOT AVAILABLE` | 結果 解釈は未実行。 |

解釈経路：

```text
技術・最適化
  → 配送充足
════════ 直接分析の境界 ════════
  → 未充足配送需要
  → 潜在的な実効配送能力要件
  → フリート増強・更新の潜在的必要性
```

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research portal status` | boundary/assessment表示 | 読取り専用 | 結果を生成しない。 |
| `./research portal check` | 根拠 schema/state/traceability検証 | Read-only validation | 研究 calculationなし。 |
| `./research artifacts` | 根拠 artifact/schema 保存先表示 | 読取り専用 | 出典 付随情報 inspection入口。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| エビデンス検証器 | [validate_fleet_interpretation_evidence.py](05_src/traffic_simulation/validation/validate_fleet_interpretation_evidence.py) | schema/status/source refs/index separation検証。 |
| ポータル状態・画面 | [serve.py](research_portal/serve.py) | 成果物からnode/panel/traceability生成。 |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| エビデンスモデル | reusable interpretation design | `reproducibility/evidence/fleet_capacity_interpretation_v1.yml` | `AVAILABLE` |
| ポータル 根拠状態 | node/link/source status | `/api/state` | runtime `AVAILABLE` |
| 研究固有の解釈 | evaluated 結果へのbounded 主張 | 保存先未定 | `NOT AVAILABLE` |

### 正本・信頼源

根拠となる成果物が解釈 出典。役割は`INTERPRETATION_ONLY`であり正式道路網 受入 chainを変更しない。

### 検証

| 検証器・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| 根拠成果物・データ構造 | `./research portal check` | 5 nodes/5 links、status/source refs/index separation valid | `PASS` |
| 解釈結果追跡 | — | 主張→評価指標→想定条件→根拠追跡可能 | `NOT AVAILABLE` |

<a id="受入done条件-14"></a>

### 受入・完了条件

根拠 設計は検証器 合格。調査-specific 解釈の完了には検証済み evaluation/sensitivityと、各主張のresult/Evidence 追跡が必要。

### 来歴

根拠 識別子、出典の確認 状況、claim/link 状況、artifact/schema 保存先を根拠となる成果物とリポジトリ索引に記録。

### 既知の制約

必須 additional 車両 件数、車両群 sizing 最適化、investment amount、実際の corporate investment predictionは`OUT OF SCOPE`。未充足 demandは車両 shortageと同義ではない。

### 未解決の判断

10 出典の完全bibliographic 付随情報が`NEEDS_SOURCE_VERIFICATION`。調査-specific 結果 解釈は上流未完了。

### 次工程への引渡し

bounded claimsと条件をSensitivity / Robustnessおよび最終publication 主張 追跡へ渡す。

## P. 感度・頑健性

### 目的

重要仮定を事前登録範囲で変化させ、結論をrobust、条件付き、insufficient 根拠へ分類する。

### 現在の状態

`PLANNED / NOT IMPLEMENTED`。過去の道路網-specific sensitivity/pilotを研究全体段階 10の現行 結果として扱わない。

### 開始条件

accepted baseline results、uncertain parameters/ranges、rerun/comparison protocol、claim interpretation。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| 段階 10ロードマップ | required domains/gate | [Research Overview Stage 10](RESEARCH_OVERVIEW.md) | `PLANNED` | routing/network/demand/battery/optimization/QUBO/scenarioを横断。 |
| 受入済み基準結果 | comparison anchor | 保存先未定 | `NOT AVAILABLE` | blocking。 |
| 感度分析登録簿・手順 | preregistered ranges | 保存先未定 | `NOT AVAILABLE` | blocking。 |

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research status` | 上流 stage 状態確認 | 読取り専用 | 感度専用コマンドなし。 |
| `./research pipeline full --dry-run` | closed 上流 gates確認 | 読取り専用 | 感度 実行は含まない。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| 汎用感度分析実行器・検証器 | — | `NOT IMPLEMENTED` |
| 履歴・道路網固有予備試験 | `reproducibility/outputs/...` | `HISTORICAL / NOT CURRENT STAGE 10` |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| 感度分析行列 | parameter×outcome comparison | 保存先未定 | `EXPECTED / NOT AVAILABLE` |
| 頑健性要約 | robust/conditional/insufficient classification | 保存先未定 | `EXPECTED / NOT AVAILABLE` |
| 失敗境界 | conditions changing conclusions | 保存先未定 | `EXPECTED / NOT AVAILABLE` |

### 正本・信頼源

段階 10 段階計画のみ。正式運用 感度 正本はない。

### 検証

| 検証器・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| 感度分析検証器 | — | preregistered ranges、complete runs、comparison/accounting valid | `NOT AVAILABLE` |

<a id="受入done条件-15"></a>

### 受入・完了条件

important uncertaintiesをsystematically varyし、missing/failed runsをaccountし、conclusion 分類を追跡可能にする。

### 来歴

将来は基準 ハッシュ値、パラメーター 登録簿、実行 行列、seeds、不具合 会計、比較 code/versionを保存する。

### 既知の制約

individual 道路網 感度 根拠の存在は終了-to-終了 研究 conclusion robustnessを示さない。

### 未解決の判断

ranges、factorial design、rerun budget、robustness threshold、missing-run policy。

### 次工程への引渡し

robustness 分類と不具合 boundariesをPublication / Reproducibility 固定へ渡す。

## Q. 公開・再現性凍結

### 目的

公開主張に必要な受入済み 成果物、設定、データ構造、ハッシュ値、ソフトウェア 版、コマンド、ポータル、documentationを一つの固定へ束ねる。

### 現在の状態

`FUTURE / NOT IMPLEMENTED`。リポジトリ索引、現行の正本、Markdown/link validatorsは現在利用可能な部分機構だが、研究全体freeze/release コマンドではない。

### 開始条件

公開対象となる全stageの受入済み 出力、検証 根拠、主張 追跡、sensitivity/limitations。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| リポジトリ索引 | current cross-reference | [research_repository_index_v17.yml](reproducibility/indexes/research_repository_index_v17.yml) | `CURRENT` | 最終 固定 成果物一覧ではない。 |
| 現行正本 | accepted network pointer | [current network authority](reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml) | `CURRENT` | 道路網 範囲のみ。 |
| ロードマップ | Stage 11 gate | [Research Overview](RESEARCH_OVERVIEW.md) | `CURRENT` | 最終 入力未完了。 |

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research validate` | 現行 authority/index/Portal横断検証 | 読取り専用 | 最終 固定を作らない。 |
| `./research portal check` | current Portal/document/artifact consistency | Read-only validation | 最終 publication 受入ではない。 |
| `./research artifacts` | current known artifact paths | 読取り専用 | complete publication 一覧ではない。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| リポジトリ索引検証器 | [validate_research_repository_index.py](05_src/traffic_simulation/network/validate_research_repository_index.py) | current pointers existence。 |
| Markdown・link validator | [validate_current_markdown_index.py](05_src/traffic_simulation/network/validate_current_markdown_index.py) | current metadata/link/inventory。 |
| 最終凍結・公開版 実行器 | — | `NOT IMPLEMENTED` |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| 現行索引 | present-state navigation | `reproducibility/indexes/` | `AVAILABLE` |
| 最終凍結成果物一覧 | all publication claims/artifacts/hashes | 保存先未定 | `EXPECTED / NOT AVAILABLE` |
| 保管・公開版 | immutable publication package | 保存先未定 | `EXPECTED / NOT AVAILABLE` |

### 正本・信頼源

段階 11のロードマップが将来ゲートを定義する。現行の道路網凍結機構は道路網範囲に限定され、研究全体の公開正本は`NOT AVAILABLE`である。

### 検証

| 検証器・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| 現行相互参照 | `./research validate` | authority/index/Portal PASS | `PASS for current scope` |
| 最終再現性監査 | — | all claims→accepted evidence、links/hashes/env/commands valid | `NOT AVAILABLE` |

<a id="受入done条件-16"></a>

### 受入・完了条件

全公開主張が固定済み 受入済み 根拠へ追跡可能、reproduction/link 監査 合格、versions/commands/hashes固定、Portal/overview/reference一致。

### 来歴

将来固定 成果物一覧にGit 変更記録、成果物 ハッシュ値、environment/software versions、コマンド、受入 IDsを保存する。

### 既知の制約

現行 indexesと道路網 受入済み 状態だけでは研究全体のpublication 固定にならない。

### 未解決の判断

freeze manifest schema、archive location、release procedure、claim inventory、final environment lock。

### 次工程への引渡し

publication、submission、archive release。

## 研究コマンド索引

`./research commands`が機械可読情報に近い正本コマンド一覧である。本節では運用上の読取・書込、前提条件、試行実行対応を補足する。全41インターフェースを収録する。

### 全体・確認・検証

| コマンド | 目的 | 前提条件 | 出力 | 変更 | 試行実行 |
|---|---|---|---|---|---|
| `./research status` | 研究全体の現在位置を表示 | ポータル・現行正本を読取可能 | 状態 | なし | いいえ |
| `./research artifacts` | 現行パスを表示 | 正本・索引を読取可能 | パス一覧 | なし | いいえ |
| `./research commands` | コマンド一覧を表示 | コマンド操作を取込み可能 | 41コマンドの索引 | なし | いいえ |
| `./research validate` | 正本・索引・ポータルを検証 | 現行成果物 | 検証結果 | なし | はい |

### 需要

| コマンド | 目的 | 前提条件 | 出力 | 変更 | 試行実行 |
|---|---|---|---|---|---|
| `./research demand status` | 需要の状態を表示 | 現行ポータル ノード 識別子 | 状態 | なし | いいえ、**現在は終了コード1** |
| `./research demand validate` | 基準需要試験と対応付け整合性を検証 | ローカルの需要・リクエスト・配送先 | 検証結果 | なし | はい |
| `./research demand build` | 基準需要→リクエスト→配送先を生成 | 安全な統合実行器 | 成果物 | 現在はなし、`NOT IMPLEMENTED` | はい |
| `./research demand future` | 将来需要の利用可否を表示 | 採択済みパラメーター | 状態・拒否理由 | なし | いいえ |

### ネットワーク

| コマンド | 目的 | 前提条件 | 出力 | 変更 | 試行実行 |
|---|---|---|---|---|---|
| `./research network status` | 受入済み道路網状態を表示 | 正本 | 状態・ハッシュ値 | なし | いいえ |
| `./research network acceptance` | 受入状態を確認 | acceptance JSON | ゲート・フラグ | なし | いいえ |
| `./research network validate` | 受入済み道路網を検証 | 現行の受入済み成果物 | 検証結果 | なし | はい |
| `./research network build` | 分離された構築を実行 | 一意な安全出力実行器 | 実行成果物 | 現在はなし、`NOT IMPLEMENTED` | はい |

### 経路計算

| コマンド | 目的 | 前提条件 | 出力 | 変更 | 試行実行 |
|---|---|---|---|---|---|
| `./research routing inputs` | 入力・判断事項を表示 | 正本・現行データ | 準備状況 | なし | いいえ |
| `./research routing status` | 工程状態を表示 | 正本 | 状態 | なし | いいえ |
| `./research routing build` | 経路コストを生成 | 採択済み範囲・方式と実行器 | 成果物 | 現在はなし、`NOT IMPLEMENTED` | はい |
| `./research routing validate` | 経路計算を検証 | 本番成果物・検証器 | 結果 | 現在はなし、`NOT IMPLEMENTED` | はい |

### 共通配送インスタンス

| コマンド | 目的 | 前提条件 | 出力 | 変更 | 試行実行 |
|---|---|---|---|---|---|
| `./research instance status` | インスタンス準備状況を表示 | リポジトリ | 状態 | なし | いいえ |
| `./research instance build` | 本番インスタンスを生成 | 検証済み経路計算・制約・生成器 | 成果物 | 現在はなし、`NOT IMPLEMENTED` | はい |
| `./research instance validate` | インスタンスを検証 | 成果物・検証器 | 結果 | 現在はなし、`NOT IMPLEMENTED` | はい |

### 古典最適化

| コマンド | 目的 | 前提条件 | 出力 | 変更 | 試行実行 |
|---|---|---|---|---|---|
| `./research optimization classical status` | 古典最適化の準備状況を表示 | リポジトリ | 状態 | なし | いいえ |
| `./research optimization classical run` | 共通インスタンスを解く | 受入済み問題例・求解器 | 解 | 現在はなし、`NOT IMPLEMENTED` | はい |
| `./research optimization classical validate` | 解を検証 | 結果・検証器 | 結果 | 現在はなし、`NOT IMPLEMENTED` | はい |

<a id="qubo--qaoa"></a>

### 制約なし二値二次最適化 / 量子近似最適化アルゴリズム

| コマンド | 目的 | 前提条件 | 出力 | 変更 | 試行実行 |
|---|---|---|---|---|---|
| `./research quantum status` | 量子工程の状態を表示 | 研究マップ | 状態 | なし | いいえ |
| `./research quantum qubo build` | 制約なし二値二次最適化を構築 | 固定済み定式化・問題例 | 制約なし二値二次最適化 | 現在はなし、`NOT IMPLEMENTED` | はい |
| `./research quantum qubo validate` | 等価性を検証 | 制約なし二値二次最適化・厳密最適値 | 結果 | 現在はなし、`NOT IMPLEMENTED` | はい |
| `./research quantum qaoa run` | 量子近似最適化アルゴリズムを実行 | 検証済み制約なし二値二次最適化・実行器 | 候補解 | 現在はなし、`NOT IMPLEMENTED` | はい |
| `./research quantum compare` | 古典・量子結果を比較 | 検証済み共通結果 | 根拠 | 現在はなし、`NOT IMPLEMENTED` | はい |

### シミュレーション・評価

| コマンド | 目的 | 前提条件 | 出力 | 変更 | 試行実行 |
|---|---|---|---|---|---|
| `./research simulation status` | simulation準備状況を表示 | 研究マップ | 状態 | なし | いいえ |
| `./research simulation run` | 計画を実行 | 検証済み計画・実行器 | 結果 | 現在はなし、`NOT IMPLEMENTED` | はい |
| `./research simulation validate` | simulation結果を検証 | 成果物・検証器 | 結果 | 現在はなし、`NOT IMPLEMENTED` | はい |
| `./research evaluate status` | 評価準備状況を表示 | 研究マップ | 状態・式 | なし | いいえ |
| `./research evaluate fulfillment` | 指標を計算 | 検証済みsimulation・評価器・範囲 | 指標 | 現在はなし、`NOT IMPLEMENTED` | はい |

### ポータル

| コマンド | 目的 | 前提条件 | 出力 | 変更 | 試行実行 |
|---|---|---|---|---|---|
| `./research portal status` | ポータル・現行状態を表示 | 正本成果物 | 状態 | なし | いいえ |
| `./research portal start` | ポータルを起動 | Python依存関係・成果物 | ローカルserver | processのみ、repo変更なし | はい |
| `./research portal check` | 正本・索引・マップ・根拠を検証 | 現行成果物 | 結果 | なし | はい |
| `./research portal build` | 単独引継ぎを生成 | 生成器 | 引継ぎ | 現在はなし、`NOT IMPLEMENTED` | はい |

### 統合実行

| コマンド | 目的 | 前提条件 | 出力 | 変更 | 試行実行 |
|---|---|---|---|---|---|
| `./research pipeline network` | 受入済み道路網を再利用・検証 | 受入済み道路網 | 検証 | なし | はい |
| `./research pipeline routing` | 入力→構築→検証 | 経路計算判断・実行器 | 成果物 | 現在はなし、`PARTIAL` | はい |
| `./research pipeline optimization` | 問題例→古典最適化→検証 | 検証済み経路計算 | 基準 | 現在はなし、`PARTIAL` | はい |
| `./research pipeline portal` | 現行状態を検証 | 正本成果物 | 結果 | なし | はい |
| `./research pipeline full` | 最初の閉じた判定基準まで実行 | 統制済み上流工程 | 工程要約 | 現在はRoutingで停止、`PARTIAL` | はい |

## 成果物・正本対応表

| 工程 | 判断 | 仕様 | 設定・登録簿 | スキーマ | 実行・出力 | 受入 | 現行正本 |
|---|---|---|---|---|---|---|---|
| 外部データ | — | 来歴記録 | source registry | 出典固有 | ローカル未加工・派生データ | 利用側工程ごと | 出典 登録簿＋利用側正本 |
| 需要 | — | 基準需要仕様 | 基準需要設定 | 組込み・設定検証 | ローカルParquet＋品質ジェイソン形式 | 独立した受入なし | 設定・仕様＋品質要約 |
| リクエスト・配送先 | — | 段階計画・設計記録 | ローカル実行要約 | `NOT AVAILABLE` | ローカルコンマ区切り形式 | 対応付け受入のみ | ポータル マップ＋道路網受入 |
| ネットワーク構築 | Three-tier Decision | 正式 Completion＋Pipeline仕様 | Three-tier registry | policy＋record schema | run_2・`three_tier.net.xml` | network acceptance JSON | 現行道路網正本 |
| 配送先マッピング | Three-tier Decision | 道路網 Pipeline仕様 | 受入済み実行 対応付け | 受入構造 | run_2 mapping JSON | network acceptance `/mapping` | 現行道路網正本 |
| ネットワーク受入 | Three-tier Decision | 道路網 Pipeline仕様 | 正本参照先 | policy・record | run_2 | `FORMAL_NETWORK_ACCEPTED=true` | 現行道路網正本 |
| 経路計算 | `UNRESOLVED` | roadmap Stage 1 | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | 段階計画・ポータル工程のみ |
| 共通インスタンス | `UNRESOLVED` | 段階計画 段階 2＋比較手順 | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | 設計のみ |
| 古典最適化 | `UNRESOLVED` | 段階計画 段階 3＋比較手順 | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | 設計のみ |
| 制約なし二値二次最適化 | `UNRESOLVED` | roadmap Stage 4A/4B | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | 設計のみ |
| 量子近似最適化アルゴリズム | `UNRESOLVED` | roadmap Stage 4C/4D | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | 設計のみ |
| シナリオ | `UNRESOLVED` | roadmap Stage 5 | EV profile＋baseline config | vehicle profile schema | `NOT AVAILABLE` | `NOT AVAILABLE` | 設計・現行仮定のみ |
| 配送シミュレーション | `UNRESOLVED` | 段階計画 段階 6＋V&V参照 | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | 設計のみ |
| 評価 | `UNRESOLVED` | roadmap Stage 7 | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | 研究設計のみ |
| 解釈 | 根拠設計 | 根拠成果物 | 根拠成果物 | Evidence schema | ポータル状態 | Evidence validator PASS | 解釈専用成果物 |
| 感度分析 | `UNRESOLVED` | roadmap Stage 10 | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | 設計のみ |
| 公開・再現性凍結 | `UNRESOLVED` | roadmap Stage 11 | リポジトリ索引（一部） | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | 将来判定基準のみ |

## 検証対応表

| 工程 | 検証器 | ゲート | 現在の結果 | 次工程を阻害するか |
|---|---|---|---|---|
| 外部データ | 利用側固有・需要 試験 | 登録出典・ハッシュ値を利用可能 | 利用可能、統合受入なし | 現行基準ではいいえ |
| 需要 | `demand validate`経由の`test_prepare_baseline_demand.py` | 設定・出典・保存則 | 実行時`PASS` | 現行基準ではいいえ |
| リクエスト・配送先 | `demand validate`経由の正本整合性 | ファイル存在・対応付け受入済み | `PASS`、再生成検証器なし | 再現性上の負債 |
| ネットワーク | `network validate`一式 | 登録簿・処理工程・スーモ・属性・接続性 | `PASS` | いいえ |
| 配送先マッピング | network acceptance・Portal validator | 39,956/39,956、許可道路区間 | `PASS` | いいえ |
| ネットワーク受入 | 正本検証器 | フラグ 真＋ハッシュ値一致 | `PASS` | いいえ |
| 経路計算 | 本番経路計算 検証器 | 必要出発地・到着地・方式・来歴 | `NOT AVAILABLE` | **yes** |
| 共通インスタンス | 本番問題例 検証器 | データ構造・完全性・実行可能性 | `NOT AVAILABLE` | **yes** |
| 古典最適化 | 正当性・結果検証器 | 定式化・検証用データ・結果 | `NOT AVAILABLE` | **yes** |
| 制約なし二値二次最適化 | 等価性検証器 | 古典・制約なし二値二次最適化等価性 | `NOT AVAILABLE` | **yes** |
| 量子近似最適化アルゴリズム | 共通実行可能性・比較 | 再現可能な候補・共通検査器 | `NOT AVAILABLE` | **yes** |
| シナリオ | scenario validator | 出典・範囲・変換 | `NOT AVAILABLE` | **yes** |
| 配送シミュレーション | 本番simulation 検証器 | 実行・不具合・来歴 | `NOT AVAILABLE` | **yes** |
| 評価 | 正本評価器 検証用データ | 範囲・分母・式 | `NOT AVAILABLE` | **yes** |
| 解釈 | Evidence validator | schema・status・source trace | 設計は`PASS`、結果判定基準は利用不可 | 結果主張にははい |
| 感度分析 | sensitivity validator | 事前登録済み行列・集計 | `NOT AVAILABLE` | **yes** |
| 公開・再現性凍結 | 最終監査 | 主張・リンク・ハッシュ値・環境・コマンド | `NOT AVAILABLE` | 最終判定基準 |

## 依存関係表

| 下流工程 | 必要条件 |
|---|---|
| 需要 | 統制済み開く-data 出典＋基準 設定・仕様 |
| リクエスト・配送先 | 検証済み基準需要＋生成・範囲取り決め |
| 配送先マッピング | 配送先＋正式・交通シミュレーターの道路網＋車両 通行許可 |
| ネットワーク受入 | スーモ validity＋対応付け＋主要到達可能性 判定基準 |
| 経路計算 | 受入済み道路網＋受入済み対応付け＋リクエスト・配送先＋解決済み範囲・配送拠点・車両・費用 |
| 共通インスタンス | 検証済み経路計算＋需要・配送先＋配送拠点・車両群・容量・電池制約 |
| 古典最適化 | 受入済み共通インスタンス＋固定済み定式化・検査器・予算 |
| 制約なし二値二次最適化 | 受入済み共通インスタンス＋固定済み古典定式化＋厳密解検証用データ |
| 量子近似最適化アルゴリズム | 検証済み制約なし二値二次最適化＋採択済み実行・復号 手順 |
| シナリオ | 受入済み基準＋根拠に基づくパラメーター・年・変換 |
| シミュレーション | 受入済み道路網・問題例・想定条件＋検証済み配送計画 |
| 評価 | 検証済みsimulation＋固定済み指標分母・範囲 |
| 解釈 | 検証済み評価＋想定条件・不確実性＋根拠成果物 |
| 感度分析 | 受入済み基準結果＋事前登録済み不確実範囲・手順 |
| 公開・再現性凍結 | 主張対象の全工程を受入済み＋主張・根拠 追跡＋再現性監査 |

## 現行ライフサイクル境界

- `CURRENT / ACCEPTED`: Three-tier Formal Completion、run_2 network、mapping、network acceptance。
- `CURRENT DESIGN`: baseline demand spec/config、comparison protocol、EV profile assumption、interpretation Evidence。
- `HISTORICAL`: strict v17、old run_4/run_5/run_6、old blockers/failures、temporary diagnostics。
- `SUPERSEDED`: 階層型混合方式 決定記録とpre-Three-階層 処理工程 policies。
- historical/superseded 成果物を現行 コマンド 入力または現行 受入として再利用しない。

## 文書の役割分担

`RESEARCH_OVERVIEW.md` = 研究概要・ロードマップ

`RESEARCH_PIPELINE_REFERENCE.md` = 現行パイプラインの実行・正本・検証リファレンス
