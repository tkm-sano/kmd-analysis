# 監査の再現手順

本ディレクトリが最終有効成果物である。兄弟の最初の試行は列名衝突で停止し、ATTEMPT_STATUS.jsonにFAILEDとして保存されている。元データは両試行とも変更していない。

## 実行環境と元入力

リポジトリルートは `/home/takuma/kmd-analysis` である。`ENVIRONMENT.json` にPython、地理ライブラリ、PROJ、sumolibの所在を記録した。元入力の所在とhashは `INPUT_MANIFEST.json`、追加のOD参照は `OD_SCOPE_AUDIT.json` にある。保全領域は別ディレクトリであり、公開cloneだけでは揃わない。

外部入力を代替・更新してから同じ結果と称してはならない。対応する入力が存在しない場合は監査不能として停止する。依存関係の追加・更新は今回実施していない。

## 主監査の再実行

同じ環境から、未存在の出力先を指定する。既存結果へ上書きしない。

```text
python -B <this_directory>/prepare_run.py --output <new_directory_under_the_same_audit_parent>
python -B <new_directory>/audit_stops.py --output <new_directory>
python -B <new_directory>/validate_audit.py
```

prepare_run.pyは追跡ファイルhashとgit statusを保存する。audit_stops.pyは各成果物を排他的に作成し、全件CSVの読戻し集計と元入力の事後hash照合を行う。validate_audit.pyは標準CSV読取器で行数、ID、判定、理由、地域集計、配分、入力不変を再検証する。これは研究の既存テストやシミュレーションを実行する手順ではない。

## 追加診断と報告に用いた処理

追加ファイルは以下の決定的な読取処理で作成した。新規ディレクトリで同じファイル名を排他的に新規作成する。

1. `BOUNDARY_DISAGREEMENTS.csv`：主CSV全件のWKTをEPSG:4326から6677へ変換し、N03全域を同じCRSへ変換する。N03_007=13111の和集合でcovered_byが偽の行を抽出する。区境界までの距離と、元N03全域にintersectsで対応する区名・コードを保存する。これは新需要の抽出ではなく不一致行の監査一覧である。
2. `CRS_TRANSFORMS.json`：pyproj.Transformer.from_crs(source,6677,always_xy=True)をsource=4326,6668,4612について作り、139.7,35.58を変換してからdescription、accuracy、definitionを記録する。入力座標の補正は行わない。
3. `OD_SCOPE_AUDIT.json`：保全領域のbaseline_capacity_fleet_assignment_20260930/OD_DOMAIN_METADATA.json、sumo_od_final_validation_20261005/PARTITION_MANIFEST.csv、classical_vrptw_baseline_20261005/prepare.pyを読む。前者の全項目、CSVの全行数・列・先頭行、prepare.pyのvehicle/C_C関連入力結合行を記録し、各入力のサイズ・hashを保存する。OD本体全行の新規検証・生成は行わない。
4. `SUPPLEMENTARY_SUMMARY.json`：ALL_STOPS_AUDIT.csvから、道路品質フラグを行内重複なしで数える。投影距離をpandas.describe(percentiles=[.5,.95,.99])で集計し、座標誤差最大、原建物距離最大、候補・原本一致数分布、往復到達真偽、PASS/CONDITIONAL/HOLD/FAILを0件も含めて記録する。既存500mメッシュparquetのmetadata.num_rowsと元ファイルhashを付記する。新メッシュ需要は生成しない。

追加診断は行判定を変更しない。主監査の再現・検証には追加診断は不要である。日本語報告書まで再現する場合は、上記ファイルを揃えた後に以下を実行する。

```text
python -B <new_directory>/build_report.py
python -B <new_directory>/finalize_delivery.py
```

build_report.pyの固定説明には今回の観測件数が含まれるため、入力hashが変わる再監査へ無検討に転用してはならない。今回の入力では機械集計と説明文の一致を確認した。FAIL88は採択したN03境界条件での判定であり、住所誤りの断定ではない。

## 実施していない処理

元データ修正、座標・形状の修復、道路スナップの新規生成、全地点間OD生成、配送需要集合の生成、経路最適化、SUMO/duarouter、VRP/量子本実験、commit/pushは実施していない。

## 判定と保全

判定規則はAUDIT_PROTOCOL.json、入力hashはINPUT_MANIFEST.json、全件結果はALL_STOPS_AUDIT.csv、独立検証はINDEPENDENT_AUDIT_VALIDATION.json、事前事後の不変確認はPROTECTION_CHECK.jsonとDELIVERY_VERIFICATION.jsonである。OUTPUT_HASHES.jsonは自身以外の成果物をhashする。
