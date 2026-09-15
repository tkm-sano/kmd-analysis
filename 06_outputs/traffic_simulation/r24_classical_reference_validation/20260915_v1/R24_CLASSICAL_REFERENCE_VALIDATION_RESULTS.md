# R24 Classical Reference Validation 実行結果

実行日: 2026-09-15  
Verdict: **`R24_CLASSICAL_REFERENCE_VALIDATED`**

## 結果概要

freeze済みR24 benchmark suiteから事前の機械的規則で選んだ21 capacity conditionsを対象に、独立した次の3系統を照合しました。

1. customer partitionとroute permutationのExact Enumeration
2. HiGHS 1.15.1によるdirected CVRP MILP
3. decoded routeを検査する独立solution validator

| 項目 | 結果 |
|---|---:|
| Validation conditions | 21 |
| Exact proven optimal | 21/21 |
| HiGHS proven optimal | 21/21 |
| Exact / HiGHS objective一致 | 21/21 |
| 独立validator合格 | 42/42 solutions |
| Validator failure | 0 |
| 最大objective差 | `9.999894245993346e-10 s` |
| Duplicate-proxy / zero-arc conditions | 3 / PASS |
| Asymmetric-cost conditions | 21 / PASS |
| Capacity violation | 0 |
| 合計計測時間 | `0.221893 s` |

Fleet semanticsは`AT_MOST_M`、subtour formulationは`LOAD_MTZ`です。主目的はrun_3のdirected travel timeで、distanceはsecondary metricです。

## Condition別結果

`m`は利用可能車両数、`used`は最適解で実際に使用した車両数です。目的値の単位は秒です。

| Condition | m | used | HiGHS objective | Exactとの差 | 判定 |
|---|---:|---:|---:|---:|---|
| `R24-ANCHOR-N004-RHO050` | 1 | 1 | 1599.547766163 | 0 | PASS |
| `R24-ANCHOR-N004-RHO070` | 1 | 1 | 1599.547766163 | 0 | PASS |
| `R24-ANCHOR-N004-RHO090` | 1 | 1 | 1599.547766163 | 0 | PASS |
| `R24-RND-N002-R01-RHO050` | 2 | 1 | 1097.881435788 | 0 | PASS |
| `R24-RND-N002-R01-RHO070` | 1 | 1 | 1097.881435788 | 0 | PASS |
| `R24-RND-N002-R01-RHO090` | 1 | 1 | 1097.881435788 | 0 | PASS |
| `R24-RND-N003-R01-RHO050` | 1 | 1 | 1650.234949576 | 0 | PASS |
| `R24-RND-N003-R01-RHO070` | 1 | 1 | 1650.234949576 | 0 | PASS |
| `R24-RND-N003-R01-RHO090` | 1 | 1 | 1650.234949576 | 0 | PASS |
| `R24-RND-N004-R01-RHO050` | 1 | 1 | 1599.547766163 | 0 | PASS |
| `R24-RND-N004-R01-RHO070` | 1 | 1 | 1599.547766163 | 0 | PASS |
| `R24-RND-N004-R01-RHO090` | 1 | 1 | 1599.547766163 | 0 | PASS |
| `R24-STR-CLUSTERED-N004-R01-RHO050` | 3 | 2 | 2699.558256966 | `4.55e-13` | PASS |
| `R24-STR-CLUSTERED-N004-R01-RHO070` | 2 | 2 | 2699.558256967 | `1.00e-09` | PASS |
| `R24-STR-CLUSTERED-N004-R01-RHO090` | 2 | 2 | 2699.558256967 | `1.00e-09` | PASS |
| `R24-STR-DISPERSED-N004-R01-RHO050` | 2 | 1 | 2364.692393502 | 0 | PASS |
| `R24-STR-DISPERSED-N004-R01-RHO070` | 1 | 1 | 2364.692393502 | 0 | PASS |
| `R24-STR-DISPERSED-N004-R01-RHO090` | 1 | 1 | 2364.692393502 | 0 | PASS |
| `R24-STR-MIXED-N004-R01-RHO050` | 1 | 1 | 2179.727537898 | 0 | PASS |
| `R24-STR-MIXED-N004-R01-RHO070` | 1 | 1 | 2179.727537898 | 0 | PASS |
| `R24-STR-MIXED-N004-R01-RHO090` | 1 | 1 | 2179.727537898 | 0 | PASS |

AnchorとPrimary n=4 R01は同一customer subsetのaliasであるため、同じ目的値になります。rhoが異なっても同じmへ丸められるdegenerate conditionsは、solver correctness確認のため独立にsolveしています。

CLUSTERED n=4 R01にはdistinct customer IDsが同一routing proxyを共有する条件が含まれます。zero-time/zero-distance transitionを許容しながらcustomer identityとcustomer-once制約を維持し、ExactとHiGHSが一致しました。

## Runtime

| 処理 | 合計 | 1 condition最大 |
|---|---:|---:|
| Exact Enumeration | `0.001394 s` | `0.000174 s` |
| HiGHS solve | `0.194078 s` | `0.021241 s` |
| 全validation処理 | `0.221893 s` | — |

HiGHSはthreads=1、random seed=0、presolve=on、relative/absolute MIP gap=0で実行しました。objective/feasibility toleranceは`1e-7`、integer decode toleranceは`1e-6`です。

## 範囲と次工程

これはsolver correctnessを確認するn≤4のvalidation executionです。full 330-condition benchmark、QUBO、QAOAは実行していません。

```text
NEXT_EXECUTABLE_TASK = run classical R24 reference benchmark
```

詳細なroute、load、distance、runtime、比較結果、provenance、SHA-256は次に保存しています。

```text
reproducibility/outputs/traffic_simulation/r24_classical_reference_validation/20260915_v1/
```
