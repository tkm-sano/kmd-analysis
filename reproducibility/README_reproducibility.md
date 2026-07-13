# Third-party reproduction package

This package performs **Computational Reproduction from Frozen Processed Inputs and Audit Reconstruction**. It does not claim full raw-data acquisition reproduction.

## Build and execute

```bash
cd /path/to/research/reproducibility
python3.11 -m venv .venv
.venv/bin/pip install -r requirements-lock.txt
.venv/bin/python build_revised_notebook.py
.venv/bin/jupyter nbconvert --to notebook --execute \
  quantum_transport_reproducibility_audit_revised.ipynb \
  --output quantum_transport_reproducibility_audit_executed.ipynb \
  --ExecutePreprocessor.timeout=1200
.venv/bin/jupyter nbconvert --to html \
  quantum_transport_reproducibility_audit_executed.ipynb
```

Run from this directory. The notebook discovers the repository root by searching upward for both `.git` and `03_data`; it does not contain a machine-specific absolute path.

## Inputs and outputs

Frozen inputs remain in the repository’s `03_data/processed` and `02_literature` trees. All generated data, figures, audit tables, logs, and manifests are written under `reproducibility/outputs`. This directory is intentionally not versioned: it is recreated by executing the authoritative notebook. The versioned deliverables are `quantum_transport_reproducibility_audit_revised.ipynb`, its PDF export under `output/pdf/`, and the curated final PNG assets under `06_outputs/`.

The notebook dynamically checks required files, columns, imports, input hashes, record counts, key uniqueness, missing evaluation handling, regenerated/stored equivalence, output creation, and slide-result reconciliation. A failed critical test downgrades the final status.

## Interpretation boundary

Synthetic unmet rates are not observed delivery failures. Route proxies are not road-network paths or optimized EVRP solutions. SOC is not evaluated. Circuit-width numbers are retained as unverified slide references rather than reproduced results.
