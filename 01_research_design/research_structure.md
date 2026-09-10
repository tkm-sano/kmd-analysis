# Research Structure

## 2026-09-09の設計更新

今後の研究パイプラインは[最新B2C配送パイプライン](../RESEARCH_PIPELINE_REFERENCE.md#b2c-pipeline-20260909)を設計正本とする。住宅向け宅配を主対象に、39,956候補地点から層化・重み付き非復元抽出し、customer数nと複数seedを実験パラメータにする。主需要単位は配送件数、Baselineは単一depot、主指標はDFR_orders。OR-ToolsとQUBO→QAOA→Qiskit Aerは同一instance・共通Hard Constraintsを使用し、独立Validatorを通して比較する。技術Scenarioではcustomer・需要・Time Window・道路条件を原則固定する。

旧記述との不整合は上記の最新方針を優先する。既存成果物の生成・受入事実は保持し、今後の設計採択を実装完了とは扱わない。

## Current reduced quantum-method branch (2026-09-10)

現在の量子側実装はfull EVRPではなく、固定depot・単一車両のroute orderingをcontrolled subproblemとする。
customer-only `n x n` position QUBOはR20 formulation gate、R21 exact QUBO validation、R22 exact
QUBO-to-Ising validationを通過した。R23 Aer/QAOA infrastructureはimplementation smokeまで完了し、
formal pilot前の `READY_FOR_PILOT` である。formal QAOA performance resultはまだ存在しない。

このbranchで得るalgorithm/simulator evidenceは、後にcapacity、time windows、battery/SOC、charging、
reachability、fleet constraintsを備えたfull EVRP/Hayate評価へ戻して解釈する。Aer simulationはsoftware
evidenceであり、future QPU runtimeやquantum advantageを直接示さない。

## Motivation and research question

Transportation applications require more than a small routing formulation: meaningful evaluation must connect problem instances, operational constraints, validation modality, and quantum-resource evidence. The current research asks how transportation-relevant problem scale and constraints are represented in quantum-routing studies, and how that evidence compares with a synthetic Tokyo EVRP scenario.

## Literature review and circuit-width extraction

The review records the problem instance, mathematical formulation, quantum encoding, reported circuit width, depth definition where available, hardware or simulator modality, and evaluation status. QAOA layer count, ansatz layers, compiled depth, logical qubits, and physical-resource estimates are kept distinct. Application-oriented benchmarking, quantum utility, and practical quantum advantage literature provide methodological context rather than deployment claims.

## Application-side requirements

The comparison separates whether a requirement is represented from how it is evaluated or validated. Current requirement groups include scale, payload, operating time, range, SOC, charging access, evidence type, and classical comparison.

## Synthetic Tokyo EVRP analysis

Population mesh data supports synthetic customer sampling; public logistics facilities provide depot proxies; charging records provide candidate-location proxies; vehicle specifications define scenario parameters; and a route proxy supports exploratory constraint evaluation. Outputs must not be interpreted as observed demand, optimized real routes, charging utilization, grid load, or operational failure rates.

## Discussion and next stage

Two directions remain open:

1. Reduced-method validation: governed R23 pilotを実行し、validated Ising HamiltonianからAer exact-expectation QAOA、binary feasibility、route metricsまでの再現性を確認する。
2. Real-world optimization: road-network travel times, calibrated or observed demand, time windows, sequential SOC and charging dynamics, classical optimization baselines, and operational validationをfull EVRP/Hayateへ統合する。
3. Application-stage framework: problem instance・constraint・simulator evidenceをexpected quantum-technology stagesと分離して接続する。

## Current limitations

- Customer demand and locations are synthetic or proxy-based.
- Route construction is not a validated road-network optimization baseline.
- Sequential SOC, charger-arrival SOC, public access, congestion, operating hours, and connector compatibility are incomplete or not evaluated.
- Circuit-width evidence is heterogeneous across encodings and validation modalities.
- Representation of a constraint is not equivalent to application validation.
