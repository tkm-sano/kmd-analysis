# 分析環境（VS Code + Jupyter）

このプロジェクトは、素材関連産業群別の主要都市流入就業者数を対象に、
古典計算資源条件と量子計算資源条件の差が、材料探索性能→軽量化率→燃費改善率→燃料費・電力費→都市流動へ
どう波及するかを検証するための最小実行環境である。

## 前提
- 生データは `data/raw/` に置く
- 整形済みデータは `data/processed/` に保存する
- Notebook は `notebooks/`、関数化したコードは `src/` に置く
- 現在の raw データは **テンプレート + ダミー値** である
- 実証版では、公的統計とレビュー結果で raw データを置き換える

## セットアップ
1. VS Code でこのフォルダを開く
2. Python 拡張と Jupyter 拡張を有効にする
3. 仮想環境を作成する
   - Windows: `py -3.11 -m venv .venv`
   - macOS/Linux: `python3.11 -m venv .venv`
4. 仮想環境を有効化する
   - Windows: `.venv\Scripts\activate`
   - macOS/Linux: `source .venv/bin/activate`
5. 依存関係を入れる
   - `pip install -r requirements.txt`

## 実行順
- `notebooks/01_load_clean.ipynb`
- `notebooks/02_build_benchmark_assumptions.ipynb`
- `notebooks/03_translate_to_engineering.ipynb`
- `notebooks/04_simulate_city_flows.ipynb`
- `notebooks/05_anova.ipynb`

## 一括実行
```bash
python src/run_pipeline.py
```

## 主要入力表
- `data/raw/city_master.csv`
- `data/raw/industry_group_master.csv`
- `data/raw/compute_resource_conditions.csv`
- `data/raw/energy_price.csv`
- `data/raw/base_inflow_2025.csv`
- `data/raw/city_condition_index.csv`
- `docs/literature_registry.csv`

## 主要出力
- `data/processed/benchmark_panel.parquet`
- `data/processed/engineering_panel.parquet`
- `data/processed/inflow_simulated.parquet`
- `outputs/tables/anova_results.csv`

## 注意
- `compute_resource_conditions.csv` は観測データではなく、文献拘束的仮定表として使う
- `city_condition_index.csv` は都市条件の補助指数であり、必要に応じて使用する
- 産業群は `metal`, `chem_polymer`, `inorganic` の三群に固定している
