<a id="r24-benchmark-instance-suite結果日本語"></a>

# R24 ベンチマーク問題例群結果（日本語）

原文実行 報告: [R24_BENCHMARK_INSTANCE_SUITE_REPORT.md](../../reproducibility/outputs/traffic_simulation/r24_benchmark_instance_suite/20260915_v1/R24_BENCHMARK_INSTANCE_SUITE_REPORT.md)

Execution verdict: **`R24_INSTANCE_SUITE_GENERATED_WITH_LIMITATIONS`**

## 生成結果

| Suite | Expected | Generated | Valid | Rejected |
|---|---:|---:|---:|---:|
| 無作為 | 80 | 80 | 80 | 0 |
| 構造上の | 27 | 27 | 27 | 0 |
| Anchor aliases | 3 | 3 | 3 | 0 |

- Independent bases: 107
- Base manifest records including aliases: 110
- Capacity conditions: 330
- Non-degenerate `READY`: 135
- `DEGENERATE_REGIME_SAME_M`: 195
- `PACKING_INFEASIBLE`: 0
- Routing validation failures: 0
- Hard rejection reasons: なし
- Specification deviations: `NONE`

<a id="duplicate-proxyとzero-arcs"></a>

## 重複代理指標とzero arcs

107 independent bases中16件に、問題例内で共有される経路計算 代理指標が含まれました。

- duplicate-proxy customer occurrences: 128
- duplicate-proxy group occurrences: 51
- zero-coordinate ordered pairs: 0
- zero-distance ordered arcs: 304
- zero-travel-time ordered arcs: 304

Zero-distance/time arcsはすべてsame 経路計算 代理指標として検証済みで、無効化やredrawをしていません。

## 準備状況

<a id="quantum-comparable-primary-subset"></a>

### 量子計算-comparable 主要な subset

- n: `{2,3,4}`
- Base instances: 30
- Valid/all OD ready: 30
- Capacity conditions: 90
- Packing feasible: 90
- Non-degenerate ready: 10
- Degenerate: 80

これはQUBO/QAOA 入力 準備状況であり、量子近似最適化アルゴリズム実行許可や資源 実行可能性を意味しません。

<a id="classical-extension-primary-subset"></a>

### 古典計算-拡張主要な subset

- n: `{5,8,10,15,20}`
- Base instances: 50
- Valid/all OD ready: 50
- Capacity conditions: 150
- Packing feasible: 150
- Non-degenerate ready: 84
- Degenerate: 66

この問題例-検証一式生成時点ではR24-specific 古典計算 容量制約付き配送経路問題 求解器と混合整数線形計画 最適化は未実行でした。その後、HiGHS 混合整数線形計画、独立厳密 Enumeration、独立検証器によるsmall-n 検証を完了し、`R24_CLASSICAL_REFERENCE_VALIDATED`となりました。全体 330-条件 ベンチマークは未実行です。

<a id="validation"></a>

## 検証

Independent 検証器が次を再検証し、すべて合格しました。

- source population count、demand、hash
- planned instance ID completeness
- 乱数の種 derivationとrandom selection再導出
- 構造上の selection再導出
- 基準 customer/q/OD ハッシュ値同一性
- 14,600 出発地・到着地 行のrun_3 道路区間 sequence、接続、距離、時間
- 全330条件のm、実際の rho、packing certificate、degeneracy
- 全347 生成済み 成果物のSHA-256

<a id="fixed-hashes"></a>

## 固定済みハッシュ値

- C_eligible: `245aad97ea49f7676dcebd414b46eb364d64e9d0fbeb4defa0c8e8b90604ca5c`
- run_3: `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`
- Frozen specification commit: `44f7960abefe4df9648dd00b738885a14813ba54`
- Generator commit: `a2944d2d97a8c535663c6096a8a20609642bd4bf`

## 実行しなかった処理

- Demand generation: `NONE`
- Routing graph regeneration: `NONE`
- CVRP/MILP optimization: `NONE`
- QUBO/QAOA: `NONE`

<a id="claim-boundary"></a>

## 主張境界

この検証一式は、大田区を基盤とする固定済み合成対象条件を満たす ベンチマーク 母集団からのrepeated-random subsetおよび条件を統制した 構造上の subsetです。実在carrierの経路、配送、車両群、配車、または全大田区配送の統計的代表標本ではありません。

```text
NEXT_EXECUTABLE_TASK = run classical R24 reference benchmark
```

後続の実行結果: [R24 古典計算 Reference 検証](../../06_outputs/traffic_simulation/r24_classical_reference_validation/20260915_v1/R24_CLASSICAL_REFERENCE_VALIDATION_RESULTS.md)
