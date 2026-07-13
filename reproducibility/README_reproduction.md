# Quantum transport reproducibility audit

Correct source deck: `/Users/tstakuma/Desktop/github/research/07_presentations/current/0712_MDR2_v2_enriched_appendix.pptx` (SHA-256 `c46822f593c4f7b2417bdf220a56e5fe380f30f0aa7a4e25dc02c7b0acb075b1`). The similarly named `/mnt/data/...appendix(1).pptx` was not used.

## Outcome

The notebook regenerates the complete synthetic-analysis chain from confirmed local snapshots: population-mesh preparation, deterministic customer synthesis, demand and service-time draws, charger screening, vehicle selection, factorial configurations, depot selection, KMeans assignments, nearest-neighbor route proxies, condition evaluation, aggregation, clustered bootstrap, and OAT sensitivity. Regenerated customer, route, and summary tables are compared with the stored artifacts. Circuit-width values and strict historical API identity remain reference-only or missing as documented.

## Run

```bash
cd /Users/tstakuma/Desktop/github/research/reproducibility
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python generate_audit.py
.venv/bin/jupyter nbconvert --to notebook --execute quantum_transport_reproducibility_audit.ipynb --output quantum_transport_reproducibility_audit.ipynb --ExecutePreprocessor.timeout=600
.venv/bin/pytest -q tests
```

The notebook resolves the repository root relative to itself and writes only beneath `reproducibility/outputs`. It treats slide numbers as reference values, never as computed results.

## Status vocabulary

- `CONFIRMED`: directly present in the deck or repository evidence.
- `DERIVED`: uniquely calculated from confirmed inputs.
- `MISSING`: required evidence is absent.
- `REFERENCE_ONLY`: a reported result without a verified derivation.
