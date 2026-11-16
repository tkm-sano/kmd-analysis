# D：車両日列に向けた外部公開コード監査

2026-11-11。実装方式を決める前に、下記4リポジトリの固定commitの実装本体・依存宣言・ライセンス・関連テストを確認した。本書に基づく[定式化](D_VEHICLE_DAY_FORMULATION.md)と[コーディング計画](D_VEHICLE_DAY_IMPLEMENTATION_PLAN.md)を先に保存し、その後に最小実装へ進む。外部コードは実行・インストールしておらず、静的監査である。

## 0. 開始時の既存D・研究条件の照合

ブランチmain、HEAD 8605d5412f6af62229a83095c35ab04c8c7dd9b1であり、未コミット/未追跡作業を保全した。既存7文書と以下の実装を読み、今回追加する日列機能を特定した。

|既存パス・入口|確認できた処理|今回の扱い|
|---|---|---|
|src/kmd_toc/column_generation/models.py：Instance/Route/enumerate_routes/route_cost|単独便の容量・順序・全列挙、有向距離|直接importして再利用。旧ファイルを変更しない|
|同master.py：solve_lp/solve_integer|HiGHS被覆/分割LP、顧客dual、限定整数選択|ソルバー・dual検査の設計を維持し、別packageで車両/slot行へ拡張|
|同runner.py：run_column_generation|LP→価格付け→負列追加→整数化、oracle診断とAOA未取得の分離|小規模GO部分を保全。新日列runnerへ無条件置換しない|
|同aoa.py：PricingAOA.run/circuit/decode|one-hot、ALiM、位相、厳密XY、COBYLA、Qiskit標本・rc検査|変更せずwrapperから利用する|
|同experiment.py・既存実測|設定/コードhash、失敗/標本率、時間・qubit・深さ/RSS|記録形式を参考に新runへ分離|
|tests/toc_cg/test_reference.py|既存19テスト|新環境で回帰検証する。旧成果物は再生成しない|

S1/S2/S3は固定需要v1の1,000/2,000/4,000地点、各1個、F=10/20/40、B=2/4/8、最大2便、顧客時間窓なしを維持する。凍結需要の8ファイルをhashで保全する。容量・積込・準備・勤務・全必要ODは採用HOLDであり、今回の人工値を採用値にしない。

Aは既存資料では実績未取得の代理規則であり、実事業者の公開されていない計画アルゴリズムを再現済みとはしていない。BはVeRyPy並列Clarke–Wright、CはOR-Tools、DはHuangである。旧study.jsonの古い需要/比較記述は凍結需要追補・D文書により置き換えられたHOLD契約として保全し、新入口に使わない。RQ・仮説は変更しない。

## 1. 固定点・ライセンス・依存

|リポジトリと固定commit|ライセンス確認|依存・実行の制限|
|---|---|---|
|[VRPy](https://github.com/romain-montagne/vrpy/tree/ff325cbe64c08d53969fc54b7ff9f7a9b2fa1d63)、ff325cbe64c08d53969fc54b7ff9f7a9b2fa1d63|LICENSEはMIT、2020 Kuifje02。コピー時は著作権・許諾表示を保つ|setup.pyは0.5.1、cspy/networkx/numpy/pulp、requirements.txtは版未固定。今回導入しない|
|[PyVRP](https://github.com/PyVRP/PyVRP/tree/1e07f972d437d6ebad8e1e241d2d807c209998c3)、1e07f972d437d6ebad8e1e241d2d807c209998c3|LICENSE.mdはMIT、Vidal/ORTEC/PyVRP contributorsの表示。コピー時は表示を保つ|pyproject.tomlは1.0.0a0、Python>=3.12、numpy>=1.26、matplotlib>=2.2、vrplib>=1.4、tqdm>=4.64.1、C++拡張/Meson。今回導入しない|
|[spkelle2](https://github.com/spkelle2/vehicle_routing_column_generation/tree/e331c4dc7c8000fb71d93f6445c2cfeb59d9fd6c)、e331c4dc7c8000fb71d93f6445c2cfeb59d9fd6c|取得した再帰treeにLICENSE/COPYING相当を確認できず、GitHubライセンス欄もnull。利用許諾不明|environment.ymlはgurobi/pandas等とpip ticdat、版未固定。Gurobiライセンスが必要とREADMEに記載。コードをコピーしない|
|[onboarding92/Vrptw](https://github.com/onboarding92/Vrptw/tree/a3000ce7ad083a978dee249e21dac4809df38f07)、a3000ce7ad083a978dee249e21dac4809df38f07|LICENSEはMIT、2020 onboarding92。コピー時は表示を保つ|NumPy/SciPy/gurobipy。版固定は未確認。教育用と明記、SSRの循環による無限反復の注意あり。今回導入しない|

commitは2026-11-11の確認時点以前に限定した。Webドキュメントの最新表示と固定ソースを混同しない。特にPyVRPはこのcommitのActivity方式を確認しており、別版のTripクラスを確認済みとはしない。本作業ではどの外部実装も転載・vendor・直接呼出しせず、設計上の参考に限定する。

## 2. VRPy：実装本体の確認

固定URLの接頭辞は上表のtreeと同じcommitである。

|ファイル・関数|確認した処理・入出力|研究への適合・不足|
|---|---|---|
|[vrpy/master_solve_pulp.py](https://github.com/romain-montagne/vrpy/blob/ff325cbe64c08d53969fc54b7ff9f7a9b2fa1d63/vrpy/master_solve_pulp.py)：_MasterSolvePulp.solve/get_duals/update、_add_route_selection_variable|NetworkX経路graphと訪問行からPuLP列変数を追加し、顧客・車両上限のconstraint.piを返す|RMP/dual/pricingを分離する設計を参考にする。既存HiGHSを置換しない|
|同ファイル：_solve、_add_set_covering_constraints|LPは被覆>=、整数段階で訪問行を等式に変更し、列を整数化。人工車両変数を整数段階で0へ固定|本研究ではLPから一度配送の等式を使う。巨大人工罰金1e10の方式は採用せず、明示的Phase Iにする|
|[vrpy/subproblem.py](https://github.com/romain-montagne/vrpy/blob/ff325cbe64c08d53969fc54b7ff9f7a9b2fa1d63/vrpy/subproblem.py)：_SubProblemBase.add_reduced_cost_attribute|edge weight=実費用−顧客双対、Sourceからの辺に車両上限双対も反映|顧客双対だけでは不足することの参考。本研究ではバース・補助目的制約も日列被約費用へ含める|
|[vrpy/subproblem_cspy.py](https://github.com/romain-montagne/vrpy/blob/ff325cbe64c08d53969fc54b7ff9f7a9b2fa1d63/vrpy/subproblem_cspy.py)：_SubProblemCSPY.solve/formulate/create_new_route、_MyREFCallback.REF_fwd/bwd/join|資源付きDiGraphをcspy.BiDirectionalへ渡す。load/time/stopsの資源とREF、total_cost<−1e−3の追加判定、edge列比較による重複排除|資源遷移と真の費用を分離する参考。共有バースの時刻別双対や車両日列を直接提供するものではない|
|[vrpy/vrp.py](https://github.com/romain-montagne/vrpy/blob/ff325cbe64c08d53969fc54b7ff9f7a9b2fa1d63/vrpy/vrp.py)：_column_generation/_find_columns/_solve|RMP→車種別価格付け→update、最終MIP。時間・反復・非改善打切りを持つ|時間を主停止にする部分は継承しない。heuristic/threshold探索の未取得を全域証明へ読み替えない|

cspyのelementary/non-elementary再試行、threshold、time_limitがあるため、単にVRPyのsolveを呼んだことを厳密価格付け証明と呼ばない。docs/mathematical_background.rst、docs/solving_options.rst、tests/test_subproblem_greedy.pyも読み、文書と本体の範囲を区別した。cspy内部の実装自体は本監査の対象外である。

## 3. PyVRP：複数便と時刻の確認

|ファイル・関数|確認した実装|本研究での扱い|
|---|---|---|
|[pyvrp/cpp/Route.h・Route.cpp](https://github.com/PyVRP/PyVRP/blob/1e07f972d437d6ebad8e1e241d2d807c209998c3/pyvrp/cpp/Route.cpp)：Route::validate、setSchedule、ScheduledActivity|depot Activityでtrip番号を増やし、各活動のtrip/start/end/wait/timeWarpを保持。車両のmaxTripsと照合|便区切り・活動時刻の構造を参考に独立データクラスを作る。timeWarpを許容する探索結果を可行解としない|
|[VehicleType.h・VehicleType.cpp](https://github.com/PyVRP/PyVRP/blob/1e07f972d437d6ebad8e1e241d2d807c209998c3/pyvrp/cpp/VehicleType.cpp)：VehicleType::maxTrips|reloadDepotsが空なら1便、それ以外はmaxReloads+1（overflow処理あり）。shift start/end/duration、start/end depot、capacityを保持|最大2便は再積込1回に相当する構造。ただし研究の準備・積込・ready・共有バースは別途必要|
|[DurationSegment.h](https://github.com/PyVRP/PyVRP/blob/1e07f972d437d6ebad8e1e241d2d807c209998c3/pyvrp/cpp/DurationSegment.h)：merge/finaliseFront/finaliseBack|便間のrelease、以前の終了、duration、wait/timeWarpを結合する資源構造|時刻を経路から再計算する設計を参考にする。顧客時間窓・releaseのモデルは研究へ追加しない|
|tests/test_Route.py、test_VehicleType.py|複数便アクセス、max_reloads違反、shift duration等のテスト|便番号・容量リセット・勤務終了の同等契約を独立テストする。外部テストは未実行|

[reloadingの公式例](https://pyvrp.org/notebooks/reloading.html)も参照した。監査したRoute/VehicleType/DurationSegmentには、複数車両で同時積込数をB以下にする本研究の共有バース制約を確認できなかった。PyVRPの最適化方式をDの列生成へ置換しない。

## 4. その他2件

spkelle2の[vehicle_routing_column_generation/algorithms.py](https://github.com/spkelle2/vehicle_routing_column_generation/blob/e331c4dc7c8000fb71d93f6445c2cfeb59d9fd6c/vehicle_routing_column_generation/algorithms.py)のHeuristicVRP._create_master_problem/_create_subproblem/solve/_add_best_routesを確認した。dict型のCSV入力、Gurobiの顧客行dual、arc二値＋到着時刻、gu.Columnによる追加、solution pool、最終binary化がある。gists/heuristic_vrp.pyとtest_algorithms.pyも確認した。時間窓付き単独経路の教育例であり、日列・共有バースは確認できない。本体にはTimeLimitへpricing_problem_mip_gapを渡す箇所があり、設定名の意味をそのまま継承しない。ライセンス未確認のため設計確認に限定し、コピーしない。

onboarding92の[src/VRPTW.py](https://github.com/onboarding92/Vrptw/blob/a3000ce7ad083a978dee249e21dac4809df38f07/src/VRPTW.py)のVRPTW.init_model/solve/add_pathと[src/ESPPRC.py](https://github.com/onboarding92/Vrptw/blob/a3000ce7ad083a978dee249e21dac4809df38f07/src/ESPPRC.py)のLabel/ESP_Label/extended_label、DSSR_ESPPRC.pyを確認した。Gurobiの訪問等式・車両行、dual取得、path tuple setの重複排除、time/load/visited-setを持つラベルがある。距離と時間を同じ配列にする前提や、初期列可行性TODO、車両数だけの分枝ではroute変数の整数性を保証しない注意がある。本研究の異なる距離/時間行列、全日時間割、整数選択の代用にはしない。依存版と独立したテスト一式は未確認であり、外部実行はしていない。

## 5. 監査後の採用判断

|機能|区分と決定|根拠・同等性確認|
|---|---|---|
|日列データ|外部設計を参考に独立実装|PyVRP Route/ScheduledActivityを参考に、DayColumnが0〜2本のTripScheduleを持つ。便・時刻の再計算テスト|
|2便の時刻伝播|外部設計を参考に独立実装|DurationSegmentの結合概念。帰着＋準備→ready、積込完了→出発を個別検査|
|バース占有|本研究固有の新規実装|固定積込intervalの格子行。1/2バース、半開区間、独立sweepで検証|
|古典価格付け|既存D再利用＋独立拡張|models.enumerate_routesを再利用して日列へ完成。小規模全日列探索と独立組合せoracle|
|RMP LP/整数|既存DのHiGHS・双対検査の設計を維持して拡張|VRPyのRMP分離を参考に、新しい顧客/車両/占有行へ対応。旧master.pyは変更しない|
|AOA接続|既存Dコードを再利用|PricingAOAを変更せずtrip候補を受け取り日列へ完成。全日列rcを再計算。候補由来とoracle診断を分離|
|可行性検証|本研究固有の新規実装|元入力から距離・時間・荷量・占有を独立再計算。変異テストと全列参照|
|ログ/再現性|既存D設計を再利用|排他的出力、設定/コードhash、全双対/棄却理由/停止状態、source snapshot|

**外部コードの直接再利用は0件である。** 外部設計を確認した結果、既存Dを残し、時刻付き車両日列の小規模参照を別packageへ独立実装する。外部ライブラリを入れただけで日列・共有バース対応が完成すると判断しない。
