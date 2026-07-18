# 交通シミュレーション用データ取得記録

このディレクトリには、東京交通シミュレーションで使用する第三者データを、どのように取得・検証・加工したかを記録する。

機械可読な出典情報の正本は [`../traffic_simulation_sources.csv`](../traffic_simulation_sources.csv) とする。Markdownの取得記録は、実行コマンド、判断事項、検証結果、失敗内容、復旧手順を補足するものであり、出典台帳の行や改変していない生データの代わりにはならない。

## データ取得ごとに必要な記録

新しく取得したデータを加工する前に、次を実施する。

1. [`_template.md`](_template.md) をコピーし、`YYYYMMDD_<dataset>_acquisition.md` という名前で保存する。
2. 配布者、配布ページ、利用条件、問い合わせ条件または選択条件、取得日を記録する。
3. 取得した原本を、対応する `03_data/raw/traffic_simulation/<source>/` に改変せず保存する。
4. SHA-256を計算し、不変のスナップショットごとに `03_data/metadata/traffic_simulation_sources.csv` へ1行登録する。
5. リポジトリ相対パスを用いて、取得・加工に使用した正確なコマンドを記録する。認証情報や秘密値は記録しない。
6. 分析利用前に、構造、対象範囲、対象期間、欠損、異常フラグ、行数またはフィーチャ数を検証する。
7. 生成データは `03_data/processed/traffic_simulation/` 以下だけに保存し、出力先を出典台帳へ記録する。
8. 生データと生成物がGitから除外され、この記録、出典台帳、実装コード、テストがGit管理対象であることを確認する。
9. 研究上の選択、機械的に決まる値、表示上の選択を分け、残る恣意性とその統制方法を記録する。
10. 実行した構造分析と未実施の交通・最適化分析を区別し、コード上・運用上の既知問題を記録する。

手順を大きく変更した場合は、変更日と理由を取得記録へ追記する。再現性に関係する修正理由を説明できるよう、失敗した取得方法も削除せず残す。

## 取得記録一覧

- [`20260717_jartic_traffic_volume_acquisition.md`](20260717_jartic_traffic_volume_acquisition.md)：JARTICの1時間交通量の取得、正規化、検証記録。
- [`20260717_mlit_n03_2026_tokyo_acquisition.md`](20260717_mlit_n03_2026_tokyo_acquisition.md)：国土数値情報N03東京都版の取得、原本検証、大田区境界生成、固定設定、恣意性の統制記録。
- [`20260717_osm_ota_ward_acquisition.md`](20260717_osm_ota_ward_acquisition.md)：日付固定Geofabrik関東PBFの取得、大田区BBOX抽出、構造分析、実行結果、恣意性、既知問題の記録。
- [`20260718_ota_baseline_open_statistics_acquisition.md`](20260718_ota_baseline_open_statistics_acquisition.md)：未最適化・古典最適化・Aer QAOAの共通需要入力に用いる人口メッシュ、大田区人口、全国人口、全国宅配便取扱実績の取得・検証記録。
- [`20260718_sumo_tokyo_motorized_typemap_design.md`](20260718_sumo_tokyo_motorized_typemap_design.md)：SUMO 1.24.0標準typemapを基準とした東京自動車系typemapの設計、作成、検証、未実施事項をまとめた単一の時系列作業記録。

可視化の生成・閲覧・解釈・表示上の恣意性・不具合履歴は、[`../../../05_src/traffic_simulation/visualization/README.md`](../../../05_src/traffic_simulation/visualization/README.md)を参照する。
