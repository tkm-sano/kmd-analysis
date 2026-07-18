# 大田区共通需要用公開統計：取得・検証記録

## 記録状態

- 記録日：`2026-07-18`
- 実施者：`Codex`
- 状態：`processed`
- 出典台帳ID：`estat_census_2020_500m_jgd2011_mesh5339`、`estat_t001141_definition`、`ota_population_20240401`、`statistics_bureau_population_20241001`、`mlit_parcel_2024`
- 関連仕様：`05_src/traffic_simulation/demand/baseline_demand_and_comparator.md`

## 配布元と選択条件

| ID | 配布者 | データセット・選択条件 | 配布ページ・取得URL | 利用条件 |
|---|---|---|---|---|
| `estat_census_2020_500m_jgd2011_mesh5339` | 総務省統計局・e-Stat | 令和2年国勢調査、500mメッシュ、JGD2011、人口及び世帯、表`T001141`、第1次地域区画`5339` | <https://www.e-stat.go.jp/gis/statmap-search?page=1&type=1&toukeiCode=00200521&toukeiYear=2020&aggregateUnit=H&serveyId=H002005112020&statsId=T001141&datum=2011>、<https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001141&code=5339&downloadType=2> | <https://www.e-stat.go.jp/terms-of-use> |
| `estat_t001141_definition` | 総務省統計局・e-Stat | 表`T001141`定義書 | <https://www.e-stat.go.jp/help/data-definition-information/downloaddata/T001141.pdf> | e-Stat利用規約 |
| `ota_population_20240401` | 大田区・東京都オープンデータ | 令和6年度「大田区の面積・人口・世帯数」、2024年4月1日 | <https://catalog.data.metro.tokyo.lg.jp/dataset/t131113d0000000166/resource/fcedcfc6-0950-4f31-8c84-d45a3eee453b>、<https://www.opendata.metro.tokyo.lg.jp/ota/R6/131113_R6_01_ootakunomenseki_jinkou_setaisuu.xlsx> | CC BY 4.0 |
| `statistics_bureau_population_20241001` | 総務省統計局 | 人口推計2024年10月1日現在、第1表 | <https://www.stat.go.jp/data/jinsui/2024np/index.html>、<https://www.stat.go.jp/data/jinsui/2024np/zuhyou/05k2024-1.xlsx> | 総務省統計局サイトポリシー |
| `mlit_parcel_2024` | 国土交通省 | 令和6年度宅配便等取扱個数 | <https://www.mlit.go.jp/report/press/jidosha04_hh_000341.html>、<https://www.mlit.go.jp/report/press/content/001906814.pdf> | 国土交通省ウェブサイト利用規約 |

認証、アカウント、APIキーは不要であった。生データはGitへ登録しない。

## 保存先とSHA-256

| 原本 | ローカル保存先 | SHA-256 |
|---|---|---|
| `tblT001141H5339.zip` | `03_data/raw/traffic_simulation/population/estat_2020_500m_jgd2011/tblT001141H5339.zip` | `8a8b47563ffe88ec1afb5a17b8d29ac987b40df65498bec4c2fcf1829777f67d` |
| `T001141.pdf` | `03_data/raw/traffic_simulation/population/estat_2020_500m_jgd2011/T001141_definition.pdf` | `f9f0ee00aa0dc820a7e8345809b21d5f7044eeb009d3a5e97694f098166db80e` |
| `131113_R6_01_ootakunomenseki_jinkou_setaisuu.xlsx` | `03_data/raw/traffic_simulation/population/ota_2024/131113_R6_01_ootakunomenseki_jinkou_setaisuu.xlsx` | `63b37310b4bf5dd6b17d4c3436983e4ac45b84fdaca395a51a4efccec496f83e` |
| `05k2024-1.xlsx` | `03_data/raw/traffic_simulation/population/japan_2024/05k2024-1.xlsx` | `0fb515bfb5bec519f306cbe22a81f170d65826ad472a173df2a485ffbe86b96e` |
| `001906814.pdf` | `03_data/raw/traffic_simulation/demand_proxy/mlit_parcel_2024/mlit_parcel_2024_details.pdf` | `854d8fbffdb745a3fbcbbb79329d79193dd2d2495fe1b717fdd56ea1ef7ebd74` |

## 取得手順

```bash
curl --fail-with-body --location \
  --output 03_data/raw/traffic_simulation/population/estat_2020_500m_jgd2011/tblT001141H5339.zip.part \
  'https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001141&code=5339&downloadType=2'
mv 03_data/raw/traffic_simulation/population/estat_2020_500m_jgd2011/tblT001141H5339.zip.part \
  03_data/raw/traffic_simulation/population/estat_2020_500m_jgd2011/tblT001141H5339.zip

curl --fail-with-body --location \
  --output 03_data/raw/traffic_simulation/population/estat_2020_500m_jgd2011/T001141_definition.pdf.part \
  'https://www.e-stat.go.jp/help/data-definition-information/downloaddata/T001141.pdf'
mv 03_data/raw/traffic_simulation/population/estat_2020_500m_jgd2011/T001141_definition.pdf.part \
  03_data/raw/traffic_simulation/population/estat_2020_500m_jgd2011/T001141_definition.pdf

curl --fail-with-body --location \
  --output 03_data/raw/traffic_simulation/population/ota_2024/131113_R6_01_ootakunomenseki_jinkou_setaisuu.xlsx.part \
  'https://www.opendata.metro.tokyo.lg.jp/ota/R6/131113_R6_01_ootakunomenseki_jinkou_setaisuu.xlsx'
mv 03_data/raw/traffic_simulation/population/ota_2024/131113_R6_01_ootakunomenseki_jinkou_setaisuu.xlsx.part \
  03_data/raw/traffic_simulation/population/ota_2024/131113_R6_01_ootakunomenseki_jinkou_setaisuu.xlsx

curl --fail-with-body --location \
  --output 03_data/raw/traffic_simulation/population/japan_2024/05k2024-1.xlsx.part \
  'https://www.stat.go.jp/data/jinsui/2024np/zuhyou/05k2024-1.xlsx'
mv 03_data/raw/traffic_simulation/population/japan_2024/05k2024-1.xlsx.part \
  03_data/raw/traffic_simulation/population/japan_2024/05k2024-1.xlsx

curl --fail-with-body --location \
  --output 03_data/raw/traffic_simulation/demand_proxy/mlit_parcel_2024/mlit_parcel_2024_details.pdf.part \
  'https://www.mlit.go.jp/report/press/content/001906814.pdf'
mv 03_data/raw/traffic_simulation/demand_proxy/mlit_parcel_2024/mlit_parcel_2024_details.pdf.part \
  03_data/raw/traffic_simulation/demand_proxy/mlit_parcel_2024/mlit_parcel_2024_details.pdf
```

## 生データ検証結果

- e-Stat ZIP：配布名`tblT001141H5339.zip`、約2.3 MB。正式CSV名は`tblT001141H5339.txt`、CP932、データ16,671行。列`T001141001`は定義書上の人口総数である。
- ZIPには正式CSVのほか`.nfs00000000108003a400000807`が含まれていた。配布ZIP自体を改変せず保存し、加工時は正式名`tblT001141H5339.txt`だけを明示抽出する。`.nfs*`を自動選択しない。
- 大田区XLSX：シート`1 `の人口は`736652`、世帯数は`414304`、基準日は2024年4月1日。
- 全国人口XLSX：第1表の総人口は`123802`千人、基準日は2024年10月1日。
- 国土交通省PDF：令和6年度宅配便取扱個数は`5,031,470,000`個。メール便は対象外。
- 国土交通省の定義では消費者間、企業から消費者、企業間等を区別せず対象要件を満たす宅配便を全国集計し、都道府県別集計を行っていない。したがって個人宅需要または大田区観測値として扱わない。

## 主計算の再検証

```text
q_base = 5,031,470,000 / 123,802,000 / 365
       = 0.111345933951539499... 宅配便個数相当／人・日

736,652 * q_base
       = 82,023.204937269... 宅配便個数相当／日

初期整数需要 = 82,023 宅配便個数相当／日
```

## 恣意性と限界

| 判断 | 統制・限界 |
|---|---|
| 500m・JGD2011を採用 | 道路網との空間対応に必要な粒度と現行測地系を事前選択。250m等へ結果を見て変更しない。 |
| 第1次地域区画5339を取得 | 大田区境界を包含する標準地域区画。N03による後段抽出前の原本であり、大田区だけの統計ではない。 |
| 2020分布を2024総数へ調整 | 年次の異なる公開統計を使う推定。2024年のメッシュ実測人口とは表現しない。 |
| 全国宅配便個数を人口換算 | 個人宅・地域別の観測値ではない。人口比例の基準シナリオに限定する。 |
| 受取頻度統計を不使用 | 単位の異なる「回／世帯・週」と直接結合しない。 |

## 加工実行と検証結果

使用設定と実装は次のとおりである。

- 設定：`reproducibility/config/traffic_simulation/baseline_demand.yml`
- 加工：`05_src/traffic_simulation/demand/prepare_baseline_demand.py`
- テスト：`05_src/traffic_simulation/validation/test_prepare_baseline_demand.py`
- 出力：`03_data/processed/traffic_simulation/demand/ota_ward_baseline_demand_2024_500m.parquet`
- 品質要約：`03_data/processed/traffic_simulation/validation/ota_ward_baseline_demand_2024_500m_quality_summary.json`

2026年7月18日に次をDocker内で実行した。

```bash
docker compose build analysis
docker compose run --rm analysis \
  pytest -q 05_src/traffic_simulation/validation/test_prepare_baseline_demand.py
docker compose run --rm analysis \
  python -m traffic_simulation.demand.prepare_baseline_demand
docker compose run --rm analysis \
  pytest -q 05_src/traffic_simulation/validation
```

結果は次のとおりである。

| 項目 | 結果 |
|---|---:|
| 大田区境界と正の面積で交差する500mメッシュ | 191 |
| 全面包含メッシュ | 122 |
| 境界メッシュ | 69 |
| 面積按分した2020年国勢調査人口 | 747,271.088683 |
| 中心点包含法による2020年人口 | 736,737 |
| 面積按分法－中心点包含法 | 10,534.088683 |
| 2024年配分人口合計 | 736,652 |
| 1日分の整数合成需要 | 82,023宅配便個数相当 |
| 加工出力の境界外面積 | `3.874458584446135e-10 m2` |
| 加工出力SHA-256 | `e7caeb262665ba3396834bb54e2dff296b3cbbd02af6922e906eb683829f5048` |
| 合成需要テスト | 13件成功 |
| 交通シミュレーション検証群 | 124件成功 |

全面包含の判定はJGD2011地理座標上の包含関係を用いる。投影後の面積比だけで判定すると、長い境界線と分割されたメッシュ辺の再投影近似の違いによって、全面包含でも約`1e-5`の人工的な面積差が生じたためである。境界メッシュの按分は平面直角座標系IX（EPSG:6677）の面積を用いる。

面積按分法と中心点包含法の差は10,534人相当であり、境界処理が無視できないことを示す。ただし、これは真の境界メッシュ人口との差ではなく、二つの空間配分規則の差である。

## Gitと次の作業

- 生データ：`.gitignore`の`03_data/raw/**`で除外する。
- Git管理：本記録、出典台帳、計算仕様。
- 完了：500mメッシュコード復元、N03交差、面積按分、2024年人口比例調整、人口・需要の最大剰余配分。
- 次：集約配送点の規則を別途確定し、宅配便個数相当を配送停止回数と混同しない形で配送問題へ接続する。
- 未実施：集約配送点、拠点、車両、未最適化走行、古典最適化、QAOA、`P_eq`算出。

## 失敗と修正

| 日付 | 症状 | 原因 | 修正 | データへの影響 |
|---|---|---|---|---|
| 2026-07-18 | `analysis`コンテナでXLSXを読み込むと`ModuleNotFoundError: openpyxl` | 現行analysisイメージに`openpyxl`が含まれていない | `docker/analysis/requirements.txt`へ`openpyxl==3.1.5`を固定し、イメージを再構築した | 原本取得・SHA-256への影響なし。修正後にDocker内加工・テスト成功 |
| 2026-07-18 | 全面包含の合成テストが`partial`になった | 投影時に同一曲線を異なる線分長で近似したため、面積比が`0.999990...`になった | 全面包含は地理座標上の位相関係で判定し、その場合の交差面積をメッシュ全面積へ固定した | 境界メッシュの面積按分は変更せず、全面包含の人工的目減りだけを除去 |
| 2026-07-18 | 初回加工が`registered filename mismatch`で停止した | 台帳の配布元ファイル名と、説明的なローカル保存名をコードが同一視した | `original_filename`と`local_raw_path`を独立項目として扱い、保存パスとSHA-256を検証するよう修正した | ハッシュ一致を再確認後に加工成功。原本変更なし |
