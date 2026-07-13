# Data policy

This public repository versions the frozen processed inputs needed by the authoritative reproducibility notebook. Raw downloads are intentionally excluded to avoid redistributing third-party material and to keep the repository reviewable.

The authoritative input list is defined in `reproducibility/build_revised_notebook.py`. Provider names, access context, limitations, and source registries are retained under `03_data/metadata/` and `02_literature/references/`.

To repeat acquisition or preprocessing, reacquire each source under its current upstream terms and run the relevant scripts under `05_src/data_processing/`. Reacquired raw files belong under `03_data/raw/`, which is ignored by Git.
