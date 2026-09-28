# R24現行研究設計ガイド（日本語）

更新日: 2026-09-15 JST

この文書は、英語で記録されている[現行研究設計](../../05_src/traffic_simulation/CURRENT_RESEARCH_DESIGN.md)と[進捗・意思決定記録](../../05_src/traffic_simulation/RESEARCH_PROGRESS_AND_DECISION_RECORD.md)を日本語で読むための案内です。固定列挙値、データ構造、ハッシュ値、数式については英語の原文正本を優先します。

## 研究目的

技術・社会・環境条件の変化が、電気自動車による住宅向けB2Cラストマイル配送の計画と運用を通じて、物流システムの運用・経済結果へどのように波及するかを評価します。

量子計算は候補となる解法です。量子優位性や、量子技術によるバッテリー性能向上を前提にはしません。古典参照解、計算資源の実行可能性、想定条件 根拠を分離して検証します。

## 現在の研究範囲

- 地理範囲: 東京都大田区
- 用途: 住宅向けB2Cラストマイル配送
- Primary vehicle class: kei-class electric commercial van
- 現在の問題: 複数車両 capacitated 経路計算であるR24/CVRP
- 現在の役割: 大田区を基盤とする条件を統制した methodological ベンチマーク
- 対象外: 実在carrierの運用再構成、観測配送経路の復元

## データと意味

道路はオープンストリートマップ由来の受入済み run_3 交通シミュレーターの道路網、建物はPLATEAU、大田区範囲はMLIT N03、人口・世帯・住宅・宅配関連統計は公開統計を使用します。需要は公開統計で較正した合成需要です。

現在の出典 計画期間はdesignated 合成 day `2026-01-01`です。これは実観測日、配車 wave、移動、tourではありません。

| 段階 | Customers/rows | Parcel-equivalents |
|---|---:|---:|
| positive household-day source | 73,547 | 82,246 |
| stable 建物 割当あり | 73,200 | 81,859 |
| positive-demand buildings | 39,956 | 81,859 |
| final routing-eligible population | 39,930 | 81,793 |

`parcel-equivalent`は、較正済み合成需要の抽象的な内容個数です。実荷物、注文、顧客、配送地点、kg、m³ではありません。

<a id="customerとrouting-proxy"></a>

## 顧客と経路計算 代理指標

> **39,930 対象条件を満たす 顧客は、大田区を根拠として最適化 問題例を生成するための出典 母集団であり、必須の単一最適化 問題例ではありません。本研究は39,930 顧客全体の同時求解を要求しません。最適化 規模は現在はベンチマーク パラメーター、将来はcomputational-capability 想定条件 変数として扱います。**

\[
|C_{\mathrm{eligible}}|=39{,}930,\qquad
C_{n,r}\subset C_{\mathrm{eligible}},\qquad
\text{Eligible Source Population}\neq\text{Optimization Instance}.
\]

39,930 顧客全体を一つの配送便、実運用planning 問題例、容量制約付き配送経路問題 / 時間窓付き配送経路問題 / 電気自動車配送経路問題、または量子計算 computerで必ず解く対象とはしません。39,930は将来問題例を生成できる現行出典 母集団 ceilingです。

> **本研究では39,930 顧客全体を単一容量制約付き配送経路問題 / 時間窓付き配送経路問題 / 電気自動車配送経路問題として解くことを必須の研究到達目標としない。**

一つのstable 正-demand 建物を一つのベンチマーク 顧客 同一性とします。道路上の道路区間-位置補正値は経路計算 代理指標であり、entrance、curb、loading 位置、実停止地点ではありません。

複数建物が同じ代理指標を共有しても、顧客 同一性は統合しません。Final 母集団では28,274 顧客が10,016 shared-代理指標 groupsに属します。

## 経路計算

- Graph: accepted V18/run_3
- Graph SHA-256: `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`
- SUMO permission class: `delivery`
- Depot: `DEP_006`
- Depot edge: `617631294`
- 目的: model/free-flow 移動 時間最小
- Distance: 同じfastest-時間 保存先上の道路距離
- Endpoint: edge plus offset

Routingはdirectedかつ接続-awareです。`i -> j`と`j -> i`を別に扱い、missing/unreachable値を0や有限罰則項へ置換しません。Population-level SCCはeligibility screeningにだけ使い、問題例では配送拠点を含む全ordered-pair 出発地・到着地をrun_3上で計算します。

<a id="capacity"></a>

## 容量

Primary 容量 単位は`METHODOLOGICAL_PARCEL_EQUIVALENT`です。

\[
q_i=N_i,\qquad Q=14
\]

\[
\rho^*\in\{0.50,0.70,0.90\},\qquad
m=\left\lceil\frac{D}{\rho^*Q}\right\rceil,
\qquad
\rho_{actual}=\frac{D}{mQ}
\]

`Q=14`は全候補を個別に収容できる最小整数として固定したmethodological 容量です。車両 積載量のkg値から変換したものではありません。`mQ>=D`だけでは十分でないため、各条件で厳密 bin-packing 事前確認を行います。

<a id="instance-suite"></a>

## 問題例 検証一式

Primary repeated-random 検証一式はハッシュ値-ranked SRSWORです。需要重み、PPS、quartile×tertile stratification、manual replacementは使用しません。

- Quantum-comparable core: `n={2,3,4}`
- Classical extension: `n={5,8,10,15,20}`
- Repetitions: 各nで10
- Structural: `n={4,10,20}` × `CLUSTERED/DISPERSED/MIXED` × 3
- Anchors: Primary R01のn=4,10,20 alias

これらの`n`は`COMPUTATIONAL BENCHMARK SIZE`であり、大田区配送の統計的代表標本 規模でも、固定されたoperational 問題例 規模でもありません。

No-redraw 規則は`sample once, validate, record`です。需要 pattern、difficulty、重複、zero 区間、容量 strength、solver/QAOA結果を理由に標本を変更しません。

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

下位層で有効な定義は継承しますが、新しい制約や主張には別の正本と検証が必要です。

<a id="future-capability-scenarioとplanning-scale"></a>

## 将来能力想定条件と計画規模

将来想定条件を少なくとも

\[
s=(\text{Computation},\text{EV},\text{Demand},\text{Society},\text{Energy})
\]

として扱い、Computation 想定条件に

\[
n_{\max}(s)=\text{scenario }s\text{で扱える最大optimization scale}
\]

を含めます。`n_max(s)`は固定された実運用顧客数ではなく、古典計算 computing、高性能計算、量子計算、量子計算-古典計算 混合型、分解、AI-assisted 最適化、量子計算 × 高性能計算、量子計算 × 高性能計算 × AIなどが支えるplanning 範囲です。原則`n_max(s) <= 39,930`とし、社会想定条件が合成 対象条件を満たす 母集団自体を変える場合は、その想定条件固有の母集団 規模を上限にできます。具体的な規模列は将来想定条件設計で定め、今回固定しません。

古典計算 規模拡大は`n -> runtime / resource / optimality / feasibility`を測り、`n_max^classical(s)`の根拠を作ります。量子計算 / 混合型 規模拡大は`n -> qubits / circuit resources / runtime / solution quality`を測り、`n_max^quantum(s)`または`n_max^hybrid(s)`へ接続します。

研究は、(1) 手法 / Solver Benchmark、(2) Future Capability 想定条件、(3) Logistics / Economic Impactの3層で整理します。評価chainは次のとおりです。

```text
Technology / Social Scenario
  -> Computational Capability
  -> n_max(s)
  -> Routing / EV Planning
  -> Operational Outcomes
  -> E_operation
  -> C_op
```

計算能力向上を実行時間短縮だけでなく、`Larger Solvable Instance -> Larger Integrated Planning Scope`として評価します。経済定義`C_op = E_operation × p_electricity`は変更しません。

## 現在の制限

- original demand 生成器 出典・来歴の一部が不完全
- 合成 household/building allocationは観測配送ではない
- 経路計算 代理指標はphysical 配送地点ではない
- run_3はモデル-completed 道路網であり、全現地規制を保証しない
- 移動 時間はfree-flow/model 時間であり、観測配送時間ではない
- 容量はmethodologicalで、physical mass/volumeではない
- 作業時間、時間窓、実車両群、reload、充電は未導入
- R24 制約なし二値二次最適化と資源 判定基準は未実行

<a id="classical-reference-validation"></a>

## 古典参照解の検証

R24 古典参照解は、HiGHS 1.15.1によるdirected 容量制約付き配送経路問題 混合整数線形計画、n≤4の独立厳密 Enumeration、独立solution 検証器として実装・検証済みです。

- Verdict: `R24_CLASSICAL_REFERENCE_VALIDATED`
- Fleet semantics: `AT_MOST_M`
- Subtour formulation: `LOAD_MTZ`
- Validation conditions: 21
- 厳密 / HiGHS optimum一致: 21/21
- Solution validation: 42/42 PASS
- Duplicate proxy / zero arc / asymmetric cost: PASS
- Full 330-条件 ベンチマーク: 未実行

実行結果は[確定成果物レポート](../../06_outputs/traffic_simulation/r24_classical_reference_validation/20260915_v1/R24_CLASSICAL_REFERENCE_VALIDATION_RESULTS.md)を参照してください。

<a id="次のtask"></a>

## 次の作業

```text
NEXT_EXECUTABLE_TASK = run classical R24 reference benchmark
```
