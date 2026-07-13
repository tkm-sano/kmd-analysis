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
90_archive/ (removed after adopting the latest-only policy)
99_quarantine/ (temporary review only; cleared after confirmation)
```

## Naming

Research artifacts use `NNN_YYYYMMDD_descriptive_file_name.ext`, or `NNN_YYYYMMDD_vNN_descriptive_file_name.ext` for versions. Names use English snake_case. External dataset identity is preserved in the provenance and renaming maps. Git internals and environment package files are excluded.

## Retention

Current and reproduction-required files remain active. Confirmed superseded versions are permanently deleted after a hash-based log is written. Uncertain files may use temporary quarantine, but quarantine is cleared after a successor or safe-deletion decision is verified. Stale Markdown is deleted after migration.
