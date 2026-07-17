# 国土数値情報N03行政区域データ2026年東京都版：取得・検証記録

## 記録状態

- 記録日：2026-07-17
- 実施者：研究環境管理者（Codex支援）
- 状態：`raw_acquired`（原本検証済み・境界抽出前）
- 出典台帳ID：`mlit_n03_2026_tokyo`
- 関連する実装計画：`05_src/traffic_simulation/implementation_plan.md`

## 配布元と利用条件

- 配布者：国土交通省
- データセット：国土数値情報N03行政区域データ、2026年（令和8年）東京都版
- データ基準日：2026年1月1日
- 配布ページ：<https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N03-2026.html>
- 実ダウンロードURL：<https://nlftp.mlit.go.jp/ksj/gml/data/N03/N03-2026/N03-20260101_13_GML.zip>
- ライセンス・利用規約：CC BY 4.0。配布ページに掲載された国土数値情報の利用条件に従う。
- アクセス要件：認証不要。取得前に公式配布ページの利用条件を確認する。
- 再配布上の注意：公式ページには、二次利用時に国土地理院への申請等が必要になる場合がある旨の注意がある。再配布前に用途ごとに要否を確認する。

パスワード、トークン、APIキー、Cookie、その他の秘密値は使用していない。

## 選択条件

- 取得日時：2026-07-17 21:04:16 JST
- データ基準日：2026-01-01
- 地理的範囲：東京都
- 配布ファイル：東京都版 `N03-20260101_13_GML.zip`
- 大田区選択条件：`N03_007="13111"`、`N03_001="東京都"`、`N03_004="大田区"`
- 選択理由：大田区行政界を東京交通シミュレーションの最小検証地域の正本にするため。
- 全国版を使用しない理由：研究対象が東京都内であり、東京都版だけで必要な属性と地物を取得できるため。保存容量と処理量を不必要に増やさない。

このデータは2026年1月1日時点の行政区域であり、現在時点の道路、建物、物流活動、交通量を表すものではない。一部地域には原典に由来する暫定境界があり得るため、配布ページの注意事項も確認する。

## 保存先と命名

- 配布時のファイル名：`N03-20260101_13_GML.zip`
- 不変の生データ保存先：`03_data/raw/traffic_simulation/boundaries/N03-20260101_13_GML.zip`
- ファイルサイズ：13,153,227バイト
- SHA-256：`94f10b26256566db970dd74b09d614f059c1e8a432f9244ac9c4add76c32ff16`
- 出典台帳：`03_data/metadata/traffic_simulation_sources.csv`
- 予定する加工スクリプト：`05_src/traffic_simulation/network/prepare_study_area.py`
- 予定する地域設定：`reproducibility/config/traffic_simulation/study_areas.yml`
- 予定する加工後出力：`03_data/processed/traffic_simulation/road_network/boundaries/ota_ward_n03_2026.parquet`
- 予定する品質サマリー：`03_data/processed/traffic_simulation/road_network/boundaries/ota_ward_n03_2026_quality_summary.json`

ZIP原本は改変せず保存し、Gitには登録しない。展開物は生データディレクトリへ恒久保存せず、加工処理内の一時領域またはZIP内GeoJSONの直接読込を使用する。

## 事前環境確認

リポジトリのルートで確認した。

```bash
docker compose config --quiet
docker compose run --rm analysis python --version
curl --version
unzip -v
```

確認した主なバージョン：

```text
curl: 8.6.0
unzip: 6.00
Python: 3.11.15
GeoPandas: 1.0.1
Shapely: 2.0.6
pyproj: 3.7.0
```

## 取得手順

公式配布URLから `.part` へ取得し、検証成功後だけ正式名へ変更した。

```bash
cd /Users/tstakuma/github/research

mkdir -p 03_data/raw/traffic_simulation/boundaries

URL="https://nlftp.mlit.go.jp/ksj/gml/data/N03/N03-2026/N03-20260101_13_GML.zip"
OUT="03_data/raw/traffic_simulation/boundaries/N03-20260101_13_GML.zip"

curl --fail-with-body --location \
  "${URL}" \
  --output "${OUT}.part"

ls -lh "${OUT}.part"
file "${OUT}.part"
unzip -t "${OUT}.part"

mv "${OUT}.part" "${OUT}"
```

取得結果：

```text
HTTP取得: 成功
ファイル形式: Zip archive data
ファイルサイズ: 13,153,227バイト
ZIP検査: No errors detected
```

## 生データの検証

### SHA-256

```bash
shasum -a 256 \
  03_data/raw/traffic_simulation/boundaries/N03-20260101_13_GML.zip
```

```text
94f10b26256566db970dd74b09d614f059c1e8a432f9244ac9c4add76c32ff16
```

### ZIP内容

```bash
unzip -l \
  03_data/raw/traffic_simulation/boundaries/N03-20260101_13_GML.zip
```

確認した8ファイル：

```text
KS-META-N03-20260101_13.xml
N03-20260101_13.cpg
N03-20260101_13.dbf
N03-20260101_13.geojson
N03-20260101_13.prj
N03-20260101_13.shp
N03-20260101_13.shx
N03-20260101_13.xml
```

### 属性・形状・座標系

Dockerの解析環境でZIP内GeoJSONを読み、次を検証した。

- GeoJSONルートが `FeatureCollection` である。
- CRSが `EPSG:6668` である。
- 必須属性 `N03_001`、`N03_004`、`N03_007` が全地物に存在する。
- 東京都版の全地物数が6,904件である。
- 大田区の3条件をすべて満たす地物が6件である。
- 大田区地物が空形状ではなく、すべて有効である。
- 行政区域コードで統合すると1地物になる。
- 統合後形状が有効である。
- `EPSG:6677` で計算した面積が約61.84km²である。

実測結果：

```text
全地物数: 6904
大田区該当地物数: 6
統合後地物数: 1
原本CRS: EPSG:6668
統合後形状: valid
EPSG:4326外接BBOX:
  west: 139.652974773
  south: 35.528198081
  east: 139.826027782
  north: 35.613210171
EPSG:6677面積: 61.84440206708418 km²
```

外接BBOXと面積は原本から算出した検証値であり、地域選定条件として手入力しない。

## 出典台帳への登録

`03_data/metadata/traffic_simulation_sources.csv` に次の状態で登録した。

```text
source_id: mlit_n03_2026_tokyo
status: raw_acquired
processing_script: 空欄
processed_outputs: 空欄
```

登録後、出典台帳のSHA-256と原本の再計算値が一致し、同じ `source_id` が1行だけ存在することを確認した。境界抽出完了後に、加工スクリプト、加工後出力、状態 `processed` を追記する。

## 加工手順

境界抽出は未実施である。次の実装後に実行する。

```text
reproducibility/config/traffic_simulation/study_areas.yml
05_src/traffic_simulation/network/study_areas.py
05_src/traffic_simulation/network/prepare_study_area.py
05_src/traffic_simulation/validation/test_study_areas.py
05_src/traffic_simulation/validation/test_prepare_study_area.py
```

予定する実行コマンド：

```bash
docker compose run --rm analysis python \
  -m traffic_simulation.network.prepare_study_area \
  --region ota_ward
```

6地物を1行政区域へ統合するが、行政界の座標を補間、単純化、バッファ拡張しない。OSM取得用BBOXは統合後行政界の外接矩形として機械的に算出する。

## 検証手順と現在の結果

現在完了しているのは原本検証と台帳登録までである。

```bash
git check-ignore -v \
  03_data/raw/traffic_simulation/boundaries/N03-20260101_13_GML.zip

git diff --check
```

```text
原本取得: 成功
ZIP検証: 成功
SHA-256照合: 成功
入力地物数: 6904
大田区該当地物数: 6
統合試験地物数: 1
形状検証: 成功
出典台帳登録: 成功
境界GeoParquet生成: 未実施
境界抽出自動テスト: 未実施
```

## 失敗と修正

| 日付 | 症状 | 原因 | 修正 | データへの影響 |
|---|---|---|---|---|
| 2026-07-17 | なし | 該当なし | 該当なし | なし |

全国版は765.94MBだが、東京都版12.54MBで必要な大田区行政界を取得できるため、全国版は取得しなかった。これは対象地域と保存容量に基づく選択であり、行政界地物の品質による選別ではない。

## 来歴とGitの確認

- 生データがGit除外対象：はい
- 生成物がGit除外対象：境界生成前。予定パスは除外対象。
- 出典台帳を更新済み：はい
- 取得記録がGit管理対象：はい
- 加工コードとテストがGit管理対象：未作成

原本ZIPは `.gitignore` の `*.zip` によって除外されている。Gitへ登録するのは、本記録、出典台帳、地域設定、実装コード、テストである。

## 解釈上の限界と次の作業

- N03は行政区域を表し、道路網や交通量は表さない。
- 2026年1月1日時点の境界であり、異なる基準年の結果と混在させない。
- 大田区該当6地物は1行政区域として統合するが、原本地物数も品質証跡として保持する。
- JARTIC観測点の件数、交通量、欠測、異常は行政界選択条件に使用しない。
- 次は地域設定、境界抽出実装、テストを作成し、大田区境界GeoParquetと品質サマリーを生成する。
- ディスク空き容量が約5.3GB、使用率98%であるため、OSM・SUMO生成前に空き容量を確保する。
