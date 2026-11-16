# 検証記録

2026-11-16。全て小規模・人工入力または既存入力の読取検査である。人間の正式実測・正式統計比較は行っていない。

## 実行前登録と履歴

TEST_01.logは初期25件、TEST_02.logは拡充38件の開発検証である。TEST_03.logは137件PASS（357.08秒、旧部分99件と新基盤38件）、TEST_04.logは追加8件PASS（14.33秒）であった。最終の計時分類修正後は隔離ソースで新基盤39件＋追加8件の47件を再検証し、全てPASSした（TEST_05.log、414.71秒）。変更のない旧部分99件と合わせ、異なる検証項目は146件、失敗0件である。前段階や修正前の件数を重複加算せず、研究の反復標本数にもしない。

単体試験のケース・上限はtest_human_comparison.pyのplan_for、test_real_timeout_control_and_no_late_success等に実行前に固定した。実経路ケースと上限はoutput/toc_delivery/human_comparison_v1_20261116_path01およびpath02のLIMITED_VALIDATION_PLAN.jsonとplan.jsonへ実行前に保存した。各実行中の配送計画コード・CLI・設定は変更していない。全CLI呼出と終了コードは各CLI_CALLS.jsonにある。

初回path01後、全自動オーケストレーションの整合確認と最終採用の一部がOTHERに分類される問題を確認した。T_totalには含まれていたが、内訳の意味を修正してpath02へ再実行した。両者は異なるexperiment_idであり、全体の試行識別子はexperiment_id+run_idである。入力、BCD設定、上限は同じで、Aの採用計画bytesも一致した（path02/REVISION_COMPARISON.json）。どちらも独立需要標本や正式な反復数へ加算しない。

## 実経路確認

人工12地点・4台・1バース、容量60・積込1800秒・サービス120秒等は共通条件をそのまま使用した。Aは固定CSVをスクリプト入力した機能確認であり、人間による計画作成の観測ではない。A/B/C/Dを順次1回ずつ新比較入口で実行した。全方式success、共通物理検証・独立D/W再計算・最終採用検証・事後verifyが通過した。同一problem/OD、非重複実行時刻、全子プロセス群の後始末もPATH_AUDIT.jsonで確認した。

|方式|fixture D km|fixture W 分|W_first|W_reload|診断用総経過 秒|診断用algorithm区間和集合 秒|正式T_total|
|---|---:|---:|---:|---:|---:|---:|---|
|A|2.951|90|90|0|22.634970878|null|null|
|B|1.660|0|0|0|44.470270003|1.580278799|null|
|C|1.309|0|0|0|45.973608654|19.640254257|null|
|D|1.660|0|0|0|50.578602916|6.225875873|null|

表は修正版path02である。初回の数値はpath01/PATH_DIAGNOSTICS.jsonとFIXTURE_DIAGNOSTICS.csvに保全した。OS cache・共有ホストの負荷は制御しておらず、両runの時間差の因果説明や性能差の推定は行わない。

上表は人工ケースの接続診断であり、配送事業者の計画、人間の所要時間、S1〜S3の研究結果ではない。全行observed=falseで、正式T_human/T_machine/T_computeもnullである。数値の優劣を論じない。計時にはソース整合確認、プロセス起動、証拠保存等の負荷を含む。

B/C/Dは各4PID、affinity=[0],[1],[2],[3]の4枝がVALIDATEDであった。CでOR Routing、全BCDでCP完成器の実呼出を確認した。Aにnative完成器ディレクトリはなく、入力した全車両・順序一致とFCFSを確認した。DはQiskit2.1.1の状態ベクトル／sample_countsシミュレータで、全枝合計8 calls、training shots258000、final shots32768を保存した。実機は使っていない。パラメータ最適化・古典マスター・完成器・シミュレータ・native各成分の記録はあるが、重複する時間を合計しない。

4結果はRESULT_SCHEMAのJSON Schema検査でもPASSした（SCHEMA_VALIDATION.json、修正版SCHEMA_VALIDATION_02.json）。初回のschemaライブラリの版取得で非機能的なdeprecation warningが出たが、検証エラーはない。

path02の実行後、新規の別作業src/kmd_toc/termination_v1/work.pyが共有作業場で更新され、事後verify B/C/Dとaggregate/adoptの計5呼出がSOURCE_HASH_MISMATCHで拒否された。これは当初の421保全対象にはなく、今回のコードもimportしていないファイルである。拒否ログを残し、共有側を戻したりガードを無効化したりせず、保存済みSOURCE_SNAPSHOT.tar.gzをverification_source_snapshotへ展開して全pinを照合した。必要な追加設定は既存原本からコピーしてhashを保存した。全方式の再検証・集計・採用判定とPATH_AUDITはこの隔離ソースでPASSした（SOURCE_ARCHIVE_VERIFICATION.json）。最初の検証を期限後に行ったのではなく、実行時の共通検証・採用は各PROCESS.jsonのとおり期限内に完了している。

## 要求された18項目との対応

|番号|確認内容|結果・主な証拠|
|---|---|---|
|1|人手の車両割当保持|PASS：test_human_v1、common evaluator、実経路AのCSV全順序照合|
|2|訪問順保持|PASS：非対称OD・逆順の手計算20km、容量分割後の順序も保持|
|3|自動最適化が起動しない|PASS：旧human回帰でNN/generate/boundaryを禁止するspy、実経路A完成器不使用|
|4|不正計画棄却|PASS：欠落・重複・121地点・負待機等、棄却後CSV原本保持|
|5|修正時間を含む|PASS：新セッション棄却→修正→採用、旧手計算timeline|
|6|休止を控除しない|PASS：排他的partitionの手計算、pause=OTHERの実セッション検査|
|7|制限時間超過|PASS：実際の0.05秒子プロセス上限とgroup終了確認。200秒負荷耐久試験ではない|
|8|BCD計算時間|PASS：各4枝の開始終了区間・和集合、native時間と分離|
|9|共通物理評価|PASS：同じinput/OD、全方式共通+独立再計算。A固有FCFSはAのみ|
|10|旧A_rule不変|PASS：凍結7ファイル、および保全421ファイル全てhash一致|
|11|未実測人手時間null|PASS：人工セッション・未実施S1〜S3、採用判定MEASURED=false|
|12|人工入力の実測混入拒否|PASS：FALSE_EMPIRICAL_CLASSIFICATION、contract_check全時間null|
|13|同じ需要共有|PASS：実経路4方式の同じproblem/OD、別需要アダプタの読取検査|
|14|欠測・失敗・timeout集計|PASS：全成功、A片側、D片側、両側、全失敗、A失敗CD成功、未完了、0分母|
|15|旧計時契約混入拒否|PASS：LEGACY_TIMING_REJECTED、旧A参照/Jを新Tへ移植しない|
|16|同一試行重複|PASS：run/trial重複、session claim、重複RESULTを拒否|
|17|各hash不一致|PASS：source/config/registration/physical/inputの不一致、採用planのhash照合|
|18|Ttotalと内訳|PASS：単調ns・イベント鎖・区間総和・compute区間のmachine包含を検証|

追加統計検査では、成功条件付き時間と全開始試行の完成率、入力不正とruntime errorの区別、CI不能理由、同じ需要系列・同じ担当者の非独立性ガードを確認した。privateな集計関数へ与えた算術fixtureは単体試験であり、登録済みの実測証拠へ保存していない。

追加需要アダプタは既存S1を読み取り専用で照合するroundtripを実行した。車両容量61への破損を共通検証が拒否し、生成manifestのhash破損も拒否した。これは新しい需要生成器の検証ではなく、B/C/DのS1実行でもない。

## 未実行・残る限界

- 実際の担当者によるS1〜S3の人手計画作成・作業マーカーの実測精度検査。
- 人間が操作するB/C/Dの正式セッション、A〜Dの実需要対応比較と統計評価。
- 新しい需要標本の生成・抽出独立性・新OD作成、需要母集団への一般化。
- 長時間・大規模・メモリ負荷上限のストレス試験、量子実機。
- 実際の配送事業者に対する業務・計画時間の代表性。

これらにPASSを付与しない。S1〜S3の実測正式値はS1_S3_RESULTS.jsonにnullとして保存する。旧結果の時刻・D/Wを転記しない。
