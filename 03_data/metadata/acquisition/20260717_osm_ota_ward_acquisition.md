# Geofabrik関東OSM PBF・大田区BBOX抽出：取得・検証記録

## 記録状態

- 記録日：2026-07-17
- 実施者：研究環境管理者（Codex支援）
- 状態：`processed`（PBF原本取得・大田区BBOX抽出・検証完了）
- 出典台帳ID：`osm_geofabrik_kanto_20260716`
- 地域ID：`ota_ward`
- 地域設定版：`1`
- 関連する実装計画：`05_src/traffic_simulation/implementation_plan.md`

## 配布元と利用条件

- 配布者：Geofabrik GmbH / OpenStreetMap contributors
- データセット：Geofabrik OpenStreetMap Kantō regional extract
- 配布ページ：<https://download.geofabrik.de/asia/japan/kanto.html>
- 日付固定ダウンロードURL：<https://download.geofabrik.de/asia/japan/kanto-260716.osm.pbf>
- 配布ファイル名：`kanto-260716.osm.pbf`
- OSMデータ時点：`2026-07-16T20:21:30Z`
- ライセンス：Open Database License（ODbL）1.0
- ライセンスURL：<https://opendatacommons.org/licenses/odbl/1-0/>
- アクセス要件：認証、APIキー、アカウントは不要
- 正式取得方式：日付固定PBFのみ。Overpass APIとブラウザーの手動エクスポートは使用しない

Geofabrikの配布物では、OpenStreetMap投稿者のユーザー名、ユーザーID、changeset IDが除かれている。再配布や公開成果物では、ODbLとOpenStreetMapの帰属表示条件を確認する。

## 選択条件

- 取得日・タイムゾーン：2026-07-17 JST
- 原本の地理的範囲：Geofabrik関東地方抽出
- 道路抽出対象：`ota_ward` version 1のN03行政界から生成した外接BBOX
- BBOXの座標系：`EPSG:4326`
- 西端：`139.652974773`
- 南端：`35.528198081`
- 東端：`139.826027782`
- 北端：`35.613210171`
- 抽出方式：`osmium extract --strategy complete_ways --set-bounds`
- 選択理由：大田区のSUMO道路網を、同一の固定PBF原本から再生成できるようにするため

BBOXはN03行政界から機械的に生成し、手入力、丸め、バッファ追加、感度分析による変更をしていない。BBOXはPBF切り出し範囲であり、研究結果の集計範囲ではない。分析対象の正本はN03大田区行政界ポリゴンである。

## 保存先と命名

### 不変の生データ

- 保存先：`03_data/raw/traffic_simulation/osm/kanto-260716.osm.pbf`
- ファイルサイズ：476,772,780バイト
- SHA-256：`aef890f28b652ed7bd2b0d77e86f263219b479fe3eedbdd8610dcfc1572c420d`

### 加工後のPBF

- 保存先：`03_data/processed/traffic_simulation/road_network/osm_extracts/osm_ota_ward_20260716.osm.pbf`
- ファイルサイズ：12,218,967バイト
- SHA-256：`10d554a13e89b815ca416c272d23d9477d52e312fa3d299f466fb3c01cf9d041`

### 来歴を保持するファイル

- 出典台帳：`03_data/metadata/traffic_simulation_sources.csv`
- 取得・抽出実装：`05_src/traffic_simulation/network/fetch_osm.py`
- 単体テスト：`05_src/traffic_simulation/validation/test_fetch_osm.py`
- 地域設定：`reproducibility/config/traffic_simulation/study_areas.yml`
- 品質サマリー：`03_data/processed/traffic_simulation/validation/osm_ota_ward_20260716_quality_summary.json`

生PBF、抽出PBF、品質サマリーはGitへ登録しない。出典台帳、取得記録、設定、コード、テストをGit管理する。

## 事前環境確認

リポジトリのルートで次を実行した。

```bash
docker compose build analysis

docker compose run --rm analysis \
  python -m pytest 05_src/traffic_simulation/validation -q

df -h /System/Volumes/Data
docker system df
```

確認結果：

```text
Docker analysis build: 成功
osmium-tool: 1.15.0
libosmium: 2.19.0
取得前のDocker内テスト: 77 passed
取得前のホスト空き容量: 10 GiB
取得後のホスト空き容量: 9.6 GiB
Dockerイメージ回収可能量: 2.41 GB
Dockerビルドキャッシュ回収可能量: 2.081 GB
```

約477MBの原本と抽出物を保存できる空き容量があることを確認し、既存のDockerイメージやキャッシュは削除せずに取得した。

## 正式な取得・抽出手順

正式処理は、原本の取得、PBF形式検証、SHA-256計算、N03境界読込、BBOX生成、ローカル抽出、道路要素検証、品質サマリー生成、台帳登録を一つの管理された処理として行う。

```bash
docker compose run --rm analysis \
  python -m traffic_simulation.network.fetch_osm \
  --region ota_ward \
  --snapshot-date 20260716
```

処理上の規則：

1. `--snapshot-date`から日付固定Geofabrik URLを生成する。
2. ダウンロード中は `kanto-260716.osm.pbf.part` として保存する。
3. Content-Length、空ファイル、PBF形式、要素数、SHA-256を検証する。
4. 検証成功後だけ `.part` を不変のPBF原本へ変更する。
5. `study_areas.yml`と登録済みN03原本から大田区行政界を再生成する。
6. 大田区行政界をEPSG:4326へ変換し、BBOXを機械生成する。
7. `complete_ways`でBBOXと交差するwayの参照nodeを保持して抽出する。
8. 抽出PBFのヘッダーBBOX、node、way、relation、`highway` way数を検証する。
9. SHA-256と品質サマリーを生成し、出典台帳を原子的に更新する。
10. 既存の原本、抽出物、品質サマリーとハッシュが一致する場合だけ再利用する。

成功時の出力：

```text
raw PBF: validated existing
BBOX extract: created
acquisition bbox: 139.652974773,35.528198081,139.826027782,35.613210171
raw sha256: aef890f28b652ed7bd2b0d77e86f263219b479fe3eedbdd8610dcfc1572c420d
extract sha256: 10d554a13e89b815ca416c272d23d9477d52e312fa3d299f466fb3c01cf9d041
raw path: 03_data/raw/traffic_simulation/osm/kanto-260716.osm.pbf
extract path: 03_data/processed/traffic_simulation/road_network/osm_extracts/osm_ota_ward_20260716.osm.pbf
quality summary: 03_data/processed/traffic_simulation/validation/osm_ota_ward_20260716_quality_summary.json
registry: 03_data/metadata/traffic_simulation_sources.csv
```

この出力が `validated existing` となっているのは、初回実行で原本PBFの取得と検証が完了し、その後に記載したBBOXヘッダー精度の修正を行って抽出処理を再実行したためである。原本を再ダウンロードしたものではない。

## SHA-256の独立検証

管理スクリプト内の計算とは別に、ホストの `shasum` で再計算した。

```bash
shasum -a 256 \
  03_data/raw/traffic_simulation/osm/kanto-260716.osm.pbf \
  03_data/processed/traffic_simulation/road_network/osm_extracts/osm_ota_ward_20260716.osm.pbf
```

```text
aef890f28b652ed7bd2b0d77e86f263219b479fe3eedbdd8610dcfc1572c420d  kanto-260716.osm.pbf
10d554a13e89b815ca416c272d23d9477d52e312fa3d299f466fb3c01cf9d041  osm_ota_ward_20260716.osm.pbf
```

再計算値、品質サマリー、出典台帳の3か所が一致した。

## PBF構造と品質サマリーの検証

```bash
docker compose run --rm analysis \
  osmium fileinfo --extended --json --no-crc \
  03_data/processed/traffic_simulation/road_network/osm_extracts/osm_ota_ward_20260716.osm.pbf
```

品質サマリーの主要結果：

| 項目 | 関東PBF原本 | 大田区BBOX抽出 |
|---|---:|---:|
| node | 59,799,475 | 1,709,568 |
| way | 9,603,616 | 323,393 |
| relation | 72,056 | 2,373 |
| `highway` way | 未集計 | 40,880 |
| ファイルサイズ | 476,772,780 bytes | 12,218,967 bytes |

抽出PBFについて次を確認した。

- PBFとして正常に読める。
- nodeとwayが0件ではない。
- `highway`タグを持つwayが40,880件存在する。
- オブジェクトがnode、way、relationの順に整列している。
- 複数versionを含む履歴PBFではない。
- ヘッダーBBOXがN03由来の取得範囲と、PBF表現精度の範囲内で一致する。
- 抽出戦略が `complete_ways` である。

`complete_ways`は、BBOXと交差するwayを途中で切断せず、そのwayが参照するBBOX外nodeも保持する。そのため、`fileinfo`が全nodeから計算する実データBBOXはヘッダーBBOXより広くなる。実データBBOXを研究対象範囲として使用せず、取得範囲はヘッダーBBOX、分析範囲はN03行政界ポリゴンから判定する。

## 出典台帳の検証

`03_data/metadata/traffic_simulation_sources.csv` に次を1行だけ登録した。

```text
source_id: osm_geofabrik_kanto_20260716
provider: Geofabrik GmbH / OpenStreetMap contributors
source_url: https://download.geofabrik.de/asia/japan/kanto-260716.osm.pbf
observation_start: 2026-07-16T20:21:30Z
observation_end: 2026-07-16T20:21:30Z
original_filename: kanto-260716.osm.pbf
sha256: aef890f28b652ed7bd2b0d77e86f263219b479fe3eedbdd8610dcfc1572c420d
status: processed
```

台帳には、原本から抽出PBFと品質サマリーへの加工対応も記録した。同じ `source_id` を再実行しても行を重複させず、原本SHA-256が変わる場合は更新を拒否する。

## 自動テスト

`test_fetch_osm.py`では、外部通信と実PBFを使用せず、次をモックで検証する。

- 日付固定URL、原本名、出典台帳ID
- 正式CLIに任意BBOX、任意URL、取得方式切替が存在しないこと
- N03由来BBOXを丸めず `osmium` へ渡すこと
- `.part`からの原子的な確定と失敗時の清掃
- 登録済みSHA-256不一致と既存生成物の不整合の拒否
- `complete_ways`と`--set-bounds`の使用
- PBFヘッダーの座標表現精度だけを許容すること
- 壊れたPBF、空PBF、`highway` wayが0件のPBFの拒否
- 品質サマリーと出典台帳の原子的更新

実行コマンド：

```bash
docker compose run --rm analysis \
  python -m pytest 05_src/traffic_simulation/validation/test_fetch_osm.py -q

docker compose run --rm analysis \
  python -m pytest 05_src/traffic_simulation/validation -q
```

## 失敗と修正

| 日付 | 症状 | 原因 | 修正 | データへの影響 |
|---|---|---|---|---|
| 2026-07-17 | 初回抽出後に `PBF extract bounds do not match the governed BBOX` で停止 | `osmium 1.15.0`がPBFヘッダーBBOXを小数7桁で保存し、N03由来の小数9桁以上の値との`1e-9度`比較を超えた | 実測ヘッダー値を確認し、PBFの表現差だけを許容する上限を`5e-8度`に固定した。丸め後BBOXを受理するテストと、大きな差を拒否するテストを追加した | 原本PBFは検証後の不変ファイルとして保持。失敗した抽出`.part`は削除され、正式抽出物、品質サマリー、台帳は成功した再実行だけから生成された。取得範囲は拡張していない |

比較した値：

```text
N03由来BBOX:
  139.652974773,35.528198081,139.826027782,35.613210171
PBFヘッダーBBOX:
  139.6529748,35.5281981,139.8260278,35.6132102
最大差:
  約0.000000029度
許容上限:
  0.00000005度
```

この許容上限はPBFヘッダーの数値表現検証にだけ使用し、`osmium extract`へ渡すBBOX、行政界、道路網、分析範囲を変更しない。

## Git除外と来歴の確認

```bash
git check-ignore -v \
  03_data/raw/traffic_simulation/osm/kanto-260716.osm.pbf \
  03_data/processed/traffic_simulation/road_network/osm_extracts/osm_ota_ward_20260716.osm.pbf \
  03_data/processed/traffic_simulation/validation/osm_ota_ward_20260716_quality_summary.json

git status --short
git diff --check
```

- 生PBFがGit除外対象：はい
- 抽出PBFがGit除外対象：はい
- 品質サマリーがGit除外対象：はい
- 出典台帳を更新済み：はい
- 取得記録がGit管理対象：はい
- 取得・抽出コードとテストがGit管理対象：はい

## ルール決定、実行、分析の整理

### ルールとして決定したこと

| 対象 | 決定したルール | 判断理由 |
|---|---|---|
| 地域 | `ota_ward` version 1とN03行政界を分析範囲の正本とする | 道路や分析結果を見て対象範囲を動かさないため |
| 取得範囲 | N03行政界から機械生成したEPSG:4326の外接BBOXを使う | 手入力座標、丸め、任意バッファを排除するため |
| 原典 | 日付固定Geofabrik関東PBFを使う | 同じ原本SHA-256から再加工できるため |
| 取得方式 | PBF方式だけを正式方式とし、Overpass等へ自動切替しない | API制限や取得時刻による結果変動を避けるため |
| 保存 | 原本は不変、生データと生成物はGit除外、来歴だけをGit管理する | 原典保全とリポジトリ容量を両立するため |
| 抽出 | `complete_ways`と`--set-bounds`を使う | 境界でwayの参照nodeを欠落させないため |
| 検証 | 形式、要素数、道路要素、BBOX、SHA-256、台帳整合を確認する | ダウンロード成功だけを取得完了としないため |
| 再実行 | 既存ファイルを上書きせず、ハッシュ一致時だけ再利用する | 同名の異なる原本への置換を防ぐため |

### 実行したこと

1. Docker解析イメージへ`osmium-tool 1.15.0`を導入し、ビルドを確認した。
2. 取得前に自動テストとディスク空き容量を確認した。
3. `kanto-260716.osm.pbf`を日付固定URLから取得した。
4. 原本の形式、データ時点、サイズ、要素数、SHA-256を確認した。
5. N03原本と地域設定を再検証し、大田区行政界からBBOXを生成した。
6. BBOX抽出PBFを生成し、PBF構造と`highway` wayの存在を確認した。
7. 品質サマリーを生成し、出典台帳を1行だけ更新した。
8. ホスト側の`shasum`でもSHA-256を独立再計算した。
9. Git除外、`.part`残存、テスト結果を確認した。
10. 登録済みPBFからレビュー用HTML地図を生成し、ブラウザで道路レイヤー、凡例、レイヤー操作を確認した。

### 実施した分析と未実施の分析

今回実施した分析は、データ取得・入力品質に関する次の構造分析である。

- 原本と抽出物のSHA-256照合
- PBFのnode、way、relation件数の集計
- 抽出物に含まれる`highway` way件数の確認
- PBFヘッダーBBOXとN03由来BBOXの整合確認
- 出典台帳、品質サマリー、実ファイルの来歴整合確認
- 自動車道路候補とOSM信号位置の表示用集計

次は実施していない。

- SUMOネットワークへの変換と接続性分析
- 実交通量、速度、渋滞、旅行時間の分析
- JARTIC観測点と道路エッジの対応付け
- 交通需要の生成、較正、妥当性検証
- 配送訪問順序と道路経路の最適化
- 古典最適化とQiskit Aer QAOAの比較

したがって、今回の件数や可視化だけから「大田区の実交通環境を再現できた」とは判断しない。

## 恣意性とその統制

| 判断箇所 | 恣意性の有無 | 統制・解釈 |
|---|---|---|
| 大田区の採用 | 研究設計上の選択 | N03属性条件と地域設定版を固定し、道路を見て境界を変更しない |
| 2026-07-16 PBFの採用 | 取得日依存の選択 | 2026-07-17に利用できる直近日付固定原本として、データ時点と取得日を分けて記録した |
| 関東地方PBF | 配布単位の選択 | 大田区だけの任意編集原本を作らず、配布原本を不変保存した |
| `complete_ways` | 技術的な選択 | 参照完全性を優先した。BBOX外nodeを大田区内データとして集計しない |
| BBOX | 恣意的設定ではない | N03行政界から無丸め・無バッファで機械生成した |
| `5e-8`度の許容値 | 実装上の固定判断 | 実測したPBFヘッダーの小数表現差だけを許容する。分析・取得範囲は変更しない |
| 表示道路の分類、色、線幅、初期表示 | 表示上の選択 | データ採否やSUMO変換規則ではない。可視化READMEで明示する |
| 自動車道路候補の表示フィルター | 表示上の選択 | 歩道等を地図から除くが、原本PBFは保持する。SUMO採否は後続工程で別に固定する |

感度分析を行わず現在の枠取りを固定する方針のため、範囲変更が必要になった場合は既存設定を上書きせず、地域設定のversionを上げて別の実験条件として扱う。

## コード上・運用上の問題点

- `fetch_osm.py`は外部配布URL、HTTP応答、Geofabrikの日付別アーカイブの存続に依存する。指定日のファイルがなければ別日や別方式へ切り替えず失敗する。
- 約477MBの原本全体の形式走査とSHA-256計算には時間とディスクI/Oが必要である。
- `complete_ways`は道路以外のwayとBBOX外参照nodeも保持するため、抽出PBF自体を大田区道路だけのデータとみなせない。
- 現在の品質条件はPBF構造と`highway` wayの存在を中心とし、自動車通行可否、道路接続、車線、turn restriction、信号現示の妥当性までは保証しない。
- PBFヘッダーの座標精度に対する許容値は`osmium`の出力表現に依存する。ツール更新時は実値とテストを再確認する必要がある。
- ファイル確定と各メタデータ更新は個別には原子的だが、全成果物を一つのファイルシステム取引として確定する実装ではない。途中失敗時はハッシュを確認して再実行する。
- 通常CIでは大容量PBFの実取得を行わず、ネットワークと実PBFをモックする。実配布物を使う統合確認は手動の再現手順として残る。
- 可視化では当初、1個のFolium `GeoJsonTooltip`を複数道路レイヤーへ再利用したため、生成JavaScriptが未定義レイヤーを参照し、凡例以降の初期化が停止した。道路レイヤーごとに別インスタンスを生成するよう修正し、ブラウザコンソールと画面で再確認した。
- レビュー用HTMLは多数の道路形状を埋め込むため約11MBあり、ブラウザによっては描画に時間がかかる。可視化固有の限界は`05_src/traffic_simulation/visualization/README.md`に記録する。

## 解釈上の限界と次の作業

- OSMは参加者が整備する地理データであり、道路、車線数、制限速度、通行条件、信号位置等の完全性と時点精度は場所によって異なる。
- BBOX内の道路が取得できても、信号現示、サイクル、オフセット、実交通量、実旅行時間はPBFに含まれない。
- `complete_ways`で保持したBBOX外node・wayを、大田区内の実績として集計しない。
- BBOX外へ出る配送経路は現在の道路計算範囲では表現しない。
- 次は抽出PBFから自動車通行可能道路を選び、全オプションを固定した `netconvert` でSUMO道路網を生成する。
- SUMO変換後、ノード、エッジ、レーン、接続性、主要道路の切断、信号位置、SUMO読込可否を検証する。
