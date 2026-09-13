# R23 N5 independent runtime optimization code audit

CODE_AUDIT_FAIL; REMEDIATION_REQUIRED.

Starting main: d4a8d78a04316414a9f19ff143264d96c88b3c9b. Previous v1 code audit was not opened during independent finding generation. Normalized complex128 scientific model, QUBO, Hamiltonian, scalar objective and bit ordering agree. The full acceptance gate fails: probability integrity guards, historical execution provenance, fail-sensitive validation and the convergence claim require correction.

Read acceptance_gate.json, finding_register.json, researcher_degrees_of_freedom.json, and the measured *_probes.json files. Every finding is independent of previous audit classifications. independent_seal.json fixes all independent artifacts before comparison; comparison is a separate later artifact.

Reproduce probes (no optimizer/scientific source writes):

```bash
PYTHONDONTWRITEBYTECODE=1 /home/takuma/.conda/envs/evrp-quantum-temp/bin/python reproducibility/tools/r23_n5_independent_audit.py
```

For archival verification use sha256sum -c SHA256SUMS in this directory. Do not overwrite sealed evidence when reproducing: run from a disposable checkout with a new output root. The report builder refuses to replace an existing seal. Historical final parameters and execution-time dirty sources are unavailable; this audit does not claim trajectory replay. All source changes are prohibited here; remediation and R24 are not executed.
