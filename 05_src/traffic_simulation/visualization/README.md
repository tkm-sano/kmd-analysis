# 交通シミュレーション可視化：前提・見方・運用手順

## 1. この可視化の目的

`render_study_area.py`は、交通シミュレーションの道路環境を構築する過程で、研究対象の行政界、OSM取得用BBOX、登録済みPBFの道路・信号、交通観測地点の位置と品質状態を確認するためのレビュー用地図を生成する。

この地図の目的は次のとおりである。

- N03から選択した大田区行政界を確認する。
- 行政界から機械生成したOSM取得用BBOXを確認する。
- 出典台帳とSHA-256を検証したPBFの自動車道路を道路種別別に確認する。
- OSMに登録された信号位置を確認する。
- JARTIC観測地点の位置、行政界内外、品質状態を確認する。
- 後続のOSM道路、SUMOネットワーク、配送ルート可視化の背景を統一する。
- コード、設定、データ間の空間的不整合を早期に発見する。

可視化は品質確認を補助するものであり、地図を見た印象だけでデータやモデルの合否を決めるものではない。地物数、CRS、SHA-256、接続性、制約状態等の自動検査を置き換えない。

特定のOSM restriction relationを確認する場合は、
`render_osm_relation_sample.py`を使用する。この地図は登録済み原本PBFを
SHA-256で再検証し、指定relationの`from`・`via`・`to`と約350 mの周辺道路を
表示する。relationの可視化は採用判断やSUMO connectionの生成を意味しない。

```bash
docker compose run --rm analysis \
  python -m traffic_simulation.visualization.render_osm_relation_sample \
  --relation-id 16016504
```

既定出力は次である。

```text
reproducibility/outputs/traffic_simulation/visualization/
  ota_ward_osm_relation_16016504.html
```

## 2. 現在の可視化方式

現在の出力は、FoliumとLeafletによる操作可能な静的HTML地図である。

できること：

- 地図の拡大・縮小
- 表示位置の移動
- レイヤーの表示・非表示
- OSM道路種別レイヤーの切替
- 道路名、OSM ID、道路種別、一方通行、車線数、制限速度等の確認
- OSM信号位置の表示
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

### 3.5 OSM道路PBF

現在の道路入力は次の出典台帳IDから解決する。

```text
osm_geofabrik_kanto_20260716
```

対応する加工PBFと品質サマリーは次である。

```text
03_data/processed/traffic_simulation/road_network/osm_extracts/
  osm_ota_ward_20260716.osm.pbf

03_data/processed/traffic_simulation/validation/
  osm_ota_ward_20260716_quality_summary.json
```

可視化処理は、出典台帳からこの2ファイルを解決し、地域ID、PBFパス、品質サマリー、抽出PBFのSHA-256が一致した場合だけ道路を表示する。任意のPBFパスをCLIから直接指定しない。

PBFには40,880件の`highway` wayがある。地図では歩道、自転車道、階段等を除き、自動車道路候補26,201件をBBOXで表示用にクリップする。これは表示上のクリップであり、登録済みPBFを変更しない。

## 4. 地図の見方

### 4.1 レイヤー

右上のレイヤーコントロールで次を切り替えられる。

| レイヤー | 意味 |
|---|---|
| `N03大田区行政界` | 分析対象の大田区行政界 |
| `行政界から生成した地図取得用矩形範囲` | OSM取得等に使用する外接矩形 |
| `OSM 高速道路・幹線道路` | 高速道路・自動車専用道路等 |
| `OSM 主要道路` | 主要幹線道路 |
| `OSM 補助幹線・未分類道路` | 補助幹線・未分類道路 |
| `OSM 住宅道路・生活道路` | 住宅道路。初期状態では非表示 |
| `OSM サービス道路・その他の自動車道路` | 構内・サービス道路等。初期状態では非表示 |
| `OSM登録信号` | OSMに登録された信号位置。初期状態では非表示 |
| `JARTIC観測地点: ...` | 指定したJARTIC加工ファイルの観測地点 |
| OpenStreetMap背景 | 位置確認用の背景タイル。研究用OSM原本ではない |

背景タイルは表示補助であり、後続で取得・SHA-256登録するOSM原本の代わりにはならない。背景地図を見て道路データを取得済みと判断しない。

### 4.2 色と線

| 表現 | 意味 |
|---|---|
| 青い境界・薄い青塗り | N03大田区行政界 |
| 赤い破線 | 行政界から生成した取得用BBOX |
| 赤い道路線 | motorway・trunkとそのlink |
| オレンジの道路線 | primary・secondaryとそのlink |
| 緑の道路線 | tertiary・unclassifiedとそのlink |
| 青い道路線 | residential・living_street |
| 灰色の道路線 | service・road等 |
| 紫の点 | OSMに登録された信号位置 |
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

### 4.4 OSM道路ツールチップ

道路へポインターを重ねると、存在する範囲で次を表示する。

- OSM ID
- 道路名と路線番号
- `highway`種別
- 一方通行
- 車線数
- 制限速度
- 通行条件
- N03大田区行政界と交差するか

空欄はPBFで属性を確認できなかったことを表し、0や規制なしを意味しない。OSM信号位置は信号現示、周期、オフセットを含まない。

### 4.5 情報パネル

右上の固定情報パネルには次を表示する。

- 地域ID、地域名、設定版
- 出典台帳ID
- 原本、API用、距離計算用CRS
- 統合前N03地物数
- EPSG:6677で計算した面積
- OSM取得用BBOX
- N03原本SHA-256
- OSM出典台帳ID、スナップショット日
- 登録済み`highway` way数、表示道路数、信号数
- 抽出PBFのSHA-256
- 研究の現在工程、状態更新日、全工程の完了・進行中・予定状態

これらは実行時に地域設定、出典台帳、N03原本から読み取った値であり、表示用に別入力しない。

研究工程の正本だけは、次の明示的な進捗設定である。

```text
reproducibility/config/traffic_simulation/research_stage.yml
```

地図左上の「研究の現在地」には現在工程を常時表示し、「全工程を表示」を開くと全工程を確認できる。現在は`SUMO道路網生成・構造検証`が進行中である。進捗率は、工程ごとの作業量が均等でないため表示しない。

工程完了時は、根拠となるコード、設定、取得記録、検証結果を`evidence`へ登録した上で、完了工程を`completed`、次の工程を`in_progress`へ変更し、`current_stage_id`と`updated_at`を同じ変更で更新する。ファイルが存在するだけでは自動的に完了扱いにしない。

## 5. 生成手順

### 5.1 Dockerイメージ

Folium依存関係を追加・変更した場合は解析イメージを再構築する。

```bash
cd "$(git rev-parse --show-toplevel)"
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

### 5.4 登録済みOSM道路とJARTICを重ねて生成する

現在の正式な生成コマンドは次である。

```bash
docker compose run --rm analysis \
  python -m traffic_simulation.visualization.render_study_area \
  --region ota_ward \
  --osm-source-id osm_geofabrik_kanto_20260716 \
  --jartic \
  03_data/processed/traffic_simulation/calibration/jartic_1h_road3_tokyo_202607042200_observations.parquet \
  --overwrite
```

可視化用の一時PBFとGeoJSON Sequenceは処理終了時に削除する。登録済みPBFと品質サマリーは変更しない。

### 5.5 出力先を指定する

出力先はリポジトリ相対パスだけを受け付ける。

```bash
docker compose run --rm analysis \
  python -m traffic_simulation.visualization.render_study_area \
  --region ota_ward \
  --output \
  reproducibility/outputs/traffic_simulation/visualization/ota_ward_boundary_only.html
```

絶対パスとリポジトリ外へ出る`..`パスは拒否する。

### 5.6 背景タイルを使わない

```bash
docker compose run --rm analysis \
  python -m traffic_simulation.visualization.render_study_area \
  --region ota_ward \
  --no-basemap
```

`--no-basemap`はOpenStreetMap背景タイルを要求しない。ただし、現在のHTMLはLeaflet本体を外部配信元から読むため、ブラウザでの表示にはネットワーク接続が必要である。完全オフライン表示が必要な場合は、Leaflet資産を管理対象として固定する別対応が必要である。

### 5.7 既存出力を更新する

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
  "$(git rev-parse --show-toplevel)/reproducibility/outputs/traffic_simulation/visualization/ota_ward_study_area.html"
```

表示後、最低限次を確認する。

1. 大田区行政界が表示される。
2. 赤いBBOXが行政界全体を包含する。
3. BBOXと行政界が同一範囲として塗られていない。
4. JARTIC観測点が表示される。
5. レイヤーを個別に切り替えられる。
6. 主要道路3レイヤーが初期表示される。
7. 住宅道路、サービス道路、信号を個別に表示できる。
8. 道路ツールチップと観測点ポップアップが開く。
9. 品質色と行政界外の黒枠が凡例どおりである。
10. 情報パネルの地域ID、CRS、SHA-256が取得記録と一致する。
11. 「研究の現在地」が実装計画と一致し、進行中工程が1件だけ表示される。

## 7. 生成後の機械検査

現行の実データでは次を期待する。

```text
region: ota_ward
boundary features: 1 (dissolved from 6)
OSM rendered motor-road ways: 26201
OSM traffic signals: 2190
JARTIC markers: 33
```

HTMLについて次を検査する。

- N03行政界レイヤーが存在する。
- BBOXレイヤーが存在する。
- 5種類のOSM道路レイヤーと信号レイヤーが存在する。
- 凡例と情報パネルが存在する。
- N03原本SHA-256が表示される。
- OSM出典台帳IDと抽出PBF SHA-256が表示される。
- 研究工程の更新日、現在工程、全工程の状態が表示される。
- 道路26,201件、信号2,190件が入力と整合する。
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
  → N03行政界、BBOX、登録済みOSM道路・信号、JARTIC地点
  → 500mメッシュ別2024年推定人口・1日合成需要

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

## 11. 2026年7月17日に実行した内容と結果

登録済みN03境界、OSM PBF、JARTIC加工データを用いて次を実行した。

```bash
docker compose run --rm analysis \
  python -m traffic_simulation.visualization.render_study_area \
  --region ota_ward \
  --osm-source-id osm_geofabrik_kanto_20260716 \
  --jartic \
  03_data/processed/traffic_simulation/calibration/jartic_1h_road3_tokyo_202607042200_observations.parquet \
  --overwrite
```

出力は次である。

```text
reproducibility/outputs/traffic_simulation/visualization/
  ota_ward_study_area.html
```

生成時に確認した件数：

| 表示対象 | 件数 |
|---|---:|
| 高速道路・幹線道路 | 973 |
| 主要道路 | 957 |
| 補助幹線・未分類道路 | 6,267 |
| 住宅道路・生活道路 | 5,543 |
| サービス道路・その他の自動車道路 | 12,461 |
| 自動車道路候補合計 | 26,201 |
| OSM登録信号 | 2,190 |
| JARTIC観測地点 | 33 |

ブラウザ表示では次を確認した。

- 左側の凡例・情報パネルに地域、CRS、BBOX、出典、SHA-256が表示される。
- 右側のレイヤーコントロールに行政界、BBOX、5道路分類、信号、JARTICが表示される。
- 大田区取得用BBOXへ表示範囲が合い、主要3道路分類が初期表示される。
- レイヤーの表示切替と道路ツールチップが動作する。
- ブラウザコンソールにJavaScriptエラーがない。

この確認は表示コードと入力の空間的整合をレビューしたものであり、道路接続、SUMO変換、交通量再現、配送経路最適化の完了を意味しない。

## 12. 可視化に含まれる判断と恣意性

### 分析条件から機械的に決まるもの

- N03行政界、統合前地物数、面積
- N03行政界から生成する取得用BBOX
- 出典台帳から解決するOSM PBFと品質サマリー
- 登録済み原本・抽出物のSHA-256
- PBFに存在するOSMタグと信号node
- JARTIC入力ファイルに存在する地点と品質状態

これらを地図の見栄えに合わせて変更しない。

### 表示上の判断として設定したもの

- 道路分類の5グループへの集約
- 道路色、線幅、透過度
- 主要3道路分類を初期表示し、住宅道路、サービス道路、信号を初期非表示にすること
- JARTIC品質状態の色と行政界外の黒枠
- 地図の初期ズーム、パネル位置、背景タイル
- 歩道、自転車道、階段等を自動車道路候補の表示から除くこと

これらには視認性を目的とする恣意性がある。表示分類はOSM原本を変更せず、SUMOへ採用する道路規則でも、交通分析の重みでもない。古典・QAOA比較では同一HTML生成規則を使用し、見栄えの差を性能差として解釈しない。

道路はBBOXで表示用にクリップする。`complete_ways`により抽出PBFへ保持されたBBOX外nodeを地図全体へ描画しないための処理であり、PBFや分析範囲を加工するものではない。行政界との交差表示も空間的なレビュー属性であり、その道路を大田区内交通として採用したことを意味しない。

## 13. 既知のコード上・運用上の問題

- 26,201件の道路形状をHTMLへ埋め込むため、出力は約11MBとなり、初回表示やレイヤー切替が重い場合がある。
- HTMLは静的スナップショットであり、交通量、速度、車両、信号現示の時間変化を保持しない。
- 道路件数は表示用フィルター後のOSM way件数であり、SUMO edge、lane、junctionの件数ではない。
- `inside_boundary`は道路形状と行政界の空間関係を示すだけで、交通量の所属や道路全体が行政界内にあることを保証しない。
- OSMタグの空欄は値がないことを示す。車線数、制限速度、通行条件を0または規制なしとして補完しない。
- 背景タイルとLeaflet関連資産を外部配信元から読むため、ネットワークがない環境では完全には表示できない。研究用PBF自体は外部背景に依存しない。
- `render_study_area.py`にはPBF来歴検証、表示用抽出、分類、HTML構築が集まっている。後続のSUMO・ルート可視化を追加する前に、台帳解決と共通地図部品を共有モジュールへ分離する余地がある。
- 合成需要レイヤーには`test_render_baseline_demand.py`があり、入力ハッシュ、合計、レイヤー名、ツールチップ、色分類を検査する。道路を含む`render_study_area.py`全体の専用テストはまだなく、既存検証テスト、生成件数確認、HTML文字列検査、ブラウザ表示確認を組み合わせている。
- ブラウザによる見た目の確認は実行環境差を受けるため、自動構造検査を置き換えない。
- 研究工程は明示的な管理判断で更新するため、設定更新を忘れると地図の現在地が古くなる。工程変更時は実装計画と`research_stage.yml`を同時に更新する。

## 14. 不具合と修正履歴

### 道路追加後に凡例・レイヤー一覧が表示されなかった問題

症状：

- HTMLを開いてもレイヤーコントロールが表示されない。
- 地図の初期化が途中で停止し、期待する範囲へズームしない。

原因：

- 1個のFolium `GeoJsonTooltip`インスタンスを5個の道路`GeoJson`レイヤーへ再利用した。
- Brancaの要素は単一の親を持つため、生成JavaScriptが最後の道路レイヤーを定義する前にそのレイヤーへ`bindTooltip`しようとした。
- ブラウザで`Cannot read properties of undefined (reading 'bindTooltip')`が発生し、後続のレイヤーコントロールと`fitBounds`が実行されなかった。

修正：

- 道路レイヤーごとに新しい`GeoJsonTooltip`を生成するよう変更した。
- HTMLを再生成し、ブラウザのキャッシュを避けて再表示した。
- 左側の凡例・情報パネル、右側の全レイヤー一覧、BBOXへの初期ズーム、道路表示を画面で確認した。
- ブラウザコンソールにJavaScriptエラーがないことを確認した。

この修正は表示コードだけに作用し、OSM PBF、道路抽出件数、N03行政界、JARTIC加工データ、分析条件を変更していない。

## 15. 500m人口・合成需要の可視化

### 15.1 入力と生成手順

入力の正本は`reproducibility/config/traffic_simulation/baseline_demand.yml`である。可視化処理は設定からGeoParquetと品質要約を解決し、地域ID、設定SHA-256、GeoParquet SHA-256、行数、人口合計、需要合計が一致した場合だけ表示する。任意の需要ファイルをCLIで直接指定しない。

```bash
docker compose run --rm analysis \
  python -m traffic_simulation.visualization.render_study_area \
  --region ota_ward \
  --baseline-demand \
  --output \
  reproducibility/outputs/traffic_simulation/visualization/ota_ward_baseline_demand.html \
  --overwrite
```

閲覧する。

```bash
open \
  "$(git rev-parse --show-toplevel)/reproducibility/outputs/traffic_simulation/visualization/ota_ward_baseline_demand.html"
```

### 15.2 レイヤーと見方

| レイヤー | 初期表示 | 意味 |
|---|---|---|
| `1日当たり合成配送需要（500メートル、191件）` | 表示 | 1日当たり宅配便個数相当量 |
| `2024年推定人口（500メートル、191件）` | 非表示 | 2020年分布を2024年大田区人口へ比例調整した推定人口 |
| `N03大田区行政界` | 表示 | 面積按分に用いた大田区境界 |

メッシュへポインターを合わせると、メッシュコード、全面包含・境界分類、境界交差率、2020年国勢調査人口、2024年推定人口、1日合成需要を表示する。合成需要レイヤーと人口レイヤーを同時表示すると重なるため、比較時は一方ずつ表示する。

色は各表示値の五分位で、薄色が低いメッシュ、濃色が高いメッシュを表す。五分位境界は凡例へ表示する。これは同一地図内の分布を読みやすくする表示上の分類であり、需要の高低を決める研究上の閾値、配送優先度、最適化重み、サービス可否判定には使用しない。別地域・別設定の地図間では五分位境界が変わり得るため、色だけを直接比較しない。

### 15.3 2026年7月18日の生成結果

- 表示メッシュ：191件
- 全面包含：122件
- 境界メッシュ：69件
- 2024年推定人口合計：736,652人
- 1日合成需要合計：82,023宅配便個数相当
- GeoParquet SHA-256：`e7caeb262665ba3396834bb54e2dff296b3cbbd02af6922e906eb683829f5048`
- `test_render_baseline_demand.py`と`test_prepare_baseline_demand.py`：合計17件成功

生成HTMLについて、両メッシュレイヤー名、凡例、191メッシュ、合計値、入力SHA-256およびLeaflet初期化コードの存在を機械検査した。この実行環境ではブラウザ操作接続を利用できなかったため、2026年7月18日の実ブラウザ目視確認は未実施である。目視未実施を機械検査済みと混同しない。

### 15.4 解釈上の禁止事項

- 表示値を実注文、実顧客、実配送先または配送停止回数と呼ばない。
- 2024年推定メッシュ人口を2024年のメッシュ実測値と呼ばない。
- 面積按分した境界メッシュ内で人口が均一だったと断定しない。
- 濃色メッシュを自動的に優先配送先へ設定しない。
- 色分けを使って入力値、境界または最適化結果を手修正しない。
- 地図表示だけで人口・需要合計やSHA-256の検証を代替しない。
