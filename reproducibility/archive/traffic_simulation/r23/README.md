# ARCHIVED HISTORICAL RECORDS

Files under this directory are retained only for provenance, auditability, and historical reproducibility. They are **NOT current scientific/status authority**. Superseded audits, failed runs, preliminary measurements and obsolete status snapshots are SUPERSEDED HISTORICAL RECORDS. Final accepted raw evidence remains backing evidence for the current summary; archival location does not invalidate that evidence.

For current R23 status and results, see [R23_STATUS.md](../../../../05_src/traffic_simulation/R23_STATUS.md). For accepted closure, see [formal closure record](../../../../reproducibility/outputs/traffic_simulation/r23_formal_closure/20260913_v1/R23_FORMAL_CLOSURE.md).

## Navigation

- [Verified old-to-new path mapping](ARCHIVE_MANIFEST.csv)
- [Archive manifest review](ARCHIVE_MANIFEST.md)
- [Final clean-run backing evidence](provenance/r23_n5_provenance_clean_run_and_formal_benchmark/20260913_v1/CLEAN_RUN_RESULTS.md)
- [Formal n=5 benchmark backing evidence](audits/r23_n5_full_formal_benchmark_and_closure_review/20260913_v1/README.md)
- [B2 mismatch assessment](audits/r23_n5_full_formal_benchmark_and_closure_review/20260913_v1/B2_SHA_CLOSURE_ASSESSMENT.md)

## Frozen references and restoration

Historical file contents, timestamps, source snapshots, old paths and SHA records are unchanged. Intra-bundle relative references retain their structure. Root-relative historical references may name retired output paths: resolve them with ARCHIVE_MANIFEST.csv, or run `python reproducibility/archive/traffic_simulation/r23/resolve_archived_path.py OLD_REPOSITORY_PATH` from the repository. The resolver verifies the target hash and size and never launches scientific code. For directories, map their contained file paths using the same manifest.

To reproduce a historical execution later, materialize the recorded Git commit in a separate external scratch directory using `git archive <recorded_commit>`, then restore archived evidence into its recorded old paths using the manifest. Never run retired authority generators against the current repository. Git history has not been rewritten.

166 files were already local-only/ignored before cleanup. They remain local-only under the archive, have exact-path .gitignore entries, and are fully preserved in the verified external backup at `/home/takuma/kmd-analysis_history_backup/20260913_r23_archive_cleanup/`. This cleanup does not newly claim that those bytes were historically in Git. Share the backup with the repository when those local historical files are needed.
