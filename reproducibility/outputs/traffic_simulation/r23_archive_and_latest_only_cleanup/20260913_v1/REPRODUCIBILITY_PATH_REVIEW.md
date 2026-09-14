# Reproducibility path review

Verified: current R23_STATUS.md → archived CLEAN_RUN_RESULTS.md → CLEAN_RUN_MANIFEST.json / SOURCE_HASHES.json / ENVIRONMENT.json → clean_runs/<instance>/RUN_START.json, result.json, RUN_END.json. Runner and scientific source/input hashes match the accepted manifest. All three run-end output SHA bindings match current archived result bytes. The manifest Git commit exists. Scientific inputs remain at their recorded active paths.

Final exact-reference records and historic raw references were relocated without changing bytes. Current index links independent exact-validation reports and the raw clean-run directory. The formal benchmark manifests, measurements and runner remain together. B2 mismatch records and assessments are retained and linked.

Old embedded root-relative paths and old per-file SHA lists were intentionally not rewritten. ARCHIVE_MANIFEST.csv and the hash-checking resolver provide old→new lookup. Re-executing an old runner later requires a separate external Git-archive materialization plus restoring recorded old evidence paths; it must not run against the retired live namespace. This cleanup validates traceability, not a new scientific reproduction.

Local-only historical bytes remain in the local archive and verified external backup; their original untracked status is explicit. No scientific package/environment changes occurred.
