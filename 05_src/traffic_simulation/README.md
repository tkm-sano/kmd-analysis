# 交通シミュレーション・配送最適化コード

このdirectoryは、既存の合成EVRP分析を上書きせずに、大田区の道路・交通・配送・最適化研究を追加する実装layerです。

現在の研究設計は[CURRENT_RESEARCH_DESIGN.md](CURRENT_RESEARCH_DESIGN.md)、意思決定履歴は[RESEARCH_PROGRESS_AND_DECISION_RECORD.md](RESEARCH_PROGRESS_AND_DECISION_RECORD.md)を正本とします。日本語での案内は[R24現行研究設計ガイド](../../docs/ja/R24_CURRENT_RESEARCH_DESIGN_GUIDE_JA.md)を参照してください。

## 現在のR24状態

| 項目 | 状態 |
|---|---|
| Gates A–D | `ACCEPTED_WITH_LIMITATIONS` |
| Routing compatibility | `ACCEPTED_WITH_LIMITATIONS` |
| Final C_eligible | 39,930 customers / 81,793 methodological parcel-equivalents |
| Instance-generation specification | `FROZEN_WITH_LIMITATIONS` |
| Benchmark instance suite | `GENERATED_WITH_LIMITATIONS` |
| Classical R24 CVRP solver | `R24_CLASSICAL_REFERENCE_VALIDATED` |
| R24 QUBO/QAOA | `NOT_EXECUTED` |

```text
NEXT_EXECUTABLE_TASK = run classical R24 reference benchmark
```

R24 instance generationのコード:

- [generate_r24_benchmark_instance_suite.py](r24_instance_generation/generate_r24_benchmark_instance_suite.py)
- [validate_r24_benchmark_instance_suite.py](r24_instance_generation/validate_r24_benchmark_instance_suite.py)

R24 classical referenceのコード:

- [r24_classical_reference](r24_classical_reference/): HiGHS MILP、独立Exact Enumeration、decoder、独立validator、validation runner
- [validation test](validation/test_r24_classical_reference.py): known optimum、capacity、asymmetry、zero arc、corrupt solution等のunit fixtures

Validation結果: 21/21 Exact/HiGHS optimum一致、42/42 decoded/exact solution validation合格、最大目的差 `9.999894245993346e-10 s`。full benchmarkは未実行です。

生成済み結果:

- Random: 80/80 valid
- Structural: 27/27 valid
- Anchor aliases: 3/3 valid
- Capacity conditions: 330/330 packing-feasible
- Non-degenerate READY: 135
- Degenerate: 195
- Routing/hard validation failure: 0

## R20–R23 reduced quantum pipeline

R20–R23はfull EVRPではなく、`INITIAL_R20_REDUCED_ROUTE_ORDERING_SCOPE_ONLY`に限定したsingle-vehicle route-ordering studyです。

| Stage | 状態 | 実装・authority |
|---|---|---|
| R20 formulation | `FORMULATION_VERIFIED = PASS` | [r20_route_ordering](r20_route_ordering/) / [R20 specification](specifications/R20_QAOA_SUBPROBLEM_SPEC.md) |
| R21 QUBO validation | `PASS` | [r21_qubo_validation](r21_qubo_validation/) |
| R22 Ising conversion | `PASS` | [r22_ising_conversion](r22_ising_conversion/) |
| R23 QAOA/Aer | `CLOSED_WITH_DOCUMENTED_LIMITATIONS` | [R23_STATUS.md](R23_STATUS.md) |

Reduced modelはcustomer-only `n × n` position encodingで、静的directed travel timeを最小化し、customer-onceとposition-onceをQUBO penaltyにします。Capacity、time window、battery/SOC、charging、fleet sizingは含みません。Aerはsoftware simulatorであり、量子実機性能やquantum advantageの証拠ではありません。

## Source-code boundaries

| Directory | 役割 |
|---|---|
| `network/` | OSM取得、clip、map matching、SUMO network生成 |
| `demand/` | 時間帯別交通需要・配送需要構築 |
| `calibration/` | JARTIC/道路交通センサス較正・validation |
| `simulation/` | SUMO config、runner、result extraction |
| `validation/` | 構造・経験的validation |
| `r20_route_ordering/` | reduced QUBO、exact reference、routing adapter |
| `r21_qubo_validation/` | reduced-QUBO stage validation |
| `r22_ising_conversion/` | QUBO-to-Ising変換とequivalence validation |
| `r23_qaoa_aer/` | R23 QAOA/Aer infrastructure |
| `r24_instance_generation/` | frozen R24 suite generatorと独立validator |
| `r24_classical_reference/` | HiGHS CVRP MILP、Exact Enumeration、decoder、独立solution validator |

新規moduleは可能な限り`traffic_simulation.paths`のcanonical path discoveryを使用し、host固有absolute pathを埋め込みません。既存の固定実装を変更する場合は、そのprovenance boundaryを明記します。

## Data boundaries

| Data | Path |
|---|---|
| Raw inputs | `03_data/raw/traffic_simulation/` |
| Processed road networks | `03_data/processed/traffic_simulation/road_network/` |
| Traffic profiles | `03_data/processed/traffic_simulation/traffic_profiles/` |
| SUMO inputs | `03_data/processed/traffic_simulation/sumo_inputs/` |
| Calibration data | `03_data/processed/traffic_simulation/calibration/` |
| Demand data | `03_data/processed/traffic_simulation/demand/` |
| Validation data | `03_data/processed/traffic_simulation/validation/` |
| Source registry | `03_data/metadata/traffic_simulation_sources.csv` |
| Reproducible outputs | `reproducibility/outputs/traffic_simulation/` |
| Curated outputs | `06_outputs/traffic_simulation/` |

Metadataに保存するpathはrepository rootからのrelative pathとします。

## 主要仕様

- [仕様index](specifications/README.md)
- [Routing Baseline](specifications/ROUTING_BASELINE_CANONICAL.md)
- [R23 Reduced Problem](specifications/R23_REDUCED_PROBLEM_CANONICAL.md)
- [R24 instance-generation仕様（日本語）](../../docs/ja/R24_INSTANCE_GENERATION_SPECIFICATION_JA.md)
- [R24 suite結果（日本語）](../../docs/ja/R24_BENCHMARK_INSTANCE_SUITE_REPORT_JA.md)

## 運用上の注意

- 既存のfrozen input/outputを暗黙に上書きしない
- source data、synthetic transformation、model assumptionを区別する
- unreachable costを0や任意のfinite penaltyへ置換しない
- solverが決めるcustomer visit orderとrouterが決めるroad pathを分離する
- READMEと個別authorityが矛盾する場合は、最新のcurrent authority、freeze済みspecification、execution manifestを優先する
