# Tokyo Traffic × Quantum Routing Research

This repository builds a public-data-based traffic approximation for Ota Ward, Tokyo, and compares a non-optimizing baseline, classical optimization, and QAOA on Qiskit Aer using the same synthetic electric-vehicle delivery problem.

> **Primary research question**
>
> Under identical vehicles, capacity, battery, departure time, demand, traffic, weather, and evaluation conditions, how much does route-order optimization change population-equivalent delivery coverage, and how do classical optimization and Aer-based QAOA differ in outcome and computational resources?

## Research objective

This research builds a reproducible traffic-simulation and route-optimization framework for Ota Ward that:

- constructs a governed road environment from date-pinned OSM data and the official N03 administrative boundary;
- calibrates and independently validates traffic conditions with public observations;
- generates traceable population-based delivery demand and EV delivery scenarios;
- compares a non-optimizing baseline, classical optimization, and Qiskit Aer QAOA under identical conditions; and
- quantifies how route optimization changes population-equivalent delivery coverage, operational outcomes, solution quality, and computational-resource requirements.

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

## Methodology overview

```mermaid
%%{init: {"theme": "dark", "themeVariables": {"background": "#0d1117", "lineColor": "#8b949e", "textColor": "#ffffff"}}}%%
flowchart TD
    D1["1. Open data<br/>N03 · OSM · JARTIC · census · public statistics"]
    D2["2. Provenance control<br/>date · license · version · SHA-256"]
    D3["3. Common research inputs<br/>Ota boundary · governed roads · synthetic demand"]
    D4["4. Validated traffic environment<br/>SUMO network · calibration · independent validation"]
    D5["5. Frozen delivery problem<br/>same demand · vehicles · constraints · seeds"]

    M1["6A. Non-optimizing baseline"]
    M2["6B. Classical optimization"]
    M3["6C. Qiskit Aer QAOA"]

    D6["7. Visit order → common road-path conversion"]
    D7["8. Same SUMO environment"]
    E1["9A. Operational and social effects<br/>distance · time · energy · delivered amount · population-equivalent coverage"]
    E2["9B. Computational resources<br/>runtime · solution quality · QUBO and circuit indicators"]
    D8["10. Final comparison<br/>population-equivalent coverage ↔ computational resources"]

    D1 --> D2 --> D3 --> D4 --> D5
    D5 --> M1
    D5 --> M2
    D5 --> M3
    M1 --> D6
    M2 --> D6
    M3 --> D6
    D6 --> D7 --> E1 --> D8
    M1 --> E2
    M2 --> E2
    M3 --> E2
    E2 --> D8

    classDef textOnly fill:none,stroke:none,color:#ffffff;
    class D1,D2,D3,D4,D5,M1,M2,M3,D6,D7,E1,E2,D8 textOnly;
    linkStyle default stroke:#8b949e,stroke-width:2px;
```

The diagram separates the two final lines of evidence. The common SUMO runs measure operational and social effects, while the solver records measure computational effort. Their final relationship is evaluated without treating a simulated QAOA resource indicator as a confirmed physical-hardware requirement or quantum advantage. Delivery constraints and EV constraints are added in controlled stages only after the preceding problem formulation passes feasibility, decoding, and small-instance validation.

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

## Open-data inputs

The study uses public sources for different, explicitly separated roles. A source used for geometry is not automatically treated as evidence for speed, demand, or legal traffic restrictions.

| Open-data snapshot | Provider | Research role | Current treatment |
|---|---|---|---|
| N03 administrative boundaries, 2026 | MLIT National Land Numerical Information | Define the Ota Ward study boundary | Select Ota Ward by municipality code and names, dissolve the six source features, and preserve the resulting geometry without smoothing, simplification, or buffering |
| Kanto OpenStreetMap PBF, dated 2026-07-16 | Geofabrik / OpenStreetMap contributors | Base road geometry, connectivity, and candidate road attributes | Pin the regional PBF by date and SHA-256, then extract the acquisition BBOX mechanically derived from the N03 boundary |
| One-hour road-type-3 traffic observations, 2026-07-04 22:00 JST | JARTIC / MLIT xROAD | Initial traffic observation and processing validation | Preserve source directions and anomaly flags; use observed traffic and speed for calibration or validation, never as an unqualified legal speed limit |
| 2020 census 500 m population mesh, JGD2011 mesh 5339 | Statistics Bureau of Japan / e-Stat | Spatial distribution for synthetic demand | Read the exact official ZIP member, decode the documented fields, intersect it with the N03 boundary, and area-weight boundary meshes |
| Ota Ward population, 2024-04-01 | Ota City open data | Target total for the 2024 population distribution | Rescale the area-weighted 2020 mesh distribution to the published ward total of 736,652 |
| Japan total population, 2024-10-01 | Statistics Bureau of Japan | Denominator for the national parcel-equivalent rate | Read the published total of 123,802,000 using the source unit conversion recorded in configuration |
| FY2024 national parcel-delivery total | MLIT | Numerator for the national parcel-equivalent rate | Use 5,031,470,000 parcels as a national aggregate; do not reinterpret it as observed Ota Ward orders or stops |

The machine-readable registry is [`traffic_simulation_sources.csv`](03_data/metadata/traffic_simulation_sources.csv). It records provider URLs, acquisition dates, source periods and areas, licenses, original filenames, SHA-256 values, processing scripts, derived outputs, and known limitations. Human-readable acquisition records document the actual download and verification operations:

- [JARTIC traffic observation](03_data/metadata/acquisition/20260717_jartic_traffic_volume_acquisition.md)
- [N03 Tokyo administrative boundary](03_data/metadata/acquisition/20260717_mlit_n03_2026_tokyo_acquisition.md)
- [OSM PBF and Ota Ward extraction](03_data/metadata/acquisition/20260717_osm_ota_ward_acquisition.md)
- [Population and parcel statistics](03_data/metadata/acquisition/20260718_ota_baseline_open_statistics_acquisition.md)

Raw source files are stored under `03_data/raw/traffic_simulation/` and excluded from Git. Their recorded hashes, not filenames alone, identify the governed snapshots used by the study.

## Transformation rules

### Boundary and coordinate systems

- Ota Ward is selected from N03 using municipality code `13111` together with the recorded prefecture, municipality, and ward names.
- The six N03 source features are dissolved into one study boundary without manually adjusting the shape to improve later results.
- Source coordinates use JGD2011 (`EPSG:6668`), web/API exchange uses WGS 84 (`EPSG:4326`), and area and distance calculations use Japan Plane Rectangular CS IX (`EPSG:6677`).
- The OSM acquisition BBOX is the minimum rectangle derived from the boundary. It controls data acquisition only; the N03 polygon remains the analysis boundary.

### Road geometry, attributes, and SUMO conversion

- Date-pinned OSM supplies the base geometry and connectivity. The governed workflow uses a regional PBF, not Overpass.
- The PBF is clipped to the recorded acquisition BBOX, converted to OSM XML with a fixed tool version, and then passed to the digest-pinned SUMO `netconvert` service. Python validation and preprocessing remain in the separate `analysis` service.
- SUMO uses left-hand traffic. Internal junction links are retained, U-turns are limited to dead ends, and isolated edges are reported rather than silently deleted.
- Missing, supplemented, unresolved, and conflicting OSM attributes are reported with their source, derivation, date, and confidence. They are not silently delegated to SUMO or typemap defaults.
- `oneway` is checked in this order: explicit OSM value, OSM implicit rule, public regulation data, and road-census evidence. A general road with no applicable evidence is interpreted as bidirectional under OSM data-consumption rules and labelled as a derived value, not a field-confirmed fact.
- `lanes` is checked using explicit and directional OSM tags, road-census data, road ledgers, limited aerial-image review, and finally a versioned structural placeholder only where permitted.
- `maxspeed` is checked using explicit, directional, and conditional OSM tags followed by public regulation information, road-census evidence, official documents, and dated legal derivation rules. Observed travel speed is not substituted for a legal speed limit.
- External road attributes are not joined by nearest distance alone. Matching considers distance, direction, overlap, road name or number, road class, and vertical layer. Ambiguous elevated roads, surface roads, carriageways, side roads, and complex junctions receive lower confidence and require review when they are critical.
- Structural-review networks may use documented placeholders on noncritical roads for connectivity and visualization checks. Formal experimental networks stop when critical route, calibration, or validation roads contain unresolved attributes, conflicts, low-confidence matches, or unrecorded manual values.
- Junction heuristics may generate candidates, but formal conversion uses a reviewed integration table; automatic junction merging is disabled for the formal network.

The authoritative policy and the current SUMO configuration are [`network_attribute_governance.md`](05_src/traffic_simulation/network_attribute_governance.md) and [`sumo_network.yml`](reproducibility/config/traffic_simulation/sumo_network.yml). The formal SUMO network has not yet been generated, so the rules above distinguish implemented input governance from the next conversion stage.

### Traffic observations

- A JARTIC observation site is expanded into source-defined directional rows only when the source contains those directions; the procedure does not invent an up/down split.
- Loop, ultrasonic, power-outage, and missing-data flags are preserved. Invalid observations remain invalid or missing rather than being imputed silently.
- Calibration observations and independent-validation observations must be separated by location or period before model fitting.

## Governed synthetic demand

The implemented baseline converts public population and parcel statistics into a reproducible one-day, population-proportional demand surface. The operation is fixed by [`baseline_demand.yml`](reproducibility/config/traffic_simulation/baseline_demand.yml) and performed by [`prepare_baseline_demand.py`](05_src/traffic_simulation/demand/prepare_baseline_demand.py).

The processing sequence is:

1. Verify the configured source filenames and SHA-256 values before reading any data.
2. Read only the recorded census ZIP member using its documented CP932 encoding and population field.
3. Reconstruct the official nine-digit JGD2011 500 m mesh geometries for mesh 5339.
4. Intersect the meshes with the unmodified N03 Ota Ward boundary. Fully contained meshes retain their population; boundary meshes receive an area ratio calculated in `EPSG:6677`.
5. Rescale the area-weighted 2020 spatial distribution to the official Ota Ward population on April 1, 2024.
6. Allocate whole people with the largest-remainder method. Equal remainders are resolved by ascending mesh code, making the result deterministic.
7. Derive the national daily parcel-equivalent rate as `5,031,470,000 / 123,802,000 / 365`.
8. Multiply each mesh's allocated population by that rate, then allocate the one-day integer demand with the same largest-remainder and tie-breaking rules.
9. Write a GeoParquet demand surface and a JSON quality summary only after total, geometry, boundary, and lineage checks pass.

The resulting rate is `0.111345933951539499` parcel-equivalents per person per day. The unrounded ward expectation is approximately `82,023.205`; deterministic integer allocation produces 82,023 parcel-equivalents.

| Item | Current generated result |
|---|---:|
| 500 m meshes intersecting Ota Ward | 191 |
| Fully contained meshes | 122 |
| Boundary-intersecting meshes | 69 |
| Area-weighted 2020 population before rescaling | 747,271.088683 |
| Allocated 2024 population | 736,652 |
| Population-normalized parcel rate | 0.111345934 parcel-equivalents/person/day |
| One-day synthetic demand | 82,023 parcel-equivalents |

The operation was validated and run in Docker as follows:

```bash
docker compose build analysis

docker compose run --rm analysis \
  pytest -q \
  05_src/traffic_simulation/validation/test_prepare_baseline_demand.py

docker compose run --rm analysis \
  python -m traffic_simulation.demand.prepare_baseline_demand

docker compose run --rm analysis \
  pytest -q 05_src/traffic_simulation/validation
```

The processor writes:

- `03_data/processed/traffic_simulation/demand/ota_ward_baseline_demand_2024_500m.parquet`
- `03_data/processed/traffic_simulation/validation/ota_ward_baseline_demand_2024_500m_quality_summary.json`

Outputs are write-once by design: the processor refuses to overwrite an existing governed result. Reproduction should use a fresh workspace, or deliberately archive and remove the old generated outputs after confirming their lineage; an overwrite flag is not provided. Generated data remain excluded from Git.

These values are not observed orders, customers, destinations, delivery stops, or household order probabilities. The national total includes multiple parcel-flow types and is used only as a population-normalized aggregate. The mesh result is therefore a governed synthetic baseline for controlled comparison, not a reconstruction of actual Ota Ward deliveries. The equations, boundary treatment, allocation rules, quality checks, and prohibited interpretations are documented in [`baseline_demand_and_comparator.md`](05_src/traffic_simulation/demand/baseline_demand_and_comparator.md).

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
