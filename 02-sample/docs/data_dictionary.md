# データ辞書

## 一　主要入力ファイル

### 1. benchmark_evidence_extraction_template.csv
文献から直接抽出した値を記録する段階の表である。研究計画書が想定した `budget_raw` と `budget_unit` を含む。

### 2. benchmark_evidence_model_input_template.csv
実行スクリプトが直接読む正規化済み入力である。`cost_index` を含み、古典条件と量子条件の比較に必要な列を持つ。

### 3. benchmark_computer_template.csv
問題類型ごとの比較統合表である。古典条件と量子条件の対応づけ後に作成する。

### 4. od_flow_template.csv
起点地域×都市×産業群の流動表である。下流のPPML重力モデルが直接読む。

### 5. translation_parameters_template.csv
材料探索改善度を軽量化率および効率改善率へ翻訳するためのパラメータ表である。

### 6. model_controls_template.csv
性能改善度の統合重み、品質閾値未達時のペナルティ、既定シナリオなどを管理する。

## 二　主要出力ファイル

### 1. benchmark_comparison.csv
文献入力から生成された比較表である。

### 2. industry_translation.csv
産業群別の改善度、軽量化率、効率改善率を格納する。

### 3. coefficient_estimates.csv
PPML重力モデルから推定された係数表である。

### 4. results_by_od.csv
起点地域×都市×産業群単位の反実仮想結果である。

### 5. results_by_city_industry.csv
都市×産業群単位へ集計した主要結果である。
