# 非時間終了規則 — termination_rules_20261116_v1

登録前に定めた実行可能な基準設定である。旧 comparison_design_20261116_v1 の retained (外側240秒/native150秒) を継承しつつ、秒数による探索配分を使用しない。目的は終了規則と動作確認であり、計算量の等量化、パラメータの最適性、収束、運用締切の保証ではない。S1/S2/S3の各5手法各1試行は運用確認であり、統計的Rではない。本実験は非実行のままである。

## 単位と共通条件

Nは地点数、Vは車両数、Kは当該段階の重複除去後ルート数である。S1=(1000,10,2バース)、S2=(2000,20,4)、S3=(4000,40,8)。Mは凍結需要各規模1件（派生関係を維持）。外側1試行は保存入力の読込、手法初期化、自由な車両割当・訪問順・最大2便の接続、積込・バース計画、全枝終了、採択、二重検査までである。内部4枝は外側Rへ加算しない。

容量60/便、1地点1単位、非空便積込1800秒、地点作業120秒、8〜20時、個別時間窓なし、有向Route OD、全地点被覆、便接続、バース排他は維持する。物理時刻の28800/70200/72000秒や出発・帰着時刻は探索時間上限ではない。品質目的は従来どおりD(0.1m整数精度)を第一、W秒を第二とする。

|手法・段階|終了と具体値/計数単位|適用範囲、進む位置、内部処理、候補保全|
|---|---|---|
|A_rule_v1+FCFS|凍結構築、受理改善最大V回、候補評価最大10000回、または有限近傍の非改善1巡|枝=試行1本。既存generateをdeadline指定なしで呼ぶ（無効な既定inf）。規則本体変更なし。1巡は既存の隣接区域境界候補の固定順、最大2V候補。容量棄却/非改善もtraceを進める。同値は受理しない。V回改善後MOVE_LIMIT、1巡無改善NO_IMPROVEMENT、評価上限EVALUATION_LIMIT。S1〜S3で2V²≤200/800/3200候補の有限上界。初期構築不能は例外として記録。nearest_orderは未訪問地点を毎回1個除く。FCFSは最大2V便の有限イベント処理。|
|B/C/D/置換共通CW|全N(N−1)有向savingsを固定順に走査|各枝1回。結合成功でルート数が減る。必要なルート削減は毎回1ルートを取り除き有限の挿入位置から選ぶ。容量不可なら例外。自由な配送先割当と順序を計算する。|
|C OR-Tools Routing|共有CustomLimit述語の有効確認回数 max(256,16N)。S1=16000、S2=32000、S3=64000|各枝のRouting呼出し1回。初期解、局所探索、LNSを同じmonitorで覆う。Checkの先頭で増加、上限回でTrueを返す。clone/restartで共有しリセットしない。以後の停止確認はacknowledgementsとして別計数。解数/改善/成功の有無に依存しない。PARALLEL_CHEAPEST_INSERTION+GUIDED_LOCAL_SEARCH、容量次元・2V自由ルート枠を維持。初期CWは常に候補集合へ保全。物理検証済みCWスケジュールもRouting前に保持し、拡大poolで完成器が新解を返さなくても既存incumbentを失わない。ReadAssignment以前に同一paramsでCloseModel。time_limitとlns_time_limitをClearField。CP-SAT fallbackは無効、CP Routingは維持。|
|共通CP-SAT完成処理|有限整数モデルの探索完了、または改善解callback最大8件、内部SAT solve当たり衝突256件|B/C各枝1回、D/置換各枝seed・最終の2回。単一worker FIXED_SEARCH、NO_RESTART、presolveなし、probingなし、linearization0、LNS/RINS/feasibility pumpなし、SAT inprocessingなし、symmetry0、gap0。衝突はnativeが競合を検出した位置で増える。256は全client solveの累積上限ではない。改善解はcallback開始で増加し8件目を保全してStopSearch。初期解なしでも有限domainの探索/内部衝突制限で終了する。整数目的は改善ごとに厳密減少し有限で、内部solveのLIMIT_REACHEDは上位へ返る。UNKNOWN/FEASIBLEを不可解/最適としない。greedy/前段の独立検証済みincumbentを維持し、探索候補を二重検証して比較する。ヒントに過ぎずxを固定しない。|
|D/置換 車両日catalogue|全単便K通り＋各ルートの2つの循環被覆隣接群との2便パターン、全V車両。生成試行は3VK以下|各枝baseとhybridの各1回。ルートを被覆集合の辞書順群へ分類、各群内はルート辞書順。各variantに群offset +1,-1の同variant-index mod群sizeを組合せる。試行カウンタは重複/重複被覆/非可行の判定前に増加。全車両を走査し固定割当しない。現在試行のseed列を必ず保全。各車両の当該seedカレンダーを使い、開始時刻1個なら既存式で第2便候補を補う。旧時間打切りprefixから、明示した有限近傍カタログへ変更。全ルート対を網羅するとは主張しない。Dと置換で同じ規則を使う。|
|D/置換 列生成|最大40round、1round新規負reduced-cost列最大20件|各枝base/hybrid各1回。round先頭からLP1回、負rc<-1e-7未登録列を(rc,index)順に追加。ゼロ/失敗LPなら終了。最後のLP/IP、零rc面の追加後IP、正の整数gap時の全宣言列IPは各最大1回。40round以外の追加LP/IPも記録。閉包は宣言済み有限catalogueのみ。|
|HiGHS LP|dual-simplex反復 max(1000,4×(等式行+不等式行+当該変数数))|各LP呼出しごと。method highs-ds、presolve無効、threads1。native pivot反復nitで計数。上限/不可行/例外を記録し、失敗dualは使用しない（pricing dualは0にし有限呼出しを続行）。LPのサイクルに無制限依存しない。|
|HiGHS IP|B&B節点4V (40/80/160)、stall節点同値、simplex反復 max(1000,4×(全master行+当該変数数))|各primary/secondary呼出しに独立適用。presolve無効、threads1、gap0。primary incumbentが存在する場合だけ同じD以下でWのsecondaryを1回実行。終了/上限で返ったincumbentを検査して保全する。節点に入る前のLP/ヒューリスティックは有限native処理であり、4Vを全内部操作数や全subMIPの総和とは呼ばない。全処理の時間上界は保証しない。|
|D/置換 pricing|最大2round、各roundすべての元CWルート1回|各枝。K_CW≤2Vなので呼出し試行≤4V（S1≤40/S2≤80/S3≤160）、外側4枝合計≤16V。round、route_indexが論理ID。失敗/空/重複/非改善でも次のIDへ進み、再試行しない。各ルートを連続最大3マクロ群へ分割。Dと置換で同一領域。時間でshots/評価/round/call数を減らさない。|
|D AOA訓練|p=2、総start数1、COBYLA目的評価最大80、tol=0.001|pricing呼出し1回ごと、startごとの上限。restart=1は初回を含む総1回であり追加1回ではない。SciPy1.16 maxiterはmaxfevへ渡る。初期評価を含み、勾配評価0、独自評価cacheなし。SciPy ScalarFunctionのlast-x cacheは挙動を変えずvalue要求とcache hitを別計数し、cache hitは新規評価/shotsへ加算しない。同じ角度の再評価も新規有限標本を消費。評価要求、評価試行、成功/失敗、サンプリングを別計数。評価前に試行数を増加、失敗で当該callを記録して終了。COBYLAの早期returnも有限非時間終了であり収束証明ではない。|
|D訓練sampling|成功評価ごと10000shots|one-hot tensorを状態計算し確率からNumPy multinomial(10000)で標本度数を生成し、標本エネルギー平均を返す。状態ベクトル厳密期待値を目的にしない。原子的sample正常return時のsum(counts)を実測shotsとして記録。開始のみ/失敗なら未観測を0にしない。訓練tensor呼出しとsampling呼出しを分離する。|
|D最終抽出|各start1回10000shots|Qiskit circuit構築・Statevector evolution→tensorとの検査→Statevector.sample_counts(10000)。回路構築、状態計算、検査tensor、samplingを別計数。12qubits以下（最大3群、4node、可変3位置）。decodeは観測された有限bitstringを1巡。部分/重複/非可行は生ログへ、元被覆を完全に持つ群順序のみ後段へ渡す。|
|D_CLASSICAL_REPLACEMENT|同一最大3群の全順列、最大3!=6通り|各pricing call。2roundとも登録済みIDとして処理し、roundを跨ぐ重複は回数に含める。量子なしの旧D_CLASSICAL_CONTROLとは別物。候補は同じマクロ群領域、同じ列生成/完成処理へ渡す。人為的な時間合わせなし。|
|親/4枝|登録済み全枝の終了を待ち、全状態回収後に選択|A1枝、BCD/置換4 fresh subprocess。終了理由NORMAL/ERROR/RESOURCE_STOP/USER_CANCELLED/EXTERNAL_INTERRUPTION、計画VALID/INVALID/NO_PLAN、採用を独立記録。異常枝も保全し、全枝成功は要求しない。正常に候補を返した枝があれば二重検証で選択する。採択keyは距離0.1m、W秒、branch ID。到着順は参照しない。|

## 資源と時間

物理4コアを実行前に検証し、各枝に1コアaffinity、OMP/BLAS/MKL/Numexpr1thread、native solver1thread。他手法と計時中に並行しない。枝tree RSS合計32768MiBを0.5秒毎に監視し、超過は外部資源停止であって正常アルゴリズム終了ではない。Aのアドレス空間4096MiBを維持。CPU時間上限は設定しない。既存OS/cgroup/ulimitはENVIRONMENTに記録する。一般の外部故障すべてについて有限秒数の終了を保証するものではない。

T_kindはcomparison_parent_wall_including_process_setup_v1を維持。親の入力hash確認・入力読込からfresh child起動・必要import・全枝終了・転送・選択・親最終二重検査までを含める。旧nested coordinator/forkを直接fresh4子へ変えるが、準備を計時外へ移さない。共通検査ライブラリの一律import/manifest保存は計時前、最終結果書出し/集計は計時後。枝中の必要ログ・候補保存・親チェック/plan転送は計時内。poll0.01秒、RSS sampling0.5秒は実行期限を作らない。perf_counter/process_timeは観測のみ。旧240秒/150秒/A180秒hard/150秒planningやRouting0.5配分は不採用理由にしない。

## seed・採用・解析

外側root_seed=2026111617からscale index/method indexでsolver/quantum seedを生成し、既存branch_seeds domain separationで4枝を生成する。量子callはbranch quantum seed,round,route_indexからSeedSequenceで生成。時刻/PIDはseedに使わない。全seedをREGISTERED.json/JOB.jsonへ保存。各手法の分布推定は行わない。品質がない失敗D/Wはnull。有効なwork上限終了候補は時間切れ失敗としない。

共通品質目標を新たに停止条件へ追加しない。今回のmanifestには新設定に適用する数値品質目標を登録しないため、到達時刻/最終到達状況は未定義nullとし、過去目標の期限到達を捏造しない。候補を観測し検査した時刻とD/W軌跡はwork.jsonlへ保存する。Jは従来の(D/D_A+W/W_A+T/T_A_ref)/3、分母0は未定義。確認用A各1回の中央値は記述用参照であり本実験のA時間参照ではない。全試行表と同一需要の差の表を分け、同じseed番号を独立試行の対応根拠にしない。旧分散/費用/本実験manifestを新設定へ流用しない。

## 根拠

値は従来有限設定（A10000、p2/80評価/2round/総start1、列生成40round/20列）を優先した。不足したRoutingの確認回数16Nは地点数に比例する公開操作予算、CPは内部SATの有限仕事と8改善解、LPは行列規模比例、IPは車両数比例、列構築は2便と2方向の被覆隣接候補を基準に定めた。既存秒数への近似や勝者選択で決めていない。いずれも最適設定/精度保証ではなく、D/W/Tをそのまま公開する基準実装である。API/ソースの確認箇所はSTOPPING_AUDIT.mdおよびsources/を参照。
