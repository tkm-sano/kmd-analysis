# Data policy

This public repository versions governed processed inputs used by the current research. Raw downloads are intentionally excluded to avoid redistributing third-party material and to keep the repository reviewable.

The prior non-SUMO route-proxy analysis and its analysis-specific frozen inputs are consolidated under `legacy/non_sumo_route_proxy_analysis/`. Shared provider records, access context, limitations, and source registries remain under `03_data/metadata/` and `02_literature/references/`.

To repeat acquisition or preprocessing, reacquire each source under its current upstream terms and run the relevant scripts under `05_src/data_processing/`. Reacquired raw files belong under `03_data/raw/`, which is ignored by Git.
