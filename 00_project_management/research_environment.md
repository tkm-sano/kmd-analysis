# Research Environment

## Platform

- Operating system: macOS
- Project root: the directory where this repository is checked out
- Python environment: create a project-local `.venv` when needed; it is excluded from Git
- Package specification for the submission audit: `reproducibility/requirements-lock.txt`
- Version control: Git

## Required Python packages

Core packages include pandas, NumPy, SciPy, scikit-learn, Matplotlib, GeoPandas, Shapely, NetworkX, Seaborn, Jupyter, nbformat, and nbclient. The submission-audit environment is pinned in `reproducibility/requirements-lock.txt`.

## Reproduction commands

```bash
python -m venv .venv
.venv/bin/pip install -r reproducibility/requirements-lock.txt
.venv/bin/jupyter nbconvert --to notebook --execute reproducibility/quantum_transport_reproducibility_audit_revised.ipynb --output-dir /tmp --output quantum_transport_reproducibility_audit_executed.ipynb --ExecutePreprocessor.timeout=1200
.venv/bin/python 05_src/constraint_evaluation/run_tokyo_synthetic_evrp_analysis.py --reproduce
.venv/bin/python 05_src/visualization/render_tokyo_synthetic_evrp_outputs.py --reproduce
```

## Known dependencies and risks

- Some files are macOS `compressed,dataless` placeholders and cannot be hashed or read until downloaded.
- Geospatial operations require compatible GDAL/GEOS/PROJ dependencies supplied through GeoPandas wheels or the local environment.
- Network access may be needed only for explicit data-refresh scripts; computational reproduction uses the retained frozen processed inputs. Raw source snapshots are not distributed in Git.
- Random seeds and scenario parameters must remain explicit in the notebook and analysis code.
