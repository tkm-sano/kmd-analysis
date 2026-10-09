# EVラストマイル配送の定量モデル

必要な配送サービスを充足しながら運用電力量を低減することを問題意識とし、経路計算とBattery性能条件の影響を扱う修士研究のコード・保存結果です。[正式RQ・主仮説](docs/QUANTITATIVE_GUIDE.md#1-research-scope)と評価範囲を区別してください。

- **Path 1**：固定顧客集合の訪問順を道路旅行時間で最適化。R0は3顧客、R1は4顧客で古典計算と理想QAOAを比較します。
- **Path 2**：20 kWh容量固定で180/220/250 Wh/kgをパック・車両質量に反映し、同じ保存軌跡のDC牽引電力量を比較します。

## 研究の流れ

実都市の道路制約、建物の分布、需要量を接続するため、OSM・PLATEAU・公的統計を組み合わせた。固定日の道路データをSUMO網へ加工し、建物と世帯・宅配統計から合成需要を作り、固定割当・時間窓・ODを持つ配送問題を構成した。

**オープンデータ取得 → 道路・建物・統計の加工 → 合成配送需要 → 古典／小規模QAOAの訪問順 → 保存SUMO軌跡 → Battery質量・DC電力量 → 対応比較・最終freeze**という流れである。建物の中間加工など未回復の工程もある。[取得方法・加工・計算を順に読む](docs/QUANTITATIVE_GUIDE.md#0-open-data-to-frozen-results)では、確認済み・再構成・推定・不明を分けている。

Notebook01〜03は合成入力の計算例、04〜05は正式保存結果の参照である。原データから全研究を一括再実行するパイプラインではない。

## 構成

`src/kmd_quantitative/` がRouting・Quantum・Simulation・Battery・Energy・Analysisの正式入口です。`configs/` は設定参照、`data/examples/` は合成入力、`results/indexes/` は凍結結果の参照、`notebooks/` は利用例、`tests/` と `scripts/` は検証、`reproducibility/` は環境・配布情報を管理します。

## インストールと最短実行

Python3.12.3/Linuxで検証しています。repository rootで：

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r reproducibility/environment/requirements-quickstart.lock.txt
.venv/bin/python -B scripts/verify_quickstart.py
```

46テストとNotebook6冊を実行します。全量科学実験は起動しません。[環境・依存範囲](docs/QUANTITATIVE_GUIDE.md#10-quickstart-and-dependencies)。

## Notebook

|順序|内容|
|---|---|
|[00_start_here](notebooks/00_start_here.ipynb)|依存・利用範囲|
|[01_classical_routing](notebooks/01_classical_routing.ipynb)|3顧客の古典経路計算|
|[02_pubo_qaoa](notebooks/02_pubo_qaoa.ipynb)|正式PUBOと教材用QAOA|
|[03_battery_energy](notebooks/03_battery_energy.ipynb)|質量・軌跡・Controlled-DC|
|[04_quantitative_results](notebooks/04_quantitative_results.ipynb)|R0/R1・Method×Battery保存結果|
|[05_scale_analysis](notebooks/05_scale_analysis.ipynb)|古典6規模の保存結果|

## 結果と再現範囲

Method×Batteryは共通64ブロックでT=0が59、非ゼロ5（percentage points）。古典6規模は3/4/5/25/99/125顧客、468論理・460異なるインスタンスです。遅延136停止/116経路、帰還期限超過4経路の記録を保持します。[正式結果・比較条件](docs/QUANTITATIVE_GUIDE.md#7-analysis-and-frozen-results)を参照してください。

小規模計算と保存結果の検証が対象です。教材QAOAの0/64・NOT_ACQUIREDは正式Protocol V2の科学実験とは別です。量子実機・量子優位は実証していません。18 kWhは残量会計に使用しますが、SOC停止・充電・再計画は実装していません。充電を含む主仮説の検証完了、全量SUMO再現、物流全体の省エネルギーは主張しません。

既存GitHubリポジトリは公開済みです。正式APIの構造再編・文書統合も反映済みです。[凍結原本との関係](docs/QUANTITATIVE_GUIDE.md#11-reproducibility-and-verification)と[非配布資料・来歴の限界](docs/QUANTITATIVE_GUIDE.md#14-limitations-and-provenance)を確認してください。

## ライセンス・データ帰属

[Apache-2.0](LICENSE)はTAKUMA SANOが公開・適用権限を持つ自作コード・Notebookの自作部分に適用します。文書・fixture・研究結果・第三者著作物へ一括適用しません。[引用情報](CITATION.cff)を参照してください。

© OpenStreetMap contributors（ODbL 1.0）、国土交通省Project PLATEAU、e-Stat等の研究入力を加工しています。[出典・利用条件・来歴の留保・道路データRelease](docs/QUANTITATIVE_GUIDE.md#13-data-attribution-and-licensing)に詳細を集約しています。帰属表示やデータ提供の実施と、すべての権利条件の独立した確認完了は区別しています。

[Quantitative Research Guide — 詳細ガイド](docs/QUANTITATIVE_GUIDE.md)
