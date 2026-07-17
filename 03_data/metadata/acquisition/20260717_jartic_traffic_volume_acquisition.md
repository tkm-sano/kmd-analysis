# JARTIC 1時間交通量：取得・検証記録

## 記録状態

- 記録日：2026-07-17
- 状態：加工・検証済み
- 出典台帳ID：`jartic_1h_road3_tokyo_202607042200`
- 観測期間：2026-07-04 22:00:00～22:59:59 JST
- 道路種別：`3`（一般国道）
- 地理的問い合わせ範囲：EPSG:4326のBBOX `139.1,35.45,140.0,35.95`
- 取得した観測地点数：33

## 配布元と利用条件

- 配布者：日本道路交通情報センター（JARTIC）／国土交通省xROAD
- 配布ページ：<https://www.jartic-open-traffic.org/>
- API仕様書：<https://www.jartic-open-traffic.org/action_method.pdf>
- WFSエンドポイント：<https://api.jartic-open-traffic.org/geoserver>
- レイヤー：`t_travospublic_measure_1h`
- 出力形式：GeoJSON
- ライセンス・利用条件：配布サイト掲載のJARTIC交通量API利用規約
- アクセス方法：HTTPS GET。秘密値は保存していない。

1時間値レイヤーには保存期間があるため、応答を直ちに不変の生データとして保存した。JARTICは東京都内の全道路を対象としておらず、取得値には観測機器の品質フラグが含まれる。

## 保存先と来歴

- 原本ファイル名：`jartic_1h_road3_tokyo_202607042200.geojson`
- 生データ保存先：`03_data/raw/traffic_simulation/jartic/jartic_1h_road3_tokyo_202607042200.geojson`
- SHA-256：`877a45cdfc8d212b813c3a05c67aad252778e09197ea73c34e6fabe694e03631`
- 出典台帳：`03_data/metadata/traffic_simulation_sources.csv`
- 取得実装：`05_src/traffic_simulation/calibration/fetch_jartic.py`
- 加工実装：`05_src/traffic_simulation/calibration/prepare_jartic.py`

GeoJSON応答はGitから除外する。データの同一性と来歴は、SHA-256、出典台帳、本記録、実装コード、テストによって保持する。

## 最初に実施した手動取得

リポジトリのルートで次を実行した。

```bash
cd /Users/tstakuma/github/research

mkdir -p 03_data/raw/traffic_simulation/jartic

OUT="03_data/raw/traffic_simulation/jartic/jartic_1h_road3_tokyo_202607042200.geojson"

curl --fail-with-body --location --get \
  'https://api.jartic-open-traffic.org/geoserver' \
  --data-urlencode 'service=WFS' \
  --data-urlencode 'version=2.0.0' \
  --data-urlencode 'request=GetFeature' \
  --data-urlencode 'typeNames=t_travospublic_measure_1h' \
  --data-urlencode 'srsName=EPSG:4326' \
  --data-urlencode 'outputFormat=application/json' \
  --data-urlencode 'exceptions=application/json' \
  --data-urlencode "cql_filter=道路種別=3 AND 時間コード=202607042200 AND BBOX(ジオメトリ,139.1,35.45,140.0,35.95,'EPSG:4326')" \
  --output "${OUT}.part"
```

`.part` を正式な原本名へ変更する前に、応答を検証した。

```bash
docker compose run --rm analysis python -c "
import json
p='${OUT}.part'
with open(p, encoding='utf-8') as f:
    data=json.load(f)
assert data.get('type') == 'FeatureCollection', data
features=data.get('features', [])
assert features, 'JARTIC response contains no features'
print('numberReturned:', len(features))
print('reported:', data.get('numberReturned'))
print('geometry:', features[0]['geometry']['type'])
print('time_code:', features[0]['properties']['時間コード'])
"

mv "${OUT}.part" "${OUT}"
shasum -a 256 "${OUT}"
git check-ignore -v "${OUT}"
```

確認結果：

```text
numberReturned: 33
reported: 33
geometry: MultiPoint
time_code: 202607042200
SHA-256: 877a45cdfc8d212b813c3a05c67aad252778e09197ea73c34e6fabe694e03631
```

## 正式な再現用取得手順

今後は手動の `curl` をコピーせず、管理されたPython取得処理を使用する。この処理は、引数とGeoJSONの検証、既存原本の上書き防止、`.part` 経由の保存、SHA-256計算、出典台帳の重複しない更新を行う。

```bash
docker compose run --rm analysis python \
  -m traffic_simulation.calibration.fetch_jartic \
  --layer 1h \
  --road-type 3 \
  --time-code 202607042200 \
  --bbox 139.1 35.45 140.0 35.95
```

原本が既に存在する場合は、再取得せず既存ファイルを検証する。実際の出力は次のとおりだった。

```text
JARTIC snapshot: validated existing
features: 33
sha256: 877a45cdfc8d212b813c3a05c67aad252778e09197ea73c34e6fabe694e03631
```

## 加工手順

```bash
docker compose run --rm analysis python \
  -m traffic_simulation.calibration.prepare_jartic \
  --source-id jartic_1h_road3_tokyo_202607042200
```

加工内容：

- 生データを出典台帳に記録されたSHA-256と照合する。
- 各フィーチャをJARTICの上り・下り別の実測2行へ変換する。
- 小型、大型、車種判別不能の交通量を推定せず転記する。
- 欠損値をゼロへ変換しない。
- 無効な測定値を削除せず、異常理由とともに保持する。
- `sumo_edge_id` と `sumo_direction` は空欄のままにする。
- JARTICからSUMOへの方向対応状態を `unresolved` とする。
- 地物をEPSG:4326のGeoParquetとして保存する。
- 加工コードと生成物のパスを出典台帳へ記録する。

観測地点ごとの2行は、JARTICが提供した上り・下り別の実測値であり、往復合計を均等分割した推定値ではない。JARTICの上り・下りをSUMOの有向エッジへ対応付けるには、別途、路線方向の確認が必要である。

## 加工後の出力

- `03_data/processed/traffic_simulation/calibration/jartic_1h_road3_tokyo_202607042200_observations.parquet`
- `03_data/processed/traffic_simulation/calibration/jartic_1h_road3_tokyo_202607042200_quality_summary.json`

加工後の出力はローカルで生成し、Gitから除外する。出力パスは `traffic_simulation_sources.csv` に記録する。

## 検証手順

専用テストと交通シミュレーション全体の検証を実行した。

```bash
docker compose run --rm analysis pytest -q \
  05_src/traffic_simulation/validation/test_fetch_jartic.py

docker compose run --rm analysis pytest -q \
  05_src/traffic_simulation/validation/test_prepare_jartic.py

docker compose run --rm analysis pytest -q \
  05_src/traffic_simulation/validation

docker compose config --quiet
git diff --check
```

本記録作成時の全テスト結果：

```text
34 passed
```

生成データを再読込し、行数、座標参照系、方向ラベル、SUMO対応状態、品質件数を確認した。

```text
入力フィーチャ数: 33
正規化後の方向別行数: 66
有効行数: 65
無効行数: 1
欠測行数: 0
座標参照系: EPSG:4326
JARTIC方向: up, down
SUMO方向対応状態: unresolved
```

無効な1行は、観測点コード `3310740` のJARTIC下り方向である。`loop_error` と `ultrasonic_error` の両方が設定されているが、無効な方向別測定は1行であり、2件ではない。この行は `valid_measurement=false` として保持し、較正・検証の目標値から除外する。これらは交通事故ではなく、観測機器の異常を表す。

## 失敗と修正の記録

| 日付 | 症状 | 原因 | 修正 | データへの影響 |
|---|---|---|---|---|
| 2026-07-17 | HTTP 400と285バイトのJSONエラー応答 | CQL式の日本語フィールド名と道路種別値を引用符で囲んだ形式を実APIが解釈できなかった | `道路種別=3 AND 時間コード=...` とし、フィールド名と値の引用符を外した。`'EPSG:4326'` の引用符だけを維持した | 失敗した `.part` を削除し、その応答を生データや加工対象として採用しなかった |

受理されたCQL形式は自動回帰テストで固定し、拒否された引用形式が再導入されないようにした。

## 解釈上の限界と次の作業

このスナップショットは、問い合わせBBOX内の33観測地点について、1時間分の方向別交通量を提供する。東京都内の全道路、車両軌跡、配送の発着地、車線別交通量、SUMOエッジIDとの直接対応は提供しない。

次は、最小検証地域について取得日を固定したOpenStreetMapデータを取得し、SUMO道路網を生成する。その後、投影座標上の距離、道路種別、確認済みの路線方向を用いて各有効観測を有向エッジ候補へ対応付け、曖昧な地点を人手で確認する。
