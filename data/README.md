# Data：小規模入力と研究入力の区別

[examples/PROVENANCE.json](examples/PROVENANCE.json)に、既存fixtureからの3つのバイト一致コピーと元SHA256を記録しました。実験データの抽出や再生成はしていません。旧notebooks/fixturesは既存テストの互換参照として保持します。配布コピーを独立に変更せず、一致検査を継続します。

|配布入力|用途・単位|種別|
|---|---|---|
|[three_customers.json](examples/three_customers.json)|デポとA/B/C、4×4 travel秒・distance m、時間窓/サービス秒、需要parcel-equivalent、期待40秒の巡回|既存の合成routing/PUBO fixture。実座標・実道路・現実の配送地点を含まない|
|[speed.csv](examples/speed.csv)|timestamp_s、speed_m_s、4標本の0〜3秒・10m/s|合成軌跡。保存SUMO実験の実測軌跡ではない|
|[speed.json](examples/speed.json)|既存の同じ小規模軌跡・期待電力量等|Controlled-DC検証用の既存証拠|

Battery条件は[正式モデルfreeze](../01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json)を参照し、別の条件表を複製しません。容量20 kWh、初期利用可能18 kWh、比エネルギー180/220/250 Wh/kg。18 kWhは残量会計・負残量判定に使用し、SOCによる停止・充電・再計画は実装していません。

Notebook01/02は共通のrouting fixture、03は速度CSVをconfigs/examples経由で取得します。APIは既存の科学処理を呼びます。欠損時の代替結果はありません。

正式需要、固定割当、OD、SUMO network、NPZ、全軌跡・中間成果・過去実験は原位置の研究保存対象です。Hayate保持台帳（Hayate保存参照: `docs/audits/hayate_github_repository_cleanup_20261009/03_HAYATE_ONLY_FILELIST.csv`、公開ツリー非同梱）と元Release台帳（Hayate保存参照: `reproducibility/release/RELEASE_ARTIFACT_REGISTER.csv`、公開ツリー非同梱）に所在・容量・hashがあります。外部由来の配布条件・個人情報確認が未完了のものを公開可能とは扱いません。Hayate上の保持と独立バックアップは別で、後者は未確認です。

入力分類・GitHub候補はPhase7データ台帳（Hayate保存参照: `docs/audits/quantitative_repository_structural_migration_20261009/51_DATA_DISTRIBUTION_REGISTER.csv`、公開ツリー非同梱）。本コピーもライセンス未適用のためRIGHTS_PENDINGです。`python -B tests/test_distribution_layout.py`で一致を確認できます。

## 外部入力の来歴と加工

以下は保存済み科学結果の生成に使われた研究入力です。上記の合成3顧客・4標本fixtureとは別です。元のPBF、CityGML、統計表、全OD、道路網、全走行軌跡は95ファイル構成に同梱していません。

|提供元・出典|確認できた版・取得記録|研究上の加工・用途|
|---|---|---|
|© OpenStreetMap contributors、[OSM](https://www.openstreetmap.org/copyright)、[Geofabrik関東](https://download.geofabrik.de/asia/japan/kanto.html)|`kanto-260716.osm.pbf`、2026-07-16版、台帳取得2026-07-17|地域抽出、道路属性・形状補正、SUMO道路網、OD・経路・走行評価へ利用。道路データベースは[ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/)|
|国土交通省Project PLATEAU、[3D都市モデル（大田区）（2025年度）](https://www.geospatial.jp/ckan/dataset/plateau-13111-ota-ku-2025)|保存された配布元メタデータはCityGML v5、`13111_ota-ku_pref_2025_citygml_1_op.zip`。2026-08-21の調査・取得記録。需要工程台帳も同名ZIPを記載|建物候補・代表点へ加工し、合成世帯の建物割当と配送地点を作成。研究側の加工であり提供機関の公式需要・配送結果ではない。最終scoped parquetまでの変換履歴は未回復|
|国土交通省、[東京都市圏物資流動調査・個人のモノの受取調査（令和6年度）](https://www.e-stat.go.jp/stat-search/files?layout=dataset&tclass1=000001223521&tclass2=000001234242&toukei=00600520&tstat=000001078042)|表ss521「世帯人数別・世帯構成別宅配受取頻度（回数）・再配達頻度（割合）」、`ss521_r06a.xlsx` / `ss521_R06`。保存記録の取得日2026-08-23、manifest固定08-29|受取経験のある世帯の人数別小計を相対需要強度へ加工。週頻度0.65148273 / 0.93035232 / 1.18813494 / 1.45298673（1人、2人、3〜4人、5人以上）。実注文の記録ではない|
|総務省統計局・e-Stat、2020年国勢調査、2023年住宅・土地統計調査|需要工程記録の表ID `000032163278`、`000040209857`、メッシュ重み `T001141034`。対象は大田区等。全採用セル・加工設定の対応は未確認|合成世帯・住宅区分、需要重み。表名や採用セルの未確認部分を確定出典として補っていない|

PLATEAUの利用条件は[サイトポリシー](https://www.mlit.go.jp/plateau/site-policy/)および各配布データの個別条件によります。出典と研究者による加工を明示し、各地方公共団体等の権利を保持します。上表の年度・ファイル名は保存資料に基づく確認であり、失われた中間parquetの同一性を保証しません。

e-Statの[利用規約](https://www.e-stat.go.jp/terms-of-use)では数値データ等の利用と著作物の条件を区別しています。ここでは数値表を加工した合成需要の出典を示しています。需要工程記録には日量期待値82,023、世帯数384,353、Poisson seed 20260829、建物割当seed 20260830があり、生成件数82,246、建物へ割当済み81,859、39,956地点です。母数の違いを維持します。生成プログラム・全採用統計セルの完全な復元は未確認です。

行政界等の補助入力には国土数値情報N03（2026年）等の記録もあります。全量再現にはこれらの入力と加工履歴が必要です。ここに元データの再配布許諾や復元可能な外部アーカイブの存在を追加で認定するものではありません。

追加確認：保存PLATEAU ZIP内READMEは、政府標準利用規約2.0、CC BY 4.0、ODC BY、ODbLの選択肢を記載しています。これは当該ZIPの条件であり、未回復の中間建物データが同ZIPだけに由来する証明ではありません。

最終道路網の変換記録は、既存lane形状をjunction座標へ接続し、lane lengthを接続後の折線長へ更新したと記録しています。保存config_snapshotの「length維持」および生成器名とは不一致があります。道路網の配布候補は最終hashが一致する実ファイルであり、再生成手順の完全性は未確認です。

## 道路データの取得

[データ専用Release](https://github.com/tkm-sano/kmd-analysis/releases/tag/road-data-20261009-rc1)から[道路データパッケージ](https://github.com/tkm-sano/kmd-analysis/releases/download/road-data-20261009-rc1/kmd-road-network-20261009-rc1.tar.gz)と[SHA256](https://github.com/tkm-sano/kmd-analysis/releases/download/road-data-20261009-rc1/kmd-road-network-20261009-rc1.tar.gz.sha256)を取得できます。14ファイル、48,285,157 bytes。archive SHA256：`e160e4fd83cbb529a81815a780c67ce1462f3e17048bdbccab8f087171ce189b`。データ専用タグは最新版のモデルコードを示しません。

空の領域に展開し、package rootで `python -B VERIFY.py` を実行してください。最終道路XMLのSHA256は `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`。SUMOの実行や全量科学実験の再現ではなく、内容とXML構造の確認です。

公開条件充足を前提とした研究者の指示により提供しました。package内の準備時点のBLOCKED/未承認表示は、配布バイトを維持した過去の記録です。後続の公開承認はRelease説明に記載しています。3集計の法的分類、追加内容/中間DBの提供範囲、PLATEAU中間加工履歴が独立に解決済みであるとは主張しません。元データの来歴を補作せず、研究の数値を維持しています。
