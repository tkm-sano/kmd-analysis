# Quantitative Research Guide

正式API・保存結果・小規模再利用の統合ガイドです。科学的凍結報告とは別の利用説明であり、研究の数値・RQ・仮説は変更しません。

- [1. Research Scope](#1-research-scope)
- [2. Model Architecture](#2-model-architecture)
- [3. Routing Model](#3-routing-model)
- [4. Quantum Model and Protocol V2](#4-quantum-model-and-protocol-v2)
- [5. Simulation and Trajectories](#5-simulation-and-trajectories)
- [6. Battery and Controlled-DC Energy](#6-battery-and-controlled-dc-energy)
- [7. Analysis and Frozen Results](#7-analysis-and-frozen-results)
- [8. Data and Configuration](#8-data-and-configuration)
- [9. Notebook Guide](#9-notebook-guide)
- [10. Quickstart and Dependencies](#10-quickstart-and-dependencies)
- [11. Reproducibility and Verification](#11-reproducibility-and-verification)
- [12. GitHub and Hayate Responsibilities](#12-github-and-hayate-responsibilities)
- [13. Data Attribution and Licensing](#13-data-attribution-and-licensing)
- [14. Limitations and Provenance](#14-limitations-and-provenance)

## 1. Research Scope

必要な配送サービスを充足しながら、その実現に伴うエネルギー消費を低減することが上位の問題意識です。本配布物はEVラストマイル配送の限定された定量モデルと保存結果を扱います。

正式RQ（原文引用）：> 量子技術の進展は、電気自動車配送の経路計算とバッテリー性能の変化を通じて、ラストマイル配送の運用電力量にどのような影響を与えるか。

正式主仮説（原文引用）：

> 同一の充電を考慮した電気自動車配送問題において、古典計算を用いた場合と比較して、量子計算を用いた場合の方が、バッテリー性能の違いによる電気自動車配送の運用電力量の差が大きくなる。

正本はHayate保存の `01_research_design/RESEARCH_QUESTION_AND_HYPOTHESIS.md`（SHA256 `abe729fc925372782bc62c5a4f3e597c09b5c214acfd31c3ec912f3efb85cb33`）。上記はその文言の引用であり、新しいRQ・仮説ではありません。**充電を考慮した正式主仮説と、今回配布する無充電・固定軌跡の評価範囲は同一ではありません。主仮説の検証完了を主張しません。**

## 2. Model Architecture

需要/地点→固定割当・時間窓・OD→古典baseline→R0/R1共通Protocol V2→取得経路→保存SUMO軌跡→Battery質量条件・Controlled-DC→Method×Battery/古典6規模→正式freeze、という接続です。

|配置|役割|
|---|---|
|`src/kmd_quantitative/routing/`|訪問順の決定と独立した可行性検査|
|`quantum/`（同src配下）|Candidate C PUBO・正式標本選択・qualification処理|
|`simulation/`|保存CSV/CSV.gzの時刻・速度読込み|
|`battery/` / `energy/`|質量条件とControlled-DC|
|`analysis/`|保存結果の検査・読込み。科学的再集計ではない|
|`configs/` / `data/examples/`|設定参照と小規模合成入力|
|`results/indexes/`|正本結果の所在・hash・schema|
|`notebooks/` / `tests/` / `scripts/`|公開利用・軽量検証|
|`reproducibility/`|環境lock・配布Manifest・凍結原本対応|

通常の利用入口はsrc APIです。旧sourceを利用者のsys.pathへ追加しません。結果原本は01_research_designに保持します。需要生成・全量割当・OD・全量SUMOの実行入口を提供する配布ではありません。

## 3. Routing Model

[solver.py](../src/kmd_quantitative/routing/solver.py)と[independent.py](../src/kmd_quantitative/routing/independent.py)が正式入口です。固定顧客集合・固定割当の単一車両/単一巡回について道路旅行時間を最小化し、訪問・時間窓・容量・帰還期限を独立に確認します。道路グラフ上のedge経路と顧客訪問順は別です。

Notebook01はデポ＋3顧客の合成fixtureで厳密探索、訪問順・旅行時間・制約を確認し、時間窓を変えて再計算します。需要の単位parcel-equivalentをkgと混同しません。小規模の厳密解法と、保存済み大規模結果のヒューリスティック・LP下界を区別します（第7節）。経路取得と配送充足も別です。

## 4. Quantum Model and Protocol V2

### PUBO構築

[builder.py](../src/kmd_quantitative/quantum/builder.py)の `build_C(model,a)` は `(q, poly)` を返す。q=n²、polyはビットindexのtupleをキーとするDecimal係数。変数indexは `(customer-1)*n+position`。`route_code(order,n)` はindexを下位bitから数える整数で、Qiskit表示文字列の左端がbit0という意味ではない。両one-hot、道路旅行時間、可行性事前表の違反完全順列に対するn次罰則を元の関数ASTから計算する。罰則Aはmodelのpenalty_s。目的は電力量でなく道路旅行時間。

入力aはnodes/travel/distance/ready/due/service/demand等の正式配列契約、modelはn/penalty_s/capacity_ok/permutations等の完全な事前情報。欠落した順列表を補ったり、任意の配送問題向けに制約を一般化するAPIではない。

### 復号と可行性

[formal.py](../src/kmd_quantitative/quantum/formal.py)が正式処理へのadapter。

- `feasible_route_table(model,a)`：事前表でcapacity/TIME_WINDOW/RETURN_HORIZONを満たす順列をroutingの独立validatorで検査し、code→経路表と事後評価用の厳密最小旅行時間を返す。表が空なら元実装と同じAssertionError。
- `parse_sample_counts(raw_counts,shots)`：Qiskit形式の文字列キーを整数へ変換し総shotsを検査。空白区切りを除去する元処理。非binary文字はValueError、shots不一致はProtocolFailure。
- `evaluate_final_counts(model,a,counts)`：整数codeを可行表へ照合し、最終経路を再度独立validatorで検査して返す。返り値は `final_feasible_count`, `sampled_feasible_routes`, `best_final_feasible_route`。

このAPIは信頼されたsampler契約の入力用。幅・負数・bool等に対する包括的入力防御を元コードに追加したものではない。未知の整数codeは除外される。正しい可行問題に可行標本がない場合は空経路一覧・Noneであり、可行問題自体がない場合とは異なる。`python -O` は使わない（正式validatorはassertを利用）。

### 最終経路選択

`select_final_route(routes)` は独立検査済みの正式recordを前提とする低水準API。道路旅行時間のDecimal値、整数bitstringの昇順でminを選ぶ。頻度・最適フラグは同点の基準ではない。空一覧はNone。正式標本の復号も必要ならevaluate_final_countsを使う。

parameter incumbentの選択は別規則：域内・有限評価から可行標本数最大→平均エネルギー最小→評価index最小、可行標本ゼロなら平均エネルギー→index。バイト一致のquantum/protocol_v2/protocol.pyに保持する。最終4096標本のみが経路取得のauthority。probe標本を混ぜない。

### 古典・量子の分担

入力構築、全順列可行性、PUBO、COBYLA、復号・独立検証・経路選択は古典処理。正式QAOAは理想StatevectorSamplerであり実機ではない。p=1、H初期状態、X mixer、最大100目的評価・各2048shots、独立seedの最終4096shots。詳細条件は凍結protocol/planを優先する。

静的回路生成元は static_reduced_circuit_resources.py（Hayate保存参照: `05_src/traffic_simulation/matched_quantum_qualification/static_reduced_circuit_resources.py`、公開ツリー非同梱） のbinary_poly_to_z/make_circuit。回路はAで正規化したpolyをx=(1−Z)/2へ変換し、RZ/RZZ/CXパリティ列とRx(2β)を構成する。scienceは保存QPYを読み、目的評価のmean_energy_sには非正規化PUBOを使用する。この違いを同一視しない。生成scriptはトップレベルに出力処理があり、importしない。今回回路生成・実験は行っていない。

### 利用例

repo rootから `PYTHONPATH=src python -B`、またはJupyterでrepoのsrcをsys.pathへ加える。既存Notebook環境を利用する。

```python
from kmd_quantitative.quantum import builder, formal
# aとmodelは02 Notebookまたは正式入力契約に従って用意する。
q, poly = builder.build_C(model, a)
counts = formal.parse_sample_counts(raw_counts, shots)
result = formal.evaluate_final_counts(model, a, counts)
print(result['best_final_feasible_route'])  # Noneも正当な結果
```

例のa/model/raw_countsは自動取得されない。環境と検証は第10・11節を参照。

### qualificationとの差

qualification_builder.pyはprefix-AND補助変数を含むQUBOで、正式Candidate Cは補助変数なしのPUBO。前者の可行性・罰則metadataは最終V2にも利用される。decoder.pyはbit配列の幅・binary・one-hot・物理条件・ancillaを独立検査する。正式V2はこのdecoderを呼ばず可行表とvalidatorを使う。両者の入力・エラー・出力形式も異なる。

### Notebookとの差

02の回路は未正規化PUBOのdense教材回路、既定64shots、最大6評価の任意最適化は未検証。正式QPYの正規化、角度、seed、2048/4096shotsの再現ではない。PUBOと最終標本判定のみ正式APIへ統一した。既定の最終可行0/64はNOT_ACQUIREDのまま。教材結果を正式R0/R1結果に置き換えない。

## 5. Simulation and Trajectories

### Routingとの接続

routingは顧客の訪問順を決定する。SUMOの道路edge列とは別物。matched Classicalの `generate.py:prepare` は保存resultのcustomer_orderをroute_sequenceへ対応付け、端点ごとのtripを作成し、position-aware duarouter_loopの保存edge経路を用いる。共有 `generate_canonical_delivery_trajectories.py:build` が隣接legの重複境界edgeを連結し、stopのlane/endPos/duration/untilを設定する。

Quantumは最終取得経路のみを扱う。最終R0 commonは78件が同一経路で保存Classical軌跡へ結合、R1は同一59件・異経路5件という既存系譜を維持する。未取得経路を新規に補完しない。今回これらの生成・再結合は実行していない。

### 道路・OD

道路networkは凍結GENERATION_PLAN.jsonのnetwork/sha256で指定。FROZEN_ENDPOINTS.parquetからnode_id/role別のedge/lane/positionをENDPOINT_READBACKへ写す。OD旅行時間はrouting目的、SUMO観測走行時間は別指標。道路グラフ読込みはnative router/SUMO側で、Pythonの汎用road APIを今回新設しない。

### Simulation入力と実行

固定訪問順、端点、道路network、leg経路、車両type、service stop条件が必要。既存planはstep/FCD周期1秒、seed=20260930、独立単一車両・背景交通なし。matched生成は `canonical_sumo_fork.cpp` のnative time-zero forkを利用する。標準SUMOバイナリだけで同じ実行環境が成立すると仮定しない。

### Trajectory出力

canonical CSVの保存列はroute_id、vehicle_id、timestamp_s、speed_m_s、x_m、y_m、lane_id、edge_id、position_m、angle_deg、slope_deg。matched版はphysical_instance_idとcanonical_trajectory_idも含む。x/y/positionはm、角度・勾配はdegree。position_mはlane上の位置で、累積走行距離ではない。

時刻はSUMO simulation時刻s、速度m/s。delta_time列・累積distance列・departure_time/arrival_time列はこのCSVにない。dtは隣接時刻差、出発/到着・native routeLengthはtripinfo/manifestの別記録。FCD観測はdeparture, arrival)で、DC評価は最初〜最後の観測点間だけ。最後の観測から到着eventまでを補間しない。

### Controlled-DCへの受渡し

```python
from kmd_quantitative.simulation.trajectory_io import read_dc_input
# repo rootからPYTHONPATH=src、またはsrcをsys.pathへ追加
# manifest_rowとhashは正式manifestから別途取得する。
t, speed = read_dc_input(path, expected_sha256=hash_value, metadata=manifest_row)
# 既存run_full_controlled_dc.pyのevaluateへ、この2配列をそのまま渡す。
```

読込みは既存 `apply_r0_method_battery.py` のdf/t/speed代入3文をSHA256確認後にASTで実行する。このR0 sourceは最終R1/R0 commonの現役依存でもある。トップレベルの監査・出力・計算loopは実行しない。エネルギー式をadapterへ移さない。

新APIの入力guardは長さ2以上の同長1次元・有限数値・非負速度・厳密1秒刻みを要求する。不正入力はValueError等で拒否し、並べ替え・補間・欠損補充しない。有効配列の数値・dtype・行順は元pandas読込みと一致。optional hashは圧縮file bytes、optional metadataはsample_count/integration_interval_count/first_sample_s/last_sample_sを確認する。これらのguardはAPI境界の検査であり、配送制約判定の変更ではない。

Controlled-DCは右端速度×dtで区間距離を扱い、Whを返す。CSVのposition差やOD距離へ置換しない。元DCの非1秒刻みassertと、新APIの早期ValueErrorは例外型が異なる。全フィールド・SUMO完了・時間窓をこの2列loaderだけで検証したとは扱わない。

保存軌跡の読込みにSUMO本体は不要です。全量生成にはnative SUMO1.24・専用duarouter_loop・canonical_sumo_fork・道路網・端点・固定assignment/result等が必要で、標準SUMOだけで同条件になるとは仮定しません。

## 6. Battery and Controlled-DC Energy

### Path 2の対象

容量20 kWhを固定し、パック比エネルギー180/220/250 Wh/kgによるパック質量の変化を車両質量へ反映する。容量増加や量子材料計算を扱わない。同一の保存走行軌跡に異なる質量条件を与える感度評価であり、実電池性能の達成・実車検証ではない。

### Battery入力・出力

[mass.py](../src/kmd_quantitative/battery/mass.py) は `official_mass_stages()` と `mass_at_specific_energy(selected)` を提供する。前者は元stage loopの全mass record、後者は既存Notebookと同じCUSTOM感度条件。入力selectedはWh/kg、計算容量は20 kWh固定。

[scenarios.py](../src/kmd_quantitative/battery/scenarios.py) の `load_model()` はhash固定の [モデルfreeze](../01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json) を新しいdictとして読む。`stage_inputs()` はEnergyに渡すB0/B1/B2の凍結入力。呼出しごとに読み直すため返却dictの編集はfreezeを書き換えない。編集した条件は正式条件ではない。

### 比エネルギーとパック質量

原sourceの関係は `m_pack = 20000 / e_pack`。B0/B1/B2のパック質量は約111.111111 / 90.909091 / 80 kg。新APIへ数式をコピーせず、review_pack_specific_energy.pyのcalcとstage loop、またはcustom用の元3文をASTとして呼ぶ。レビューsourceのmain全体・文献処理・表書込みは起動しない。stage選定用の相関式を今回変更・更新していない。

### 車両質量

B0車両基準1100 kgからB0パック質量を差し引いた共通残余に各パック質量を加える。車両質量は1100 / 1079.79797979798 / 1068.888888888889 kg。Energyに渡すrunning_mass_kgは共通運転者55 kgを含む1155 / 1134.79797979798 / 1123.888888888889 kg。積載・追加設備は0 kg。パック軽量化の結果として車両質量が変わる。

### Controlled-DC入力

[controlled_dc.py](../src/kmd_quantitative/energy/controlled_dc.py) の `evaluate(t,v,model,pressure,stage)` は元run_full_controlled_dc.pyの関数そのものを公開する。tは秒、vはm/s、1秒間隔の同長numpy配列、pressureは既存Crr条件p_bar、stageはrunning_mass_kg等の凍結dict。配列順を変更しない。

CSV入力はSimulation API `read_dc_input` で検査する。Energy低水準APIのassert/例外は元関数と同一で、一般的入力validatorではない。一部の異長配列はNumPy broadcastで計算され得るため、直接呼ぶ側も契約を守る。Simulationの等長/有限値/1秒guardを通す。`python -O` は使わない。欠損補充・端点補間・並べ替えはしない。

### 出力と18 kWh

返り値は `(out, arrays)`。outの主項目はtraction_DC_Wh/net_DC_Wh/cumulative_DC_Wh、observed_interval_count/observed_distance_m、成分Wh、Wh_per_observed_km、initial/minimum/terminal_stock_Wh、stock_integrity、boundary等。arraysはroll/translational/rotational/aero/wheel/dcの区間Wh配列（N−1要素）。負仕事は符号付き成分と非負の負側magnitudeを区別する。

**18 kWhは実際の残量会計に使われる。** 元核は `18000 - np.cumsum(dc)` を計算し、負残量をSTOCK_INTEGRITY_FAILとして記録する。18000は核内固定値であり、返却modelのstock_accountingだけを編集して可変SOCモデルにできるわけではない。残量で走行を打ち切らず、clampせず、充電やSOC依存効率を計算しない。

### 物理モデル・評価境界

元freeze/実装では右端速度×dtで区間距離、隣接速度二乗差で並進・回転運動エネルギーを扱う（加速度配列は返さない）。転がり抵抗係数は `0.005+(0.01+0.0095*(3.6*v/100)^2)/p_bar`。p_bar=4.5/2.6はCrrの上下境界で、実際の圧力変更実験や信頼区間ではない。

g=9.80665 m/s²、rho=1.2041 kg/m³、CdA=1.175 m²、回転等価質量61 kgは段階共通。roll+translation+rotation+aeroの仕事を3600でJ→Whへ変換し、合計wheelの正側を一定効率0.90で除してDC電力量とする。成分ごとに正側を先に切り取る処理ではない。平坦、回生なし、補機対象外、turn loss対象外。負wheel仕事を充電として扱わない。

内部会計のnearは相対1e-11・絶対1e-7 Wh。新APIの数値回帰は元関数との完全一致。`scalar_check` も元関数を公開する。

### Simulation接続・実行例

既存Notebook環境でrepo rootから `PYTHONPATH=src python -B`：

```python
from pathlib import Path
from kmd_quantitative.simulation.trajectory_io import read_dc_input
from kmd_quantitative.battery.scenarios import load_model, stage_inputs
from kmd_quantitative.energy.controlled_dc import evaluate

t, speed = read_dc_input(Path('notebooks/fixtures/speed.csv'))
model = load_model()
for stage in stage_inputs():
    out, arrays = evaluate(t, speed, model, 4.5, stage)
    print(stage['stage_id'], out['net_DC_Wh'])
```

このCSVは人工4標本で、SUMOの科学結果ではない。正式保存軌跡を使う場合はmanifestと圧縮ファイルhashをread_dc_inputへ渡す。実軌跡1,319標本も過去の移行検証で6条件の回帰に使用したが、配布fixtureに複製していない。

## 7. Analysis and Frozen Results

### 対象と正式な実装

`src/kmd_quantitative/analysis/` は保存結果の読込み専用APIです。既存の分析ソース・表・freezeは原位置で保持します。物理移動、科学的集計の再実装、新規実験、欠損補完は行いません。

- [method_battery.py](../src/kmd_quantitative/analysis/method_battery.py)：最終共通Protocol R0/R1。
- [scale_analysis.py](../src/kmd_quantitative/analysis/scale_analysis.py)：古典6規模の保存表と診断。
- [result_io.py](../src/kmd_quantitative/analysis/result_io.py)：13の保存ファイルについてSHA256・サイズ・列/キー・行数を検査。返却値は新しいdict/DataFrameです。

統合分析ソース（Hayate保存参照: `01_research_design/scenario_evaluation/matched_r0_r1_common_protocol_scale_method_battery_20261008/analyze_frozen_results.py`、公開ツリー非同梱）と古典Scale×Battery分析ソース（Hayate保存参照: `05_src/literature_analysis/analyze_classical_scale_battery.py`、公開ツリー非同梱）にはトップレベルの検証・集計・書込みがあります。APIはこれらをimportしません。数式をAPIに複製せず、生成済み結果を読みます。

### Method×Batteryの比較構造

正式R0は3顧客、R1は4顧客。各78実験条件で最終標本からR0は78経路、R1は64経路を取得しました。R1の14未取得は配送不可能を意味しません。歴史的R0の40/78取得結果とは別です。

`parent_id, replicate_id` で対応する計画78ブロックから、両側に経路がある64を使用します。26 parent・25 groupに属し、3 subset replicateは独立した量子反復や独立地理標本ではありません。R0/R1で同じ顧客課題でもありません。未取得14の値をゼロにせず、`population()`は除外理由と空欄を残します。

`contrasts()`は64×2 Crr×2比較＝256行。`energies()`は64×2 Crr×3 Battery＝384行。全R0で同一経路、R1で59同一・5異経路。4条件それぞれTゼロ59・非ゼロ5（正1・負4）で、4条件を256独立標本にまとめません。

### 古典6規模の比較構造

n=3,4,5,25,99,125。各78論理インスタンス、合計468論理に対して460実体です。R5は78論理が70実体を参照し、他の規模は各78実体。重複対応を独立サンプルとして数えません。

n≤5はEXHAUSTIVE_PERMUTATIONS / PROVED_OPTIMAL。n≥25はDETERMINISTIC_HEURISTIC_3_SWEEPS_PLUS_HIGHS_ASSIGNMENT_LP / BOUNDED_GAP_NOT_GLOBAL_OPTIMUM。顧客構成、地理、時間窓、解法が異なるため、顧客数単独の因果効果ではありません。大規模側の量子計算結果はありません。

`conditions()`はデポDEP_006、容量216 parcel-equivalent（kgではない）、静的departure=0 s、return deadline=32400 s、TW幅7200 s、顧客service=102 s等の保存条件を返します。実業務の条件を実測したことは意味しません。

### 評価指標

正式freezeの定義：

- Battery saving (%) = `100*(E_B0-E_Bk)/E_B0`。分母は各scale・method・経路・Crr条件のB0 DC Wh。
- D = Classical saving − Quantum saving。
- T = D_R1 − D_R0。主表示単位はpercentage points（pp）。元の正式仮説のkWh応答差と同一ではありません。
- `_Wh`のsaving contrastも保存されていますが、ppと混ぜません。
- 直接の電力量差はQuantum − Classical。saving Dと符号の定義が異なります。

`summary()`は最終freezeの4条件の保存集計です。母数64、中央値0、標準偏差はddof=1。`mean_decimal`は元のDecimal文字列を保持します。T=0は計算性能の同等性、量子優位性、統計的有意差を示しません。

### 古典側の集計単位

`battery_summary()`は24行、各scale×Crr×B1/B2について78論理の削減率分布（percent）。Scale×Battery interactionの集計そのものではありません。

`interaction_summary()`は既存112行を返します。40行のEQUAL_PARENT_MEAN_CONTRASTはブロック内の規模差→parent内3replicate平均→26parent等重みの集計（pp）です。他の72行はREPLICATE_LOGICAL_REDUCTION、UNIQUE_PHYSICAL_REDUCTION、EQUAL_PARENT_REDUCTION（percent）。`summary_type`, `unit`, `count`, `planned_count`, `algorithm_stratum` を保ち、異なる推定対象を混ぜません。B2が元分析の主対象、B1は副対象です。

### 入力ファイル

`result_io.artifacts()`がパス・SHA256・サイズ・schema・保存行数の一覧を返します。ファイルは既存パスで配布する必要があります。主な所在：

| API | 保存入力 |
|---|---|
| freeze / summary | `final_quantitative_study_20261008/FINAL_QUANTITATIVE_RESULT_FREEZE.json`, `FINAL_SCALE_METHOD_BATTERY_SUMMARY.csv` |
| population / contrasts / energies | `matched_r0_r1_common_protocol_scale_method_battery_20261008/COMMON_MATCHED_POPULATION.csv`, `SCALE_METHOD_BATTERY_MATCHED_CONTRASTS.csv`, `DIRECT_METHOD_ENERGY_SCALE_COMPARISON.csv` |
| routes / battery_summary / interaction_summary | `01_research_design/methodology/MATCHED_CLASSICAL_ROUTE_SCALE_SUMMARY.csv`, `MATCHED_CLASSICAL_BATTERY_SCALE_SUMMARY.csv`, `CLASSICAL_SCALE_X_BATTERY_SCALE_SUMMARY.csv` |
| methods / conditions / service_diagnostics | `quantitative_scale_boundary_synthesis_20261008/CLASSICAL_QUANTUM_SCALE_COMPARISON.csv`, `SCALE_INSTANCE_COMPARISON.csv`, `LOGISTICS_SERVICE_SCOPE.csv` |
| battery_conditions / trajectory_validation | `01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json`, `MATCHED_CLASSICAL_TRAJECTORY_VALIDATION.json` |

上表のディレクトリ短縮名は `01_research_design/scenario_evaluation/` 配下です。既存結果をコピー・加工した新しいfreezeは作成しません。

### 出力と検査

JSONはdict、CSVは既存Notebookと同じ `pandas.read_csv` のDataFrameを返します。CSVで `raw=True` を指定すると文字列dictのリストになり、Decimalの原文・空欄・行順を保持します。DataFrame表示では空欄がNaNへ変換されますが、ゼロ補完・行除外・再集計はしません。APIはファイル出力を行いません。

欠損はFileNotFoundError、改変はValueError、未登録artifact keyはKeyError。hash確認とschema確認はバイト整合性検査で、モデルの科学的妥当性を新たに証明するものではありません。証拠内の絶対パスや外部ファイル参照は来歴文字列で、自動追跡しません。`root=`は同じ相対配置を復元したディレクトリに指定でき、hashを回避する機能ではありません。

### Authority・処理区分

FROZEN_RESULTは元の保存値、NOTEBOOK_PRESENTATIONはその表示、SMOKE_TESTはAPI接続検査です。今回はDETERMINISTIC_REAGGREGATIONを公開APIに追加していません。テスト内のDecimal恒等式・件数照合は保存値の整合性確認に限定し、新しい結果や検定を保存しません。

release manifest（Hayate保存参照: `reproducibility/release/RELEASE_MANIFEST.json`、公開ツリー非同梱）と正式source/freezeは変更しません。Phase6の入力hash catalogは再利用の契約であり、過去のauthorityを置換しません。古典側はroute execution、Battery validation、後続Scale×Battery分析の保存記録を区別します。先行validationのNOT_YET_EXECUTEDを後続分析未実施と誤読しません。

### 配送充足の境界

静的可行性、SUMO走行完了、SUMO観測時刻の診断、現実の全需要充足を区別します。古典matched460はL2 COMPLETEでも、L3遅延はR4が73停止/61経路、R5が63停止/55経路、合計136停止/116経路。帰還期限超過はR4=1、R5=3の計4経路です。全域465経路の別診断と混同しません。

APIはこれらを除外しません。native VRPTW全条件再検証はFalse、実業務充足は未検証。電力量を計算できることと配送条件を満たすことは別です。未配送による低消費を省エネルギー達成としません。

### エネルギー境界

20 kWh容量固定、180/220/250 Wh/kgによるパック・車両質量条件、同一軌跡内の比較です。18 kWhは既存残量会計条件。2 Crr境界は圧力変更実験・信頼区間ではありません。DC Whは保存観測区間のみ、平坦・回生なし・補機対象外・エネルギー側積載0 kg・効率一定。充電・計算・通信・設備・製造を含む社会全体のエネルギーではありません。

入口は[正式結果Index](../results/indexes/CANONICAL_RESULTS.json)と[凍結研究報告](../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_STUDY_REPORT.md)です。Indexは新しいfreezeではなく、13保存ファイルを参照します。`from kmd_quantitative.analysis import method_battery as mb, scale_analysis as scale` の後、`mb.summary()`、`scale.service_diagnostics()`等を利用できます。

## 8. Data and Configuration

[CANONICAL_CONFIG_INDEX.csv](../configs/CANONICAL_CONFIG_INDEX.csv)は19の役割別参照です。需要・固定割当・OD・routing・PUBO/QAOA・SUMO・Battery/DC・統合分析・古典6規模・検証を対象とします。同じfreezeを複数の役割が参照します。設定だけでなく、入力bindingや実験計画も区別して記録しています。

正式設定は元位置に保持します。Indexのsource_path、SHA256、サイズ、using_implementation、パラメータ参照、既定値抜粋、seed方針、外部入力を確認してください。物理移動・設定値の変更・正式設定のコピーは行っていません。source freezeとauthority chainは既存のままです。Index自身は新しいfreezeではありません。

[examples/NOTEBOOK_INPUTS.json](../configs/examples/NOTEBOOK_INPUTS.json)は小規模Notebookの**入力パスを指定する設定例**です。正式実験設定ではなく、QAOAの回路・角度・seed・shots・最適化条件を上書きしません。Notebook02の既定値はgamma=0.001、beta=0.2、shots=64、seed=20261009、DO_OPTIMIZE=False。正式Protocol V2のp=1・最終4096標本等とは別です。

Notebook adapterはこの設定からdata/examplesのfixtureを選び、登録hashを検査します。入力が欠損・改変されていれば停止し、旧fixtureへ自動フォールバックしません。初期入力の値を変える場合はNotebookのメモリ上の条件変更例を使ってください。新しい入力ファイルを登録する場合は独立したDEMONSTRATIONとして来歴・hashを更新し、正式freezeを書き換えないでください。




[examples/PROVENANCE.json](../data/examples/PROVENANCE.json)に、既存fixtureからの3つのバイト一致コピーと元SHA256を記録しました。実験データの抽出や再生成はしていません。旧notebooks/fixturesは既存テストの互換参照として保持します。配布コピーを独立に変更せず、一致検査を継続します。

|配布入力|用途・単位|種別|
|---|---|---|
|[three_customers.json](../data/examples/three_customers.json)|デポとA/B/C、4×4 travel秒・distance m、時間窓/サービス秒、需要parcel-equivalent、期待40秒の巡回|既存の合成routing/PUBO fixture。実座標・実道路・現実の配送地点を含まない|
|[speed.csv](../data/examples/speed.csv)|timestamp_s、speed_m_s、4標本の0〜3秒・10m/s|合成軌跡。保存SUMO実験の実測軌跡ではない|
|[speed.json](../data/examples/speed.json)|既存の同じ小規模軌跡・期待電力量等|Controlled-DC検証用の既存証拠|

Battery条件は[正式モデルfreeze](../01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json)を参照し、別の条件表を複製しません。容量20 kWh、初期利用可能18 kWh、比エネルギー180/220/250 Wh/kg。18 kWhは残量会計・負残量判定に使用し、SOCによる停止・充電・再計画は実装していません。

Notebook01/02は共通のrouting fixture、03は速度CSVをconfigs/examples経由で取得します。APIは既存の科学処理を呼びます。欠損時の代替結果はありません。

## 9. Notebook Guide

各冊は独立kernelで上からRun All。順序は00→01→02→03→04→05です。

|Notebook|用途・変更できる条件|
|---|---|
|[00_start_here](../notebooks/00_start_here.ipynb)|依存とhash・環境の確認|
|[01_classical_routing](../notebooks/01_classical_routing.ipynb)|3顧客の正式古典solver、時間窓変更|
|[02_pubo_qaoa](../notebooks/02_pubo_qaoa.ipynb)|正式PUBO/判定と教材回路、γ/β/seed/shots|
|[03_battery_energy](../notebooks/03_battery_energy.ipynb)|質量・保存軌跡・DC、比エネルギー/速度係数|
|[04_quantitative_results](../notebooks/04_quantitative_results.ipynb)|R0/R1・Method×Battery保存結果と表示フィルタ|
|[05_scale_analysis](../notebooks/05_scale_analysis.ipynb)|古典6規模保存結果と表示フィルタ|

01〜03は小規模計算、04〜05は保存結果表示で、新しい科学結果ではありません。fixtureは人工データ、各assertは初期条件の基準値を含みます。任意の問題規模に対応する汎用solver UIではありません。02の既定値はgamma=0.001、beta=0.2、shots=64、seed=20261009、DO_OPTIMIZE=False。任意COBYLA最大6評価は通常無効で自動検証外。既定0/64・NOT_ACQUIREDを隠したり正式科学結果に置き換えたりしません。

adapters.pyは[依存台帳](../notebooks/fixtures/dependencies.json)の38依存をhash照合し、正式APIへ接続します。数理処理をNotebookへ重複実装しません。通常の検証はNotebookを保存し直しません。`notebooks/test_notebooks.py --save-outputs` は表示出力を保存するため、比較検証では一時配置のみで使います。`--report NEW_PATH.json` は新規報告先を指定します。

## 10. Quickstart and Dependencies

Python3.12.3/Linuxで新規venvへのインストールと公開cloneの実行を検証済みです。今回の文書統合では既存の検証用venvを使います。他OS/Python・Colabは未検証です。

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r reproducibility/environment/requirements-quickstart.lock.txt
.venv/bin/python -m pip check
.venv/bin/python -B scripts/verify_quickstart.py
```

リポジトリ直下で実行します。lockは実際に解決したランタイム依存版で、全OSのwheelハッシュロックではありません。[直接依存](../notebooks/requirements.txt)と[固定版](../reproducibility/environment/requirements-quickstart.lock.txt)を参照してください。UIは不要です。既存Jupyter UIから使うkernel登録例は `.venv/bin/python -m ipykernel install --user --name kmd-notebooks`（UI操作自体は未検証）。通常のPython利用はrepo rootで `PYTHONPATH=src .venv/bin/python -B`。wheelとしてのpipインストールを提供したものではありません。


|範囲|必要なもの|今回の扱い|
|---|---|---|
|CORE|Python3.12.3、numpy2.3.1、pandas2.2.3、scipy1.16.0、highspy1.15.1、正式source・小規模fixture・保存集計|軽量API検証。凍結ソースの必要部分への接続を含む|
|NOTEBOOK|CORE、qiskit2.1.1、nbformat5.10.4、nbclient0.10.2、ipykernel6.30.1と推移依存|6冊の既定セル。教材回路のためQiskitはquickstartに含む|
|QUANTUM_OPTIONAL|正式Protocolの専用環境、worker/QPY等|本番最適化・実機・高負荷シミュレーションは未復元|
|SUMO_OPTIONAL|SUMO/native fork、専用router、道路ネットワーク、全OD、worker設定|保存軌跡APIはSUMO不要。全量運行は対象外|
|FULL_RESEARCH|元のanalysis/qgpu/native環境、大容量入力と全量証拠|既存requirements-analysis.txtとRelease Manifestを保持。quickstartとの同一環境化はしない|

[quickstart lock](../reproducibility/environment/requirements-quickstart.lock.txt)はNOTEBOOKまでの実測解決版です。既存analysis定義（Hayate保存参照: `reproducibility/environment/requirements-analysis.txt`、公開ツリー非同梱）のnumpy/scipy等とは用途が異なるため上書きしません。これは正式研究環境の完全復元ではありません。OS、ネイティブライブラリ、配布物の永続保存は別途必要です。

外部ライブラリはpipで取得し、ソースをこのリポジトリへ再配布しません。インストール成功はライセンス互換性・自作コードの公開権限確認とは別です。

## 11. Reproducibility and Verification

### 実行用コピーの方針


[対応表](../reproducibility/release/FROZEN_RUNTIME_SOURCES.json) に凍結原本・実行用配置・SHA256・読込み範囲を記録しています。5ファイルをバイト一致で配置し、科学的な計算文を変更していません。旧原本は研究当時の証拠として元位置に保持します。コピーを別の現役実装として改良・管理しません。変更が必要になった場合は、原本のfreezeを更新せず、別の科学的変更として検討してください。

| 機能 | 実行用配置（src/kmd_quantitative/以下） | 接続方法 |
|---|---|---|
| Candidate Cと正式標本判定 | quantum/protocol_v2/science.py | builder/formalが既存の必要な関数・文だけをASTで読み込む |
| NotebookのProtocol定義 | quantum/protocol_v2/protocol.py | 定義のみ読込み |
| Battery質量 | battery/frozen_sources/review_pack_specific_energy.py | massが既存の計算文のみをASTで読み込む |
| Controlled-DC | energy/frozen_sources/run_full_controlled_dc.py | controlled_dcがevaluate/scalar_check/nearを公開 |
| 保存軌跡読込み | simulation/frozen_sources/apply_r0_method_battery.py | trajectory_ioが読込みの3文だけをASTで読み込む |

### 実行してはいけない入口

コピーしたファイル全体を汎用CLIとして起動しないでください。`__file__` から構築される全量実験用パスは新配置に移植していません。特に旧R0軌跡sourceにはトップレベルの科学計算・書込みがあり、直接importしてはいけません。公開adapterが選ぶ処理のみが検証対象です。Controlled-DCのmain/preflight、scienceの実験worker・最適化は呼び出しません。

### 原位置に残すもの

旧science・R1 worker・Battery/Controlled-DC原本は、source freezeと研究結果の追跡用に保持します。R1 workerは回帰テストがAST比較の証拠として読むため配布集合に残しますが、通常のAPIとNotebookはworkerを起動しません。全量QAOA/SUMO workerの旧パス依存は今回の移植対象外です。

`01_research_design/` のモデルfreezeと正式結果は、設定・保存結果の読込み依存として残します。これは旧配置の計算コード実行とは異なります。結果の入口は [保存結果の入口](#7-analysis-and-frozen-results) と結果Indexです。元のfreezeやauthority chainのパス・値・hashは変更しません。



### 軽量検証と保全

第10節の1コマンドで既存45 API/契約テスト＋原本一致1テスト、Notebook6冊を実行します。`-O`はassertを無効化するため禁止。全量SUMO/OD、正式QAOA最適化、旧互換リンクの検証は含めません。CIも同じ入口を使います。

公開基準commit 2efe70f854c4871547db6fac9c169db8cd06e706では実clone検証・GitHub Actions成功の記録があります。[基準CI](https://github.com/tkm-sano/kmd-analysis/actions/runs/37904061464)。その後の構造再編・今回の文書統合はローカル検証対象で、未commit・未pushです。新しいリモートCI成功を主張しません。

Distribution Manifestは配布hashを管理し、科学的Release Manifestとは別です。歴史的rights/publicationフィールドは準備時点の記録であり、後続の公開実施記録と区別してください。元のsource freeze・authority・結果は変更しません。Notebook01〜05は基準出力との完全一致を検査し、00の依存表示差を別扱いにします。

## 12. GitHub and Hayate Responsibilities

GitHubは正式API・小規模入力・Notebook・主要集計・検証の利用場所、Hayateは全量科学データ・過去の研究環境と監査の保存場所です。元13,360件のRelease Manifest、全OD、全軌跡、中間成果、native fork/専用router環境、全量worker/QPY/instance/validator等はGitHubにすべて含まれません。小規模利用の成功を全量科学実験の再現成功としません。

Hayate原位置で保持することと、独立した永続バックアップを持つことは別です。研究保存台帳・生成記録はdocs/audits等にあり、公開文書の統合対象外です。Git追跡解除は物理削除ではなく、現行treeから外れても過去のGit履歴には残ります。

全量研究の設定・入力・source対応はHayateのRELEASE_MANIFEST.jsonとRELEASE_ARTIFACT_REGISTER.csv、公開側のconfigs/CANONICAL_CONFIG_INDEX.csvに記録されています。後者に辿れることは、未配布の入力を取得したことを意味しません。

## 13. Data Attribution and Licensing

### ライセンス適用範囲


既存の[LICENSE](../LICENSE)はApache License, Version 2.0（SPDX: `Apache-2.0`）です。TAKUMA SANOが公開・ライセンス適用権限を持つ**自作コードおよびNotebookの自作部分**には、既に承認された方針に基づき同ライセンスを適用しています。これは将来の適用候補ではなく、この範囲への適用宣言です。LICENSE本文は変更していません。

配布Manifestのlicense_scopeは元の適用記録です。ただし全内容について単独著作・権利処理完了を認定したものではありません。共同研究・所属機関・第三者由来の部分、Notebookの保存研究結果や外部データはこの宣言から除外し、該当権利者の承認・元の利用条件を別途確認します。今回の公開判断を、第三者由来部分の独立した権利確認完了や新たな許諾とは扱いません。

研究結果・fixture・文書へApache-2.0を一括適用しません。第三者ライブラリは各自のライセンスに従います。適用対象の利用・改変・再配布では、LICENSEの提供、改変表示、必要な著作権・帰属表示と該当NOTICEの保持等、LICENSEの条件に従ってください。元のLICENSE付録の`[yyyy]`/`[name of copyright owner]`は記入例であり、全成果物の権利者の認定ではありません。

既存の公開Git履歴もこの宣言によって新たに権利処理済みにはなりません。公開判断の前提と独立検証の限界は、下記のデータRelease説明にも記録しています。


### 外部入力の帰属と加工


以下は保存済み科学結果の生成に使われた研究入力です。上記の合成3顧客・4標本fixtureとは別です。元のPBF、CityGML、統計表、全OD、道路網、全走行軌跡はコード配布に同梱していません。

|提供元・出典|確認できた版・取得記録|研究上の加工・用途|
|---|---|---|
|© OpenStreetMap contributors、[OSM](https://www.openstreetmap.org/copyright)、[Geofabrik関東](https://download.geofabrik.de/asia/japan/kanto.html)|`kanto-260716.osm.pbf`、2026-07-16版、台帳取得2026-07-17|地域抽出、道路属性・形状補正、SUMO道路網、OD・経路・走行評価へ利用。道路データベースは[ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/)|
|国土交通省Project PLATEAU、[3D都市モデル（大田区）（2025年度）](https://www.geospatial.jp/ckan/dataset/plateau-13111-ota-ku-2025)|保存された配布元メタデータはCityGML v5、`13111_ota-ku_pref_2025_citygml_1_op.zip`。2026-08-21の調査・取得記録。需要工程台帳も同名ZIPを記載|建物候補・代表点へ加工し、合成世帯の建物割当と配送地点を作成。研究側の加工であり提供機関の公式需要・配送結果ではない。最終scoped parquetまでの変換履歴は未回復|
|国土交通省、[東京都市圏物資流動調査・個人のモノの受取調査（令和6年度）](https://www.e-stat.go.jp/stat-search/files?layout=dataset&tclass1=000001223521&tclass2=000001234242&toukei=00600520&tstat=000001078042)|表ss521「世帯人数別・世帯構成別宅配受取頻度（回数）・再配達頻度（割合）」、`ss521_r06a.xlsx` / `ss521_R06`。保存記録の取得日2026-08-23、manifest固定08-29|受取経験のある世帯の人数別小計を相対需要強度へ加工。週頻度0.65148273 / 0.93035232 / 1.18813494 / 1.45298673（1人、2人、3〜4人、5人以上）。実注文の記録ではない|
|総務省統計局・e-Stat、2020年国勢調査、2023年住宅・土地統計調査|需要工程記録の表ID `000032163278`、`000040209857`、メッシュ重み `T001141034`。対象は大田区等。全採用セル・加工設定の対応は未確認|合成世帯・住宅区分、需要重み。表名や採用セルの未確認部分を確定出典として補っていない|

PLATEAUの利用条件は[サイトポリシー](https://www.mlit.go.jp/plateau/site-policy/)および各配布データの個別条件によります。出典と研究者による加工を明示し、各地方公共団体等の権利を保持します。上表の年度・ファイル名は保存資料に基づく確認であり、失われた中間parquetの同一性を保証しません。

e-Statの[利用規約](https://www.e-stat.go.jp/terms-of-use)では数値データ等の利用と著作物の条件を区別しています。ここでは数値表を加工した合成需要の出典を示しています。需要工程記録には日量期待値82,023、世帯数384,353、Poisson seed 20260829、建物割当seed 20260830があり、生成件数82,246、建物へ割当済み81,859、39,956地点です。母数の違いを維持します。生成プログラム・全採用統計セルの完全な復元は未確認です。

行政界等の補助入力には国土数値情報N03（2026年）等の記録もあります。全量再現にはこれらの入力と加工履歴が必要です。ここに元データの再配布許諾や復元可能な外部アーカイブの存在を追加で認定するものではありません。

追加確認：保存PLATEAU ZIP内READMEは、政府標準利用規約2.0、CC BY 4.0、ODC BY、ODbLの選択肢を記載しています。これは当該ZIPの条件であり、未回復の中間建物データが同ZIPだけに由来する証明ではありません。

最終道路網の変換記録は、既存lane形状をjunction座標へ接続し、lane lengthを接続後の折線長へ更新したと記録しています。保存config_snapshotの「length維持」および生成器名とは不一致があります。道路網の配布候補は最終hashが一致する実ファイルであり、再生成手順の完全性は未確認です。

### 道路データの取得

[データ専用Release](https://github.com/tkm-sano/kmd-analysis/releases/tag/road-data-20261009-rc1)から[道路データパッケージ](https://github.com/tkm-sano/kmd-analysis/releases/download/road-data-20261009-rc1/kmd-road-network-20261009-rc1.tar.gz)と[SHA256](https://github.com/tkm-sano/kmd-analysis/releases/download/road-data-20261009-rc1/kmd-road-network-20261009-rc1.tar.gz.sha256)を取得できます。14ファイル、48,285,157 bytes。archive SHA256：`e160e4fd83cbb529a81815a780c67ce1462f3e17048bdbccab8f087171ce189b`。データ専用タグは最新版のモデルコードを示しません。

空の領域に展開し、package rootで `python -B VERIFY.py` を実行してください。最終道路XMLのSHA256は `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`。SUMOの実行や全量科学実験の再現ではなく、内容とXML構造の確認です。

公開条件充足を前提とした研究者の指示により提供しました。package内の準備時点のBLOCKED/未承認表示は、配布バイトを維持した過去の記録です。後続の公開承認はRelease説明に記載しています。3集計の法的分類、追加内容/中間DBの提供範囲、PLATEAU中間加工履歴が独立に解決済みであるとは主張しません。元データの来歴を補作せず、研究の数値を維持しています。

### 保存結果の帰属範囲


以下の13件について、[入力データの出典・加工表示](#13-data-attribution-and-licensing)を関連する帰属表示とします。© OpenStreetMap contributors。道路入力は[OpenStreetMap](https://www.openstreetmap.org/copyright)データベースに由来し、そのデータベースは[ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/)で利用できます。PLATEAU・e-Stat等の出典と加工は上記data文書に記載しています。

これらは原道路網・元統計表そのものではありません。研究結果のCSVであることだけでDerivative Databaseと判定せず、逆に統計的集計であることだけでODbLの条件がなくなるとも判断していません。改変道路データからのProduced Workに該当する公開では、ODbL §4.3の表示と、§4.4・§4.6の改変データまたは全変更方法・追加内容の提供条件を確認する必要があります。最終道路網は下記Releaseから取得できます。最終XMLの提供が中間DBを含む全義務を満たすか、また一部集計の法的分類は独立に確定していません。帰属表示と提供の実施を、法的判断の確定と混同しません。

|保存ファイル|内容・公開前の残件|
|---|---|
|[CLASSICAL_SCALE_X_BATTERY_SCALE_SUMMARY.csv](../01_research_design/methodology/CLASSICAL_SCALE_X_BATTERY_SCALE_SUMMARY.csv)|集計値。道路データの提供条件の充足を要確認|
|[MATCHED_CLASSICAL_BATTERY_SCALE_SUMMARY.csv](../01_research_design/methodology/MATCHED_CLASSICAL_BATTERY_SCALE_SUMMARY.csv)|集計・シミュレーション結果。道路データの提供条件の充足を要確認|
|[MATCHED_CLASSICAL_ROUTE_SCALE_SUMMARY.csv](../01_research_design/methodology/MATCHED_CLASSICAL_ROUTE_SCALE_SUMMARY.csv)|集計・道路OD派生結果。道路データの提供条件の充足を要確認|
|[MATCHED_CLASSICAL_TRAJECTORY_VALIDATION.json](../01_research_design/methodology/MATCHED_CLASSICAL_TRAJECTORY_VALIDATION.json)|シミュレーション検証/来歴。道路データの提供条件の充足を要確認|
|[FINAL_QUANTITATIVE_RESULT_FREEZE.json](../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_RESULT_FREEZE.json)|統合集計/来歴。道路データの提供条件の充足を要確認|
|[FINAL_QUANTITATIVE_STUDY_REPORT.md](../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_STUDY_REPORT.md)|研究説明。道路データの提供条件の充足を要確認|
|[FINAL_SCALE_METHOD_BATTERY_SUMMARY.csv](../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_SCALE_METHOD_BATTERY_SUMMARY.csv)|集計値。道路データの提供条件の充足を要確認|
|[COMMON_MATCHED_POPULATION.csv](../01_research_design/scenario_evaluation/matched_r0_r1_common_protocol_scale_method_battery_20261008/COMMON_MATCHED_POPULATION.csv)|研究内部識別子・可用性。原データ複製の個別問題は識別されない。研究全体の入力条件の確認とは区別|
|[DIRECT_METHOD_ENERGY_SCALE_COMPARISON.csv](../01_research_design/scenario_evaluation/matched_r0_r1_common_protocol_scale_method_battery_20261008/DIRECT_METHOD_ENERGY_SCALE_COMPARISON.csv)|ブロック別シミュレーション出力。道路データの提供条件の充足を要確認|
|[SCALE_METHOD_BATTERY_MATCHED_CONTRASTS.csv](../01_research_design/scenario_evaluation/matched_r0_r1_common_protocol_scale_method_battery_20261008/SCALE_METHOD_BATTERY_MATCHED_CONTRASTS.csv)|ブロック別派生指標。道路データの提供条件の充足を要確認|
|[CLASSICAL_QUANTUM_SCALE_COMPARISON.csv](../01_research_design/scenario_evaluation/quantitative_scale_boundary_synthesis_20261008/CLASSICAL_QUANTUM_SCALE_COMPARISON.csv)|計算/研究設計の集計。原データ複製の個別問題は識別されない。研究全体の入力条件の確認とは区別|
|[LOGISTICS_SERVICE_SCOPE.csv](../01_research_design/scenario_evaluation/quantitative_scale_boundary_synthesis_20261008/LOGISTICS_SERVICE_SCOPE.csv)|シミュレーション時刻診断集計。道路データの提供条件の充足を要確認|
|[SCALE_INSTANCE_COMPARISON.csv](../01_research_design/scenario_evaluation/quantitative_scale_boundary_synthesis_20261008/SCALE_INSTANCE_COMPARISON.csv)|座標範囲・識別子・集計値。bboxの元建物加工履歴および道路データ提供条件を要確認|

座標範囲を持つSCALE_INSTANCE_COMPARISONは、建物代表点のmin/maxを含みます。全建物集合ではありませんが公開地理情報との照合可能性は残ります。科学的数値・freezeは変更していません。本節は条件整理であり、研究結果へのApache-2.0一括適用ではありません。

## 14. Limitations and Provenance

静的可行性、SUMO走行完了、実時刻での時間窓・帰還診断、実業務の全配送充足は別です。未配送で電力量が減ったことを省エネルギー成果としません。量子優位、量子実機、量子材料計算、全車両同時運行、社会全体の省エネルギーは実証していません。充電を含む主仮説の成立を本モデルだけで判定しません。

### 凍結報告の非配布参照

凍結報告と同階層の次の6資料はHayateに保持し、GitHubに含めません。報告のリンクは歴史的証拠として書き換えず、GitHub上では開けません。主要API/Notebook実行には不要ですが、これらを必要とする詳細検証は公開コードだけでは完結しません。

|ファイル|扱い|
|---|---|
|`FINAL_ARTIFACT_MANIFEST.csv`|成果物の対応・検証証拠|
|`FINAL_MECHANISM_SUMMARY.csv`|機構別集計|
|`FINAL_SPEED_DISTRIBUTION_SUMMARY.csv`|速度分布集計|
|`FINAL_SENSITIVITY_VERIFICATION.csv`|感度検証証拠|
|`FINAL_RESULT_SUMMARY.csv`|詳細結果集計|
|`FINAL_IDENTIFIABILITY_AND_LIMITATIONS.md`|研究当時の識別可能性・限界|

### 旧ガイドからの対応

次の旧文書はHayateに保持し、公開treeでは本ガイドへ集約しました。旧URLが自動転送されるとは限りません。過去の文書にある旧候補件数、未公開表示、移行途中の依存説明を現在の状態と混同しないでください。

|旧パス|現在の公開先|
|---|---|
|`CURRENT_EXECUTION.md`|[第10節](#10-quickstart-and-dependencies)|
|`configs/README.md`|[第8節](#8-data-and-configuration)|
|`data/README.md`|[第8節](#8-data-and-configuration)|
|`docs/quantitative/ANALYSIS_API_AND_FROZEN_RESULTS.md`|[第7節](#7-analysis-and-frozen-results)|
|`docs/quantitative/BATTERY_AND_ENERGY_API.md`|[第6節](#6-battery-and-controlled-dc-energy)|
|`docs/quantitative/CURRENT_EXECUTION_GUIDE.md`|[第10節](#10-quickstart-and-dependencies)|
|`docs/quantitative/GITHUB_AND_HAYATE.md`|[第12節](#12-github-and-hayate-responsibilities)|
|`docs/quantitative/QUANTITATIVE_MODEL_INDEX.md`|[第2節](#2-model-architecture)|
|`docs/quantitative/QUANTUM_API_AND_FROZEN_PROTOCOL.md`|[第4節](#4-quantum-model-and-protocol-v2)|
|`docs/quantitative/RUNTIME_AND_FROZEN_SOURCES.md`|[第11節](#11-reproducibility-and-verification)|
|`docs/quantitative/SIMULATION_AND_TRAJECTORY_API.md`|[第5節](#5-simulation-and-trajectories)|
|`notebooks/README.md`|[第9節](#9-notebook-guide)|
|`reproducibility/environment/DEPENDENCY_SCOPE.md`|[第10節](#10-quickstart-and-dependencies)|
|`reproducibility/environment/QUICKSTART_ENVIRONMENT.md`|[第10節](#10-quickstart-and-dependencies)|
|`results/README.md`|[第7節](#7-analysis-and-frozen-results)|
