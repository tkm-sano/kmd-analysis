<a id="research-environment"></a>

# 研究環境

<a id="platform"></a>

## 実行基盤

- 基本ソフト：macOS。
- プロジェクトの最上位：リポジトリの識別ファイルから判定する。保存する付随情報と実行コードはリポジトリ相対パスを使い、取得先の場所に依存しない。
- 実行環境：必要に応じてプロジェクト内に`.venv`を作成する。これは版管理対象外とする。
- 提出資料の監査用パッケージ仕様：`legacy/non_sumo_route_proxy_analysis/reproducibility/requirements-lock.txt`。
- 版管理：Git。

<a id="required-python-packages"></a>

## 必要な実行パッケージ

主要パッケージはpandas、NumPy、SciPy、scikit-learn、Matplotlib、GeoPandas、Shapely、NetworkX、Seaborn、Jupyter、nbformat、nbclient。提出資料の監査環境は`legacy/non_sumo_route_proxy_analysis/reproducibility/requirements-lock.txt`で固定している。

<a id="reproduction-commands"></a>

## 再現用コマンド

```bash
python -m venv .venv
.venv/bin/pip install -r legacy/non_sumo_route_proxy_analysis/reproducibility/requirements-lock.txt
.venv/bin/jupyter nbconvert --to notebook --execute legacy/non_sumo_route_proxy_analysis/reproducibility/quantum_transport_reproducibility_audit_revised.ipynb --output-dir /tmp --output quantum_transport_reproducibility_audit_executed.ipynb --ExecutePreprocessor.timeout=1200
.venv/bin/python legacy/non_sumo_route_proxy_analysis/src/constraint_evaluation/run_tokyo_synthetic_evrp_analysis.py --reproduce
.venv/bin/python legacy/non_sumo_route_proxy_analysis/src/visualization/render_tokyo_synthetic_evrp_outputs.py --reproduce
```

<a id="known-dependencies-and-risks"></a>

## 既知の依存関係とリスク

- リポジトリはクラウド同期対象のデスクトップ領域の外へ移動済み。新しく取得した作業領域では、ハッシュ値を計算する前に、実データを伴わない`dataless`ファイルがないことを確認する。
- 地理空間処理には、地理情報処理パッケージまたはローカル環境から提供される、互換性のあるGDAL・GEOS・PROJの依存ライブラリーが必要。
- 通信が必要となるのは、明示的なデータ更新スクリプトを使う場合のみ。計算の再現には保持済みの固定した加工入力を使う。未加工の原資料は版管理で配布しない。
- 乱数の種と想定条件のパラメーターは、ノートブックと分析コードで明示する。
