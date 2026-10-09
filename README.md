# EVラストマイル配送の定量モデル

既存の正式Python実装と保存結果を、Notebook6冊から小規模に利用するための構成です。公開条件充足を前提とした研究者の公開判断と、独立に検証された来歴・権利の範囲は区別しています。権限を持つ自作コード・Notebookへのライセンス適用範囲は末尾に明示します。

## 研究目的・正式RQ

必要な配送サービスを充足しながら、その実現に伴うエネルギー消費を低減することが上位の問題意識です。本配布物はEVラストマイル配送の限定された定量モデルと保存結果を扱います。

正式RQ（原文引用）：

> 量子技術の進展は、電気自動車配送の経路計算とバッテリー性能の変化を通じて、ラストマイル配送の運用電力量にどのような影響を与えるか。

正式主仮説（原文引用）：

> 同一の充電を考慮した電気自動車配送問題において、古典計算を用いた場合と比較して、量子計算を用いた場合の方が、バッテリー性能の違いによる電気自動車配送の運用電力量の差が大きくなる。

正本はHayate保存の `01_research_design/RESEARCH_QUESTION_AND_HYPOTHESIS.md`（SHA256 `abe729fc925372782bc62c5a4f3e597c09b5c214acfd31c3ec912f3efb85cb33`）。上記はその文言の引用であり、新しいRQ・仮説ではありません。**充電を考慮した正式主仮説と、今回配布する無充電・固定軌跡の評価範囲は同一ではありません。主仮説の検証完了を主張しません。**

## Path 1：経路計算

固定された顧客集合・単一車両・単一巡回の訪問順を、道路旅行時間最小化として比較します。R0は3顧客、R1は4顧客。古典側は小規模全列挙、正式Candidate Cは古典的な全順列可行性事前評価を利用するPUBOとp=1理想QAOAです。実機・計算速度優位の実証ではありません。保存SUMO軌跡をDC牽引電力量へ接続します。道路上の最短経路と顧客訪問順を区別します。

## Path 2：比エネルギー・質量・電力量

名目容量20 kWhを固定し、比エネルギー180/220/250 Wh/kgの違いをパック質量へ反映します。車両質量の変化は**バッテリーパックが軽くなる結果**であり、車体自体の軽量化ではありません。同じ保存軌跡を使う感度比較です。初期利用可能18 kWhは残量会計・負残量判定に使いますが、SOCによる走行停止・充電・再計画は実装していません。量子材料計算も実施していません。

## 保存結果と配布内容の読み方

|対象|区別する内容|
|---|---|
|正式実装|srcのAPIが凍結sourceへ接続する。全量科学実験のworker/入力がすべて配布されるわけではない|
|Notebook01〜03|合成小規模入力による計算。02の教材QAOAは正式Protocol V2の再実験ではない|
|Notebook04〜05|正式freeze・既存集計の読込み/表示。新しい科学結果の生成ではない|
|Method×Battery|共通64比較ブロック。T=D_R1−D_R0、D=Classical saving%−QAOA saving%、単位pp。仮説のkWh差とは別|
|古典6規模|3/4/5/25/99/125顧客。条件・解法が異なり、規模単独の因果効果や大規模QAOA結果ではない|

配送・エネルギーの[評価範囲と用語](docs/quantitative/GITHUB_AND_HAYATE.md)、[正式集計の母数・条件](docs/quantitative/ANALYSIS_API_AND_FROZEN_RESULTS.md)、[最終freeze](01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_RESULT_FREEZE.json)を参照してください。

## 実行

Python3.12.3/Linuxの[環境手順](reproducibility/environment/QUICKSTART_ENVIRONMENT.md)に従います。

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r reproducibility/environment/requirements-quickstart.lock.txt
.venv/bin/python -m pip check
.venv/bin/python -B scripts/verify_quickstart.py
```

[Notebook一覧](notebooks/README.md)の00→01→02→03→04→05を使用します。45件の軽量API/契約テストと6冊の既定セルを実行し、正式な全量実験は起動しません。教材QAOAのNOT_ACQUIREDを正式QAOA再現成功と扱いません。

## 正式API・入力・結果

- [Model Index](docs/quantitative/QUANTITATIVE_MODEL_INDEX.md)：routing / quantum / simulation / battery / energy / analysis。
- [Quantum API](docs/quantitative/QUANTUM_API_AND_FROZEN_PROTOCOL.md)：Candidate Cと凍結scienceへの接続。
- [Simulation API](docs/quantitative/SIMULATION_AND_TRAJECTORY_API.md)：保存軌跡。
- [Battery/Energy API](docs/quantitative/BATTERY_AND_ENERGY_API.md)：固定20kWhで比エネルギー変更→パック質量→車両質量→DC牽引電力量。
- [Analysis API](docs/quantitative/ANALYSIS_API_AND_FROZEN_RESULTS.md)：R0/R1・Method×Battery・古典6規模の保存結果。
- [設定](configs/README.md)、[合成fixture](data/README.md)、[結果Index](results/README.md)。

正式sourceとfreezeは原位置・元バイトのまま保持します。必要な旧R0処理も含みます。道路旅行時間最小化と電力量評価、経路取得と配送充足、保存結果表示と新規実験を区別します。量子優位性・量子材料計算・全配送充足・システム全体の省エネを実証したものではありません。

## 配布境界

小規模実行に必要なsource・fixture・集計を含みます。全OD、SUMO network、native環境、過去の全ログ、元の13,360件Release ManifestはHayate研究保存対象です。これらの独立保存・全量再現は別課題です。文書中の「Hayate保存参照」はGitHub同梱を意味しません。既存Git履歴の容量・内容は現行treeを縮減しても残ります。

GitHub Actionsの実行状況はリポジトリのActionsタブで確認してください。今回の公開は研究者の公開条件充足の前提に基づく実行判断です。[引用情報](CITATION.cff)の著者TAKUMA SANOは確認済みですが、所属機関/共同研究者を含む権利の承認は別途必要です。

## 利用条件・ライセンスの適用範囲

既存の[LICENSE](LICENSE)はApache License, Version 2.0（SPDX: `Apache-2.0`）です。TAKUMA SANOが公開・ライセンス適用権限を持つ**自作コードおよびNotebookの自作部分**には、今回の承認に基づき同ライセンスを適用します。これは将来の適用候補ではなく、この範囲への適用宣言です。LICENSE本文は変更していません。

対象候補の43パスは[配布Manifest](reproducibility/release/GITHUB_DISTRIBUTION_MANIFEST.json)の `license_scope` で特定しています。ただし43ファイルの全内容について単独著作・権利処理完了を認定したものではありません。共同研究・所属機関・第三者由来の部分、Notebookの保存研究結果や外部データはこの宣言から除外し、該当権利者の承認・元の利用条件を別途確認します。今回の公開判断を、第三者由来部分の独立した権利確認完了や新たな許諾とは扱いません。

研究結果21件、fixture9件、文書等22件へApache-2.0を一括適用しません。第三者ライブラリは各自のライセンスに従います。適用対象の利用・改変・再配布では、LICENSEの提供、改変表示、必要な著作権・帰属表示と該当NOTICEの保持等、LICENSEの条件に従ってください。元のLICENSE付録の`[yyyy]`/`[name of copyright owner]`は記入例であり、全成果物の権利者の認定ではありません。

既存の公開Git履歴もこの宣言によって新たに権利処理済みにはなりません。公開判断の前提と独立検証の限界は、下記のデータRelease説明にも記録しています。

## 研究入力の出典と加工表示

保存結果は外部公開データを用いた研究上の加工・シミュレーション・集計を含みます。道路入力は © OpenStreetMap contributors、[OpenStreetMap](https://www.openstreetmap.org/copyright) のデータベースは [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/) で提供されています。詳細な出典、加工内容、未同梱の原データは [dataの来歴](data/README.md#外部入力の来歴と加工)、保存結果ごとの範囲と未充足条件は [resultsの帰属表示](results/README.md#外部入力由来の保存結果) を参照してください。

帰属表示の追加だけで公開条件がすべて充足したとは判断していません。改変道路データに関する提供条件と、一部の加工履歴の確認が残ります。自作コード・NotebookのApache-2.0適用を、外部データや研究結果へ一括拡張するものではありません。

## 道路データの取得

[データ専用Release](https://github.com/tkm-sano/kmd-analysis/releases/tag/road-data-20261009-rc1)から[道路データパッケージ](https://github.com/tkm-sano/kmd-analysis/releases/download/road-data-20261009-rc1/kmd-road-network-20261009-rc1.tar.gz)と[SHA256](https://github.com/tkm-sano/kmd-analysis/releases/download/road-data-20261009-rc1/kmd-road-network-20261009-rc1.tar.gz.sha256)を取得できます。14ファイル、48,285,157 bytes。archive SHA256：`e160e4fd83cbb529a81815a780c67ce1462f3e17048bdbccab8f087171ce189b`。データ専用タグは最新版のモデルコードを示しません。

空の領域に展開し、package rootで `python -B VERIFY.py` を実行してください。最終道路XMLのSHA256は `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`。SUMOの実行や全量科学実験の再現ではなく、内容とXML構造の確認です。

公開条件充足を前提とした研究者の指示により提供しました。package内の準備時点のBLOCKED/未承認表示は、配布バイトを維持した過去の記録です。後続の公開承認はRelease説明に記載しています。3集計の法的分類、追加内容/中間DBの提供範囲、PLATEAU中間加工履歴が独立に解決済みであるとは主張しません。元データの来歴を補作せず、研究の数値を維持しています。
