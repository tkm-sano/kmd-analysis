# R23 runtime remediation contract

Authority: independent audit commit `33ae964bca0e61199621ee976a927cd4069e1723`, `20260913_v2_independent`. Original finding IDs remain unchanged; the remediation artifact maps the differently numbered request sections to them.

## Probability and output contract

Scientific model, λ=4.0, p=1, COBYLA, fixed_0.1, raw full-state denominator and absolute tolerance 1e-12 are unchanged. Float64 or complex128 inputs are required; float32/complex64 are rejected, not converted. Unit norm, finite intermediate/results and the original range tolerance are required. Violations raise V4InputError; no normalization, clipping, NaN replacement or invalid-mass repair is permitted. Tiny roundoff within the original 1e-12 range tolerance is retained as-is.

`r23-v4-indexed-report-v1` reports P_total, P_feasible, P_optimal over all supplied optimum states, P_invalid, and the minimum-cost feasible route above the original reporting threshold. It explicitly omits full records, most-probable-state diagnostics and energy variance. It is not the complete original result schema. The optimizer scalar and selection semantics are unchanged.

## Historical evidence and claims

Historical scientific results, exact references, manifests and execution records are immutable. Current legacy generator entrypoints are retired because they could overwrite evidence or emit unconditional PASS; their exact previous sources are archived separately and remain in git. Archival PASS strings are not executable acceptance authority. The new assertion harness calls the actual candidate and independent references; missing/unexecuted checks are NOT_TESTED/PARTIAL/BLOCKED, never VERIFIED. Empty, duplicated or tampered test manifests fail their gate.

Existing records show route recovery 3/3 and relative route gap zero 3/3; native optimizer success is 2/3. rank01 success=false and cap reached. rank02/03 remain unreauthorized pending execution/resource provenance closure. All P_feasible values are below 1%; P_optimal is about 5.45e-5 to 6.64e-5. Original rank01 consumed 42.62h and reported 201.58GiB absolute peak RSS. Independent audit FAIL and previous result NOT_REPRODUCED remain on record. No quantum advantage, general optimizer superiority, robustness or general scaling law follows. n≥6 is not recommended under the current exact CPU Aer method.

COBYLA and p=1 were fixed before n5, after B2 results existed; baseline continuity is the rationale, not a claim of B2 independence. Recovered timestamped runner creation/diffs support pre-run cap300/maxiter300/default options, with residual process-attestation limitations. Reconstructed snapshots do not retroactively change recorded commit metadata.

## Prospective benchmark contract (not executed here)

Formal comparison is NOT_TESTED. Historical numbers are PRELIMINARY_ONLY. Do not claim formal 33.7× acceleration or 327× memory reduction. Original absolute peak 201.6GiB and candidate approximately 0.615GiB observed RSS / reported increments are not interchangeable; the 0.615 figure itself is not a validated absolute process peak. Preserve exact original metric labels in citations.

Freeze the next benchmark manifest before outcomes: host hayate, AMD EPYC 9684X, 192 physical/384 logical CPUs (verify actual host), one process, one thread, affinity [0] (fail if unavailable), OMP_NUM_THREADS=1, OPENBLAS_NUM_THREADS=1, MKL_NUM_THREADS=1, Aer max_parallel_threads=1. Use frozen Python/dependency authority, exact CPU statevector, rank01 initial [0.1,0.1], p1, unchanged Hamiltonian and seed17. These are prospective resource controls, not claims about historical settings. No optimizer run is implied.

Use five fresh-process repetitions per implementation in pre-fixed alternating original/candidate order. Record one separately labeled warm-up evaluation, then one measured evaluation and full final reporting per process. Save all times, failures and warm-up costs; do not drop fastest/slowest/failed repetitions. Report `T_total=T_setup+T_warmup+T_evaluation+T_final`; report the evaluation boundary separately. Setup includes input/reference preparation; circuit/Hamiltonian/index construction and backend creation are charged where they actually occur. Do not omit repeated construction from evaluation. Final includes actual helper guards, optimum lookup and route decoding. Declare all caches; no reuse beyond the code under test. A failed side makes paired speedup NOT_TESTED/PARTIAL, not successful-only aggregation.

Memory is absolute process peak RSS in bytes, from independent /proc VmHWM sampling plus ru_maxrss*1024, with PID/process boundary recorded. Report RSS snapshots and increments separately and reconcile discrepancies before comparison. Parent/child and thread accounting must be explicit. Historical rank02/03 ru_maxrss values disagree with contemporaneous process RSS; do not treat them as validated memory savings.

## Future formal execution metadata

Before launching, freeze a new authority manifest and new output namespace. Require clean committed source, full source manifest, git commit, source/runner/helper/authority SHA256, environment path and dependency versions, host/CPU, thread/affinity/OMP/BLAS/Aer settings, command line, effective optimizer options including defaults and cap, and all seeds (explicit NOT_APPLICABLE where appropriate). Never overwrite the historical n5 namespace.

At completion retain timezone-aware start/end timestamps, native termination, final parameters, complete compact objective trace and SHA256, resource metric/units/PID/timer boundaries, source hashes rechecked against launch, stdout/stderr and process exit code. `execution_provenance.validate_formal_run_metadata` provides a fail-closed structural admission guard. Missing metadata is FORMAL_RUN_PROVENANCE_INCOMPLETE; syntactically valid metadata alone does not establish scientific acceptance. Bind all hash entries to archived files and verify them before promotion. Legacy runner outputs cannot be promoted without this contract and independent review.

R24 remains NOT_AUTHORIZED_PENDING_R23_REMEDIATION. After remediation, a different task must perform `R23_N5_RUNTIME_OPTIMIZATION_CODE_AUDIT_POST_REMEDIATION_RERUN`; only a subsequent independent PASS permits phase closure and consideration of R24. No new audit PASS is declared by the remediation author.
