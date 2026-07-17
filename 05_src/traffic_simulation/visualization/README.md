# 交通シミュレーション可視化：前提・見方・運用手順

## 1. この可視化の目的

`render_study_area.py`は、交通シミュレーションの道路環境を構築する前段階で、研究対象の行政界、OSM取得用BBOX、交通観測地点の位置と品質状態を確認するためのレビュー用地図を生成する。

この地図の目的は次のとおりである。

- N03から選択した大田区行政界を確認する。
- 行政界から機械生成したOSM取得用BBOXを確認する。
- JARTIC観測地点の位置、行政界内外、品質状態を確認する。
- 後続のOSM道路、SUMOネットワーク、配送ルート可視化の背景を統一する。
- コード、設定、データ間の空間的不整合を早期に発見する。

可視化は品質確認を補助するものであり、地図を見た印象だけでデータやモデルの合否を決めるものではない。地物数、CRS、SHA-256、接続性、制約状態等の自動検査を置き換えない。

## 2. 現在の可視化方式

現在の出力は、FoliumとLeafletによる操作可能な静的HTML地図である。

できること：

- 地図の拡大・縮小
- 表示位置の移動
- レイヤーの表示・非表示
- JARTIC地点のクリック
- 観測点属性と品質状態のポップアップ表示

できないこと：

- 時間経過による交通量、速度、渋滞の変化
- 車両の移動アニメーション
- 信号現示の時間変化
- SUMO実行とのリアルタイム連動
- 外部データの自動更新
- 古典・QAOA配送ルートの動的比較

したがって、現在の地図は「インタラクティブに閲覧できる静的スナップショット」であり、動的交通シミュレーションではない。

## 3. 入力データの前提

### 3.1 地域設定

地域設定の正本は次である。

```text
reproducibility/config/traffic_simulation/study_areas.yml
```

現在の地域IDは`ota_ward`、設定版は`1`である。地域IDから次を解決する。

- 出典台帳ID：`mlit_n03_2026_tokyo`
- 行政区域コード：`N03_007="13111"`
- 都道府県名：`N03_001="東京都"`
- 市区町村名：`N03_004="大田区"`
- API用CRS：`EPSG:4326`
- 距離・面積用CRS：`EPSG:6677`

行政界の座標とBBOXは設定ファイルへ手入力しない。

### 3.2 N03行政界

N03原本は次である。

```text
03_data/raw/traffic_simulation/boundaries/N03-20260101_13_GML.zip
```

原本SHA-256：

```text
94f10b26256566db970dd74b09d614f059c1e8a432f9244ac9c4add76c32ff16
```

大田区は3属性条件をすべて満たす6地物を選択し、座標を単純化、補間、平滑化、バッファ処理せず、1つのMultiPolygonへ統合する。原本CRSは`EPSG:6668`である。

### 3.3 OSM取得用BBOX

BBOXは、大田区行政界を`EPSG:4326`へ変換した後、その外接矩形から機械的に生成する。

```text
west:  139.652974773
south:  35.528198081
east:  139.826027782
north:  35.613210171
```

BBOXはOSM等の矩形問い合わせに使用する取得範囲であり、研究対象範囲そのものではない。BBOX内には大田区行政界外の領域も含まれる。分析対象の内外判定にはN03行政界ポリゴンを使用する。

### 3.4 JARTIC観測地点

現在表示するJARTIC加工データは次である。

```text
03_data/processed/traffic_simulation/calibration/
  jartic_1h_road3_tokyo_202607042200_observations.parquet
```

これは2026年7月4日22時台、道路種別3、1時間値の単一スナップショットである。東京全域、全道路、全時間帯の交通状況を表さない。

正規化データには1観測地点について上り・下りの2行がある。可視化では`source_id`と`observation_code`で行をまとめ、同じ座標に方向別マーカーを重ねない。現在は33観測地点を表示する。

## 4. 地図の見方

### 4.1 レイヤー

右上のレイヤーコントロールで次を切り替えられる。

| レイヤー | 意味 |
|---|---|
| `N03 administrative boundary` | 分析対象の大田区行政界 |
| `Mechanically derived acquisition BBOX` | OSM取得等に使用する外接矩形 |
| `JARTIC: ...` | 指定したJARTIC加工ファイルの観測地点 |
| OpenStreetMap背景 | 位置確認用の背景タイル。研究用OSM原本ではない |

背景タイルは表示補助であり、後続で取得・SHA-256登録するOSM原本の代わりにはならない。背景地図を見て道路データを取得済みと判断しない。

### 4.2 色と線

| 表現 | 意味 |
|---|---|
| 青い境界・薄い青塗り | N03大田区行政界 |
| 赤い破線 | 行政界から生成した取得用BBOX |
| 緑の点 | 該当地点の表示対象行がすべて有効 |
| オレンジの点 | 有効行と無効行が混在 |
| 赤い点 | 表示対象行がすべて無効 |
| 黒い外周 | 観測座標が大田区行政界外 |

JARTICの品質色は交通量の大小を表さない。緑は交通量が多いこと、赤は渋滞していることを意味しない。

### 4.3 JARTICポップアップ

観測地点をクリックすると次を表示する。

- 出典ID
- 常時観測点コード
- 有効行数／全行数
- 大田区行政界内か
- 無効理由
- 経度・緯度

欠測値や異常フラグは0へ変換しない。`valid_measurement`が欠損している場合は、可視化上は有効とみなさない。

### 4.4 情報パネル

右上の固定情報パネルには次を表示する。

- 地域ID、地域名、設定版
- 出典台帳ID
- 原本、API用、距離計算用CRS
- 統合前N03地物数
- EPSG:6677で計算した面積
- OSM取得用BBOX
- N03原本SHA-256

これらは実行時に地域設定、出典台帳、N03原本から読み取った値であり、表示用に別入力しない。

## 5. 生成手順

### 5.1 Dockerイメージ

Folium依存関係を追加・変更した場合は解析イメージを再構築する。

```bash
cd /Users/tstakuma/github/research
docker compose build analysis
```

Foliumの固定バージョンは次へ記録する。

```text
docker/analysis/requirements.txt
```

### 5.2 行政界だけを生成する

```bash
docker compose run --rm analysis \
  python -m traffic_simulation.visualization.render_study_area \
  --region ota_ward
```

### 5.3 JARTICを重ねて生成する

```bash
docker compose run --rm analysis \
  python -m traffic_simulation.visualization.render_study_area \
  --region ota_ward \
  --jartic \
  03_data/processed/traffic_simulation/calibration/jartic_1h_road3_tokyo_202607042200_observations.parquet
```

`--jartic`は複数回指定できる。ただし、異なる日時を同じ静的地図へ重ねる場合は、地点の重なりと品質色の解釈に注意する。時間変化を比較する目的では、将来の時系列可視化を使用する。

### 5.4 出力先を指定する

出力先はリポジトリ相対パスだけを受け付ける。

```bash
docker compose run --rm analysis \
  python -m traffic_simulation.visualization.render_study_area \
  --region ota_ward \
  --output \
  reproducibility/outputs/traffic_simulation/visualization/ota_ward_boundary_only.html
```

絶対パスとリポジトリ外へ出る`..`パスは拒否する。

### 5.5 背景タイルを使わない

```bash
docker compose run --rm analysis \
  python -m traffic_simulation.visualization.render_study_area \
  --region ota_ward \
  --no-basemap
```

`--no-basemap`はOpenStreetMap背景タイルを要求しない。ただし、現在のHTMLはLeaflet本体を外部配信元から読むため、ブラウザでの表示にはネットワーク接続が必要である。完全オフライン表示が必要な場合は、Leaflet資産を管理対象として固定する別対応が必要である。

### 5.6 既存出力を更新する

既存HTMLは暗黙に上書きしない。レビュー用の同名出力を明示的に更新する場合だけ`--overwrite`を指定する。

```bash
docker compose run --rm analysis \
  python -m traffic_simulation.visualization.render_study_area \
  --region ota_ward \
  --jartic \
  03_data/processed/traffic_simulation/calibration/jartic_1h_road3_tokyo_202607042200_observations.parquet \
  --overwrite
```

正式な比較結果を保存する場合は同名上書きではなく、データ取得日、交通シナリオID、設定版を含む別名を使用する。

## 6. 閲覧手順

現在の生成済み地図をmacOSで開く。

```bash
open \
  /Users/tstakuma/github/research/reproducibility/outputs/traffic_simulation/visualization/ota_ward_study_area.html
```

表示後、最低限次を確認する。

1. 大田区行政界が表示される。
2. 赤いBBOXが行政界全体を包含する。
3. BBOXと行政界が同一範囲として塗られていない。
4. JARTIC観測点が表示される。
5. レイヤーを個別に切り替えられる。
6. 観測点のポップアップが開く。
7. 品質色と行政界外の黒枠が凡例どおりである。
8. 情報パネルの地域ID、CRS、SHA-256が取得記録と一致する。

## 7. 生成後の機械検査

現行の実データでは次を期待する。

```text
region: ota_ward
boundary features: 1 (dissolved from 6)
JARTIC markers: 33
```

HTMLについて次を検査する。

- N03行政界レイヤーが存在する。
- BBOXレイヤーが存在する。
- 凡例と情報パネルが存在する。
- N03原本SHA-256が表示される。
- JARTICマーカー数が入力と整合する。
- `.part`ファイルが残っていない。
- 出力がGit除外対象である。

既存の交通シミュレーションテストも実行する。

```bash
docker compose run --rm analysis \
  python -m pytest 05_src/traffic_simulation/validation -q

git check-ignore -v \
  reproducibility/outputs/traffic_simulation/visualization/ota_ward_study_area.html
```

## 8. Git管理と再現性

Git管理する。

```text
05_src/traffic_simulation/visualization/__init__.py
05_src/traffic_simulation/visualization/render_study_area.py
05_src/traffic_simulation/visualization/README.md
docker/analysis/requirements.txt
```

Git管理しない。

```text
reproducibility/outputs/traffic_simulation/visualization/*.html
```

HTMLは実行時生成物であり、コード、設定、登録済み入力から再生成する。背景タイルは閲覧時に外部サービスから取得されるため、閲覧時点により背景表示が変わる可能性がある。研究用OSM原本と比較証跡は、別途固定・ハッシュ登録する。

## 9. 禁止事項と注意事項

- 地図を見てN03行政界の座標を手修正しない。
- BBOXを見栄えのために丸めたり拡張したりしない。
- 背景タイルをOSM取得済み原本として扱わない。
- JARTIC品質色を交通量や渋滞の色として解釈しない。
- 行政界外観測点を理由なく削除しない。
- 目視で都合のよい観測地点だけを選ばない。
- 静的な単一時点地図から時間変化を推定しない。
- 地図画像だけを根拠にSUMO道路接続が正しいと判断しない。
- 古典・QAOA比較で異なる背景、縮尺、入力、交通環境を使わない。

目視で問題を発見した場合は、原本、設定、変換コード、自動テストのどこに原因があるかを確認する。手動修正が必要な場合は、対象ID、変更前後、理由、確認日を追跡可能な補正表へ記録する。

## 10. 後続の可視化

道路環境構築に合わせ、次の順で追加する。

```text
render_study_area.py
  → N03行政界、BBOX、JARTIC地点

render_osm_network.py
  → OSM道路種別、一方通行、制限速度、信号位置

render_sumo_network.py
  → SUMOエッジ、レーン、ジャンクション、接続、孤立成分

render_route_comparison.py
  → 古典・QAOAの訪問順序と道路経路

render_traffic_timeline.py
  → 時刻別交通量、速度、渋滞、車両位置

sumo-gui
  → 車両、信号、車線変更、停止、渋滞の動的確認
```

動的可視化では、時刻、交通シナリオID、SUMO設定版、乱数seedを必ず表示・記録する。古典・QAOA配送ルートを比較する場合は、同じ交通環境、出発時刻、道路経路生成規則、seed群を用いる。
