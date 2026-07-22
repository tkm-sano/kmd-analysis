# Folder Structure and Policy

## Before

The project mixed current scripts, raw and processed data, generated figures, legacy outputs, multiple presentations, backups, submissions, caches, and project documentation at the repository root.

## Final Target Structure

This is the intended final logical layout. It shows where each research stage leaves its source data, governed configuration, implementation, regenerable products, and reviewed deliverables. A `[P]` entry is planned and must not be interpreted as implemented merely because it appears in this diagram.

```text
research/
├── 00_project_management/                 [G] repository policy, environment, and research study guide
├── 01_research_design/                    [G] questions, hypotheses, and analysis design
├── 02_literature/                         [G] evidence and directly linked references
│   ├── references/                        [G] inventory, paper registry, and BibTeX
│   └── extraction_tables/                 [G] structured evidence extraction
├── 03_data/
│   ├── raw/                               [L] immutable third-party snapshots
│   │   └── traffic_simulation/            [L] N03, OSM, JARTIC, census, and related sources
│   ├── processed/                         [R] governed intermediate datasets
│   │   └── traffic_simulation/            [R] boundaries, demand, SUMO networks, and audits
│   ├── synthetic/                         [R] generated research instances
│   └── metadata/                          [G] source registry and chronological acquisition records
├── 04_notebooks/                          [P] active, exploratory, and archived notebooks
├── 05_src/                                [G] implementation
│   ├── traffic_simulation/
│   │   ├── network/                       [G] boundary, OSM, and SUMO-network preparation
│   │   ├── demand/                        [G] governed synthetic delivery demand
│   │   ├── calibration/                   [G] JARTIC preparation and calibration
│   │   ├── simulation/                    [P] scenario construction and SUMO execution
│   │   ├── validation/                    [G] unit tests, fixtures, and governance checks
│   │   └── visualization/                 [G] review-map generation
├── 06_outputs/                            [G] reviewed figures, tables, maps, and reports
│   └── traffic_simulation/                [G] selected traffic-study deliverables
├── 07_presentations/                      [G] current presentation and cited assets
├── 08_documents/                          [G] manuscript and supplementary material
├── reproducibility/
│   ├── config/                            [G] versioned machine-readable settings
│   │   └── traffic_simulation/            [G] study area, demand, SUMO, and typemap policy
│   └── outputs/traffic_simulation/        [R] current regenerable runtime products
├── legacy/non_sumo_route_proxy_analysis/  [G] prior proxy data, code, figures, and audit package
├── docker/                                [G] isolated analysis and SUMO environments
├── compose.yaml                           [G] canonical service boundary
├── README.md                              [G] repository entry point and current status
└── LICENSE                                [G] repository license
```

Legend:

- `[G]`: Git-managed source, policy, metadata, test, or reviewed deliverable.
- `[L]`: local governed source data; excluded from Git and reacquired from its recorded source.
- `[R]`: regenerable artifact; excluded from Git unless explicitly promoted as a reviewed deliverable.
- `[P]`: planned location or module that is not yet evidence of implementation.

The intended artifact flow is:

```text
03_data/raw + 03_data/metadata + reproducibility/config
                         │
                         ▼
                      05_src
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
      03_data/processed      reproducibility/outputs
              │                     │
              └──────────┬──────────┘
                         ▼
                  06_outputs / 08_documents
```

The numbered directories describe the research lifecycle. `reproducibility/` is the machine-oriented execution boundary: it does not replace the source records, implementation, or reviewed research outputs in the numbered directories.

## Compact Path Inventory

```text
00_project_management/
01_research_design/
02_literature/{quantum_routing,benchmarking_methodology,quantum_utility,references,extraction_tables}/
03_data/{raw/{population,charging,logistics,vehicle_specs,road_network},interim,processed,synthetic,metadata}/
04_notebooks/{active,exploratory,archived}/
05_src/{data_processing,literature_analysis,traffic_simulation,visualization}/
06_outputs/{figures/active,tables,maps,reports}/
07_presentations/{current,assets,references,archived_versions}/
08_documents/{manuscripts,abstracts,supplementary}/
reproducibility/{config,outputs/traffic_simulation}/
legacy/non_sumo_route_proxy_analysis/{data,src,outputs,reproducibility}/
docker/{analysis}/
compose.yaml
.dockerignore
90_archive/ (removed after adopting the latest-only policy)
99_quarantine/ (temporary review only; cleared after confirmation)
```

The repository root contains `README.md`, `LICENSE`, Git and Docker configuration, the numbered research directories, the current traffic-simulation `reproducibility/` boundary, the consolidated non-SUMO archive, and the isolated `docker/` environments. Current presentations are stored under `07_presentations/current/`; temporary execution logs and historical cleanup inventories are not retained.

The Tokyo traffic-simulation extension uses dedicated subtrees: source-specific raw inputs under `03_data/raw/traffic_simulation/`, generated inputs under `03_data/processed/traffic_simulation/`, source records in `03_data/metadata/traffic_simulation_sources.csv`, implementation under `05_src/traffic_simulation/`, reproducible run products under `reproducibility/outputs/traffic_simulation/`, and reviewed final artifacts under `06_outputs/traffic_simulation/`. Canonical paths are defined in `05_src/traffic_simulation/paths.py`; new modules do not use host-specific paths or fixed parent indexes. The frozen synthetic EVRP route-proxy line is isolated under `legacy/non_sumo_route_proxy_analysis/` and is not a formal traffic-simulation input.

## Naming

Research artifacts use `NNN_YYYYMMDD_descriptive_file_name.ext`, or `NNN_YYYYMMDD_vNN_descriptive_file_name.ext` for versions. Names use English snake_case. External dataset identity is preserved in the provenance and renaming maps. Git internals and environment package files are excluded.

## Retention

Current and reproduction-required files remain active. Confirmed superseded versions, caches, temporary execution logs, and historical cleanup inventories are deleted. Scientific provenance, validation summaries, manifests, and the current Japanese revision audit remain because they support interpretation or reproduction.
