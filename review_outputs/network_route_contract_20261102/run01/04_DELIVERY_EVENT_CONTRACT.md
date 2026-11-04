# 配送イベント契約 SERVICE102_V1

判定：**モデル定義と算術境界PASS、native継続監視・地域実装への接続HOLD**。正式に定義するのは「モデル上の配達完了」であり、実際の荷物引渡しではない。既存の候補指標や過去83走行を本契約受入済みへ昇格しない。

## 記録する時刻

|イベント|定義・証拠|
|---|---|
|物理的到着|独立観測された配送地点への到着。未観測ならnull|
|native停車開始a|stop-output.started。task ID、actType、stop順、lane・positionに結び付ける|
|モデル作業開始s|A=max(a,ready)、B=a|
|モデル作業完了c|s+102秒。ただし当該場所でcまで連続したnative停車を検証した場合だけ確定|
|native停車終了|stop-output.ended。車両が走行を再開する時刻|
|最初の正速度標本|native終了後のFCD/状態記録。1秒観測の別時刻|
|デポ帰着|tripinfo.arrival>=0、期待最終edge/lane/position・route完了と対応|

公式 [StopOutput](https://sumo.dlr.de/docs/Simulation/Output/StopOutput.html) と [v1.24.0保存資料](https://raw.githubusercontent.com/eclipse-sumo/sumo/v1_24_0/docs/web/docs/Simulation/Output/StopOutput.md) に照合。stop行は停車が終了した時に出力される。startedは停車開始、endedは走行再開であり、配達作業の観測ではない。未出力行だけで未配達とは断定できない。取得ページ・URL・hashは `official_sources/`。

[車両・stopの公式定義](https://sumo.dlr.de/docs/Definition_of_Vehicles,_Vehicle_Types,_and_Routes.html) のdurationは最低停車時間、untilは最も早い再開時刻。早着時に「readyまで待機＋その後102秒」を自動で意味するとは限らない。既存Aのduration102・absolute untilを保持し、実際の保持がモデル完了に足りるか検査する。不足ならFAILとして残す。

## 場所と連続性

予定laneと観測laneが一致し、観測停車位置が宣言startPos…endPos内であること。SUMO1.24.0ソースの既定startPosはmax(0,endPos−0.2m)。厳密なendPos一点一致は要求せず、根拠のない許容距離は追加しない。位置・lane違いをclampやfriendlyPosで補正しない。

1秒stepごとにtask対応、stop状態・位置・中断・teleport・collisionを記録し、s…cの区間が連続していることを確認する。stop-outputだけで完了しない停車を観測するため、active-stop ledgerを必須とする。実装はまだ既存native runnerへ接続しておらず、G4全体はHOLD。

## ケース別判定

|条件|処理|
|---|---|
|予定時刻／遅着|aを確認しsを計算、102秒の成立を確認してc確定|
|早着|Aのreadyまで待機を別記し、sから102秒連続停車を確認|
|停車がc以降も続く|cとendedを別時刻に保存。endedまで作業時間を延長しない|
|endedがなく、active ledgerがcまで証明|モデル完了を確定、native再開はnull|
|102秒の途中で終了|評価horizon時点のIN_PROGRESS。Aの期限がhorizonより後なら定時性INDETERMINATE、期限を過ぎた完了不足はNOT_COMPLETED。最終配送完了と観測打切りを分ける|
|c前に走行再開|サービス中断FAIL、NOT_COMPLETED。都合よく102秒を補完しない|
|場所が違う／task対応不明|FAILまたはHOLD、完了時刻null、INDETERMINATE|
|stop行欠落・出力破損|連続監視がなければHOLD／INDETERMINATE|
|到達不能・未出発／未サービスを完全に確認|NOT_COMPLETED、理由と観測期間を保存|
|完了後に帰庫不能|各taskの完了は保持しreturnは別FAIL。低DCを効率改善にしない|
|異常終了|既に証明したtaskのみ保持、残りは証拠に応じ未完了／未知。runは受入不可|

安全異常や位置不適合のあるrunは主比較から成功扱いしない。ただし台帳から消さず、不適合とtask状態を併記する。

## Aの期限・固定分母

D03期限=d_i=元NPZのdue_start_i+service_i、service=102秒。根拠は保存 `causal_engineering_audit_20261027/run01/verify_a.py` のNPZ読取り／D03式、行別 `A_NATIVE_TASK_COMPLETION.csv`、D10/D11採用記録。元のdue_startも別列で保存。D10/D11の36条件・未取得14の古典切替を変更しない。

ON_TIME iff 証明済みc_i≤d_i（等号を含み時間許容なし）、LATE iff 証明済みc_i>d_i。NOT_COMPLETED、INDETERMINATEを別保存。

主指標 F_PE=Σ(q_i×I[ON_TIME])/Σq_i、副指標 F_count=ΣI[ON_TIME]/|D|。Dは各問題で固定された全配送需要。未取得・未配達・未知で分母を縮小しない。未知がある点率はnullとし、PE下限=定時PE/全PE、上限=(定時PE+未知PE)/全PE。件数版も同じ上下限原理を使う。依存した36政策や測定seedを物理独立標本と数えない。

## Bと受入出力

`UNIFIED_NO_CUSTOMER_WINDOWS_V1`を維持。ready／顧客deadlineをAから追加しない。モデル完了・未完了・未知の件数と固定PE、帰庫時刻、観測境界を報告し、根拠のない定時率は計算しない。

必須出力：完全入力・binary/library環境hash、effective route／vType／stop XML、stop-output、active-stop ledger、FCD速度・時刻・lane・position、tripinfo（unfinished/undeparted含む）、collision／warning／teleport、exit理由・horizon・資源。sourceの欠損状態をtask別に保存する。作業イベントはMODEL、native時刻はOBSERVED_SIMULATION、実荷物引渡しは未観測と列で区別する。

実装入口 `measurement_contract.py:measure_service`、テスト `validate_measurements.py`。今回35fixture中18サービス境界＋固定分母等を保存 (`MEASUREMENT_TEST_CASES.csv`)。過去26単体・7合成nativeのPASSを保持するが、今回の追加契約をnativeで検証したとは主張しない。G4をPASSへ進めるには極小網でactive ledgerとnative出力の対応を検証し、その後に受入済み地域網へ接続する。
