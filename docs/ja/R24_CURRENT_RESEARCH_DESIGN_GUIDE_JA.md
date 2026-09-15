# R24現行研究設計ガイド（日本語）

更新日: 2026-09-15 JST

この文書は、英語で記録されている[現行研究設計](../../05_src/traffic_simulation/CURRENT_RESEARCH_DESIGN.md)と[進捗・意思決定記録](../../05_src/traffic_simulation/RESEARCH_PROGRESS_AND_DECISION_RECORD.md)を日本語で読むための案内です。固定enum、schema、hash、数式については英語の原文authorityを優先します。

## 研究目的

技術・社会・環境条件の変化が、EVによる住宅向けB2Cラストマイル配送の計画と運用を通じて、物流システムの運用・経済結果へどのように波及するかを評価します。

量子計算は候補となる解法です。量子優位性や、量子技術によるバッテリー性能向上を前提にはしません。古典参照解、計算資源の実行可能性、scenario evidenceを分離して検証します。

## 現在の研究範囲

- 地理範囲: 東京都大田区
- 用途: 住宅向けB2Cラストマイル配送
- Primary vehicle class: kei-class electric commercial van
- 現在の問題: multi-vehicle capacitated routingであるR24/CVRP
- 現在の役割: 大田区を基盤とするcontrolled methodological benchmark
- 対象外: 実在carrierの運用再構成、観測配送routeの復元

## データと意味

道路はOSM由来のaccepted run_3 SUMO network、建物はPLATEAU、大田区範囲はMLIT N03、人口・世帯・住宅・宅配関連統計は公開統計を使用します。需要は公開統計で較正した合成需要です。

現在のsource horizonはdesignated synthetic day `2026-01-01`です。これは実観測日、dispatch wave、shift、tourではありません。

| Stage | Customers/rows | Parcel-equivalents |
|---|---:|---:|
| positive household-day source | 73,547 | 82,246 |
| stable building assignmentあり | 73,200 | 81,859 |
| positive-demand buildings | 39,956 | 81,859 |
| final routing-eligible population | 39,930 | 81,793 |

`parcel-equivalent`は、較正済み合成需要の抽象的な内容個数です。実parcel、注文、customer、stop、kg、m³ではありません。

## Customerとrouting proxy

一つのstable positive-demand buildingを一つのbenchmark customer identityとします。道路上のedge-offsetはrouting proxyであり、entrance、curb、loading position、実停止地点ではありません。

複数buildingが同じproxyを共有しても、customer identityは統合しません。Final populationでは28,274 customersが10,016 shared-proxy groupsに属します。

## Routing

- Graph: accepted V18/run_3
- Graph SHA-256: `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`
- SUMO permission class: `delivery`
- Depot: `DEP_006`
- Depot edge: `617631294`
- Objective: model/free-flow travel time最小
- Distance: 同じfastest-time path上の道路距離
- Endpoint: edge plus offset

Routingはdirectedかつconnection-awareです。`i -> j`と`j -> i`を別に扱い、missing/unreachable値を0や有限penaltyへ置換しません。Population-level SCCはeligibility screeningにだけ使い、instanceではdepotを含む全ordered-pair ODをrun_3上で計算します。

## Capacity

Primary capacity unitは`METHODOLOGICAL_PARCEL_EQUIVALENT`です。

\[
q_i=N_i,\qquad Q=14
\]

\[
\rho^*\in\{0.50,0.70,0.90\},\qquad
m=\left\lceil\frac{D}{\rho^*Q}\right\rceil,
\qquad
\rho_{actual}=\frac{D}{mQ}
\]

`Q=14`は全candidateを個別に収容できる最小整数として固定したmethodological capacityです。Vehicle payloadのkg値から変換したものではありません。`mQ>=D`だけでは十分でないため、各条件でexact bin-packing preflightを行います。

## Instance suite

Primary repeated-random suiteはhash-ranked SRSWORです。需要重み、PPS、quartile×tertile stratification、manual replacementは使用しません。

- Quantum-comparable core: `n={2,3,4}`
- Classical extension: `n={5,8,10,15,20}`
- Repetitions: 各nで10
- Structural: `n={4,10,20}` × `CLUSTERED/DISPERSED/MIXED` × 3
- Anchors: Primary R01のn=4,10,20 alias

No-redraw ruleは`sample once, validate, record`です。Demand pattern、difficulty、duplicate、zero arc、capacity strength、solver/QAOA結果を理由にsampleを変更しません。

## 生成済み結果

- Random: 80/80 valid
- Structural: 27/27 valid
- Anchor: 3/3 valid
- Independent bases: 107
- Base records including aliases: 110
- Capacity conditions: 330
- Packing feasible: 330
- Non-degenerate READY: 135
- Degenerate: 195
- Routing failures: 0
- Hard rejections: 0

## 問題の拡張順序

```text
R23 single-vehicle route ordering
  -> R24/CVRP multi-vehicle + capacity
  -> VRPTW time windows/service time
  -> EVRP battery/SOC/charging
```

下位layerで有効な定義は継承しますが、新しい制約やclaimには別のauthorityとvalidationが必要です。

## 現在の制限

- original demand generator provenanceの一部が不完全
- synthetic household/building allocationは観測配送ではない
- routing proxyはphysical stopではない
- run_3はmodel-completed networkであり、全現地規制を保証しない
- travel timeはfree-flow/model timeであり、観測配送時間ではない
- capacityはmethodologicalで、physical mass/volumeではない
- service time、time window、実fleet、reload、chargingは未導入
- R24 QUBOとresource gateは未実行

## Classical reference validation

R24 classical referenceは、HiGHS 1.15.1によるdirected CVRP MILP、n≤4の独立Exact Enumeration、独立solution validatorとして実装・検証済みです。

- Verdict: `R24_CLASSICAL_REFERENCE_VALIDATED`
- Fleet semantics: `AT_MOST_M`
- Subtour formulation: `LOAD_MTZ`
- Validation conditions: 21
- Exact / HiGHS optimum一致: 21/21
- Solution validation: 42/42 PASS
- Duplicate proxy / zero arc / asymmetric cost: PASS
- Full 330-condition benchmark: 未実行

実行結果は[確定成果物レポート](../../06_outputs/traffic_simulation/r24_classical_reference_validation/20260915_v1/R24_CLASSICAL_REFERENCE_VALIDATION_RESULTS.md)を参照してください。

## 次のtask

```text
NEXT_EXECUTABLE_TASK = run classical R24 reference benchmark
```
