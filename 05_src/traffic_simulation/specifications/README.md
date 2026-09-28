<a id="交通シミュレーション仕様index"></a>

# 交通シミュレーション仕様索引

## 現行仕様

- [経路計算の基準](ROUTING_BASELINE_CANONICAL.md): directed 経路計算 費用と到達可能性の正本
- [R23 Reduced Problem](R23_REDUCED_PROBLEM_CANONICAL.md): R23 縮約した訪問順序問題の正本
- [R20 量子近似最適化アルゴリズム subproblem 仕様](R20_QAOA_SUBPROBLEM_SPEC.md): supporting coefficientと制約なし二値二次最適化仕様
- [R23 実装 取り決め](R23_IMPLEMENTATION_CONTRACT.md): R23実装契約
- [R24 問題例生成 仕様](../../../reproducibility/outputs/traffic_simulation/r24_instance_generation_specification/20260915_v1/R24_INSTANCE_GENERATION_SPECIFICATION.md): 固定済み問題例生成正本
- [R24 問題例生成仕様（日本語）](../../../docs/ja/R24_INSTANCE_GENERATION_SPECIFICATION_JA.md): 上記英語正本の日本語案内

<a id="r23-current-authority"></a>

## R23 現行の正本

[R23_STATUS.md](../R23_STATUS.md)を参照してください。Accepted 参照先の補完、最終 clean-実行 根拠、正式 ベンチマーク、限界への現行 索引です。このディレクトリに残る過去の実行 設計、実行制御、remediation 取り決めは固定手順と再現性を支える記録であり、その過去の記録 状況は現行の正本ではありません。

[R23 過去の記録 archive](../../../reproducibility/archive/traffic_simulation/r23/README.md)の確認や正本-生成 出力を、現在状況の正本として使用しないでください。

<a id="r24-current-authority"></a>

## R24 現行の正本

- [Current Research Design](../CURRENT_RESEARCH_DESIGN.md)
- [R24現行研究設計ガイド（日本語）](../../../docs/ja/R24_CURRENT_RESEARCH_DESIGN_GUIDE_JA.md)
- [Generated suite report](../../../reproducibility/outputs/traffic_simulation/r24_benchmark_instance_suite/20260915_v1/R24_BENCHMARK_INSTANCE_SUITE_REPORT.md)
- [Generated 検証一式結果（日本語）](../../../docs/ja/R24_BENCHMARK_INSTANCE_SUITE_REPORT_JA.md)
- [古典参照解の検証実行結果](../../../06_outputs/traffic_simulation/r24_classical_reference_validation/20260915_v1/R24_CLASSICAL_REFERENCE_VALIDATION_RESULTS.md)
- [古典参照解実装](../r24_classical_reference/): HiGHS 混合整数線形計画、厳密 Enumeration、復号器、独立検証器

```text
NEXT_EXECUTABLE_TASK = run classical R24 reference benchmark
```
