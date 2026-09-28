# 環境・再現性・詳細資料の案内

[研究案内](../README.md)に戻る。現在地と次の作業は[現在の実行状況](../00_project_management/CURRENT_EXECUTION.md)を参照する。本索引は実行許可を与えない。

## 環境と実行方法の資料

- [研究案内](../reproducibility/environment/README.md)：標準の環境管理ツール・交通シミュレーターの環境の説明。本文の日付付き進捗は当時の記録。個別ベンチマークには当該実行の正本の実行環境を使う。
- [統合研究用コマンド操作](20260903_20260903_research_cli.md)：`./research commands`など既存コマンドの操作資料。科学実行は専用の実行・判定の正本の監督入口・予算・実行許可を優先する。
- [研究案内](../reproducibility/README.md)：設定・環境・生成物の保存境界。過去段階の実行計画を含むため、現在の次の作業は現在の実行状況で確認する。

## 旧研究案内の内容の整理

| 内容 | 扱い |
|---|---|
| 研究タイトル、入力が合成条件を含むこと、主張範囲 | 研究案内に短縮して保持 |
| 問い・仮説、最新の進捗 | 正本から引用・参照 |
| ディレクトリ案内 | 研究案内に保持 |
| コマンド操作、環境、問題例生成コード | 本索引から参照 |
| 2026-09-15〜27の進捗・規模・旧次の作業 | 下記の当時の仕様・報告へのリンクに置換 |
| 詳細な数値・監査履歴 | まとめおよび正本成果物へ参照 |

既存の成果物は移動・改名・削除していない。以下は旧研究案内から継承した参照先であり、名称に「現行」とあっても日付・範囲を確認する。過去時点の未実行記述を最新状態へ転用しない。

## 継承した詳細参照先

- [最小構成の電気自動車配送経路問題の量子計算資源に関する静的監査](../reproducibility/outputs/traffic_simulation/r24_minimal_evrp_quantum_resource_audit/20260927_v1/MINIMAL_EVRP_QUANTUM_RESOURCE_AUDIT.md)
- [評価規模の正本](../reproducibility/outputs/traffic_simulation/r24_evaluation_scale_authority/20260927_v1/EVALUATION_SCALE_AUTHORITY.md)
- [第0段階の実行・判定の正本](../reproducibility/outputs/traffic_simulation/r24_s0_baseline_authority/20260926_v1/S0_BASELINE_AUTHORITY.md)
- [研究段階の見通し](../01_research_design/RESEARCH_STAGE_ROADMAP.md)
- [電気自動車配送経路問題における古典・量子計算の比較](../01_research_design/CLASSICAL_QUANTUM_EVRP_COMPARISON_PLAN.md)
- [劣化・技術向上条件の比較](../01_research_design/BATTERY_SCENARIO_COMPARISON_PLAN.md)
- [量子化学/材料研究開発と二系統の統合](../01_research_design/BATTERY_QUANTUM_CHEMISTRY_RESEARCH_PIPELINE.md)
- [R24現行研究設計ガイド（日本語）](../docs/ja/R24_CURRENT_RESEARCH_DESIGN_GUIDE_JA.md)
- [R24 問題例生成仕様（日本語）](../docs/ja/R24_INSTANCE_GENERATION_SPECIFICATION_JA.md)
- [R24 ベンチマーク 問題例群結果（日本語）](../docs/ja/R24_BENCHMARK_INSTANCE_SUITE_REPORT_JA.md)
- [R23 状況](../05_src/traffic_simulation/R23_STATUS.md)
- [現行研究設計](../05_src/traffic_simulation/CURRENT_RESEARCH_DESIGN.md)
- [研究進捗と意思決定記録](../05_src/traffic_simulation/RESEARCH_PROGRESS_AND_DECISION_RECORD.md)
- [固定済み問題例生成仕様](../reproducibility/outputs/traffic_simulation/r24_instance_generation_specification/20260915_v1/R24_INSTANCE_GENERATION_SPECIFICATION.md)
- [生成済み問題例群の報告](../reproducibility/outputs/traffic_simulation/r24_benchmark_instance_suite/20260915_v1/R24_BENCHMARK_INSTANCE_SUITE_REPORT.md)
- [経路計算の互換性再検証](../reproducibility/outputs/traffic_simulation/r24_routing_compatibility_revalidation/20260915_v1/R24_ROUTING_COMPATIBILITY_REVALIDATION.md)
- [方法論上の容量仕様](../reproducibility/outputs/traffic_simulation/r24_methodological_capacity_specification/20260915_v1/R24_METHODOLOGICAL_CAPACITY_SPECIFICATION.md)
- [経路計算の基準](../05_src/traffic_simulation/specifications/ROUTING_BASELINE_CANONICAL.md)
- [古典参照解の検証実行結果](../06_outputs/traffic_simulation/r24_classical_reference_validation/20260915_v1/R24_CLASSICAL_REFERENCE_VALIDATION_RESULTS.md)
- [統合研究用コマンド操作](../docs/20260903_20260903_research_cli.md)
- [生成器](../05_src/traffic_simulation/r24_instance_generation/generate_r24_benchmark_instance_suite.py)
- [独立検証器](../05_src/traffic_simulation/r24_instance_generation/validate_r24_benchmark_instance_suite.py)
- [文書参照・保管履歴の監査](../docs/ja/MARKDOWN_REFERENCE_AUDIT_20260915.md)

## 成果物の取得と照合

`reproducibility/outputs/traffic_simulation/`の生成物には版管理対象外のファイルがある。新規複製だけで全結果が揃うとは限らない。保存済み成果物を取得し、当該実行の成果物一覧／SHA-256と照合する。欠落を補うために科学実行を自動再開しない。

旧R24 問題例群の生成コード・独立検証器は上記リンクに保持した。入力条件・出力先・実行許可を確認してから扱う。完了済み量子状態/標本抽出の予算を再利用しない。

研究案内の更新は凍結済み検証一覧の研究案内のハッシュ値との差分になる。歴史的成果物一覧は書き換えず、次の実行の正本で文書変更の来歴として扱う。科学コード・設定・結果を変更したことにはしない。
