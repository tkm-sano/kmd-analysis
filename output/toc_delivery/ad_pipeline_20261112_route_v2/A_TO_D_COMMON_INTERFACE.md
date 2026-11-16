# A〜D共通入出力：2026-11-12統合版の差分仕様

本書は今回の実行入口において、2026-11-11の `toc_delivery_common/COMMON_INTERFACE_SPEC.md` の「未実装」「未取得」「Aは外部参照のみ」という状態記述を更新する。旧文書・旧結果は履歴として保全する。運行条件の正本は引き続き `configs/toc_delivery/common_conditions_v1_1.json`。今回の接続/予算/seedは `configs/toc_delivery/ad_pipeline_v1.json` と実行前登録hashで識別する。

## 入力・識別

schema_version=1.0の `input.json` と `od/manifest.json`、float64距離[m]・時間[s]、bool到達性の3npyを使用する。保存形式・既存のS1〜S3厳密凍結検査を維持した。

`Experiment.kind` に **road_validation** を追加し、実道路かつROAD_ラベルの小規模/中間規模だけを表す。S1/S2/S3には使用できない。旧読み手はこの追加値を認識できないので、新しい `common.models` を使う。研究規模は従来どおり **frozen_research**、人工問題は **synthetic_validation**。小問題をS1と偽称したり、人工ODで実道路検証を通す入口を設けない。

全方法が `roads/inputs/<case>/` の同じディレクトリを読み、Problem hash・OD hash・凍結CSV/manifest hash・条件hashを照合する。車両IDの順序がready式のvを定める。共通Problemのmethod_settingsは空、方法固有設定はPlan側へ保存する。需要の配送先ID・原座標・需要単位・出典とsnapは別フィールド。

`Snap.reviewed=true` は保存した地図・道路属性・接続・距離の点検を意味する。今回、各建物の現地進入権や測量を完了したという意味ではない。`evidence=sha256:<SNAP_REVIEW.json>` に点検範囲を明記する。Depotは公式構内図とOSMの車両進入通路を照合した入口モデルであり、既存代理中心座標の無根拠な承認ではない。

## 道路ODの新しい生成口

旧 `generate_local_od` は変更せず、新しい `pipeline.roads` が分割・checkpoint・gzip原応答hash・再開を担当する。hintは生成時の**元照会座標**と組み合わせ、返却snapのずれは拒否する。snap座標への丸め直しでhintを無効化しない。道路graph・ID順・hint・block_sizeのcontext変更は通常の再開で拒否する。

地図点検後のhint変更は、初回ODを保全して明示的な移行記録を作り、変更点を含まないブロックだけ再利用した。Table負距離は同じhintのRoute再取得による距離/時間の対として訂正し、補正前・後を保全。値の切り上げや直線距離による修復ではない。

その後、正のTable距離にも連結Routeとの不一致を検出したため、上記Table生成物は採用保留とした。**最終採用版は `pipeline.route_pairs` の全ordered pair Route方式**。同じRoute objectの距離・時間・注釈node列を保存し、既存のTable距離は一切流用しない。S1からS2/S3へ引き継ぐのは検証済みRoute pairのみ。保存schemaは同じで、OD fingerprint・matrix_service・pipeline_v2設定と原応答で版を区別する。入力/出力の型や共通条件を変える修正ではない。

## 共通計画出力

Plan.method_idは **A/B/C/D**。A1/A2/A3はmethod_id=Aの規則ベース推計で、condition/offsetと佐川実績ではない旨をmethod_settingsに保持する。Dのexecution_kindはquantum_circuit_simulator、他はclassical。全手法が共通のTrip/Visitを返す。

各Tripは物理vehicle_id、連続trip_no=1/2、同じdepotのorigin/destination、順序付きVisit、ready_s、berth_id、loading start/end、departure/return、distance_m、waiting_sを持つ。Visitはstop_id、arrival/service_start/service_endの整数秒。T_programには共通入力の読込開始からこのPlanの共通独立検査完了までを含める。

実行器は `result.json` と `plan.json` を保存する。主要フィールドはstatus、D_km、W_min、T_program_s、elapsed_wall_s、timing_events、validation、second_validation、input_hash、OD_hash、method、primary、other_limit、max_rss_KiB、environment。旧共通run_measuredのT_sをT_program_sへ明示的に改名する。失敗時の正式D/W/Tはnull、経過時間と失敗理由は保持する。独立の事後監査時間とJSON保存時間は研究Tの終了後。

結果の一意キーは版/root・scenario・condition・source pathで管理する。Plan.plan_idだけを全ε条件や修正版に対するグローバル一意キーとして使わない。修正前結果と再試行は独立ディレクトリへ保存し、過去の計画を上書きしない。

方法固有段階は初期構築、Routing改善、日列変換、AOA提案、LP/IP、物理車両/バース完成をtiming_eventsとmethod_settingsへ記録する。Dには有限領域の全列参照とglobal gapの未知を区別した設定を保存する。計画中のreadyや時刻を評価器が修正することはない。

## 接続の確定状態

|方法|今回の実行入口|限定・帰属|
|---|---|---|
|A1〜A3|baseline_a.create_plan→共通Plan/検査|固定規則、FCFS。人手時間は別感度で実測ではない|
|B|directed_cw→complete_routes→共通Plan/検査|VeRyPy節約量利用の有向CW派生。上流の対称前提を黙って適用しない|
|C|directed_cw→OR-Tools route pool→同じcomplete_routes|Routing段階と勤務/バース完成段階を分ける|
|D|CW seed→既存日列/AOA→event master LP/IP→共通Plan/検査|マクロ/seed calendarの有限領域。古典補充と量子提案を区別|

評価は全て `D=sum(d_ij)/1000 km`、`W=sum(load_start-ready)/60 min`。共通v1.1のdeparture/service/ceil-each-arc規約で全時刻を検査する。プログラムTの同条件比較と、人手Tの未校正感度を別表にする。可行な参照A2から両方向εを固定済みで、根拠は今回outputのEPSILON_REFERENCES.json。S1の各方法の可行性は最終報告と対応CSVを正本とする。

Dの最終整数選択はD-lex-v1。B/Cと同じく主目的が同じなら他方を最小化し、各IPの主/副段階の合計予算30秒を維持する。修正前の任意同点選択はD_PRE_LEXICOGRAPHICへ保全し、D_LEX_POLICY_REVISION.jsonとEFFECTIVE_SETTINGS.jsonで初期設定からの差を追える。A・共通条件・OD・ε・seed・量子探索条件は変更しない。
