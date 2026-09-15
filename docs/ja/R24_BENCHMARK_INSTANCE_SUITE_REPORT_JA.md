# R24 Benchmark Instance Suite結果（日本語）

原文execution report: [R24_BENCHMARK_INSTANCE_SUITE_REPORT.md](../../reproducibility/outputs/traffic_simulation/r24_benchmark_instance_suite/20260915_v1/R24_BENCHMARK_INSTANCE_SUITE_REPORT.md)

Execution verdict: **`R24_INSTANCE_SUITE_GENERATED_WITH_LIMITATIONS`**

## 生成結果

| Suite | Expected | Generated | Valid | Rejected |
|---|---:|---:|---:|---:|
| Random | 80 | 80 | 80 | 0 |
| Structural | 27 | 27 | 27 | 0 |
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

## Duplicate proxyとzero arcs

107 independent bases中16件に、instance内で共有されるrouting proxyが含まれました。

- duplicate-proxy customer occurrences: 128
- duplicate-proxy group occurrences: 51
- zero-coordinate ordered pairs: 0
- zero-distance ordered arcs: 304
- zero-travel-time ordered arcs: 304

Zero-distance/time arcsはすべてsame routing proxyとして検証済みで、無効化やredrawをしていません。

## Readiness

### Quantum-comparable primary subset

- n: `{2,3,4}`
- Base instances: 30
- Valid/all OD ready: 30
- Capacity conditions: 90
- Packing feasible: 90
- Non-degenerate ready: 10
- Degenerate: 80

これはQUBO/QAOA input readinessであり、QAOA実行許可やresource feasibilityを意味しません。

### Classical-extension primary subset

- n: `{5,8,10,15,20}`
- Base instances: 50
- Valid/all OD ready: 50
- Capacity conditions: 150
- Packing feasible: 150
- Non-degenerate ready: 84
- Degenerate: 66

R24-specific classical CVRP solverはまだ実装されておらず、MILP/CP-SAT optimizationは実行していません。

## Validation

Independent validatorが次を再検証し、すべてPASSしました。

- source population count、demand、hash
- planned instance ID completeness
- seed derivationとrandom selection再導出
- structural selection再導出
- anchor customer/q/OD hash同一性
- 14,600 OD rowsのrun_3 edge sequence、connection、distance、time
- 全330条件のm、actual rho、packing certificate、degeneracy
- 全347 generated artifactのSHA-256

## Fixed hashes

- C_eligible: `245aad97ea49f7676dcebd414b46eb364d64e9d0fbeb4defa0c8e8b90604ca5c`
- run_3: `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`
- Frozen specification commit: `44f7960abefe4df9648dd00b738885a14813ba54`
- Generator commit: `a2944d2d97a8c535663c6096a8a20609642bd4bf`

## 実行しなかった処理

- Demand generation: `NONE`
- Routing graph regeneration: `NONE`
- CVRP/MILP optimization: `NONE`
- QUBO/QAOA: `NONE`

## Claim boundary

このsuiteは、大田区を基盤とするfreeze済み合成eligible benchmark populationからのrepeated-random subsetおよびcontrolled structural subsetです。実在carrierのroute、delivery、fleet、dispatch、または全大田区配送の統計的代表sampleではありません。

```text
NEXT_EXECUTABLE_TASK = implement and validate classical R24 CVRP reference solver
```
