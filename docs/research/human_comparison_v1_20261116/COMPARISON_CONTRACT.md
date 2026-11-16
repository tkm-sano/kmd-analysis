# A〜D共通比較・計時契約

契約ID：human-inclusive-AD-v1-20261116。主指標：D km、W 分、T_total 秒。[採択RQ](RQ_ADOPTED_V1.md)に従う。主比較は、人間・候補生成・積込決定・採用までを含む配送計画生成方式全体の比較である。量子処理だけの因果効果を推定する契約ではない。

## 入力と物理条件

|項目|固定した扱い|
|---|---|
|S1/S2/S3|1000/2000/4000地点、10/20/40台、2/4/8バース|
|需要|1地点1配送単位、全地点ちょうど1回、時間窓なし|
|容量・便|60配送単位／便、最大2便。利用可能台数であり全台稼働義務なし|
|空車両・空便|空便を作らず、積込・運行・待機を発生させない|
|作業|積込1800秒／非空便、配達120秒／地点、帰着後追加準備0秒|
|勤務|08:00〜20:00。最終帰着が終了以内|
|初便ready|車両index v、台数Vについて28800+(3600*(2*v+1))//(2*V)|
|再積込ready|第1便の帰着+追加準備0秒|
|OD|同一Routeの有向距離m・静的時間秒。各arcごとに移動秒を切上げ|

これらは研究上の共通設定であり実車両の積載能力や対象事業者の実測値とはしない。既存S1〜S3のhashを固定する。追加需要は別の生成manifest、seed、候補母集団hash、同じ拠点・物理条件・Route ODを登録する。既存ODの再生成は行わない。ケースの5入力ファイルhashはA〜D共通であり、方式別上書き・同じ入力の別名登録を拒否する。不達、非有限OD、hash不一致、入力不正は実行失敗から区別する。

## 意思決定

Aは人間の車両割当と全訪問順をそのまま保持し、容量分割とFCFSだけを機械処理する。人間の修正は許すが記録する。B/C/Dは既存の4枝候補生成と最適化完成器を用いる。Aを完成器へ通さず、全方式FCFSへの変更もしない。各方式の積込決定の違いを方式差に含める。

Dは全非空便の拠点出発・地点間・拠点帰着距離の合計／1000である。Wは各便の積込開始−readyの合計／60である。readyは作業開始可能時刻であって希望時刻ではない。負待機を0へ修正しない。積込時間やsolver penaltyをD/Wへ加えない。W_first、W_reload、車両別拘束時間、最終帰着、超過、便イベント、バース利用はPlanとvalidation.jsonに保存する。

## 共通計時

開始は対象需要の読込・hash確認の前、終了は最終の共通物理検証・独立指標再計算・採用判定を完了した時点である。start以前の登録・環境準備では入力の内容を読まない。実験者は事前に対象配置を見ず、方式固有チューニングもしないことを確認する。

T_totalには全修正、棄却試行、入力操作、確認、休止、待機、プロセス起動・初期化・IPC・必要なシリアライズと最終採用を含める。最終報告・事後集計・保管用tarは計画作成に不要であり除外する。セッション中の証拠保存は計時に含まれるため、この実装での計測には記録処理の負荷がある。旧native T_programは別値として保存する。

同一boot・hostのCLOCK_MONOTONICナノ秒を用いる。HUMANは担当者または登録観察者の開始・終了マーカーで指定された作業区間、MACHINEはCLI受理後の整合確認、子プロセス実行と後始末、OTHERはそのどちらでもない休止・待機・操作間隔である。並行する手作業は許さず、機械処理の完了後に再度作業マーカーを開始する。この排他的な時間割当の場合だけ `T_total=T_human+T_machine+T_other` が成立する。人手区間をマーカーし忘れた時間を推定補完しない。pauseはOTHERであり総時間から控除しない。人手マーカーの精度は申告・観察の精度に依存する。

T_computeはB/C/Dの各枝でmethods.generate（完成器を含む）が開始してから終了するまでの実測区間の和集合である。全枝の観測が完了した場合だけ値を出す。枝時間を足してwallにしない。入力・共通検証・IPCを含むT_machineとは異なる。人間が順序を決定するAのT_computeはnullである。Dのパラメータ最適化区間は目的関数中のシミュレーションを含む。回路生成・状態ベクトル・サンプリング・復号・最終処理のnative時間と、古典LP/IP/CP/OR区間を保存するが、重複を含むので合計をT_computeやT_totalにしない。実機を使用しない。

## 資源と停止

4物理コアの利用枠を共通化し、Aは1プロセスnative1thread、B/C/Dは4枝各1コアnative1threadとする。異なる方式を計時中に同時実行しない。内部枝は試行数に加算しない。CPU affinity、CPU時間、RSS、環境・ライブラリ、seed、未選択枝の結果も保存する。OS page cacheと共有ホストの他負荷は制御しておらず、完全cold startとは呼ばない。

ケースにtotal_limit_s、machine_limit_s、native_limit_sを必須登録し、native≤machine≤totalとする。外側上限は最終検証・採用までである。機械処理は子プロセス群を停止・回収する。メモリは登録したプロセス木RSS和の上限（共有ページを重複計上し得る）を監視し、Aには追加でaddress space4096MiBを適用する。小規模確認はメモリ負荷限界の検証ではない。

人間が休止中の期限は次の操作時に検出する。期限後の候補を成功に遡及しない。最終採用前に可行候補があった場合もcandidate_feasibilityと採用feasibilityを分ける。nativeの時間上限で後から得た計画は診断として保全し、正式成功へ昇格させない。ヒューリスティックの未発見は問題自体の実行不能の証明ではない。

## 状態・null・証拠

statusはsuccess、TOTAL_TIMEOUT、MACHINE_OR_NATIVE_TIMEOUT、MEMORY_LIMIT、INPUT_INVALID、INVALID_MANUAL_PLAN、INVALID_PLAN、NO_VERIFIED_PLAN、PROCESS_ERROR_OR_NO_VERIFIED_PLAN、abnormal_interruption等を区別する。入力状態、終了理由、各attemptの検証結果、candidate_feasibility、採用feasibilityは別に保存する。未開始・未完了は登録試行との差分として表示する。

正式採用計画がない場合のD/W/T_totalと各採用内訳はnullで、T_attemptと棄却値を診断に残す。contract_checkの人工結果はobserved=falseで、正式時間は全てnull、測ったテスト経過はdiagnostic_elapsedに隔離する。人工計画のD/Wはfixture診断であり実需要結果ではない。再起動時はrecoverで異常終了とし、boot間の経過時間を作らない。再試行は別run_id、analysis_role=retry、retry_ofで元試行を残す。

スキーマはconfigs/toc_delivery/human_comparison_v1_result_schema.json、証拠検査はanalysis.verify_sessionである。旧契約、旧A、旧Tref、source/input/physical/registration hash差、重複登録、単調時計・イベント鎖・計画hash不整合を拒否する。元データや人間の行為を暗号署名で実証するものではないため、記録の監督と保管も実測手順の一部である。
