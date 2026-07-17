# 国土数値情報N03行政区域データ2026年東京都版：取得・検証記録

## 記録状態

- 記録日：2026-07-17
- 実施者：研究環境管理者（Codex支援）
- 状態：`processed`（原本検証・大田区境界抽出・自動テスト完了）
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
- 加工スクリプト：`05_src/traffic_simulation/network/study_areas.py`
- 地域設定：`reproducibility/config/traffic_simulation/study_areas.yml`
- 加工後出力：`03_data/processed/traffic_simulation/road_network/boundaries/ota_ward_n03_2026.parquet`
- 品質サマリー：`03_data/processed/traffic_simulation/validation/ota_ward_n03_2026_quality_summary.json`
- 加工後境界SHA-256：`7b54c39e1826c224bf0a1f8617afe2a8434df45b1572c57d46e2a64a93325aca`

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

`03_data/metadata/traffic_simulation_sources.csv` に取得時点で登録し、境界生成成功後に加工来歴を追記した。

```text
source_id: mlit_n03_2026_tokyo
status: processed
processing_script: 05_src/traffic_simulation/network/study_areas.py
processed_outputs:
  03_data/processed/traffic_simulation/road_network/boundaries/ota_ward_n03_2026.parquet
  03_data/processed/traffic_simulation/validation/ota_ward_n03_2026_quality_summary.json
```

登録後、出典台帳のSHA-256と原本の再計算値が一致し、同じ `source_id` が1行だけ存在することを確認した。

## 加工手順

次の設定、実装、テストを作成した。

```text
reproducibility/config/traffic_simulation/study_areas.yml
05_src/traffic_simulation/network/study_areas.py
05_src/traffic_simulation/validation/test_study_areas.py
```

2026-07-17 21:40:37 JSTに次を実行した。

```bash
docker compose run --rm analysis \
  python -m traffic_simulation.network.study_areas \
  --region ota_ward
```

処理順は次のとおりである。

1. YAMLのスキーマ、地域ID、状態、必須項目、CRS、許可された用途を検証する。
2. 出典台帳IDから原本のリポジトリ相対パスと期待SHA-256を解決する。
3. ZIP原本のSHA-256、ZIP形式、原本名、ZIP内GeoJSON数を検証する。
4. ZIPを恒久展開せず、ZIP内GeoJSONを直接読む。
5. 原本CRSをメタデータから読み、CRS不明の場合は停止する。
6. 行政区域コード、都道府県名、市区町村名の3条件を同時に満たす6地物を選ぶ。
7. 空形状と無効形状を拒否し、6地物を1つのMultiPolygonへ統合する。
8. 原本CRSの境界、API用CRSの境界、距離計算用CRSの境界をそれぞれ生成する。
9. EPSG:4326境界の外接矩形をOSM取得用BBOXとして機械的に算出する。
10. EPSG:6677の投影後境界から面積を算出する。
11. 原本CRSを保持したGeoParquetと品質サマリーを一時名へ書き、成功後だけ正式名へ変更する。

6地物を1行政区域へ統合したが、行政界の座標を補間、単純化、平滑化、バッファ拡張していない。生成物が存在する場合は上書きを拒否する。同じ入力と設定を再処理する場合は、既存生成物の来歴を確認した上で別版として扱う。

## 固定した設定

設定の正本は `reproducibility/config/traffic_simulation/study_areas.yml` である。

| 項目 | 固定値 | 理由 |
|---|---|---|
| スキーマ版 | `1` | 設定形式の互換性を明示するため |
| 地域ID | `ota_ward` | CLI、生成物名、後続処理で共通参照するため |
| 地域設定版 | `1` | 原典・選択条件の変更を追跡するため |
| 状態 | `active` | 正式な最小検証地域として使用するため |
| 出典台帳ID | `mlit_n03_2026_tokyo` | 原本とSHA-256へ一意に結び付けるため |
| 行政区域コード | `N03_007="13111"` | 大田区の機械可読な選択条件 |
| 都道府県条件 | `N03_001="東京都"` | コードだけの誤選択を検出するため |
| 市区町村条件 | `N03_004="大田区"` | コードと名称の不整合を検出するため |
| 原本CRS | `EPSG:6668` | 原本メタデータから読み取った値。設定で上書きしない |
| API用CRS | `EPSG:4326` | OSM等の緯度経度問い合わせに用いるため |
| 距離・面積用CRS | `EPSG:6677` | 東京を含む平面直角座標系でメートル計算するため |
| 取得範囲生成 | `boundary_envelope` | 手入力BBOXを排除するため |
| 道路切り出し | `intersects_boundary` | 外接矩形を分析対象そのものにしないため |

設定には座標値、BBOX、ホスト固有の絶対パス、秘密情報を保存しない。N03の基準年、原本、選択条件を変更する場合は、同じ地域設定版を上書きせず `version` を上げる。

## 恣意性とその統制

### 研究判断として残る恣意性

- 東京全域ではなく大田区を最小検証地域に選んだことは研究設計上の判断である。環境・データ統合を小規模に検証する目的であり、大田区が東京全体を統計的に代表するとは仮定しない。
- 2026年版N03を採用したことは、取得時点で利用できる基準年と研究時点を合わせる判断である。異なる基準年を使えば行政界が変わり得る。
- 全国版ではなく東京都版を取得したことは、必要範囲、保存容量、処理量に基づく判断である。東京都内の同じN03地物を選別・修正したものではない。
- 面積計算にEPSG:6677を採用したことは、東京地域のメートル単位計算に適した座標系を選ぶ技術判断である。原本形状そのものは変更しない。
- OSM取得に行政界の外接矩形を使うと行政界外も取得範囲へ含まれる。これは矩形問い合わせの技術的制約への対応であり、分析対象は引き続き行政界ポリゴンで判定する。

### 処理から排除した恣意性

- JARTIC観測点数、交通量、欠測、異常値、道路密度、物流量を見て地域境界を変更していない。
- 都合のよい地物だけを手作業で選ばず、公開属性の3条件を全件へ適用した。
- BBOXの座標を手入力、丸め、拡張していない。
- 行政界を単純化、補間、平滑化、バッファ処理していない。
- CRSを欠落時に推測して付与せず、原本メタデータにない場合は停止する。
- SHA-256不一致、未知の設定項目、重複YAMLキー、絶対パス、不正CRS、空・無効形状を許容しない。
- 生成後の結果を見て設定値を調整していない。設定変更時は版を上げ、旧設定と生成物を残す。

したがって、対象地域の選定自体には明示された研究判断がある一方、選定後の境界抽出と座標算出は登録済み原本と固定設定から決定的に行う。今後の報告では「大田区での最小統合試験」と表現し、東京全域の代表性や実交通の完全再現を主張しない。

## 検証手順と現在の結果

原本検証、台帳登録、地域設定、境界抽出、生成物検証まで完了した。

```bash
git check-ignore -v \
  03_data/raw/traffic_simulation/boundaries/N03-20260101_13_GML.zip

git diff --check

docker compose run --rm analysis \
  python -m pytest 05_src/traffic_simulation/validation -q
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
境界GeoParquet生成: 成功
境界出力地物数: 1
境界出力CRS: EPSG:6668
境界出力形状: 有効
境界SHA-256照合: 成功
境界抽出自動テスト: 18件成功
交通シミュレーション検証テスト全体: 52件成功
```

## 失敗と修正

| 日付 | 症状 | 原因 | 修正 | データへの影響 |
|---|---|---|---|---|
| 2026-07-17 | なし | 該当なし | 該当なし | なし |

全国版は765.94MBだが、東京都版12.54MBで必要な大田区行政界を取得できるため、全国版は取得しなかった。これは対象地域と保存容量に基づく選択であり、行政界地物の品質による選別ではない。

## 来歴とGitの確認

- 生データがGit除外対象：はい
- 生成物がGit除外対象：はい。GeoParquetと品質サマリーの両方を確認済み。
- 出典台帳を更新済み：はい
- 取得記録がGit管理対象：はい
- 加工コード、設定、テストがGit管理対象：はい

原本ZIPは `.gitignore` の `*.zip` によって除外されている。Gitへ登録するのは、本記録、出典台帳、地域設定、実装コード、テストである。

## 解釈上の限界と次の作業

- N03は行政区域を表し、道路網や交通量は表さない。
- 2026年1月1日時点の境界であり、異なる基準年の結果と混在させない。
- 大田区該当6地物は1行政区域として統合するが、原本地物数も品質証跡として保持する。
- JARTIC観測点の件数、交通量、欠測、異常は行政界選択条件に使用しない。
- 次はこの行政界からOSM取得用BBOXを呼び出す `fetch_osm.py` と、外部通信をモック化したテストを作成する。
- ディスク空き容量が少なく使用率99%であるため、OSM・SUMO生成前に十分な空き容量を確保する。
