# Quantum Transportation Research Workspace

## Overview

This project evaluates the problem scale and application-side requirements of quantum computing for transportation, using quantum-routing literature and a Tokyo synthetic EVRP constraint analysis. The canonical statement of the current research is the MDR2 presentation dated 2026-07-12.

The study does not claim real-world routing performance or practical quantum advantage. The Tokyo case uses public-data proxies and synthetic customer configurations to examine payload, operating-time, range, SOC-model coverage, and charging-related constraints.

## Primary files

- Current presentation: `07_presentations/current/0712_MDR2_v2_enriched_appendix.pptx`
- Authoritative analysis and submission notebook: `reproducibility/quantum_transport_reproducibility_audit_revised.ipynb`
- Analysis runner: `05_src/constraint_evaluation/run_tokyo_synthetic_evrp_analysis.py`
- Renderer: `05_src/visualization/render_tokyo_synthetic_evrp_outputs.py`
- Literature extraction tables: `02_literature/extraction_tables/`
- Curated final PNG tables: `06_outputs/tables/`
- Notebook figures: regenerated under `reproducibility/outputs/figures/` when the authoritative notebook is executed

Only the authoritative notebook and curated final PNG tables are versioned as deliverables. Notebook figures—including the complete circuit-width survey figures—are regenerated locally under `reproducibility/outputs/figures/` and excluded by `.gitignore`, together with intermediate CSVs, validation logs, PDF exports, and duplicate SVG/PDF renderings.

## Execution order

1. Create or activate the Python environment described in `00_project_management/research_environment.md`.
2. Validate raw and processed input availability.
3. Run the Tokyo synthetic EVRP analysis.
4. Render tables and figures from generated CSVs.
5. Compare output values and assets with the presentation asset map.

The research logic is documented in `01_research_design/research_structure.md`; data origins are in `03_data/metadata/data_provenance.md`; the repository policy is in `00_project_management/folder_structure.md`.
