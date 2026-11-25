> 2026-11-20の現行案内：研究仕様の唯一の正本は[研究仕様1〜7・凍結v1](../../frozen/配送計画最適化_評価指標と実験条件_1-7.md)、積込規則は[FCFS_v1](../FCFS_OPERATING_POLICY_V1.md)です。以下は固定JSON・schema v1.1の実装記録として保全し、研究仕様正本と区別します。現行の計画比較はB/C/Q（内部D）で、Aは外部参照です。1地点1単位の現行モデルでは1便当たり最大60配送先。数値表やschemaを今回変更しません。[現行実装対応](../TOC_DELIVERY_SPEC.md)を参照してください。

---

# A〜D共通入出力仕様（schema v1.0・条件 v1.1）

採用日2026-11-11。実装は`src/kmd_toc/common/`。条件の正本はCOMMON_CONDITIONS_V1.mdが参照するJSONである。solverを選ぶ設定と共通の問題データを分離する。旧`study.json`/`contracts.py`は凍結履歴として維持し、新入口から読まない。

v1.1ではA〜D共通に帰着後準備を0秒とする。積込1800秒と作業120秒は研究上の固定仮定として維持する。顧客作業は訪問時刻の伝播を通じた帰着・次便ready・勤務期限の計算に使用し、変動モデルは持たない。旧v1.0設定・既存結果を保持し、旧条件hashの入力を現行条件として読込むことは拒否する。

## 共通入力の保存構成

```text
instance/
  input.json                  # schema_version, Problem全フィールド, problem_hash, od_hash
  od/manifest.json            # ID順序、道路来歴、OD全内容hash、各配列ファイルhash
  od/distance_m.npy           # float64 [n,n], m
  od/duration_s.npy           # float64 [n,n], 生の移動秒
  od/reachable.npy            # bool [n,n]
```

`save_problem`は既存ディレクトリを上書きしない。`load_problem`は配列hash、OD内容hash、input内容hash、条件pin、入力制約を検査する。ODはread-only mmapで読み、hash・監査は逐次走査する。A〜Dで別の行列を再生成せず、同じinstanceとod_hashを指定する。配列のID順序は`depot, stops...`で厳密一致を要求する。入出力JSONの重複キーとNaN/Infinityを拒否する。

|レコード/フィールド|型|単位・意味|
|---|---|---|
|Stop.stop_id|非空str|固定配送先ID。一意|
|Stop.longitude / latitude|finite float|EPSG:4326、度。原CSV座標をfloatへ読込。原トークンは凍結CSVとそのhashに残る|
|Stop.demand|int（bool不可）|delivery_unit、採択値1|
|Stop.snap|Snap|別表の道路対応。原需要を変更しない|
|Stop.source|object|kind/source/generation/sha256。実測・文献・合成・仮定の種別を保持|
|Snap.longitude / latitude|finite float|OSRM nearestで得た道路上の位置、度|
|Snap.distance_m|finite float|原座標からのsnap距離[m]。OD費用へ加算しない|
|Snap.hint / node_ids|str / int[]|同じOSRM graphでの対応位置・候補端点。nodeだけへ勝手に丸めない|
|Snap.graph_id|str|使用graphの版識別子|
|Snap.reviewed / evidence|bool / str|手動アクセス確認の有無・証拠識別。実道路はsha256:64桁hash|
|Vehicle.vehicle_id|非空str|物理車両の一意ID|
|Vehicle.capacity / max_trips|int|60配送単位/便、最大2便|
|Vehicle.first_ready_s|int|配列内の車両順vから均等式で検査|
|Vehicle.return_deadline_s|int|JST午前0時からの秒、72000|
|Depot.depot_id|非空str|単一拠点ID、stop_idと非重複|
|Depot.longitude / latitude / snap|float / float / Snap|拠点の採択車両出入口と道路位置|
|Depot.entrance_verified / entrance_evidence|bool / str|実車両出入口の確認と証拠。代理座標だけではtrueにしない|
|Berth.berth_id / depot_id|str / str|一意バースID・所属拠点|
|Berth.opening_s / closing_s|int / int|28800 / 72000秒|
|Berth.loading_s / preparation_s|int / int|1800 / 0秒|
|Experiment.scenario_id|str|S1/S2/S3、検証はTEST_N4等の明示ラベル|
|Experiment.conditions_version / conditions_sha256|str / str|採択版・設定ファイルhash|
|Experiment.random_seed|intまたはnull|方法のseed。固定需要はseedで再生成しない|
|Experiment.data_hashes|object|od、実研究ではdemand_manifest/demand_csv必須|
|Experiment.environment|object|計算環境。実行環境はrun_resultにも別記録|
|Experiment.method_settings|object|共通instanceでは空。実行別設定はPlan側へ記録|
|Experiment.kind|enum|frozen_research / synthetic_validation|

実研究入力は既存`load_frozen_demand`で8ファイル全体をpin検査し、S1〜S3の件数・車両・バース・全属性を照合する。synthetic_validationをS1等の名前で保存すること、実研究で人工ODを使うことを拒否する。`from_frozen`は道路snap・確認済みDepot・ODが揃った場合だけProblemを組み立てる。道路不足を0や直線距離で埋める機能はない。

## ODと生成契約

論理的な1レコードは`(origin_id,destination_id,distance_m,duration_s,reachable,road_version)`である。IDはmanifestの順序から対応付ける。到達不能は両数値NaN（OSRM応答ではnull）とreachable=false。未計算はINCOMPLETE manifestに保持し、COMPLETEとして読めない。reachable=trueのNaN・負値・非有限値、片側だけnull、誤った対角、shape不一致を拒否する。実研究実行には全必要ペアのreachable=trueを要求する。非対称を検査し保存するが、全ての実データが非対称になることを強制はしない。

metadataはkind/units/road_version/graph_id、source_url/acquired_at/osm_timestamp、raw_sha256、osrm_version/profile/profile_sha256、graph_artifacts（各生成物hash）、build_commands/generated_at、directed=true/route_policy=fastest_same_route/fallback_speed_allowed=falseを持つ。日付・版が不明なら未確認とし、実研究完成manifestを作らない。

`LocalOSRM`は数値loopback HTTPのみ許し、公開ホスト・localhost名・リダイレクトを拒否する。nearestは複数候補を返すだけで自動承認しない。snap距離100m超をHOLDとし、100m以下でもreviewedと証拠が必須。原座標とsnapの測地距離と申告値の差3m超を拒否する。この測地距離は品質検査専用であり、配送距離・ODには使用しない。高速道路、反対車線、私道、建物からの接続、拠点出入口は人による根拠確認を要する。証拠hashの形式・reviewedフラグは現地アクセスの自動実証ではない。

`generate_local_od(ids,snaps,metadata,new_directory)`は最大100×100のブロックを逐次書込みし、同一要求でdistance,durationを受け取る。hint・snap座標を固定し、戻りのsnap座標やdata_versionの変化を拒否する。生応答をresponses/*.json.gzへ残す。失敗は途中ファイルとINCOMPLETE manifestを残し、再試行は新ディレクトリへ行う。自動修復・推定・自動再開はない。OSRM実サーバとの接続試験は未実施で、stub試験の成功と区別する。

## 共通出力

`Plan`は`schema_version,plan_id,method_id,problem_hash,od_hash,trips,method_settings,execution_kind`を持つ。B/C/Dは同一Planを独立検査する。Aは出典付き参照水準なので運行Planが取得できない場合に架空のルートを作らない。

|レコード/フィールド|型|単位・意味|
|---|---|---|
|Plan.method_id|enum B/C/D|方法識別。人工検証にはmethod_settings.validation_onlyを明示|
|Plan.execution_kind|enum|classical / quantum_circuit_simulator。Dの実機時間と混同しない|
|Trip.vehicle_id / trip_no|str / int|物理車両、連続便番号1/2。0便はレコードなし|
|Trip.origin_id / destination_id|str / str|共通Depotと一致する必要がある|
|Trip.visits|Visit[]|訪問先の順序。使用便は非空|
|Visit.stop_id|str|原配送先ID|
|Visit.arrival_s / service_start_s / service_end_s|int|到着・作業開始・終了、JST秒|
|Trip.ready_s|int|積込準備完了。第2便は第1便再計算帰着と同時（+0秒）|
|Trip.berth_id|str|明示バース割当|
|Trip.load_start_s / load_end_s|int|連続1800秒の積込占有|
|Trip.departure_s / return_s|int|拠点発着、JST秒|
|Trip.distance_m|finite float|共通有向ODからの全arc合計と絶対誤差1e-6m以内で一致|
|Trip.waiting_s|int|load_start−ready。積込作業を含めない|

`save_plan`は既存ファイルへの上書きを拒否する。`Validation`はfeasible、violations[{code,context,detail}]、D_km/W_min/W1_min/W2_min/ready_to_loading_end_min、独立再計算したtrip_metricsを返す。1件でも違反があれば正式なD/Wはnullである。再計算診断は残るが採用結果にしない。入力とPlanは補正しない。将来補正する場合は別plan_idで両方保存・検証する。

## Tの実行契約

```python
from kmd_toc.common import load_problem, run_measured
result = run_measured(
    lambda: load_problem("instance"),
    lambda problem, mark: method_all_processing(problem, mark),
)
```

T開始前にProblemやODを読込して渡さない。create_planの範囲へ初期解・変換・調整・探索・サンプリング・復号・整数化・後処理を入れる。最後に共通検査器が実行され、その完了イベントまでをT_sとする。計画未取得、入力不足、違反計画はstatus=INPUT_HOLD/ERROR/INFEASIBLE_PLAN、D/W/T=nullとし、elapsed_wall_sと例外・違反を保持する。FEASIBLEでも最適性証明を意味しない。道路取得/OD生成は前処理秒として別保存する。

結果はrun_result.jsonにPlan、Validation、D_km/W_min/T_s、elapsed_wall_s、timing_events、environment、errorを保持する。偽時計テストで全段階包含を、実時計テストで読込前/検証後の境界と秒単位を検証する。任意callbackの内部で作業を隠していないことまでは自動検証できないため、各solverの統合レビューも必要である。

## A〜Dとの接続・版管理

|方法|接続口|残る作業|
|---|---|---|
|A|出典付きD/W/Tの外部参照台帳|同条件か、異条件参考かの区別。数値未取得はnull|
|B|indexed_solver_input→VeRyPy→Plan→validate_plan|CW経路を物理車両2便・バースへ結合するwrapperが未実装|
|C|indexed_solver_input→OR-Tools→Plan→validate_plan|物理車両/2便/ready/バース/εの一体化が未実装|
|D|to_vehicle_day / from_vehicle_day→Plan→validate_plan|入力m→既存Dのkm、各arc秒切上げ。出力は時間・距離を保全し明示バースを要求。大規模価格付け・疎主問題・秒精度検証は未完|

D出力に元々存在しない各訪問時刻は、保存された出発と順序から共通ODで展開する。保存されたready/積込/出発/帰着/距離は書き換えず、不一致を共通検査器へ渡して拒否する。D adapterを作ったことと、DのS1求解可能性は別である。

schema_version、conditions_version、設定pin、凍結需要pin、OD/Problem hashを併用する。条件変更は新しい版へ分岐し、文書生成表・テスト・参照計画を更新する。現在はε、資源予算・探索seed・A参照の採用が未完で、本比較実行を許可するスクリプトは追加していない。
