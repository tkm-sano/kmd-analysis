# 検証記録

検証はcontract_checkであり、正式統計実験の反復ではない。初期予定はVALIDATION_MANIFEST.json、420秒への別登録はVALIDATION_AMENDMENT_R2.json、試験fixtureの10秒枠はTIMEOUT_FIXTURE_AMENDMENT.json、実Routeガード確認はROUTE_GUARD_REGISTRATION.jsonに、各実行前に保存した。初期失敗・未実行・修正履歴を削除していない。

## テストログと修正履歴

|ログ|実行結果|扱い|
|---|---|---|
|TEST_DEVELOPMENT_01|collection error 1|新テストのkeyword構文誤り。修正してログ保全|
|TEST_DEVELOPMENT_02|34 passed / 1 failed|Plan metadataのtupleとJSON listの表現差をテストが同一視できなかった。raw bytes一致とcanonical全Plan一致へ修正|
|TEST_DEVELOPMENT_03|35 passed|初期参照/集計/プロセス試験|
|TEST_DEVELOPMENT_04|40 passed|親の実検証と実timeout状態を追加|
|TEST_REGRESSION_01|239 passed / 2 skipped|旧A/BCD+当時の新規40件。skipは任意Qulacs未導入|
|TEST_FROZEN_CODE_01|40 passed|schema等の反映後|
|TEST_FROZEN_CODE_02/03|各41 passed|入力段階timeoutの分母、実行前検証、PID/途中資源を追加|
|TEST_REGRESSION_02|237 passed / 3 failed / 2 skipped|親fixture2件で1.5秒以内に候補が到着せず正常timeout。旧C3秒試験もRouting前に予算停止。失敗を保全|
|TEST_REGRESSION_03|240 passed / 2 skipped|親fixtureだけ10秒へ分離後の全回帰。旧C試験も通過、旧ソースは不変|
|TEST_ROUTE_GUARD_FINAL|42 passed|実道路全ケースの旧Table拒否を登録へ追加後の新規全件|

同じ試験の再実行を足して新しい検証件数にしない。最終の既存を含む全回帰は240通過/2skip、最後の登録ガード追加後は新規42通過である。旧A/B/C/Dソース・既存テストを修正して成績を合わせたものではない。

旧C3秒試験の保存worker_resultでは、input_load_end=1.139270秒、directed_CW_end=1.257145秒、INSUFFICIENT_ROUTING_BUDGETで協調停止し、検証済みincumbentを1.486485秒で返していた。既存の「VALIDATEDならRoutingに到達」というテスト前提が、NFS入力/検証の遅延で成立しなかった。LEGACY_C_SHORT_BUDGET_DIAGNOSTIC.jsonに原因と実ログを保存した。後の通過でこの環境敏感性を消したことにはしない。新主比較のCでは実際に4つのOR_Routing呼出を確認した。

## 必須ケースとの対応

|要求|検証内容|結果|
|---|---|---|
|全成功/片側/双方失敗/A失敗でもCD成功|fixtureのpaired全分類、JなしのCD生値保持|通過|
|A参照未指定/未完了/失敗/Plan不一致|事前run_ids集合全件を必要とし成功分へ縮小しない|通過|
|中央値と個々AのJ|4/8秒の人工Aから中央値6秒、個々のAは1へ固定しない|通過（研究参照値ではない）|
|W_A=0/非有限/0分母|J=nullと個別理由、epsilonなし|通過|
|時間/資源/input/旧A/旧契約/旧Tref混入|identityとschema照合、方法別共通上書き禁止|通過|
|旧Table混入|全実道路caseのRoute pair metadata必須、syntheticは明示例外|通過。実S1〜S3もガードで受入/全pin一致|
|MOVE_LIMIT有効計画|A実S1〜S3/小規模とunit。limit_stop_countへ加算しない|通過|
|期限前に親検証済み計画あり/なし|実子processを止め、前者は採用チェックポイント保持、後者null|通過|
|入力読込中のtimeout|登録済み物理有効入力を有効入力実行分母に保持|通過|
|不正計画/入力不正/子エラー|負待機plan、hash改変、実子RuntimeError|通過、修復や0補正なし|
|未実行/リトライ|予定起点でnull行、retry_ofは元試行を置換せず表に残す|通過。small02の実未実行4件も集計|
|実タイムアウト/孫process回収|direct watchdog1.5秒で実子・孫を作り、PGID限定TERM/KILLとsubreaper回収|通過。300秒/メモリ負荷試験ではない|
|原bytesと意味/全時刻|Plan roundtrip、A実6接続+新単独S2|通過。D/Wだけを同一性根拠にしない|
|初便FCFS検算|旧A_rule_v1テストで360/720/1440分を再確認|通過。BCDへ固定値として課さない|

## 実経路と計画同一性

`A_checks01` と `A_checks02` は各S1/S2/S3を1回ずつ、新規比較入口で実行した。全て共通物理・独立Decimal・A固有規則を通過し、原単独出力とbytes、全Plan、D/W/W内訳、input hashが一致。原CLIの新規単独S2は1回実行し、原S2 hashと一致した。Tの値は一致を要求せず、旧nativeと新親wallを分けた。A_IDENTITY_VALIDATION.jsonを参照。

初回small01は90秒上限、A成功/BCD3件が依存初期化中にtimeout。3件のD/W/T_programはnullでT_attemptとcleanupを保存し、全て成功率の分母へ含めた。方式入口に達しなかったため、これをBCD実経路確認PASSとはしなかった。

small02は420秒/内部90秒で登録したが、実行前のPID/部分資源記録の補強により未実行のまま保全した。後のsmall03は同じ12地点/4台/1バース、同じBCD設定、同じ420秒/内部90秒で実行し、A/B/C/D全4件がVALIDATEDとなった。Aは完成器0呼出、BはCW4/CP4、CはCW4/OR4/CP4、DはCW4/hybrid4/CP8/AOA8を観測した。DはQiskit2.1.1、完了量子呼出8件を未選択枝込みで記録した。BCDは4PID/4異なる1コアであり、供給便の内部順序保持も実出力で照合した。

登録別の全試行/対応表/参照は各tables directory。まとめのALL_EXECUTION_HISTORY.jsonは比較予定18/実行14/未実行4、新単独S2を別に1件とし、技術的再実行を独立標本へ加算しない。small03の参照は事前指定のA1件によるcontract_check用で、正式T_A_refではない。

事後監査130項目は、各版source snapshot pin、全出力hash、逐次実行、deadline、子回収、A bytes/Plan/指標、実関数経路、BCD branch/core、D実backend、pool内部順序、参照中央値/J、旧失敗分母、未実行、既存328file保全を検査して全通過した。後から追加した登録ガードは実Route入力3件と新規42テストで確認し、旧A計画を再生成・置換していない。

## 未実行

正式統計実験、需要標本/反復/精度/検出力の設計、正式参照数値、BCDのS1〜S3全面実験、共通FCFS診断、量子効果分離対照、対象実績照合、実機/有料計算、300秒やメモリ枯渇負荷、他OSは未実行。任意Qulacsの2skipをPASSとは記さない。NFS初期化/短時間試験の揺らぎは将来の環境・cache契約で管理すべき制約として残す。
