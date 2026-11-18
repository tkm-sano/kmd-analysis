# non_time_variance_pilot_20261117_v1 事前プロトコル

2026-11-17のユーザー依頼に基づく固定75試行。r_pilot=5（各S1/S2/S3×A/B/C/D/D_CLASSICAL_REPLACEMENT）。5は有限初期測定件数であり、精度・検出力・真の収束・十分性を保証しない。旧terminationの15試行とcomparison_designの90試行は件数・分散・費用へ算入しない。本実験はHOLD、追加実規模確認や需要生成をしない。

## 固定条件

正本は既存configs/toc_delivery/termination_rules_20261116_v1.json、docs/research/termination_rules_20261116_v1/STOPPING_RULES.mdとCOUNTER_DEFINITIONS.json。略記でなく全単位・内側ループ・例外を継承する。A_rule_v1/FCFS凍結、B全有向CW、C各枝max(256,16N)確認、D各枝2round×元CWルート・call総start1・初期込み80評価上限・p2・最大3群・tol0.001、訓練/最終各10000shots。共通CP内部solve当たり256衝突/8改善/有限完了、有限車両日カタログ、列生成40round/20新列、LP規模比例反復/IP4V節点を固定。80を実評価数としない。Dはstatevectorと有限抽出、実QPUではない。

凍結Route有向OD、同一familyの入れ子S1=(1000,10,2),S2=(2000,20,4),S3=(4000,40,8)、各M=1。容量60、最大2便、1地点1単位、非空便積込1800秒、作業120秒、8〜20時、個別時間窓なし、車両割当/訪問順/便接続/バース排他を維持。需要間分散を推定しない。

同じ登録4物理コア、BCD/対照の内部4枝各1コア/native1thread、Aは既存実行器と同じ単一子1コア/AS4GiB、RSS木合計32GiB監視を継承。外側は逐次。全枝回収後、距離0.1m→W秒→branch IDで採択。独立外側の最良値選択をしない。T_kind=comparison_parent_wall_including_process_setup_v1、親の入力hash確認/読込・子起動/import・全枝回収・転送/選択・最終二重検査を含む。既存executeを変更せず呼ぶ。SOURCE確認等も既存通りT内。準備importと最終RESULT出力は既存境界のまま。追加ラッパーの登録照合・時刻/状態保存はT外に別記。

保存先は既存workspaceの新ID、既存NFSと入力パスを使用。依存prefix/interpreterを既存と同じにし、新規install・暖機・キャッシュclear/prefetch・I/O最適化・ログ変更をしない。OS page cacheと共有ホスト負荷は制御せず、完全coldや時間の独立性を主張しない。

## 登録・乱数・順序

pilot.py registerが最初の実規模試行前に全75件、入力/OD/設定/実行・解析source hash、snapshot、環境を固定。root=202611170917、SeedSequence([root,scale_index,method_index,repeat])からsolver/quantum各seed、既存branch_seedsのdomain separationで内部枝、D callはSeedSequence([branch_quantum_seed,round,route_index])。Aのseedは全てnull。旧root/系列を再利用せず旧登録の数値との衝突も検査する。設定内の旧root_seed/validation件数は既存確認用の未使用metadataであり、新一覧の生成には使わない。順序seed=202611170918、NumPy PCG64で各反復ブロック15条件をshuffle。ラベル/seedで対応標本にしない。A参照会員は規模ごとの登録済み5件すべて。

REGISTERED/PILOT_MANIFESTは同じ内容、REGISTRATION_LOCKで両方のbytesと一覧・snapshotを固定。登録先存在時は上書きしない。MAIN_MANIFESTはexecutable=false、正式R/h/率精度/比較範囲/seed/順序/A時間会員はnull。

## 停止・再開

固定一覧を一度ずつ実行して終了。p値・CI幅・0分散・勝敗で件数を変えず、旧240/150秒、wall/CPU/dtime制限を復活しない。pollは監視のみ。正常な遅さは停止理由にしない。コード/入力不一致、RSS超過、回収不能、外部終了/ユーザー中断は記録して残り未実行。完了RESULTを上書きせず、失敗のseed置換・再試行もしない。STARTEDのみ/途中directoryは未完了として保全し自動再起動を拒否。flockと実行PID/boot/starttick記録で二重管理を防止、再開前に残存子を検査する。中断確定RESULTのある試行は再起動せず未実行分のみ継続可能（元の安全停止理由の解消が必要）。バッチ内で計画・計時へ影響する変更が必要なら混合・自動追加せず元バッチを保全する。

## 解析（旧の時間上限制御/集計入口は使わない）

登録/開始/正常終了/採用/確定失敗/未完了/未実行を分離。成功D km/W min/T秒/Jは全採用trial ID、n、平均/標本SD/中央値/min/max/分散。失敗品質はnull、全開始T_attemptは別、未完了の経過は費用完了値に使わない。AのD/Wは決定的参照、相違を隠さずdistinct値表示、計時/取得は5記録。長時間を外れ値除外・補正しない。

独立Welchの差D−C/D−置換を規模別D/W/T/Jに記述。S2距離D−Cを継承基準、他は探索的。各群n>=2、合成SE>0、有限分散/独立初期化/概ね正規の少数標本近似。両群0分散やn不足は理由付きnull、0幅CIを作らない。非有意は同等/非劣性ではない。時間の共有ホスト相関の限界を明記。J=(D/D_A+W/W_A+T/median(T_A全指定会員))/3。全A会員採用・D/W一致・正の分母必須、A各行を1へ置換せず、区間は確立参照に条件付く。

計画取得=親採用かつ二重検査成功、可行=検証済み可行計画を取得した試行（失敗は不可行の証明ではない）。既存品質目標D/Wはcomparison_design設定の凍結A値を記述用継承、停止/採否に使わない。確定開始全数を分母、未実行除外、未確定があれば全開始率区間保留、確定のみ暫定率を別表示。入力失敗/中断等の確定取得失敗も分母へ含める。Wilson/Clopper–Pearson両側95%、点ごとの区間で同時保証なし。厳密な親初到達時刻は未観測null、終Tを代入せず、枝内部候補時刻は別scope。期限なしの今回に旧restricted-time/cap補完を使わない。

## 未採用の本実験候補

距離半幅h=1/5/10km、率Wilson最悪半幅0.15/0.10/0.05、全3規模の費用を含む。既存継承案はS2通常95%、S1/S3探索的95%（配分上は全規模に同じhを感度として適用）。3規模主要案はD−Cの3距離比較をfamily、Bonferroniでalpha=0.05/3の区間精度。Holm検定と混同しない。

分散は(1)観測点推定、(2)各正分散にchi-square上側（各群alpha=.025、2群同時95%/規模、3規模主要案ではalpha=.05/6）、(3)観測分散へ両群対称にsigma_add²追加、sigma_add=1/5/10km。(0は観測のみ)。0をchi-squareに代入して上界にせず、ゼロ観測群の未知分散は未識別。両群ゼロの品質必要Rはnull。片群ゼロの点推定は観測仮定に限るとの警告を付す。

数値Welch t補正で必要成功数を算定。全15条件均等Rと、C/Dのsqrt(v_C*c_D/(v_D*c_C))比を用いた整数配分（最低各2成功、Welch幅再確認、厳密整数最適とは主張しない）を比較。その他手法は率精度数、均等は全15条件の最大必要数。A品質参照1とA計時/率反復を分離。予備各cellのexact成功率95%下限pを仮定しBinomialで必要成功数へ達する確率90%となる総試行数を計算。各cell条件付き計画感度、全条件同時保証なし。率数だけで距離を保証せず、未識別時は品質統合R/費用null、率だけの参考費用は独立表示。

費用は新75件の全確定T_attempt平均を用い、観測maxを掛ける感度も表示（厳密上界ではない）。未完了残存なら予測に制約明記。試行間gap、wrapperのT外/共通準備、登録/解析/出力を別計測、重複加算しない。内部並列は既にTへ含むため再度4で割らない。4×wallは予約core時間で実CPUと区別。有限wall上界は未保証。1/4/24時間は期待費用の参考、承認予算ではない。

## 検証と保全

新管理/解析は人工fixtureで、一覧改変/設定混入/完了再実行/未完了区別/0分散/n不足/無分母/main拒否を検証。既存終了規則テストを再利用するが実規模は追加しない。README/凍結入力/OD/A/旧結果・manifest/既存未コミット・human sessionを変更しない。SOURCE_SNAPSHOTと初期diff/hash、最終保全照合を保存。

## 方法論の適用範囲

旧PROTOCOL/design.py/design_report.pyと補足入口を確認し、固定需要と需要間変動の区別、独立群Welch、率区間、条件付き成功数、費用配分を継承。旧cap/期限・S2だけの費用表・0幅CIは継承しない。
[NIST率CI](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm)はWilson/二項exact、[OR-Tools公式](https://developers.google.com/optimization/cp/cp_solver)はFEASIBLEとOPTIMAL等の状態区別、[Python公式time](https://docs.python.org/3/library/time.html)は経過/CPU時計の区別に使用。[Campelo & Wanner (2020)](https://doi.org/10.1007/s10732-020-09454-w)はアルゴリズム比較の試行/問題数設計の文脈（DOI先の本文は今回web取得不能、既存PROTOCOLの記載を参照）。これらが5回/10000shots/80評価/有限予算の十分性や最適性を認定したとは解釈しない。
