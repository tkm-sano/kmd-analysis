<a id="classical-and-qaoa-comparison-protocol"></a>

# 古典計算 ・ 量子近似最適化アルゴリズム比較手順

## 2026-09-09の設計更新

今後の研究パイプラインは[最新B2C配送パイプライン](../../RESEARCH_PIPELINE_REFERENCE.md#b2c-pipeline-20260909)を設計正本とする。住宅向け宅配を主対象に、39,956候補地点から層化・重み付き非復元抽出し、顧客数nと複数乱数の種を実験パラメータにする。主需要単位は配送件数、基準は単一配送拠点、主指標はDFR_orders。OR-Toolsと制約なし二値二次最適化→量子近似最適化アルゴリズム→Qiskit Aerは同一問題例・共通必須制約を使用し、独立検証器を通して比較する。技術想定条件では顧客・需要・時間窓・道路条件を原則固定する。

旧記述との不整合は上記の最新方針を優先する。既存成果物の生成・受入事実は保持し、今後の設計採択を実装完了とは扱わない。

<a id="common-instance"></a>

## Common 問題例

Both solvers receive the same frozen customers, vehicles, demands, distance/travel-time/energy matrices, constraints, feasibility checker, objective and final evaluator. Vehicle class is fixed by vehicle type: a small delivery van uses `delivery`, while a heavy freight vehicle uses `truck`.

The formal road review covers the candidate subgraph selectable by any compared algorithm, not only the route ultimately selected. It includes all reachable edges between depots, customers and charging facilities plus the preregistered alternative-route buffer.

## 乱数の種の役割

Shared instance, demand and traffic seeds create common experimental conditions. Classical solver, QAOA parameter initialization and QAOA sampling use separate preregistered seed sets. Equal integers across solver-specific seeds do not imply equivalent randomness.

<a id="fairness-and-outputs"></a>

## 公平性 ・ 出力

Separate equal-budget comparisons from best-reference comparisons. Record what time is included: preprocessing, QUBO generation, optimization, circuit evaluation, shots, decoding, repair and final evaluation. Apply the same feasibility and evaluation functions to raw and repaired outputs, and retain both.

For `INITIAL_R20_REDUCED_ROUTE_ORDERING_SCOPE_ONLY`, raw invalid bitstrings are
discarded and no repair is performed. Any future repaired-output comparison is
a separate full-EVRP or sensitivity protocol and must not be mixed into the
R21/R22 evidence or the initial R23 raw-QAOA metrics.

First compare objective and feasibility on the frozen static instance. Then map both visit orders with the same road-routing rule and evaluate them under the same SUMO traffic seeds. Report static optimization quality separately from realized traffic performance. Qiskit Aer results do not establish quantum advantage.

The reduced quantum path currently has R21 QUBO-equivalence PASS and R22
QUBO-to-Ising full-state-equivalence PASS. R23 is `ACCEPTED_WITH_LIMITATIONS`; formal
QAOA evidence does not yet exist. The frozen initial R23 baseline uses CPU Aer
exact expectation, six instances, `p={1,2,3}`, COBYLA, and 18 configurations;
finite shots, GPU/H100, optimizer comparison, and cloud QPU are excluded.
