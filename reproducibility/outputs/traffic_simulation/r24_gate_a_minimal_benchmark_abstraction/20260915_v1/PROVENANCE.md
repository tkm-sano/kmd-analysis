# Provenance

Decision date: 2026-09-15 JST. Repository start commit: `5bb6829ced63195dcbd3ce5785c8e66331994b6b`. Existing tracked worktree was clean at inspection. This output directory is ignored by repository rules and is not committed or staged.

## Primary inputs

| input | sha256 |
|---|---|
| `daily_requests.csv` | `4bb78cf27b2a3e9a0648cca39266cb06de4dee0789febed9cd74b61a8e4c2f99` |
| `request_building_mapping.csv` | `bdbb2b2c25c2a64f7fe0f6e4b89fa812a02d152d7cdbd10f17b34ce3601f88e4` |
| `building_delivery_stops_scoped.csv` | `fcfca5cb87bc482f1d98306c98823773e872f200c58ecb9090aa12985e3e80e0` |
| `candidate_delivery_edge_connections.csv` | `226ff0d1ae91f08ea872cd99a3da5092fee19cf99259f7da81db79135762df7a` |
| `candidate_validation_manifest.json` | `c99d877a255f58433a642a4ac88854d2af02f1879579631360c46f1221bd986f` |
| `ROUTING_BASELINE_CANONICAL.md` | `9eb9966d922a0164d94cd0e4c1c1b805d172bb429c1efcd93d50d721d67f1260` |
| planning-horizon decision | `cfc270784c179916f5db0af305f6b2e5b1b78e72b6477263cfcb98991af2383d` |

Input paths are relative to repository root. The source counts, joins, geometry ranges and duplication statistics were recomputed read-only with repository `.conda/bin/python` and pandas. No demand generator, mapper, router, sampler or optimizer was executed. No source or historical artifact was modified.

The R03 manifest calls its run_2 network accepted for that historical mapping. This package does not promote it to the current canonical run_3 Routing Baseline; the distinction is why final eligibility remains pending. Output hashes are recorded in `SHA256SUMS.txt`, excluding that manifest itself to avoid self-reference.

