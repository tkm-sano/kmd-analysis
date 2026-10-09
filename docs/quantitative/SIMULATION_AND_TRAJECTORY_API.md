# Simulation / Trajectory API

## 1. 役割と現在の範囲

新しい入口は [trajectory_io.py](../../src/kmd_quantitative/simulation/trajectory_io.py)。保存CSV/CSV.gzをControlled-DCが受け取る時刻・速度配列へ読み込む。SUMO、routing、Battery、Energyの数理実装は追加していない。全量SUMO workerは原位置に保持し、起動しない。

## 2. Routingとの接続

routingは顧客の訪問順を決定する。SUMOの道路edge列とは別物。matched Classicalの `generate.py:prepare` は保存resultのcustomer_orderをroute_sequenceへ対応付け、端点ごとのtripを作成し、position-aware duarouter_loopの保存edge経路を用いる。共有 `generate_canonical_delivery_trajectories.py:build` が隣接legの重複境界edgeを連結し、stopのlane/endPos/duration/untilを設定する。

Quantumは最終取得経路のみを扱う。最終R0 commonは78件が同一経路で保存Classical軌跡へ結合、R1は同一59件・異経路5件という既存系譜を維持する。未取得経路を新規に補完しない。今回これらの生成・再結合は実行していない。

## 3. 道路・OD

道路networkは凍結GENERATION_PLAN.jsonのnetwork/sha256で指定。FROZEN_ENDPOINTS.parquetからnode_id/role別のedge/lane/positionをENDPOINT_READBACKへ写す。OD旅行時間はrouting目的、SUMO観測走行時間は別指標。道路グラフ読込みはnative router/SUMO側で、Pythonの汎用road APIを今回新設しない。

## 4. Simulation入力と実行

固定訪問順、端点、道路network、leg経路、車両type、service stop条件が必要。既存planはstep/FCD周期1秒、seed=20260930、独立単一車両・背景交通なし。matched生成は `canonical_sumo_fork.cpp` のnative time-zero forkを利用する。標準SUMOバイナリだけで同じ実行環境が成立すると仮定しない。

## 5. Trajectory出力

canonical CSVの保存列はroute_id、vehicle_id、timestamp_s、speed_m_s、x_m、y_m、lane_id、edge_id、position_m、angle_deg、slope_deg。matched版はphysical_instance_idとcanonical_trajectory_idも含む。x/y/positionはm、角度・勾配はdegree。position_mはlane上の位置で、累積走行距離ではない。

時刻はSUMO simulation時刻s、速度m/s。delta_time列・累積distance列・departure_time/arrival_time列はこのCSVにない。dtは隣接時刻差、出発/到着・native routeLengthはtripinfo/manifestの別記録。FCD観測はdeparture, arrival)で、DC評価は最初〜最後の観測点間だけ。最後の観測から到着eventまでを補間しない。

## 6. Controlled-DCへの受渡し

```python
from kmd_quantitative.simulation.trajectory_io import read_dc_input
# repo rootからPYTHONPATH=src、またはsrcをsys.pathへ追加
# manifest_rowとhashは正式manifestから別途取得する。
t, speed = read_dc_input(path, expected_sha256=hash_value, metadata=manifest_row)
# 既存run_full_controlled_dc.pyのevaluateへ、この2配列をそのまま渡す。
```

読込みは既存 `apply_r0_method_battery.py` のdf/t/speed代入3文をSHA256確認後にASTで実行する。このR0 sourceは最終R1/R0 commonの現役依存でもある。トップレベルの監査・出力・計算loopは実行しない。エネルギー式をadapterへ移さない。

新APIの入力guardは長さ2以上の同長1次元・有限数値・非負速度・厳密1秒刻みを要求する。不正入力はValueError等で拒否し、並べ替え・補間・欠損補充しない。有効配列の数値・dtype・行順は元pandas読込みと一致。optional hashは圧縮file bytes、optional metadataはsample_count/integration_interval_count/first_sample_s/last_sample_sを確認する。これらのguardはAPI境界の検査であり、配送制約判定の変更ではない。

Controlled-DCは右端速度×dtで区間距離を扱い、Whを返す。CSVのposition差やOD距離へ置換しない。元DCの非1秒刻みassertと、新APIの早期ValueErrorは例外型が異なる。全フィールド・SUMO完了・時間窓をこの2列loaderだけで検証したとは扱わない。

## 7. 正式な実装場所

[処理一覧（Hayate保存参照: `docs/audits/quantitative_repository_structural_migration_20261009/25_SIMULATION_PROCESS_INVENTORY.csv`、公開ツリー非同梱）にA〜Kのsource・関数・入出力・副作用・依存を記録。保存軌跡読込み以外は既存位置を維持する。Native FCD canonicalizeは出力書込みを伴い、APIから実行しない。

## 8. 凍結codeとの関係

source freeze、最終freeze、旧R0 Battery、routing/Quantum APIを変更しない。新srcファイルは薄いadapterで、原sourceを物理移動したものではない。hash固定の原sourceが配布集合に必要。旧4互換symlinkは読込みAPIに不要。

## 9. 小規模実行

既存notebooks/requirements.txt環境を用い、repo rootで `python -B tests/test_simulation_api.py`、`python -B notebooks/test_notebooks.py`。Notebook03はspeed.jsonと同値の人工speed.csvを使用し、SUMO実測結果とは表示しない。6人工ケース（3Battery×2圧力）の旧入力・新入力でDC record/配列が完全一致。別途、実際の保存COMPLETE軌跡1件の読込みも確認したが、配布fixtureには複製していない。

## 10. 外部依存・限界

読込みとNotebookにはSUMO本体・道路データ不要。Python/numpy/pandasと凍結sourceが必要。全量生成にはnative SUMO1.24、専用duarouter_loop、canonical_sumo_fork、道路network、endpoint、固定assignment/result、出力領域等が必要。Hayate絶対パスとLinux fork依存は元workerに残る。実行APIの移植は今回対象外・未検証。

静的時間窓可行性、SUMO stop開始時刻診断、実業務配送充足は区別する。audit.pyのnative_start_after_dueは診断であり全時間窓再検証ではない。保存観測区間DC Whは総旅行・物流システム全体のエネルギーではない。公開権利は未確定。詳細：第4段階回帰（Hayate保存参照: `docs/audits/quantitative_repository_structural_migration_20261009/28_PHASE4_REGRESSION_TEST_RESULTS.md`、公開ツリー非同梱）。
