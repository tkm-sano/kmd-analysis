# 東京都市配送 × 量子未来社会

東京都大田区を対象に、公開データを基盤とする合成配送需要と道路ネットワークを用いて、古典計算・量子計算を含む配送計画手法と将来条件の影響を検討する研究リポジトリです。

現在の中心課題は、実配送会社の運用再現ではなく、**大田区を基盤とする統制されたCVRPベンチマーク**です。観測されていない配送先、運行、車両群を実態として主張しません。

更新基準日: **2026-09-15**

## 現在の結論

R24 benchmark instance suiteは、freeze済み仕様どおり生成・検証済みです。

| 項目 | 現在の状態 |
|---|---|
| R23 | `R23_CLOSED_WITH_DOCUMENTED_LIMITATIONS` |
| Gate A | `GATE_A_ACCEPTED_WITH_LIMITATIONS` |
| Gate B | `GATE_B_ACCEPTED_WITH_LIMITATIONS` |
| Gate C | `GATE_C_ACCEPTED_WITH_LIMITATIONS` |
| Gate D | `GATE_D_ACCEPTED_WITH_LIMITATIONS` |
| Routing compatibility | `ROUTING_COMPATIBILITY_ACCEPTED_WITH_LIMITATIONS` |
| Final eligible population | `39,930 customers / 81,793 methodological parcel-equivalents` |
| Instance specification | `R24_INSTANCE_GENERATION_SPEC_FROZEN_WITH_LIMITATIONS` |
| Instance suite | `R24_INSTANCE_SUITE_GENERATED_WITH_LIMITATIONS` |
| Classical R24 solver | `R24_CLASSICAL_REFERENCE_VALIDATED` |
| R24 QUBO/QAOA | `NOT_EXECUTED` |

```text
NEXT_EXECUTABLE_TASK = run classical R24 reference benchmark
```

## R24 instance suite

### Suite構成

| Suite | 規模 | 生成結果 |
|---|---|---:|
| Primary: Repeated Random | `n={2,3,4,5,8,10,15,20}` × 10 repetitions | 80/80 valid |
| Secondary: Controlled Structural | `n={4,10,20}` × 3 structures × 3 repetitions | 27/27 valid |
| Reference: Fixed Anchor | Primary R01のn=4,10,20 alias | 3/3 valid |

独立に生成したbase instanceは107件、anchor aliasを含むmanifest recordは110件です。全baseで`DEP_006`を含む全ordered-pair ODをaccepted run_3上で計算し、SUMO `delivery` connection、turn、edge sequence、partial-edge distance/timeを検証しています。

### Capacity条件

各customer demandとcapacityは次のとおりです。

\[
q_i=N_i,\qquad Q=14
\]

\[
\rho^*\in\{0.50,0.70,0.90\},\qquad
m=\left\lceil\frac{D}{\rho^*Q}\right\rceil
\]

同一customer subsetを3条件で共通利用します。全330条件がexact bin-packing preflightでfeasibleでした。

- non-degenerate `READY`: 135
- `DEGENERATE_REGIME_SAME_M`: 195
- `PACKING_INFEASIBLE`: 0

Degenerate条件は保存しますが、後のcapacity-effect比較からは除外します。

### Duplicate routing proxy

Building identityはrouting proxyとは別に保持します。Duplicate proxyを理由にcustomerを除外・統合・再抽選しません。

- within-instance duplicate proxyを含むindependent base: 16/107
- 検証済みzero-distance ordered arcs: 304
- 検証済みzero-travel-time ordered arcs: 304
- routing validation failure: 0
- hard rejection: 0
- redraw: 0

## 固定入力

| 入力 | 固定値 |
|---|---|
| Source horizon | designated synthetic day `2026-01-01` |
| Eligible customers | 39,930 |
| Total demand | 81,793 methodological parcel-equivalents |
| Depot | `DEP_006` |
| Primary vehicle class | kei-class electric commercial van |
| Routing graph | accepted V18/run_3 |
| run_3 SHA-256 | `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2` |
| C_eligible SHA-256 | `245aad97ea49f7676dcebd414b46eb364d64e9d0fbeb4defa0c8e8b90604ca5c` |

## 重要な主張範囲

許可される説明は、次の範囲です。

> 大田区を基盤とする、freeze済み合成eligible benchmark populationから作成したrepeated-random subsetおよびcontrolled structural subset。

次の主張は禁止されています。

- 大田区の実配送全体を統計的に代表する
- 実在carrierのroute、dispatch、fleetを再現する
- 実観測parcel、order、customer、stopである
- methodological capacityをkg、m³、メーカー公称payloadとみなす
- model free-flow travel timeを実観測配送時間とみなす
- 現在の結果をquantum advantageの証拠とみなす

## 最初に読む資料

日本語で現在地を確認する場合は、次の順序を推奨します。

1. [R24現行研究設計ガイド（日本語）](docs/ja/R24_CURRENT_RESEARCH_DESIGN_GUIDE_JA.md)
2. [R24 instance-generation仕様（日本語）](docs/ja/R24_INSTANCE_GENERATION_SPECIFICATION_JA.md)
3. [R24 benchmark instance suite結果（日本語）](docs/ja/R24_BENCHMARK_INSTANCE_SUITE_REPORT_JA.md)
4. [R23 status](05_src/traffic_simulation/R23_STATUS.md)

英語の原文authorityは、固定ID、schema、hash、enumを機械的に保持するため残しています。

| 正式資料 | 役割 |
|---|---|
| [Current Research Design](05_src/traffic_simulation/CURRENT_RESEARCH_DESIGN.md) | 現在採用されている研究設計の統合authority |
| [Research Progress and Decision Record](05_src/traffic_simulation/RESEARCH_PROGRESS_AND_DECISION_RECORD.md) | 研究進行と判断のhistorical record |
| [Frozen instance-generation specification](reproducibility/outputs/traffic_simulation/r24_instance_generation_specification/20260915_v1/R24_INSTANCE_GENERATION_SPECIFICATION.md) | n、seed、sampling、structural、anchor、validationの正本 |
| [Generated instance-suite report](reproducibility/outputs/traffic_simulation/r24_benchmark_instance_suite/20260915_v1/R24_BENCHMARK_INSTANCE_SUITE_REPORT.md) | 実生成結果 |
| [Routing compatibility revalidation](reproducibility/outputs/traffic_simulation/r24_routing_compatibility_revalidation/20260915_v1/R24_ROUTING_COMPATIBILITY_REVALIDATION.md) | final eligible populationとrun_3 compatibility |
| [Methodological capacity specification](reproducibility/outputs/traffic_simulation/r24_methodological_capacity_specification/20260915_v1/R24_METHODOLOGICAL_CAPACITY_SPECIFICATION.md) | q_i、Q、rho、mの正本 |
| [Routing Baseline](05_src/traffic_simulation/specifications/ROUTING_BASELINE_CANONICAL.md) | directed routing costとreachabilityの正本 |

## 実行入口

日常的な研究実行・検証はrepository rootの`./research`に集約しています。

```bash
./research commands
```

詳細は[統合Research CLI](docs/20260903_20260903_research_cli.md)を参照してください。

R24 instance suiteの再現コードは次の2ファイルです。

- [generator](05_src/traffic_simulation/r24_instance_generation/generate_r24_benchmark_instance_suite.py)
- [independent validator](05_src/traffic_simulation/r24_instance_generation/validate_r24_benchmark_instance_suite.py)

生成済みartifactは次のdirectoryにあります。

```text
reproducibility/outputs/traffic_simulation/r24_benchmark_instance_suite/20260915_v1/
```

このdirectoryは生成物policyによりgitignore対象ですが、`SHA256SUMS.txt`が全artifactを検証します。

## 現在の研究パイプライン

```text
R23 closure
  -> Gate A customer/proxy semantics
  -> Gate B vehicle class
  -> Gate C/D methodological capacity
  -> run_3 routing compatibility
  -> final C_eligible
  -> instance-generation specification freeze
  -> R24 benchmark instance suite generation          [完了]
  -> classical R24 CVRP reference validation          [完了]
  -> classical benchmark execution                    [次]
  -> R24 QUBO design and validation
  -> Resource Gate
  -> QAOA where authorized
  -> R23/R24 comparison
  -> VRPTW / EVRP extensions
  -> operational and economic outcomes
```

## 今回まだ実行していないもの

- full 330-condition R24 classical benchmark
- R24 QUBO generation
- R24 QAOA/QPU/statevector execution
- routing graph regeneration
- synthetic demand regeneration
- physical kg/volume capacity scenario
- observed dispatch、shift、service-time、time-window model

## Repository構造

| Directory | 内容 |
|---|---|
| `00_project_management/` | 研究管理、環境、構造規則 |
| `01_research_design/` | 研究設計と分析方法 |
| `02_literature/` | 文献記録 |
| `03_data/` | raw/processed dataとmetadata |
| `05_src/` | 実装、仕様、検証コード |
| `06_outputs/` | 主要な出力案内 |
| `reproducibility/` | config、environment、manifest、execution artifact |
| `docs/` | 利用ガイドと日本語案内 |
| `legacy/` | 現行authorityではない過去資産 |

今回のMarkdown整理方針とarchive対象は[Markdown参照・archive監査](docs/ja/MARKDOWN_REFERENCE_AUDIT_20260915.md)に記録しています。

READMEと個別記録が矛盾する場合は、最新のcurrent authority、freeze済みspecification、execution manifest、SHA-256記録を優先してください。
