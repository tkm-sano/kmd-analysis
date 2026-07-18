# Tokyo Traffic × Quantum Routing Research

This repository develops a public-data-based traffic approximation for Ota Ward, Tokyo, and is designed to compare a non-optimizing baseline, classical optimization, and QAOA on Qiskit Aer using the same synthetic electric-vehicle delivery problem.

> **Primary research question**
>
> Under identical vehicles, capacity, battery, departure time, demand, traffic, weather, and evaluation conditions, how much does route-order optimization change population-equivalent delivery coverage, and how do classical optimization and Aer-based QAOA differ in outcome and computational resources?

## Scope

This research does not claim to provide a complete digital twin of Tokyo, reconstruct an operator's real delivery routes, predict customer orders, or demonstrate quantum advantage. Its purpose is to compare classical and quantum-computing methods under controlled, reproducible conditions using:

- a traffic approximation calibrated and independently validated against public observations;
- a governed synthetic delivery problem;
- traceable sources, assumptions, and transformation rules; and
- identical road, demand, vehicle, traffic, and evaluation conditions across methods.

## Study design

1. Fix the Docker environments and data-provenance rules.
2. Derive the Ota Ward boundary from Japan's National Land Numerical Information N03 dataset.
3. Acquire road geometry and connectivity candidates from a date-pinned OpenStreetMap PBF snapshot.
4. Convert the governed OSM input into a SUMO network and validate its structure.
5. Calibrate general traffic with multiple observations, including JARTIC data, and validate it on separate observations.
6. Build synthetic delivery demand from population meshes and public aggregate statistics.
7. Give the same frozen delivery problem to the non-optimizing baseline, a classical solver, and Aer-based QAOA.
8. Convert each visit order into road paths using the same rules and run them in the same SUMO environment.
9. Compare population-equivalent delivery coverage, driving outcomes, solution quality, runtime, and QAOA resources.
10. Add EV constraints, driver-experience effects, weather, and incidents incrementally so that their effects remain separable.

The classical and QAOA branches must share the same frozen problem instance, road network, vehicle constraints, traffic conditions, route-conversion rules, and simulation seeds. Raw solver output, decoded solutions, repaired solutions, and SUMO outcomes are stored separately.

## Current status

Status date: **2026-07-18**. The machine-readable source of truth is [`research_stage.yml`](reproducibility/config/traffic_simulation/research_stage.yml).

| Status | Stage |
|---|---|
| Complete | Docker and repository environments |
| Complete | Data acquisition, SHA-256, and provenance rules |
| Complete | N03 Ota Ward study boundary |
| Complete | Baseline JARTIC and date-pinned OSM inputs |
| Complete | Review maps for roads, observations, population, and synthetic demand |
| **In progress** | **SUMO network generation and structural validation** |
| Planned | Observation expansion, general traffic demand, calibration, and independent validation |
| Planned | Formal delivery problem, classical optimization, and Qiskit Aer QAOA |
| Planned | Common-SUMO driving comparison, EV evaluation, and driver-experience sensitivity |

The formal QAOA comparison has not yet been implemented or executed. The current phase governs and validates the road-network inputs required before optimization results can be interpreted.

## Governed synthetic demand

The initial baseline area-weights the 2020 census 500 m population distribution at the N03 Ota Ward boundary and rescales it to the ward's population on April 1, 2024. It uses a population-normalized rate derived from the fiscal-year 2024 national parcel-delivery total published by Japan's Ministry of Land, Infrastructure, Transport and Tourism.

| Item | Current generated result |
|---|---:|
| 500 m meshes intersecting Ota Ward | 191 |
| Allocated 2024 population | 736,652 |
| Population-normalized parcel rate | 0.111345934 parcel-equivalents/person/day |
| One-day synthetic demand | 82,023 parcel-equivalents |

These values are not observed orders, customers, destinations, or delivery stops. They form a population-proportional baseline scenario derived from national parcel statistics. The equations, boundary treatment, largest-remainder allocation, and prohibited interpretations are documented in [`baseline_demand_and_comparator.md`](05_src/traffic_simulation/demand/baseline_demand_and_comparator.md).

## Compared methods

| Method | Role | Status |
|---|---|---|
| Non-optimizing baseline | Fixed-order comparator that does not reorder requests by distance or time | Specified; implementation planned |
| Classical optimization | Classical solver applied to the common delivery problem | Planned |
| Qiskit Aer QAOA | Incrementally constrained QUBO evaluated on Aer | Planned |

Delivery and EV constraints will not be introduced all at once. Each constraint stage must pass decoding, feasibility, and small-instance checks before expansion. Qiskit Aer is a simulator; its results will not be presented as evidence of physical quantum-hardware performance.

## Main evaluation

For population mesh `g` and method `m`, let `N_g` be the public population, `q` the synthetic demand per person over the evaluation period, and `C_gm` the amount delivered before the deadline. A candidate definition of population-equivalent delivery coverage is:

```text
P_gm = min(N_g, C_gm / q)
P_m  = sum_g(P_gm)
```

In addition to differences among the baseline, classical, and QAOA results, the study will store driving distance, travel time, delay, completion rate, constraint violations, energy use, charging, solution quality, runtime, QUBO size, and circuit-evaluation counts separately. `P_m` is a population-equivalent measure based on public population and synthetic demand; it is not the number of real people who received a delivery.

## Reproducible environments

Docker Compose separates responsibilities:

- `analysis`: Python 3.11 for input validation, geospatial processing, demand generation, tests, and classical methods.
- `sumo`: digest-pinned Eclipse SUMO 1.24.0 for `netconvert`, `sumo`, and `duarouter`.

Both services use `linux/amd64` as the canonical platform. Apple Silicon systems run it through Docker Desktop's architecture emulation, while AMD64 Linux systems can run it natively.

```bash
git clone <repository-url>
cd research

docker compose config
docker compose build analysis
docker compose run --rm analysis python --version
docker compose run --rm sumo sumo --version
docker compose run --rm analysis pytest -q 05_src/traffic_simulation/validation
```

Raw third-party data and generated derivatives are intentionally excluded from Git. Full regeneration therefore requires acquiring the governed source snapshots described in the acquisition records and verifying their hashes. Source URLs, acquisition dates, licenses, SHA-256 values, processing scripts, and output relationships are recorded in [`traffic_simulation_sources.csv`](03_data/metadata/traffic_simulation_sources.csv).

## Visualization

The interactive Ota Ward population and synthetic-demand map can be generated with:

```bash
docker compose run --rm analysis \
  python -m traffic_simulation.visualization.render_study_area \
  --region ota_ward \
  --baseline-demand \
  --output \
  reproducibility/outputs/traffic_simulation/visualization/ota_ward_baseline_demand.html \
  --overwrite
```

See [`visualization/README.md`](05_src/traffic_simulation/visualization/README.md) for the road, signal, and JARTIC review map, layer interpretation, display choices, and operating instructions. Generated HTML files are runtime artifacts and are not committed to Git.

## Repository guide

| Path | Contents |
|---|---|
| [`00_project_management/`](00_project_management/) | Environment, folder policy, and research management |
| [`01_research_design/`](01_research_design/) | Research design and logical structure |
| [`02_literature/`](02_literature/) | Quantum routing, benchmarking, and literature records |
| [`03_data/metadata/`](03_data/metadata/) | Data provenance, acquisition records, and source registry |
| [`05_src/traffic_simulation/`](05_src/traffic_simulation/) | Traffic environment, demand, calibration, validation, and visualization |
| [`05_src/constraint_evaluation/`](05_src/constraint_evaluation/) | Existing synthetic EVRP constraint analysis |
| [`06_outputs/`](06_outputs/) | Reviewed figures, tables, maps, and reports |
| [`07_presentations/current/`](07_presentations/current/) | Current presentation artifacts |
| [`reproducibility/config/`](reproducibility/config/) | Versioned experiment and traffic settings |
| [`reproducibility/outputs/`](reproducibility/outputs/) | Git-ignored, regenerable runtime outputs |
| [`docker/`](docker/) | Isolated Docker environments and operating notes |

## Key documents

- [Traffic-simulation implementation plan](05_src/traffic_simulation/implementation_plan.md)
- [Road-attribute and external-data matching governance](05_src/traffic_simulation/network_attribute_governance.md)
- [Synthetic-demand and non-optimizing-baseline specification](05_src/traffic_simulation/demand/baseline_demand_and_comparator.md)
- [Traffic-simulation visualization guide](05_src/traffic_simulation/visualization/README.md)
- [Data-acquisition record policy](03_data/metadata/acquisition/README.md)
- [Docker environments and SUMO execution boundary](docker/README.md)
- [Folder structure and retention policy](00_project_management/folder_structure.md)
- [Prior reproducibility-audit notebook](reproducibility/quantum_transport_reproducibility_audit_revised.ipynb)

## Data and model governance

- Record acquisition date, version, and SHA-256 for source data, settings, and generated artifacts.
- Distinguish observations, source attributes, estimates, assumptions, and sensitivity-analysis values.
- Do not silently pass missing road attributes to SUMO defaults.
- Separate structural-review networks from formal experimental networks.
- Separate calibration observations from independent-validation observations.
- Use common roads, demand, constraints, traffic conditions, and seed sets for classical and QAOA comparisons.
- Do not commit raw data, generated networks, or runtime results.
- Do not modify boundaries, source inputs, or matching rules to improve downstream results.

The governing principle is traceability: every adopted value should identify its source or derivation, date, version, confidence, and relationship to the generated output. Low-confidence road matching and unresolved critical attributes are not silently accepted into formal experiments.

## Prior research line

The repository retains the quantum-routing literature analysis and Tokyo synthetic EVRP constraint analysis that preceded the traffic-simulation extension. That research line keeps its frozen inputs and reproducibility audit; the new traffic layer is additive and does not overwrite it.

## Limitations

- Public data cannot reconstruct all vehicle OD flows, real delivery trajectories, customer demand, or every signal phase.
- OSM road attributes contain missing and conflicting values that require external matching and manual review on critical roads.
- Population-proportional synthetic demand does not directly represent business deliveries, daytime population, regional e-commerce use, or redelivery.
- Results from Ota Ward must not be generalized directly to all of Tokyo or other regions.
- Qiskit Aer results must not be presented as physical quantum-hardware performance or proof of quantum advantage.
- Driver-experience effects remain a hypothetical sensitivity analysis until sufficient Tokyo-specific evidence is available.

See [`LICENSE`](LICENSE) for repository licensing. Third-party datasets remain subject to their own licenses and terms recorded in the source registry.
