# Folder Structure and Policy

## Before

The project mixed current scripts, raw and processed data, generated figures, legacy outputs, multiple presentations, backups, submissions, caches, and project documentation at the repository root.

## After

```text
00_project_management/
01_research_design/
02_literature/{quantum_routing,benchmarking_methodology,quantum_utility,references,extraction_tables}/
03_data/{raw/{population,charging,logistics,vehicle_specs,road_network},interim,processed,synthetic,metadata}/
04_notebooks/{active,exploratory,archived}/
05_src/{data_processing,scenario_generation,route_proxy,constraint_evaluation,sensitivity,literature_analysis,visualization}/
06_outputs/{figures/active,tables,maps,reports}/
07_presentations/{current,assets,references,archived_versions}/
08_documents/{manuscripts,abstracts,supplementary}/
reproducibility/{config,data,outputs,src,tests}/
docker/{analysis}/
compose.yaml
.dockerignore
90_archive/ (removed after adopting the latest-only policy)
99_quarantine/ (temporary review only; cleared after confirmation)
```

The repository root contains `README.md`, `LICENSE`, Git and Docker configuration, the numbered research directories, the self-contained `reproducibility/` package, and the isolated `docker/` environments. Current presentations are stored under `07_presentations/current/`; temporary execution logs and historical cleanup inventories are not retained.

The Tokyo traffic-simulation extension is additive and uses dedicated subtrees: raw and processed inputs under `03_data/{raw,processed}/traffic_simulation/`, implementation under `05_src/traffic_simulation/`, reproducible run products under `reproducibility/outputs/traffic_simulation/`, and reviewed final artifacts under `06_outputs/traffic_simulation/`. It does not replace or overwrite the frozen synthetic EVRP analysis.

## Naming

Research artifacts use `NNN_YYYYMMDD_descriptive_file_name.ext`, or `NNN_YYYYMMDD_vNN_descriptive_file_name.ext` for versions. Names use English snake_case. External dataset identity is preserved in the provenance and renaming maps. Git internals and environment package files are excluded.

## Retention

Current and reproduction-required files remain active. Confirmed superseded versions, caches, temporary execution logs, and historical cleanup inventories are deleted. Scientific provenance, validation summaries, manifests, and the current Japanese revision audit remain because they support interpretation or reproduction.
