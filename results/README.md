# Results：凍結結果への参照入口

[indexes/CANONICAL_RESULTS.json](indexes/CANONICAL_RESULTS.json)はAnalysis APIが扱う13ファイルの相対パス・hash・サイズ・schemaを示す参照Indexです。正式な結果は既存の原位置に保持します。summariesへの重複コピーや新しい集計は作っていません。Indexは新しい研究結果・freezeではありません。

|対象|正式な参照|
|---|---|
|Path 1 最終R0/R1|[FINAL_QUANTITATIVE_RESULT_FREEZE.json](../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_RESULT_FREEZE.json)|
|Path 2条件・質量|[CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json](../01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json)|
|Method×Battery|[最終4条件summary](../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_SCALE_METHOD_BATTERY_SUMMARY.csv)|
|古典6規模|[route summary](../01_research_design/methodology/MATCHED_CLASSICAL_ROUTE_SCALE_SUMMARY.csv)、[Battery summary](../01_research_design/methodology/MATCHED_CLASSICAL_BATTERY_SCALE_SUMMARY.csv)|
|配送充足診断|[LOGISTICS_SERVICE_SCOPE.csv](../01_research_design/scenario_evaluation/quantitative_scale_boundary_synthesis_20261008/LOGISTICS_SERVICE_SCOPE.csv)|

APIの既存 `root=` に復元したrepository rootを指定できます。相対配置とhashを維持してください。Hayate絶対パスは不要です。必要な表がない場合はFileNotFoundError、改変はValueErrorとなり、別結果で補いません。保存証拠内部の絶対パスは来歴文字列で、自動アクセスしません。

```python
from kmd_quantitative.analysis import method_battery as mb, scale_analysis as scale
print(mb.summary())
print(scale.service_diagnostics())
# 同じ相対構造で復元した別rootを明示することも可能
# print(mb.summary(root=restored_repository_root))
```

実行環境と相対importは[Analysis API案内](../docs/quantitative/ANALYSIS_API_AND_FROZEN_RESULTS.md)。Notebook04/05のAPIは変更していません。小規模保存表の表示に全軌跡やSUMOは不要ですが、生成過程の完全再実行にはそれらが必要です。

母数・単位：R0=3顧客、R1=4顧客、理想QAOAの経路取得と配送充足は別。Method×Battery共通64、各条件ゼロ59・非ゼロ5、Tはpercentage points。古典6規模は468論理/460実体、遅延136停止/116経路、帰還超過4を除外しません。DCは保存区間の車両牽引Whのみで、社会全体のエネルギーや実業務の全配送需要充足を実証したものではありません。

[GitHub Distribution Manifest](../reproducibility/release/GITHUB_DISTRIBUTION_MANIFEST.json)は配布技術候補を管理します。13,360ファイルの元Release Manifestと区別し、権利未確定のため公開完了とは扱いません。

## 外部入力由来の保存結果

以下の13件について、[入力データの出典・加工表示](../data/README.md#外部入力の来歴と加工)を関連する帰属表示とします。© OpenStreetMap contributors。道路入力は[OpenStreetMap](https://www.openstreetmap.org/copyright)データベースに由来し、そのデータベースは[ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/)で利用できます。PLATEAU・e-Stat等の出典と加工は上記data文書に記載しています。

これらは原道路網・元統計表そのものではありません。研究結果のCSVであることだけでDerivative Databaseと判定せず、逆に統計的集計であることだけでODbLの条件がなくなるとも判断していません。改変道路データからのProduced Workに該当する公開では、ODbL §4.3の表示と、§4.4・§4.6の改変データまたは全変更方法・追加内容の提供条件を確認する必要があります。最終道路網は下記Releaseから取得できます。最終XMLの提供が中間DBを含む全義務を満たすか、また一部集計の法的分類は独立に確定していません。帰属表示と提供の実施を、法的判断の確定と混同しません。

|保存ファイル|内容・公開前の残件|
|---|---|
|[CLASSICAL_SCALE_X_BATTERY_SCALE_SUMMARY.csv](../01_research_design/methodology/CLASSICAL_SCALE_X_BATTERY_SCALE_SUMMARY.csv)|集計値。道路データの提供条件の充足を要確認|
|[MATCHED_CLASSICAL_BATTERY_SCALE_SUMMARY.csv](../01_research_design/methodology/MATCHED_CLASSICAL_BATTERY_SCALE_SUMMARY.csv)|集計・シミュレーション結果。道路データの提供条件の充足を要確認|
|[MATCHED_CLASSICAL_ROUTE_SCALE_SUMMARY.csv](../01_research_design/methodology/MATCHED_CLASSICAL_ROUTE_SCALE_SUMMARY.csv)|集計・道路OD派生結果。道路データの提供条件の充足を要確認|
|[MATCHED_CLASSICAL_TRAJECTORY_VALIDATION.json](../01_research_design/methodology/MATCHED_CLASSICAL_TRAJECTORY_VALIDATION.json)|シミュレーション検証/来歴。道路データの提供条件の充足を要確認|
|[FINAL_QUANTITATIVE_RESULT_FREEZE.json](../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_RESULT_FREEZE.json)|統合集計/来歴。道路データの提供条件の充足を要確認|
|[FINAL_QUANTITATIVE_STUDY_REPORT.md](../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_STUDY_REPORT.md)|研究説明。道路データの提供条件の充足を要確認|
|[FINAL_SCALE_METHOD_BATTERY_SUMMARY.csv](../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_SCALE_METHOD_BATTERY_SUMMARY.csv)|集計値。道路データの提供条件の充足を要確認|
|[COMMON_MATCHED_POPULATION.csv](../01_research_design/scenario_evaluation/matched_r0_r1_common_protocol_scale_method_battery_20261008/COMMON_MATCHED_POPULATION.csv)|研究内部識別子・可用性。原データ複製の個別問題は識別されない。研究全体の入力条件の確認とは区別|
|[DIRECT_METHOD_ENERGY_SCALE_COMPARISON.csv](../01_research_design/scenario_evaluation/matched_r0_r1_common_protocol_scale_method_battery_20261008/DIRECT_METHOD_ENERGY_SCALE_COMPARISON.csv)|ブロック別シミュレーション出力。道路データの提供条件の充足を要確認|
|[SCALE_METHOD_BATTERY_MATCHED_CONTRASTS.csv](../01_research_design/scenario_evaluation/matched_r0_r1_common_protocol_scale_method_battery_20261008/SCALE_METHOD_BATTERY_MATCHED_CONTRASTS.csv)|ブロック別派生指標。道路データの提供条件の充足を要確認|
|[CLASSICAL_QUANTUM_SCALE_COMPARISON.csv](../01_research_design/scenario_evaluation/quantitative_scale_boundary_synthesis_20261008/CLASSICAL_QUANTUM_SCALE_COMPARISON.csv)|計算/研究設計の集計。原データ複製の個別問題は識別されない。研究全体の入力条件の確認とは区別|
|[LOGISTICS_SERVICE_SCOPE.csv](../01_research_design/scenario_evaluation/quantitative_scale_boundary_synthesis_20261008/LOGISTICS_SERVICE_SCOPE.csv)|シミュレーション時刻診断集計。道路データの提供条件の充足を要確認|
|[SCALE_INSTANCE_COMPARISON.csv](../01_research_design/scenario_evaluation/quantitative_scale_boundary_synthesis_20261008/SCALE_INSTANCE_COMPARISON.csv)|座標範囲・識別子・集計値。bboxの元建物加工履歴および道路データ提供条件を要確認|

座標範囲を持つSCALE_INSTANCE_COMPARISONは、建物代表点のmin/maxを含みます。全建物集合ではありませんが公開地理情報との照合可能性は残ります。科学的数値・freezeは変更していません。本節は条件整理であり、研究結果へのApache-2.0一括適用ではありません。

## 道路データの取得

[データ専用Release](https://github.com/tkm-sano/kmd-analysis/releases/tag/road-data-20261009-rc1)から[道路データパッケージ](https://github.com/tkm-sano/kmd-analysis/releases/download/road-data-20261009-rc1/kmd-road-network-20261009-rc1.tar.gz)と[SHA256](https://github.com/tkm-sano/kmd-analysis/releases/download/road-data-20261009-rc1/kmd-road-network-20261009-rc1.tar.gz.sha256)を取得できます。14ファイル、48,285,157 bytes。archive SHA256：`e160e4fd83cbb529a81815a780c67ce1462f3e17048bdbccab8f087171ce189b`。データ専用タグは最新版のモデルコードを示しません。

空の領域に展開し、package rootで `python -B VERIFY.py` を実行してください。最終道路XMLのSHA256は `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`。SUMOの実行や全量科学実験の再現ではなく、内容とXML構造の確認です。

公開条件充足を前提とした研究者の指示により提供しました。package内の準備時点のBLOCKED/未承認表示は、配布バイトを維持した過去の記録です。後続の公開承認はRelease説明に記載しています。3集計の法的分類、追加内容/中間DBの提供範囲、PLATEAU中間加工履歴が独立に解決済みであるとは主張しません。元データの来歴を補作せず、研究の数値を維持しています。
