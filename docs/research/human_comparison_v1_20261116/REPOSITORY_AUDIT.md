# 既存資産・入出力・計時の監査

2026-11-16。作業HEADは8605d5412f6af62229a83095c35ab04c8c7dd9b1である。AGENTS.md、README、git status、原RQ・仮説、設定と実装を確認した。多数の未追跡研究資産とREADME/.gitignoreの既存変更がある。[開始時状態](GIT_STATUS_BEFORE.txt)と[421ファイルの開始時hash](PRESERVATION_BEFORE.json)を保存した。checkout/reset/commit/pushは行わない。

## 確認対象と呼出経路

|方式・資産|実際の入口と処理|出力・現行計時|今回の扱い|
|---|---|---|---|
|旧A_rule_v1|scripts/run_a_rule_v1.py内worker → baseline_a/rule_inputs.py・rule_v1.py|角度初期区域、NN、容量分割、境界O/H改善、FCFS。単独T_program|凍結7ファイルと保存済み結果を保全。人手時間へ流用しない|
|旧比較A|scripts/run_comparison_v1.py → comparison_v1/worker.py|新契約A_rule経路と、さらに古いDWT内Aは別物。比較v1のT_program|legacy_program_onlyで旧比較CLIへ委譲|
|既存人手A|scripts/run_a_human_v1.py → baseline_a/human_v1.py|CSVの割当・順序を維持、容量60で分割、FCFS、二重検証。旧セッションの段階時間|基礎処理は再利用。旧CLI・設定・結果は変更しない|
|B|dwt.parallel.execute_parallel → worker.execute → methods.generate|有向Clarke–Wright候補と共通完成器、4枝|方式と探索方針を保持し新しい外側セッションに接続|
|C|同上 → routing_pool → 共通完成器|OR Routing候補生成、4枝|同上|
|D|同上 → hybrid/EventDayMaster、PricingAOA → 共通完成器|古典LP/IP、価格付け、AOAシミュレーション、4枝|同上。実機は使用しない|

旧人手CLIは担当者の経験・ツール・事前未閲覧・正式な反復構造を一括して登録しない。段階の経過時間を人手の実作業時間と同一視できない。新モードでは事前登録と作業開始・終了の明示マーカーを追加する。自己申告または観察者のマーカーは連続的な注意の独立証明ではない。

## 共通処理と方式固有処理

Problemはstop_id、vehicle_id、berth_idの文字列ID、有向ODのm/秒、整数秒イベントを持つ。Planは非空TripとVisitを持つ。新入口のAは未割当需要のカタログを開示し、人間のCSV `vehicle_id,sequence,stop_id` を受け取る。IDの改名・地点の追加削除・順序補正をしない。human_v1.complete_manualはcompile_groupへ恒等順序関数を渡すため、rule_v1のNNやgenerateを実行しない。

共通完成器はB/C/Dのroute poolからルートを選び、車両・便・積込開始を決定する。便内部の訪問順は保持するが、完成計画全体を単に時刻計算する処理ではない。Aをこの完成器へ渡さない。AのFCFSをB/C/Dの物理制約にしない。

全方式の最終計画はcommon.validation.validate_planと、生成器の経路・バース計算を呼び出さないbaseline_a.program_validation.audit_plan（Decimalによる独立再計算）で確認する。Aだけはmanual_groupsとの全順序一致および独立FCFS検査も行う。正式D/Wは独立再計算値であり、native solverの目的値ではない。

## 入力・条件・予算の監査

正本はconfigs/toc_delivery/common_conditions_v1_1.json、frozen_demand_v1.json、凍結Route入力とOD manifestである。共通条件JSONの旧Table由来の説明文と、Route実データは区別する。新契約はRoute manifestを要求し、Table混入を拒否する。旧900秒準備、上流PE、旧102秒サービスへ読み替えない。

既存CPU並列規約は4物理コア、各枝native1 threadであり、単コアへの暗黙フォールバックを認めない。旧native予算tauと新T_totalは境界が異なる。新契約で `total_limit_s >= machine_limit_s >= native_limit_s > 0` をケースごとに必須とし、全方式で同一値を用いる。

旧Jおよび旧A参照管理はcomparison_v1/analysis.py等に存在するが、A_ruleのT_programを用いる参照はhuman-inclusiveのAには適格でない。新契約ではJを常にnullとする。

## 比較を妨げていた事項と対応

|事項|対応・残る限界|
|---|---|
|人間の割当・順序と時間が未観測|計時・棄却・修正・採用ツールを追加。実測そのものは未実施|
|旧human時間と旧program時間の境界差|新契約ID、T_kind、phase、observed、source/input hashで隔離|
|需要seed・内部枝・人の反復の混同|case/run/participant/solver_seed/quantum_seed/repetition/analysis_roleを分離|
|S1⊂S2⊂S3の非独立性|同じfamily_id、independent_draw=false。独立3需要として推論しない|
|中断・boot変更・不正CSV|終了記録と棄却原本を保存。再起動後の単調時計差を生成しない|
|対象事業者の代表性|実務方式・人員・時間・作業分布の資料がなく未検証|

新規コードはsrc/kmd_toc/human_comparison_v1、CLIはscripts/run_human_comparison_v1.py、設定と結果スキーマはhuman_comparison_v1_*へ分離した。既存アルゴリズムや目的関数を変更せず、観測用ラッパーだけを子プロセス内に装着する。最終保全確認はPRESERVATION_FINAL.jsonで行った。別作業で新規作成されたtermination_v1/work.pyの更新による事後hash拒否は、共有ファイルを戻さず、実行時snapshotの隔離検証で扱った。詳細はVALIDATION_RECORD.mdに記録した。
