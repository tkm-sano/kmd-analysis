# 検証記録

実装検証と実規模動作確認を分ける。本実験Rや分散測定として使わない。機械可読な検証結果の正本は各batchのREGISTERED.json、runs/*/RESULT.json、ALL_RESULTS.json、TELEMETRY.json、FINAL_AUDIT.jsonである。未完了/失敗行を削除せず、未観測の品質を0にしない。

## 小規模・境界検証

最終コードに対するUNIT_RELEASE.xml/logで15件通過した。実テストはtests/toc_termination_v1/test_termination.pyにある。

|要求上のリスク|検証|
|---|---|
|正常構築と探索|人工有向ODで5手法の全体計画、Routing/CP-SAT/HiGHS/AOA実APIを実行し物理二重検査|
|初期解なし・不可行・無改善|Routing初期assignmentなし、容量を0とした試験用RoutingでNO_PLAN終了、CP候補なしでも検証済みincumbentを保全|
|重複のみ・非可行catalogue|試行前に計数し、重複被覆/make_day棄却でも全有限patternsを終了|
|評価失敗|tensor評価例外でattempt=1/failure=1、再試行せず終了。未実行shotsを実測0として補完しない|
|上限直前/到達|CustomLimit第4回で停止・以後ack別計数。AOA強制81要求で新規評価80、訓練800000shotsを超えず、評価済み角度から最終抽出候補を保全|
|時計だけの変更|A clock=1対10^12で同一計画。RoutingのLedger時計を変えて同じroutes/countersとなることを実APIで確認。native CustomLimitは時計を参照しないtagged sourceも確認|
|CP境界で候補保全|1改善解callbackでWORK_BUDGET_REACHEDとなり、その計画が物理検査を通過|
|4枝・異常枝・同点|small_01は全枝ERRORを回収。単体ではERROR枝と3VALID枝を混ぜ、入力順が逆でもbranch ID最小を採用|
|実測shots/計数|実Qiskit/NumPyでtrainのsum(counts)=10000、final=10000、初期評価/実callback/SciPy cache/optimizer nfev/検査tensor/回路呼出しを区別|
|C拡大poolで初期計画を失うリスク|Routingが重複被覆候補を追加しCP候補がなくても、独立検証済みCW計画を保全して返す|
|物理契約|同じ容量、最大2便、全地点、帰着/勤務、便接続、積込・バース排他をcommon+independentで検査。Aはrule/FCFS検査も実施|
|旧モード保全|A・dwt.methods・comparison_v1.execution・READMEの開始時hashと一致。旧ソースへ変更なし|
|混入・中途停止|time/max_deterministic_time/null work budgetを新configで拒否。未実行と失敗は全行集計へ残す。phaseが本実験ならCLI実行しない|

小規模全体実行はsmall_01〜small_05の5batch×5手法=25試行である。small_01の5失敗は修正前の記録として残し、small_02〜05は各5件全て終了・採用された。最終batchはsmall_05であり、採用設定はその後変更しない。修正理由と影響範囲はAMENDMENTS.json。scales_01はCアダプターの候補保全不備を実行前に見つけたため、0試行のままWITHDRAWN.jsonを添付し保全した。実規模の正本はscales_02である。同じseedを再登録しても未起動の登録を実行反復へ数えない。

## 既存回帰テスト

既存A_rule_v1とtoc_comparison_v1を実行し、127通過、2失敗であった。REGRESSION_01.xml/logを保全した。失敗は旧15秒予算の置換対照（END_TO_END_BUDGET_EXHAUSTED）と旧10秒予算のinvalid-plan process-control（期限内に検査前へ進めずNO_PLAN）である。コード変更なしの単独再確認REGRESSION_ISOLATEDでは後者は通過し、前者の旧時間切れは再現した。旧試験の上限を増やして通過扱いにする修正は行わない。開始時source hashとの一致および新版の非時間検証を区別する。全回帰テストが通過したとは主張しない。

## S1〜S3の登録済み15試行

scales_02/REGISTERED.jsonの順序でS1→S2→S3、各A→B→C→D→D_CLASSICAL_REPLACEMENT、各1試行を実行する。物理コア[0,1,2,3]、内部1/4枝、1thread、RSS32768MiB/A AS4096MiB。設定hash=07bea5d2419f23c2d6fa063ba65341e7347cfe911c10bc6c171daef5cc6c8773、snapshot hash=2c671e81e7516a4e81f58cd72223fe3ede18a84edae382d17f602914f2df4c6b。入力hash・全seed・コードhashはmanifest正本を参照する。秒数による打切り、旧上限超過を理由とする不採用、成功を得るための追加実行を行わない。

最終の15行D/W/T、全枝の操作カウンタ・状態・由来・実測shots・CPU/RSS、未完了/失敗と監査判定は本ファイルの末尾とFINAL_REPORT.md、scales_02/RESULTS.csv、TELEMETRY.json、FINAL_AUDIT.jsonへ集約する。Tには計時内の必要テレメトリI/Oも含まれるため、ソルバー単体時間とは区別する。OS page cache/NFSの共有状態は制御していない。単一確認試行から平均差・分散・速度優位・収束は推定しない。

最終監査: {"experiment_id": "termination_rules_20261116_v1", "non_time_rules_configuration_complete": true, "implementation_complete": true, "required_functional_validation_complete": true, "actual_scale_attempts": 15, "adoptable_attempts": 15, "failures_preserved": 0, "unfinished_actual_scale_attempts": 0, "main_start_allowed": false, "main_started": false, "R_a_fixed": false, "h_D_adopted": false, "remaining_before_main": ["new-setting variance and cost measurement", "adopt R, precision and analysis/multiplicity conditions; formal seed/order/A reference registration"], "old_results_unchanged": true, "strict_all_baseline_files_unchanged": false, "pretrial_unrelated_change_preserved": true, "README_unchanged": true, "main_manifest": "MAIN_MANIFEST.json", "scale_manifest": "output/toc_delivery/termination_rules_20261116_v1/scales_02/REGISTERED.json"}

全15行のD/W/T、実測shotsと費用はFINAL_REPORT.mdおよびscales_02/RESULTS.csvに保存した。厳密な全baseline不変と、無関係な登録前変更を保持した保全判定を区別する。根拠はPRETRIAL_UNRELATED_CHANGE.jsonである。
