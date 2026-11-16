# D：車両日列コーディング計画

2026-11-11。[外部コード監査](D_EXTERNAL_CODE_AUDIT.md)→[定式化](D_VEHICLE_DAY_FORMULATION.md)→本計画の保存を完了後に実装する。既存src/kmd_toc/column_generation/を変更せず、新規src/kmd_toc/vehicle_day/へ最小参照を分離する。外部コードの転載は0件である。

## 1. アーキテクチャと契約

|予定ファイル|主な関数・クラスと入出力|
|---|---|
|vehicle_day/model.py|Vehicle、DayProblem、TripSchedule、DayColumn、ObjectiveProfile。元人工行列/運行→不変データとhash|
|vehicle_day/generation.py|make_day、enumerate_days、seed_plan。順序・開始時刻→日列、全格子可行列、初期規則計画|
|vehicle_day/validation.py|validate_day、validate_plan、assign_berths、independent_plan_oracle。元入力/選択列→再計算・原因・参照最良解|
|vehicle_day/master.py|solve_lp、solve_integer、reduced_cost。顧客/車両/占有/補助行→双対・整数選択・状態|
|vehicle_day/pricing.py|exact_price、aoa_day_candidates。全日列又は既存AOA→完成候補・全rc・由来|
|vehicle_day/runner.py|run_day_cg。初期列→Phase I/II→改善列→限定整数選択・oracle差|
|scripts/run_vehicle_day_validation.py|設定/新出力先→全試行JSON/CSV、コード・依存・seed・最大RSS|
|tests/toc_vehicle_day/|必須16項目、独立全組合せ、既存19テストを含む受入検証|
|configs/toc_delivery_d/vehicle_day_validation_v1.json|人工値のみ。凍結需要の設定と混在させない|

時間は秒、Wは分、人工距離はkmラベルの合成値とする。0便は空tuple、未選択車両も未使用である。既存モデルのRouteとPricingAOAを参照し、元の距離/需要を変更しない。新規wrapperは時刻/資源双対を管理し、旧AOAに日列全体を解いたというラベルを付けない。

## 2. Phase別の計画と完了条件

|Phase|作業・作成ファイル/関数|入力→出力|テスト・完了条件|依存・リスク|
|---|---|---|---|---|
|1 日列構造|model.pyの不変class、identity/hash、0〜2便|人工行列・車両条件→DayProblem/DayColumn|0/1/2便と荷量・便間非重複。元IDを保持|外部監査と定式化後。旧データ契約を上書きしない|
|2 時刻/可行性|generation/validationのmake_day、時刻伝播、slot、sweep|経路・積込start→ready/出発/帰着/占有|準備・勤務・積込前出発・1/2バース・格子感度の変異テスト|Phase1。readyの恣意的変更と生成器/検証器の同じ誤りに注意|
|3 主問題|master.pyのLP/整数、Phase I、全双対|日列とprofile→π/σ/κ/μ・選択|強双対、c−Aᵀdual、人工変数0、限定列可行性|Phase2。CP-SATは双対取得元にしない|
|4 古典価格付け|全格子日列oracle、runner反復、重複排除|RMP双対→負rc日列・再解・停止|全日列LP/整数と独立組合せoracle、LP単調性、限定整数gap|Phase3。全列挙は6顧客/2車両等のguard内に限定|
|5 AOA接続|pricing.pyから既存PricingAOA呼出し、候補完成|顧客subset/π/proxy→AOA便→日列全rc|量子由来便の顧客/順序保持、負日列追加、oracle未取得との差|Phase4後。まず安全なk=3、L=3、8qubitを使う。全域証明なし|
|6 統合検証|validation script、JSON/CSV、再現記録|4/5/6顧客・2車両・B=1/2→全結果|必須16項目、全列最良値・LP・最小rc・D/W/積込秒、全失敗を保存|Phase1〜5。人工条件を大田区の実績と称さない|
|7 研究規模判定|READINESS文書、資源式、HOLD台帳|小問題の実測・固定研究条件→個別判定|日列/CG/AOA/バース/研究規模の判定を分離|Phase6。S1〜S3を実行しない|

## 3. 今回の小規模設定と停止

4/5/6顧客、2車両、各最大2便、B=2を基本にB=1を追加する。q_i=1、人工便容量2、初便ready0、作業・移動・積込・準備は各120秒、勤務終了1680秒、格子120秒である。距離行列は顧客IDを並べ替えた有向環の合成距離としてファイルへ全値を保存する。これは研究車両の性能採用ではない。

主目的DとWを別profileとして両方検査し、優先順位を置かない。補助上限の双対を持つ試験も設ける。全日列上限・顧客数/車両数guard、反復上限、追加列数上限、AOA評価数・shotsを実行前の新規設定へ固定する。時間上限を主停止にしない。

初期計画はID順の規則構築を使えるが、最終の車両・便・順序は列選択で変更可能とする。初期可行性がない場合はPhase Iを使う。AOA側に全列挙oracleの改善列を補充せず、oracleは診断だけにする。量子が変更した顧客/順序と、古典が決めた便組合せ・時刻・車両をログで区別する。

## 4. 環境・再現性・保全

HiGHS/Qiskitを含む既存Dの版固定lockを新規の隔離venvへ導入し、既存D環境・A〜C・旧成果を変更しない。新依存が不要なら外部4ライブラリは入れない。使用Python/パッケージ/HiGHS版、CPUスレッド、設定/入力/コードhash、solver_seed、全双対、候補の由来、測定標本、失敗原因、T内訳を保存する。

新規出力へ排他的作成し、既存結果を上書きしない。Tは初期構築・LP・AOA・完成・整数化・独立検証までを測る。全列参照の診断時間を別記し、公式のA〜D比較時間と混同しない。

最終受入では既存Dの19テストを同じ隔離環境で実行し、旧ソースhashと凍結需要8ファイルを作業前後で照合する。本計画の全Phase完了とS1〜S3適用GOは同義ではない。

## 5. 実施後の対応

本計画の初版はAUDIT_PLAN_GATE.jsonとPLAN_SNAPSHOTへ保存し、実装開始時刻より先であることを記録した。Phase1〜4を小規模参照として実装し、Phase5の既存AOA接続とPhase6の人工検証を行った。計41テスト、主22ケースと追加6ケースを記録した。Phase7の判定は[READINESS](D_VEHICLE_DAY_READINESS.md)に示す。

人工距離fixtureの有向環案は、車両割当の改善を明確に検証するため有向線の合成距離へ具体化した。追加の非対称時間行列でも訪問順→帰着→2便readyを検査した。候補限定による見逃しを記録し、S1〜S3はHOLDを維持する。これは研究の需要・道路・車両条件の変更ではない。
