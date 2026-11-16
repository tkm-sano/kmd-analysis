# D：Huang列生成法＋AOAの実装計画

2026-11-10改訂。設計IDはD-HUANG-CG-AOA-v1である。[原著監査](D_METHOD_REVIEW.md)、[定式化](D_FORMULATION.md)、[資源・リスク](D_FEASIBILITY_AND_RISKS.md)を前提とする。本書の全体計画に対し、追加工程で小規模の独立参照実装と縮小検証を行った。**予定ファイル表と研究用Phaseは全て実装済みという意味ではない。** 最新の実装範囲は[報告](D_REFERENCE_IMPLEMENTATION_REPORT.md)と[研究規模判定](D_SCALING_READINESS.md)を正本とする。Dの手法は再選定しない。

## 1. 実装の境界

原著の根拠は[HuangらarXiv v1、§III–IV](https://arxiv.org/html/2503.17051v1)である。以下の三つを別の実行profileとする。

1. paper-literal：表示式、被覆LP、ALiM、XYを可能な範囲でそのまま検査する。固定拠点との矛盾を隠さず、出力を可行性検査する。
2. paper-interpreted：P02の顧客重複添字とP03の固定拠点を補正した独立参照実装である。原著の数値完全再現とは称さない。
3. study-day-columns：一度訪問等式、時刻付き車両日列、最大2便、バース占有行、対称ε制約profileを加える独自拡張である。

論文固有のコード・instance・設定が未確認のため、profile 1/2から「著者実装を再現済み」と結論しない。原著の4〜6顧客とS1〜S3を同じ実行可能規模として扱わない。旧単一車両QAOAの実験結果・凍結コードは変更しない。

## 2. アーキテクチャと作成予定ファイル

既存の凍結需要読込器を利用し、新しいCG処理を旧routing/quantum経路から分離する案である。以下は予定パスであり、実在する実装という意味ではない。

|予定パス|責務・主な入口|
|---|---|
|src/kmd_toc/column_generation/contracts.py|PricingContext、RouteColumn、VehicleDayColumn、MasterResult、RunResultの契約|
|src/kmd_toc/column_generation/master.py|被覆LP・分割LP・日列LP、双対符号変換、残差、master_variant|
|src/kmd_toc/column_generation/columns.py|順序・車両・時刻・入力hashを含む列IDと重複管理|
|src/kmd_toc/column_generation/pricing.py|双対snapshot→AOA問題、候補顧客・位置数・係数の管理|
|src/kmd_toc/column_generation/aoa/encoding.py|位置qubit表、固定t=0の除去、bit順|
|src/kmd_toc/column_generation/aoa/cost.py|原著literalと補正ALiM、QUBO→Ising、offset・単位|
|src/kmd_toc/column_generation/aoa/xy_mixer.py|環状XY、初期状態、厳密ブロック参照、指定合成|
|src/kmd_toc/column_generation/aoa/optimizer.py|角度・COBYLA・再開始・評価ログ|
|src/kmd_toc/column_generation/aoa/sampling.py|訓練/最終shots、backend/solver seed、測定履歴|
|src/kmd_toc/column_generation/aoa/decode.py|one-hot・拠点・容量・重複検査、真のルート被約費用|
|src/kmd_toc/column_generation/day_completion.py|trip候補→車両別0/1/2便・時刻候補→日列、完全な被約費用|
|src/kmd_toc/column_generation/classical_pricing.py|同一領域の列挙/MIP/ラベリング参照、価格付け下界の取得可否|
|src/kmd_toc/column_generation/integer_master.py|最終日列の整数選択、人工列の排除、限定列gap|
|src/kmd_toc/column_generation/certificates.py|探索領域・停止理由・LP/IP証明範囲の記録|
|src/kmd_toc/column_generation/runner.py|初期列→LP→AOA→日列→再解→整数化→共通検証の制御|
|src/kmd_toc/planning_validation.py、planning_metrics.py|A〜D共通の完全配送・容量・時間・バース検証、D/W/T。既存同等機能があれば拡張前に照合する|
|configs/toc_delivery_d/huang_cg_aoa.json|手法固有の設定。需要pinや旧study.jsonを上書きしない|
|tests/toc_cg/|数式・回路・双対・日列・接続・変更検知の将来テスト|

旧src/kmd_toc/contracts.pyの常時HOLD契約を新仕様のready判定へ流用しない。旧src/kmd_quantitative/routing/solver.pyの固定担当・単一経路入口をCG主問題と呼ばない。新契約と既存の公開入口の名前衝突を確認してから実装する。

### 2.1 ライブラリ案と環境

- 量子回路：隔離したPython/Qiskit環境を新設する将来計画である。Qiskit 2.1.1は既存凍結環境でメタデータを確認した参照版であり、その環境を改変しない。採用lock、Aer又はStatevectorSamplerの使い分け、CPU/GPU、実行backendはPhase 1/2で決める。
- 角度探索：SciPy COBYLAである。Qiskitへの移植は独立実装であり、原著のQamomile/QURI Partsと同一環境とは称さない。
- RMP：SciPy HiGHS又はhighspyでLP双対を取得する。原著のCBCとの小問題照合を別profileで行う。整数選択はHiGHS MIP/CBC/MPSolver、時間割の小問題参照はCP-SATを候補とする。
- OR-Tools Routingは比較対象CのVRP探索であり、Dの内部LPソルバーとは区別する。CP-SATからLP双対を得る設計にはしない。
- Qamomileの投稿前snapshotはPython<3.12等を宣言するため、現在のQiskit環境へ無条件で同居させない。ソース複製時のライセンス確認を先行させる。今回は導入しない。

## 3. 入出力契約

すべてのIDは文字列として保持する。距離はkm、道路時間・時刻は内部秒、待機の公開値は分、荷物は個である。Nは訪問地点数、Pは総荷物個数、Fは物理車両数、Bはバース数である。主需要のq_i=1を維持する。

|境界|必須情報・制約|
|---|---|
|CommonInput|load_frozen_demandから得る不変需要、scenario_id、manifest/hash、ID順、OD識別子/hash、距離・時間・到達性、車両/運行profileのhash|
|OperationalProfile|F、車両別Q、最大2便、B、外生の第1便ready、積込規則、帰着準備、地点作業時間、勤務終了、時間格子。未確定nullのまま本実験を開始しない|
|PricingContext|instance_hash、iteration、LP解/dual_snapshot_id、master_variant、formulation_id、π/σ/κ/μ又はδ、候補顧客ID、L、Q、OD参照、単位変換、λ、量子設定|
|AOAResult|bit表、角度・全評価履歴、最終標本と頻度、energy/offset、復号結果、棄却理由、回路ゲート数/深さ/backend、処理段階の時間|
|RouteColumn|ordered_stop_ids、拠点発着、訪問係数、parcel_count、distance_km、travel_seconds、service_seconds、生成iteration・標本の来歴、真のroute reduced cost、検証結果|
|VehicleDayColumn|vehicle_id、trip数0/1/2、各trip順序、ready/start/end/departure/return、W1/W2、D、占有区間/格子行、source_hash、完全な日列reduced cost|
|MasterResult|LP/IP状態、目的profile、primal/dual残差、列集合hash、双対、探索領域、人工変数、限定列gap、証明範囲|
|RunResult|完全な採用計画又は失敗、D/W1/W2/W/T_first/T_final、実行資源、停止理由、seed、全入力/コード/設定hash、fallbackと候補生成別寄与|

RouteColumnのIDは順序を含む。非対称ODでは逆向きルートも別物である。VehicleDayColumnは同じ顧客集合でも車両・時刻・便順が違えば別列である。source_hashは過去需要の値を新しい荷物個数へ読み替える入口にしない。

結果は全配送地点が一度ずつ含まれ、日列主問題と独立validatorの両方を通ったものだけを評価対象とする。人工列、未配送、Q超過、H超過を「低距離・低待機」の数値としてプロットしない。

## 4. 原著設定と提案設定

[原著§IV、図2–5](https://arxiv.org/html/2503.17051v1#S4)の確認値と、独立実装を有限手順にする提案を区別する。

|項目|原著で確認した値|独立参照実装への提案・確定状態|
|---|---|---|
|深さp|1/2/3を検討、以後2|p=2を参照、1/3は原著の傾向検証。研究規模への採用は資源ゲート後|
|古典角度探索|COBYLA|同じ手法。SciPy版とオプションを固定する|
|評価回数|不明|各再開始の目的評価上限200。これは本研究提案である|
|収束|不明|信頼領域のtol=10^-3、maxiter=200を提案。目的差ftolと混同しない|
|初期角度|不明|層l=1,…,pについてγ_l=0.1l/p、β_l=(π/4)(1-l/(p+1))を第1開始点にする案。共通費用正規化の下で定義し、原著値と称さない|
|再開始|不明|第1開始に加え2回、計3回。追加開始角はsolver_seed管理の乱数で作り、実角度も保存する|
|訓練shots|各回路1000|1000を参照する。期待値の計算法・同一shotからの項評価を固定する|
|最終shots|訓練と独立した数は不明|各再開始4096を提案。これは成功保証ではなく標本数である|
|λ_cap、λ_visit|1、1|人工問題の参照値として記録。道路距離の尺度が違う研究版へ1を自動継承しない|
|列追加K|1/5/10を検討|小問題は5を中心に1/10も確認。実際の負列がK未満なら取得分のみ|
|初期状態|one-hotな単一解|t=0固定、残り位置は拠点の基底状態を提案。原著と同一とは未確認|
|XY合成|式(20)、詳細不明|小規模は厳密ブロック参照、実用は2次Suzuki–Trotter。分割sを変え誤差を検証後に固定|
|原著の実験反復|各instance 10 samples|sampleの独立性・seed不明。著者反復の定義は再現できない|
|計算側seed|不明|研究版はsolver_seed=1101,…,1110の10試行を提案。需要seedを導入する意味ではない|

提案角度は角度範囲・周期の取り方と費用正規化に依存する。再開始の乱数分布はγ∈[0,2π)、β∈[0,π)の独立一様を候補とし、正規化してもIsing係数が整数になるとは限らないため、これを厳密な周期全域と主張しない。全係数を正の共通費用尺度c0で割り、物理単位の被約費用・許容誤差は元単位へ戻す。λも同じ尺度で変換する。研究版のc0、λ、sは予備検証後・本実験前に固定するHOLDである。

許容誤差は無次元化した被約費用に10^-7を提案する。LP残差と丸め誤差を含む感度確認を行い、真に負と確認できない境界値は改善証明に使わない。価格付けのスコアを距離そのものと誤認しない。

### 4.1 反復の終了規則

- 原著規模の独立参照：改善列未取得が5完全ラウンド連続、又は200ラウンド到達を探索停止候補とする。全域の厳密価格付けで非負下界が確認できる場合は、その証明で停止できる。
- 毎回の角度探索・最終測定・候補復号を完了したラウンドだけを未取得回数へ数える。失敗したLPやbackend例外は未取得ラウンドではない。
- 同一双対で同じ決定的状態を5回処理しても証明は強くならない。再開始・候補領域を記録し、単なる未取得停止と表示する。
- 小問題の整数主問題は限定列gap=0まで解く案とする。研究規模のgap・探索ノード・列数上限は資源検証後の事前登録事項である。
- 研究版は反復上限I_max、各反復の価格付け領域数P_max、日列候補上限J_maxを必ず定義してから実行する。小規模の200をそのままS3へ採用しない。
- wall時間を主たる収束規則にしない。資源・安全停止はRESOURCE_ABORT又はWATCHDOG_ABORTと記録し、最適終了や価格付け完了へ読み替えない。
- 終了状態は定式化書§6の証明状態と一致させる。限定列整数最適と全VRP整数最適を分ける。

## 5. 全体の計算手順

以下は将来実装する擬似コードであり、今回実行していない。

~~~text
load_and_verify_frozen_demand(scenario)     # 再生成しない
load_and_verify_common_OD_and_operations()
require_all_shared_conditions_ready()
start_method_clock()
for each pre-registered symmetric epsilon profile:
    build_initial_route_and_vehicle_day_columns()
    if no feasible restricted coverage:
        run_explicit_phase_I_or_return_NO_FEASIBLE_INITIAL_POOL()
    repeat:
        solve_RMP_LP_to_declared_accuracy()
        freeze_duals_and_scope()
        for each declared pricing domain:
            construct_Huang_position_ALiM_XY_problem()
            train_finite_restarts_and_take_final_samples()
            decode_and_validate_route_candidates()
            complete_routes_to_time_fixed_vehicle_day_columns()
            recompute_full_reduced_cost_with_all_duals()
            add_only_unique_feasible_strictly_negative_day_columns()
        update_termination_state_and_coverage_certificate()
    until declared stopping condition
    solve_restricted_integer_day_master()
    reject_any_artificial_column_or_unserved_customer()
    assign_concrete_berth_ids_to_capacity_checked_intervals()
    independently_validate_whole_plan()
retain_observed_nondominated_valid_plans_with_no_D_W_priority()
record_T_first_T_final_and_all_stage_costs()
~~~

Phase Iで人工的な配送充足変数を使う場合、それは初期LPを解くための手段である。人工変数の合計を0へする独立段階と、その後の本来の目的を分け、任意の巨大罰金がD/Wを歪める方法は既定にしない。Phase Iで価格付けする目的・双対も別に導出する必要がある。**人工変数が0の整数可行解を得なければ配送計画は取得できていない。** 原著の単独配送初期列を車両制約付き研究版へそのまま入れても初期可行性は得られない。

## 6. Phase別計画

### Phase 1：原著の定式化確認

|項目|計画|
|---|---|
|目的・作業|式(7)/(8)の差、双対、被約費用、P02添字、P03固定拠点、ALiM容量、XY非可換合成を確定する。掲載版・著者資料も確認する|
|予定ファイル|本4文書の追補、contracts.py、手計算fixture仕様。原著・旧成果を改変しない|
|ライブラリ|文献・stdlibによる仕様確認。将来の数式照合はNumPy/SciPy|
|入力|arXiv/TeX、入手できれば最終掲載版・著者コード|
|出力|literal/補正の版差表、変数表、LP/双対と厳密小問題の期待値|
|テスト計画|被覆対分割の反例、h=-2/-1/0/1の容量項、one-hotで原文重複項が0になること|
|完了条件|採用する解釈と原著との差、未公開設定の補足、証明範囲を明記する|
|依存・リスク|先行作業なし。最終版・著者確認が得られなければ完全再現のHOLDが残る|

### Phase 2：原著規模の再現

|項目|計画|
|---|---|
|目的・作業|まず古典LP＋全列列挙の小CVRPを照合し、次にAOAを接続する。4〜6顧客の人工問題、図2–5の因子を分離する|
|予定ファイル|master.py、aoa各ファイル、classical_pricing.py、参照config、tests/toc_cgの原著規模試験|
|ライブラリ|隔離Qiskit、SciPy/HiGHS、必要なら原著比較用CBC。導入は別途実装段階で行う|
|入力|固定した人工instance。原著の具体instanceが入手できない場合は独立生成データと明示する|
|出力|LP双対、厳密最小被約費用、AOA標本・可行率・列履歴・限定整数解・段階時間|
|テスト計画|基底全列挙でQUBO/Ising一致、bit順、XYone-hot保存、t=0固定、非可換合成誤差、n=2環の辺二重計上、厳密価格付けとの照合|
|完了条件|同一数式の古典oracleと整合し、原著との差を追跡できる。図が似ているだけで再現成功としない|
|依存・リスク|Phase 1。λの下負荷選好、非可行測定、独自初期値・未公開設定の影響|

### Phase 3：A〜D共通入力への接続

|項目|計画|
|---|---|
|目的・作業|凍結需要読込、ODのID順・非対称性・単位、運行入力を共通契約へ接続する|
|予定ファイル|contracts.py、runner.py、共通validation/metrics、接続テスト|
|ライブラリ|既存frozen_demand読込器、CSV/JSON/hash処理。大規模ODをここで生成しない|
|入力|v1 CSV/manifest/pin、別工程で採用されたOD、根拠付きQ・運行profile|
|出力|不変CommonInput、来歴hash、全手法で共有する検証仕様|
|テスト計画|需要hash改変の拒否、入力順とOD順の一致、到達不能・欠損OD・null運行値の拒否、旧単位の入力拒否|
|完了条件|S1/S2/S3のN/F/B、q=1、時間窓なしが一致し、準備と手法固有時間を分けられる|
|依存・リスク|Phase 1/2、道路・容量・運行HOLDの解消。需要固定はOD採用の証拠ではない|

### Phase 4：複数車両・最大2便

|項目|計画|
|---|---|
|目的・作業|ルート列から物理車両日列を作り、一度配送・最大2便・容量・時間接続を主問題へ接続する|
|予定ファイル|columns.py、day_completion.py、integer_master.py、classical_pricing.py|
|ライブラリ|HiGHS等のLP/MIP、CP-SATは小規模時間検証の候補|
|入力|trip候補、車両Q、ready、作業時間、準備、H、共通OD|
|出力|0/1/2便の日列、完全配送の整数選択、初期列/Phase Iの状態|
|テスト計画|未使用車0便、1便、2便、第2便のみ拒否、未使用便への顧客/積込割当拒否、便間の同一顧客再訪拒否、帰着前積込拒否、容量超過、割当・順序の変更が帰着へ伝播する例|
|完了条件|全地点一度、各車最大2便、拠点発着、勤務内を独立validatorが確認する|
|依存・リスク|Phase 3。初期可行列不足、単独列だけではF台制約を満たせない、長い便の量子資源が未解決|

### Phase 5：バース・積込条件

|項目|計画|
|---|---|
|目的・作業|有限時間格子上の積込占有行を日列主問題へ加え、D/W両方向のε制約、完全な日列被約費用を接続する|
|予定ファイル|master.py、day_completion.py、certificates.py、共通バース検証|
|ライブラリ|LP/MIP、interval coloring、時間割参照用CP-SAT|
|入力|B、積込規則、準備、外生ready、時間精度Δ、事前profile ε/η|
|出力|競合を解消した選択日列、berth_id、W1/W2、全双対を含む価格付け履歴|
|テスト計画|半開区間、同時終了/開始、B+1重複の拒否、Wに積込/準備を含めない、ready改竄拒否、日列被約費用とMIP参照の一致|
|完了条件|バースと2便の不適合を事後削除で処理せず、完全配送と両立させる。候補生成と厳密価格付けを明確に分ける|
|依存・リスク|Phase 4。時刻候補が単一では不十分、日列爆発、Wがルート単体の加法費用ではない|

### Phase 6：研究規模の実験

|項目|計画|
|---|---|
|目的・作業|資源ゲート通過後にS1→S2→S3、Cとの共通profile比較、solver試行を行う。現時点ではHOLDである|
|予定ファイル|研究用config、runner.py、実行台帳。凍結需要は読取専用|
|ライブラリ|確定した量子backend・LP/MIP、CはOR-Tools Routingと共通時間制約処理|
|入力|同じv1需要/OD/Q/F/B/運行/εprofile、事前登録した評価・反復上限|
|出力|可行計画集合又は失敗、D/W/T、試行ごとのRAM/CPU/GPU・列数・反復数・shots|
|テスト計画|C/D共通validator、全地点維持、古典価格付け対照、T境界、fallbackの識別|
|完了条件|長い便・資源・価格付け領域の問題を解消し、失敗を隠さず全試行を記録する|
|依存・リスク|Phase 5と資源HOLD解消。小AOAだけでS規模に拡張可能という前提は置かない|

### Phase 7：結果監査

|項目|計画|
|---|---|
|目的・作業|D/W/Tを全便から再集計し、証明範囲・原著との差・Cとの比較を監査する|
|予定ファイル|結果監査器、比較表・既定7図の出力機能、再現手順。実データ取得前に結果曲線を作らない|
|ライブラリ|確定した集計/描画ライブラリ、共通validator|
|入力|全試行の原出力、入力hash、列・回路・停止・資源ログ|
|出力|絶対値・同一入力差分・観測非劣関係、失敗率、再現台帳、図1〜7|
|テスト計画|Dに全発着距離を含む、W1+W2=W、T_first≤T_final、手法内選択/検証を時間から除外していないこと|
|完了条件|シミュレータ時間をQPU時間と呼ばず、限定列解を大域最適と呼ばず、各規模・各試行を識別して報告する|
|依存・リスク|Phase 6。固定需要1例/規模から異なる配置への頑健性を主張できない|

## 7. 公平性・時間・出力の確定規則

共通需要・OD作成は共通準備であり手法固有Tと分ける。ただし、D用の初期列作成、問題変換、全LP、角度調整、サンプリング、復号、時刻候補作成、整数化、バース割当、可行性検査、採用計画確定はDのTへ含める。T_first、T_final、段階wall時間、CPU秒、最大RSS、GPUメモリ、shots/回路/量子ジョブを保存する。並列段階のwall時間は単純合計せず、実際の経過時間と併記する。

量子実機のqueue、転送、QPU実行とシミュレータwall時間は別列とする。未実施のQPU時間を推計値で本測定値に置換しない。Cも同じ全体計画が利用可能になる境界まで計測する。

Cが経路距離だけを探索しFCFS時間割を付ける一方、Dが日列で時刻・Wを探索する場合、探索可能範囲が異なる。このままの差は「各全体方式の差」であり量子部分の効果とは言えない。同一ε制約profileと時間割の探索自由度をCでも扱えるよう調整するか、相違を分離して報告する。内部AOA寄与の対照では同一RMP・日列完成器・候補領域・停止規則の価格付け部分だけを古典化する。

D/Wは無順位の計画性能、Tは方法の性能として扱う。失敗・未配送に都合のよい有限D/Wを与えない。全体可行計画集合の観測三指標非劣関係を記録するが、探索されていない完全パレートフロントの主張はしない。

## 8. 最初の実装と着手ゲート

最初に実装する最小機能は、**4顧客程度の全列列挙を持つRMP・双対・真の被約費用の参照系**である。その後に同じ価格付け式のALiM/XY回路を接続する。S1を先に走らせたり、旧TSPコードへ新ラベルを付けたりしない。

前工程では、この小規模独立参照系はP02/P03を別版で扱い、設定補足を明記する条件でCONDITIONAL GOであった。追加工程で検証した現在の範囲は§9に示す。著者数値の完全再現とS1〜S3の運行計画はHOLDである。後者の解除には[資源・HOLD一覧](D_FEASIBILITY_AND_RISKS.md)の長い便の価格付け、日列完成、共通OD/容量/運行、Cの比較自由度を確定する必要がある。

## 9. 追加工程の到達点と実装差分

小規模独立参照系は実行検証を完了してGOとなった。実際の最小構成はmodels.py、master.py、aoa.py、reduction.py、runner.py、experiment.pyである。初期計画のaoaサブディレクトリ等へ形式だけ合わせるための分割は行わず、独立参照として分離した。新規設定はconfigs/toc_delivery_d/huang_reference_v1.json、依存lockはreproducibility/environment/huang_cg_aoa_v1/requirements.lock.txtである。

小規模batchはsolver_seed=1101/1102の2試行、AOA非改善1ラウンドで終了する診断設定とした。前節の10試行/非改善5ラウンド案を実行済みとはしない。初期計画のマルチトリップ・日列・バース・ε制約は未実装である。次はその小規模古典oracleと共通validatorを作り、マクロ展開後の時間/資源双対へ接続する。
