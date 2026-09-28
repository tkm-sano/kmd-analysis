# 環境・再現性・詳細資料の案内

[README](../README.md)に戻る。現在地と次taskは[CURRENT_EXECUTION](../CURRENT_EXECUTION.md)を参照する。本索引は実行許可を与えない。

## 環境と実行方法の資料

- [環境構築の資料](../reproducibility/environment/README.md)：native Conda・SUMO環境の説明。本文の日付付き進捗は当時の記録。個別benchmarkには当該実行authorityのPython環境を使う。
- [統合Research CLI](20260903_20260903_research_cli.md)：`./research commands`など既存CLIの操作資料。科学実行は専用authorityの監督入口・予算・実行許可を優先する。
- [再現性資料の構成](../reproducibility/README.md)：設定・環境・生成物の保存境界。過去段階の実行計画を含むため、現在の次taskはCURRENT_EXECUTIONで確認する。

## 旧READMEの内容の整理

| 内容 | 扱い |
|---|---|
| 研究タイトル、入力が合成条件を含むこと、主張範囲 | READMEに短縮して保持 |
| 問い・仮説、最新の進捗 | 正本から引用・参照 |
| directory案内 | READMEに保持 |
| CLI、環境、instance生成コード | 本索引から参照 |
| 2026-09-15〜27の進捗・規模・旧next task | 下記の当時の仕様・報告へのリンクに置換 |
| 詳細な数値・監査履歴 | summaryおよび正本成果物へ参照 |

既存の成果物は移動・改名・削除していない。以下は旧READMEから継承した参照先であり、名称に「Current」「現行」があっても日付・scopeを確認する。過去時点の未実行記述を最新状態へ転用しない。

## 継承した詳細参照先

- [Minimal EVRP量子resource静的監査](../reproducibility/outputs/traffic_simulation/r24_minimal_evrp_quantum_resource_audit/20260927_v1/MINIMAL_EVRP_QUANTUM_RESOURCE_AUDIT.md)
- [評価規模authority](../reproducibility/outputs/traffic_simulation/r24_evaluation_scale_authority/20260927_v1/EVALUATION_SCALE_AUTHORITY.md)
- [S0 authority](../reproducibility/outputs/traffic_simulation/r24_s0_baseline_authority/20260926_v1/S0_BASELINE_AUTHORITY.md)
- [研究段階ロードマップ](../01_research_design/RESEARCH_STAGE_ROADMAP.md)
- [Classical/Quantum EVRP比較](../01_research_design/CLASSICAL_QUANTUM_EVRP_COMPARISON_PLAN.md)
- [劣化・技術向上条件の比較](../01_research_design/BATTERY_SCENARIO_COMPARISON_PLAN.md)
- [量子化学/材料R&Dと二系統の統合](../01_research_design/BATTERY_QUANTUM_CHEMISTRY_RESEARCH_PIPELINE.md)
- [R24現行研究設計ガイド（日本語）](../docs/ja/R24_CURRENT_RESEARCH_DESIGN_GUIDE_JA.md)
- [R24 instance-generation仕様（日本語）](../docs/ja/R24_INSTANCE_GENERATION_SPECIFICATION_JA.md)
- [R24 benchmark instance suite結果（日本語）](../docs/ja/R24_BENCHMARK_INSTANCE_SUITE_REPORT_JA.md)
- [R23 status](../05_src/traffic_simulation/R23_STATUS.md)
- [Current Research Design](../05_src/traffic_simulation/CURRENT_RESEARCH_DESIGN.md)
- [Research Progress and Decision Record](../05_src/traffic_simulation/RESEARCH_PROGRESS_AND_DECISION_RECORD.md)
- [Frozen instance-generation specification](../reproducibility/outputs/traffic_simulation/r24_instance_generation_specification/20260915_v1/R24_INSTANCE_GENERATION_SPECIFICATION.md)
- [Generated instance-suite report](../reproducibility/outputs/traffic_simulation/r24_benchmark_instance_suite/20260915_v1/R24_BENCHMARK_INSTANCE_SUITE_REPORT.md)
- [Routing compatibility revalidation](../reproducibility/outputs/traffic_simulation/r24_routing_compatibility_revalidation/20260915_v1/R24_ROUTING_COMPATIBILITY_REVALIDATION.md)
- [Methodological capacity specification](../reproducibility/outputs/traffic_simulation/r24_methodological_capacity_specification/20260915_v1/R24_METHODOLOGICAL_CAPACITY_SPECIFICATION.md)
- [Routing Baseline](../05_src/traffic_simulation/specifications/ROUTING_BASELINE_CANONICAL.md)
- [Classical reference validation実行結果](../06_outputs/traffic_simulation/r24_classical_reference_validation/20260915_v1/R24_CLASSICAL_REFERENCE_VALIDATION_RESULTS.md)
- [統合Research CLI](../docs/20260903_20260903_research_cli.md)
- [generator](../05_src/traffic_simulation/r24_instance_generation/generate_r24_benchmark_instance_suite.py)
- [independent validator](../05_src/traffic_simulation/r24_instance_generation/validate_r24_benchmark_instance_suite.py)
- [Markdown参照・archive監査](../docs/ja/MARKDOWN_REFERENCE_AUDIT_20260915.md)

## 成果物の取得と照合

`reproducibility/outputs/traffic_simulation/`の生成物にはGit管理対象外のファイルがある。新規cloneだけで全結果が揃うとは限らない。保存済み成果物を取得し、当該runのmanifest／SHA-256と照合する。欠落を補うために科学実行を自動再開しない。

旧R24 instance suiteの生成コード・独立validatorは上記リンクに保持した。入力条件・出力先・実行許可を確認してから扱う。完了済みstate/samplingの予算を再利用しない。

READMEの文書更新は凍結済み検証一覧のREADMEハッシュとの差分になる。歴史的manifestは書き換えず、次の実行authorityで文書変更の来歴として扱う。科学コード・設定・結果を変更したことにはしない。
