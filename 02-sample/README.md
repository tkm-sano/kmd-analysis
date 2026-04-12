# 分析環境パッケージ

本フォルダは、量子計算による材料探索効率の改善が都市への就業流入に及ぼす影響を評価するための**統合分析環境**である。研究計画書で示された二段階構成、すなわち「文献レビューに基づく技術ショックの構成」と「一般化交通費弾力性を推定する重力モデル」を一つの作業環境に統合してある。

## この環境に含めたもの

1. 現行の研究計画書・精査報告書・モデル説明・実装仕様書  
2. 公式統計と主要文献の取得一覧  
3. 上流文献抽出表、比較表、下流流動表のテンプレート  
4. 動作確認用のデモ入力・デモ出力  
5. 重力モデル実行スクリプト、および入力検証・実行ラッパー  
6. データ管理、レビュー手順、実行手順を記した補助文書  

## 重要な留意点

- 本環境に含まれる `data/demo/` の数値は**動作確認用の例示値**であり、実証値ではない。
- `sources/` には公式データ源と文献の**取得先一覧**を入れてある。公開統計や論文本文そのものは原則として同梱していない。
- 実証分析では、`data/templates/` の各テンプレートを用いて実データを整備し、`data/actual_input/` に配置してから実行する。
- 本研究は静学的反実仮想比較であり、時間外挿を前提としない。

## 基本的な使い方

### 一　まず構造を確認する
- `docs/` で研究計画とモデル仕様を確認する。
- `sources/` で文献・データ取得先を確認する。
- `config/project_settings.yaml` で対象都市、対象産業群、問題類型を確認する。

### 二　上流入力を整備する
- 文献抽出段階では `data/templates/benchmark_evidence_extraction_template.csv` を用いる。
- 実行用の正規化済み入力は `data/templates/benchmark_evidence_model_input_template.csv` を用いる。
- 問題類型ごとの比較表は `data/templates/benchmark_computer_template.csv` に対応する。

### 三　下流入力を整備する
- 起点地域×都市×産業群の流動表は `data/templates/od_flow_template.csv` を用いる。
- 翻訳パラメータは `data/templates/translation_parameters_template.csv` を用いる。
- 制御パラメータは `data/templates/model_controls_template.csv` を用いる。

### 四　デモ実行する
```bash
python src/run_analysis_environment.py demo
```

### 五　実データで実行する
1. `data/actual_input/` に次の4ファイルを置く。  
   - `benchmark_evidence.csv`  
   - `od_flow.csv`  
   - `translation_parameters.csv`  
   - `model_controls.csv`
2. 入力を検証する。  
```bash
python src/validate_inputs.py --input_dir data/actual_input
```
3. 実行する。  
```bash
python src/run_analysis_environment.py actual --input_dir data/actual_input --output_dir data/output/actual_run
```

## ディレクトリの要点

- `docs/` 研究計画、精査報告書、モデル説明、実装仕様
- `sources/` 公式データ源・主要文献の取得一覧
- `config/` シナリオ設定、都市定義、問題類型定義、DMP、レビュー手順
- `data/demo/` 動作確認用入力
- `data/templates/` 実データ整備用テンプレート
- `data/seeds/` 初期種データ
- `data/output/demo_run/` デモ出力
- `src/` 実行コード
- `workflow/` 実行補助ファイル

## 推奨作業順序

1. `sources/official_data_sources.csv` と `sources/core_literature_sources.csv` を確認する。  
2. `config/review_protocol_template.md` に従って文献抽出規則を固定する。  
3. `data/templates/` を埋めて `data/actual_input/` に実データを配置する。  
4. `src/validate_inputs.py` で検証する。  
5. `src/run_analysis_environment.py` で実行する。  
6. 出力を `data/output/` で確認する。  
