# Common v1 audit reproduction

Run from repository root. Do not reuse an existing output directory. No demand
generation, routing optimization experiment, or public OSRM request is needed.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
  /home/takuma/.cache/kmd-analysis/venvs/vehicle-day-v1/bin/python -m pytest \
  tests/toc_common tests/toc_cg tests/toc_vehicle_day tests/toc_search_improvement \
  tests/test_toc_contracts.py -q -p no:cacheprovider

OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
  /usr/bin/time -v /home/takuma/.cache/kmd-analysis/venvs/vehicle-day-v1/bin/python \
  scripts/audit_toc_common.py --output /tmp/common-v1-new-audit
```

Use the existing environment lock at
`reproducibility/environment/vehicle_day_v1/requirements.lock.txt` if the local
environment is absent. The new module requires Python and NumPy; the regression
suite additionally uses pytest/SciPy/Qiskit. No install was performed in this task.
Actual environment versions are recorded in ENVIRONMENT_VEHICLE_DAY.txt.

The old public API regression was run with the existing .conda Python 3.11.15:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
  /usr/bin/time -v /home/takuma/kmd-analysis/.conda/bin/python -m pytest tests \
  --ignore=tests/toc_cg --ignore=tests/toc_vehicle_day \
  --ignore=tests/toc_search_improvement --ignore=tests/toc_common \
  --ignore=tests/test_toc_frozen_demand.py --ignore=tests/test_toc_contracts.py \
  -q -p no:cacheprovider
```

This reports 45 passed and 4 pre-existing failures. Their evidence is in
PREEXISTING_REGRESSION_FAILURES.json. Do not rewrite the release manifest or
restore historical links as part of this audit. The frozen demand test file is
excluded because its class setup invokes demand bundle generation; the new tests
read the existing pinned bundle and corrupt temporary byte copies only.

`audit_final/` is the final data/fixture run. `audit_results/` is the first audit
and is preserved. Timing differences are measurements, not performance claims.
The tests' synthetic matrices are explicitly labelled and must never be used as
the S1–S3 research OD. Fixture construction is a specified witness, not VeRyPy,
OR-Tools, or AOA execution.

Real road precomputation remains HOLD until the entrance, snap reviews and local
OSRM graph/profile provenance exist. `common.od.generate_local_od` provides the
opt-in block writer, tested with injected responses only. No live server was
queried. Raw OSM hash checks are read-only.

PRESERVATION_BEFORE.json inventories all original tracked files plus the existing
research/code/test/result directories (47,440 files; excludes caches and Git
internals). PRESERVATION_AFTER.json hashes exactly this same list. TASK_FILE_HASHES.json
lists the new task source/doc files. FINAL_REVIEW.json records gate ordering,
unchanged file count, status/diff checks and individual readiness decisions.

To independently recheck preservation:

```python
from pathlib import Path
import hashlib, json
p = Path('output/toc_delivery/common_v1_audit_20261111/PRESERVATION_BEFORE.json')
for name, expected in json.loads(p.read_text())['files'].items():
    h = hashlib.sha256()
    with Path(name).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    assert h.hexdigest() == expected['sha256'], name
```

Do not run S1–S3 solvers, regenerate frozen demand, commit or push when reproducing
these checks.
