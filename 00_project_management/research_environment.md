# Research Environment

## Platform

- Operating system: macOS
- Project root: `/Users/tstakuma/Desktop/github/research`
- Python environment: create a project-local `.venv` when needed; it is excluded from Git
- Package specification for the submission audit: `reproducibility/requirements-lock.txt`
- Version control: Git

## Required Python packages

Core packages include pandas, NumPy, SciPy, scikit-learn, Matplotlib, GeoPandas, Shapely, NetworkX, Seaborn, Jupyter, nbformat, and nbclient. The submission-audit environment is pinned in `reproducibility/requirements-lock.txt`.

## Reproduction commands

```bash
python -m venv .venv
.venv/bin/pip install -r reproducibility/requirements-lock.txt
TOKYO_EVRP_REPRODUCE=1 .venv/bin/jupyter nbconvert --to notebook --execute --inplace 04_notebooks/active/tokyo_synthetic_evrp_constraint_gap_analysis.ipynb
.venv/bin/python 05_src/constraint_evaluation/run_tokyo_synthetic_evrp_analysis.py --reproduce
.venv/bin/python 05_src/visualization/render_tokyo_synthetic_evrp_outputs.py --reproduce
```

## Known dependencies and risks

- Some files are macOS `compressed,dataless` placeholders and cannot be hashed or read until downloaded.
- Geospatial operations require compatible GDAL/GEOS/PROJ dependencies supplied through GeoPandas wheels or the local environment.
- Network access may be needed only for explicit data-refresh scripts; reproduction should prefer retained raw snapshots.
- Random seeds and scenario parameters must remain explicit in the notebook and analysis code.
