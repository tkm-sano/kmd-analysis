# 時間依存監査

対象HEADは8605d5412f6af62229a83095c35ab04c8c7dd9b1である。追跡外ソースが多数あるためHEADのみを版とせず、BASELINE.json、GIT_STATUS_BEFORE.txt、GIT_DIFF_BEFORE.patch、各REGISTERED.jsonの全ファイルhashとSOURCE_SNAPSHOTを用いる。既存のREADMEと.gitignoreの未コミット差分を保全し、旧src/scripts/configを変更せずtermination_v1を追加した。読み取った実配置と要約はLEGACY_INSPECTED.jsonに保存した。旧PROTOCOL/REPRODUCE/MAIN_MANIFEST/TELEMETRY(90行)/確認失敗診断/varianceとconfirmationのソースtar目録/COMPLETION_STATUS/FINAL_AUDITを確認した。旧manifestのS3・D native153.584秒>150秒による不採用は変更しない。

新入口はscripts/run_termination_rules.pyである。旧CLIの秒数付きモードは過去再現専用として保全し、新設定を旧comparison_v1.validate_manifestへ押し込まない。旧スキーマは正のwall予算を必須とし採用値をdeadlineで排除するため、新contract whole-method-finite-work-v1を用いる。共通物理検査、A固有検査、物理モデル、参照J、入力inventory、4枝seed生成を再利用する。旧関数が同じmoduleにimportされても下表の時間付き実行関数を呼ばない。

分類: 1=配送物理時間、2=測定、3=poll、4=探索/採否の時間制御、5=外部環境。TIME_DEPENDENCY_HITS.txtは旧入口から追跡したrg生結果であり、単なるremainingという未訪問集合も含む。NEW_CALL_GRAPH.jsonに新経路の使用/非使用関数を記録する。

|設定/場所・関数|旧既定値・範囲|分類|新版の処置|
|---|---|---|---|
|comparison_design設定profiles.retained / design.make_plan|outer240秒、native150秒、C_routing_fraction0.5、D各配分fraction|4|新設定へ取り込まず、有限処理規則へ置換。旧ファイル保全。|
|scripts/run_comparison_design.py main/stage、comparison_v1.execution.run|pilot全体21600秒、残りwallと次試行capで省略、300秒reserve|4|新runは登録済みIDを一巡。全体残り秒数・省略・短縮なし。明示中断/資源停止時は未実行IDを残す。|
|comparison_v1.execution.execute/supervise|SIGALRM、outer deadline、計時後候補不採用、native deadline失敗|4|呼ばない。runner.executeは時計を採否に使用しない。start前保存、全枝終了、最終二重検査を維持。|
|comparison_v1.worker A|planning150秒、absolute180秒SIGALRM|4|呼ばない。凍結rule_v1.generateをdeadline省略で直接実行。|
|baseline_a.rule_v1.generate|deadline=math.inf（wrapperは有限値を上書き）|4(無効)|凍結本体変更なし。新adapterは上書きしない。有限時計値で常に非作動。10000候補/V改善/有限近傍を終了規則とする。人工的な巨大秒数は指定しない。|
|baseline_a.rule_v1.nearest_order remaining|未訪問集合を空まで|時間制御でない|毎回要素を除く有限構築として再利用。|
|comparison_v1.worker BCD|remaining×0.9とnative_cap最小|4|旧worker非使用。4 fresh childを直接起動。|
|dwt.budget.Budget.left/mark/verify|deadline、validation reserve8%、jitter、動的検査reserve|4/2|Budgetを作らない。Ledgerの時計は観測のみ。検査時間による候補処理の短縮なし。|
|dwt.methods.generate/complete|C配分、CP remaining、incumbentの時間内採否|4|新solvers.routing_pool/complete/solve_completion、時間無制限native＋有限操作/モデル。|
|pipeline.classical.routing_pool|60秒、params.time_limit|4|旧関数非使用。新params time_limit.ClearField、CustomLimit共通確認回数。|
|Routing DefaultRoutingSearchParameters lns_time_limit|使用版では0.1秒(100000000nanos)|4|lns_time_limit.ClearFieldをCloseModel前に実行。時間配分式を残さない。未指定はv9.14 routing.ccによりInfiniteDuration=無効。|
|Routing init/LNS/finalizer|seed読込、初期戦略、GLS、内側LNS|4|同じCP探索を維持し共通monitorを登録。LNS近傍は有限モデル。CP-SAT fallback無効、max_deterministic_timeを代用しない。solution_limit単独は採用しない。|
|pipeline.completion.complete_routes|CP-SAT30秒、dwt呼出しは残り秒数|4|同一x/被覆/時刻/cumulative/目的を新adapterへ継承。時間パラメータ未設定。NO_RESTART、内部衝突256、改善解8、有限整数探索。SAT inprocessingとsymmetryを無効にし、内側のdtime予算による前処理量調整も使わない。|
|dwt.methods.hybrid catalogue|stageの35%で列生成停止、実行速度依存prefix|4|全車両、単便＋2方向の循環被覆隣接パターンを有限列挙。旧prefixと候補集合が異なることを明記。|
|dwt.methods.hybrid BoundedMaster.allowance/lp/ip|stage end、LP time_limit、IP min(30秒,remaining)|4|新FiniteMasterはLP simplex反復とIP節点/内部simplex反復、未設定の時間制限。|
|pipeline.hybrid.EventDayMaster.ip|primary30秒、secondaryはremaining>0.001だけ|4|行列・列検査は継承、lp/ip両方override。secondaryはprimary incumbentがあれば1回、秒数判定なし。互換引数secondsが渡れば拒否。|
|dwt.methods.hybrid quantum_end|量子35%等、途中round/routeを省略|4|全2round×元CWルートを処理。shots/evaluationの時間依存削減なし。|
|column_generation.aoa.PricingAOA.run|COBYLA maxiter80(旧retained)、restarts1、train1000/final4096|非時間規則/2|有限構造・回路・sample目的を継承。train/final各10000、目的評価guard、失敗/call終了、実測ledgerを追加。SciPy内部cacheは計測し挙動を保つ。|
|dwt.parallel.execute/_branch_entry|dependency_setup240秒、残り時間、coordinator20%reserve、join猶予|4|cpu_profile/branch_seedsだけ再利用、execute非使用。新親は全枝を無期限pollし回収。到着順ではなくbranch IDで同点処理。|
|dwt.experiment.execute/worker|startup240秒、output30秒、watchdog/kill|4|旧入口非使用。新品の通常経路にjoin/wait timeoutなし。|
|comparison_v1.execution.cleanup|terminate0.2秒、kill/reap2秒|5/4|新入口非使用。明示外部中断・RSS超過時のみ所有sessionをkillしwait。通常探索を猶予秒数で切らない。|
|rule_v1/validation/audit/completion/vehicle_day|8〜20時、return deadline、便接続、積込1800秒、地点作業120秒、berth calendar|1|全て維持。相違は物理検査違反として不採用。|
|perf_counter/process_time、rusage、stages|T、CPU、観測候補時刻、メモリ|2|維持。計時内外の範囲はSTOPPING_RULES。A rule時計も順序処理の観測に使用。|
|runner.execute poll/sampling|poll0.01秒、RSS0.5秒|3|poll周期だけ。停止条件はプロセス終了または資源超過。時間超過では停止しない。|
|tree_RSS_limit/A RLIMIT_AS|合計32768MiB、A4096MiB|5|維持、RESOURCE_STOP等を正常終了と分離。RSSsampling間の厳密peak保証はしない。|
|RLIMIT_CPU/cgroup/環境|EXTERNAL_ENVIRONMENT.json参照|5|CPU上限を新設しない。OS/cgroup/外部SIGTERMはアルゴリズム完了と区別し未完了を残す。|
|pipeline.roads/route_pairs|HTTP120/60秒、OD生成queue90秒、join2秒|5|凍結ODを読込む今回の実行で呼ばない。OD再生成せず、過去入力/ODを変更しない。|
|evaluation.py/design_report.py|旧期限付き参照/到達時刻/採用schema|2/4|旧結果解析専用として保全。新aggregateは失敗null/全行を残し、新A参照のみJを計算。旧費用・分散を混ぜない。|
|run_dwt.py/run_dwt_bundle.py|旧CPU4モードCLI|4|既存入口は保全。今回の明示指示に対応する別CLIを新設し、CPU4制約は同じにする。|

## 使用版とソース確認

実行環境はOR-Tools9.14.6206、SciPy1.16.0（同梱HiGHS1.8.0）、Qiskit2.1.1である。最新版ページだけを根拠とせずsources/に該当tagのソースを保存した。hashとURLはSOURCE_INDEX.jsonへ保存する。

- [Routing options](https://developers.google.com/optimization/routing/routing_options)、[common tasks](https://developers.google.com/optimization/routing/routing_tasks)、[Python Solver API](https://or-tools.github.io/docs/python/classortools_1_1constraint__solver_1_1pywrapcp_1_1Solver.html)を参照した。APIページの版と実使用9.14との差はローカルAPIとtagged sourceで照合した。
- [OR-Tools v9.14 search.cc](https://github.com/google/or-tools/blob/v9.14/ortools/constraint_solver/search.cc): SearchLimit::InstallはEnterSearch/BeginNextDecision/PeriodicCheck/RefuteDecisionに登録。CustomLimit::CheckWithOffsetはcallbackを呼び、cloneも同じcallbackを保持。停止後の再確認をackとして区別する。内部関数の実行単位で必ず1回というカウンタではない。
- [v9.14 local_search.cc](https://github.com/google/or-tools/blob/v9.14/ortools/constraint_solver/local_search.cc): FindOneNeighborのループは候補生成前にTopPeriodicCheckする。失敗/非改善候補でも経路が進む。1回の近傍生成・finalizer内部は有限モデルの探索であり、callback回数を全native操作数とは主張しない。
- [v9.14 routing.cc](https://github.com/google/or-tools/blob/v9.14/ortools/constraint_solver/routing.cc): GetTimeLimitとGetLnsTimeLimitはフィールド未指定時InfiniteDuration。初回CloseModel時点から両フィールドを解除する。
- [v9.14 sat_parameters.proto](https://github.com/google/or-tools/blob/v9.14/ortools/sat/sat_parameters.proto)、[integer_search.cc](https://github.com/google/or-tools/blob/v9.14/ortools/sat/integer_search.cc)、[optimization.cc](https://github.com/google/or-tools/blob/v9.14/ortools/sat/optimization.cc): max_number_of_conflictsは内部solveごとの開始衝突との差。linear scanは有限整数目的を厳密に縮め、非FEASIBLEを返す。NO_RESTARTはsat_parameters_pb2のenum、Python cp_modelに同名定数があると仮定しない。最適性/不可解の証明を記すときは有限route-poolの整数目的に限定し、gap=0とboundを保存する。
- [HiGHS v1.8.0 HighsOptions.h](https://github.com/ERGO-Code/HiGHS/blob/v1.8.0/src/lp_data/HighsOptions.h)、[HighsMipSolverData.cpp](https://github.com/ERGO-Code/HiGHS/blob/v1.8.0/src/mip/HighsMipSolverData.cpp): mip_max_nodesはnum_nodes+nodeOffsetで判定。root LP/heuristic/subMIPを含む全反復の総上限ではない。単一solveのfinite binary domainとnative有限ルーチン、simplex反復制限を併用し時間上界とはしない。SciPyが未認識optionsをそのままHiGHSへ渡す警告はログ保全し、実同梱APIでoption名を検証した。
- [SciPy1.16.0 COBYLA adapter](https://github.com/scipy/scipy/blob/v1.16.0/scipy/optimize/_cobyla_py.py): maxiter→maxfev。ScalarFunction初期評価とlast-x memoizationがあるため、optimizer value request/cacheと実objective callbackを別計数する。最大80を80最適化反復と呼ばない。
- [StatevectorSampler](https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.primitives.StatevectorSampler)、[StatevectorEstimator](https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.primitives.StatevectorEstimator)を確認したが、この実装はいずれのprimitiveも使用しない。[Qiskit2.1.1 quantum_state.py](https://github.com/Qiskit/qiskit/blob/2.1.1/qiskit/quantum_info/states/quantum_state.py)のsample_counts→sample_memory→rng.choice(size=shots)を使用する。訓練はNumPy multinomialの度数で有限標本平均、finalはStatevector.sample_counts。shots変更だけで厳密Estimatorを有限標本化したと誤記しない。

## 意味上の差分

外側比較用時間上限は撤廃した。品質目標は新たな停止条件にしない。正常完了は有限処理を終えたことを意味し、最適性・真の収束・事業者実績改善の主張ではない。S1/S2/S3全てを本実験対象範囲とするが、本作業の15試行は分散推定や本実験ではない。旧設定と異なるため費用/分散を再測定してから本実験R・精度・解析条件を定める。A代表性の再検証を今回の完了条件へ追加しない。

追加照合: v9.14 constraint_solver.ccのSolver::TopPeriodicCheckはTopLevelSearch()->PeriodicCheckを直接呼ぶ。CustomLimitの呼出し頻度をwall-clockで決める経路ではない。使用中VeRyPy parallel_savings.pyは既存VERYpy_SOURCE_SNAPSHOT.tar.gzの同名メンバーとSHA256一致し、全N(N−1)/2個を生成して逆方向を追加するため、正常終了時のCW計数N(N−1)を確認した。カウンタのattempt/success/観測shots/optimizer cache/列挙候補の意味はCOUNTER_DEFINITIONS.jsonを正本とする。Dの2roundは同じbase LP双対による2巡であり、roundごとの双対更新を意味しない。

保全監査の例外: 開始時baselineと比べhuman_comparison_v1/session.pyのhashが1件異なった。変更は最初の小規模登録前であり、全登録snapshot/現行版はc42ee95b…で一致する。変更元は未特定であり、この作業で編集したものではない。本比較の実行経路でも使用しない。現行版を上書きせず、開始時hash・各snapshot・初回監査・PRETRIAL_UNRELATED_CHANGE.jsonを保全した。全baseline不変という判定と、今回の対象を保全して登録前の無関係な変更を保持した判定を区別した。
