# R23 current authority

| Dimension | Current state |
|---|---|
| R23 | `R23_CLOSED_WITH_DOCUMENTED_LIMITATIONS` |
| Code audit | `CODE_AUDIT_PASS_WITH_LIMITATIONS` |
| Reproducibility | `RESULT_REPRODUCED_WITH_LIMITATIONS` |
| Clean run | `R23_PROVENANCE_CLEAN_RUN_PASSED` |
| Unresolved CRITICAL / MAJOR | 0 / 0 |
| R24 | `R24_READY_TO_START`; `R24_NOT_STARTED` |

This file is the sole current R23 index. Roadmap, next steps and the research dashboard refer here. Scientific definitions remain in the canonical specifications; historical documents never override this current status.

## Final scientific evidence

Exact optimal route recovery: **3/3**. Optimizer reported success: **2/3**. rank01: success=false, nfev=300, objective evaluation cap reached. These are distinct outcomes.

Current reproducibility authority is the provenance-complete clean run. Historical rank02/03 lineage remains strongly inferred; it was not rewritten. See [clean-run results](../../reproducibility/archive/traffic_simulation/r23/provenance/r23_n5_provenance_clean_run_and_formal_benchmark/20260913_v1/CLEAN_RUN_RESULTS.md), [launch manifest](../../reproducibility/archive/traffic_simulation/r23/provenance/r23_n5_provenance_clean_run_and_formal_benchmark/20260913_v1/CLEAN_RUN_MANIFEST.json), [exact-reference validation](../../reproducibility/archive/traffic_simulation/r23/provenance/r23_n5_provenance_clean_run_and_formal_benchmark/20260913_v1/EXACT_REFERENCE_VALIDATION.md), and [raw run evidence](../../reproducibility/archive/traffic_simulation/r23/provenance/r23_n5_provenance_clean_run_and_formal_benchmark/20260913_v1/clean_runs/).

## Formal implementation benchmark

n=5 rank01 fixed objective workload; output equivalence PASSED.

| Metric | Baseline | V4 | Observed baseline/V4 ratio |
|---|---:|---:|---:|
| Runtime | 1106.778772 s | 21.575394 s | 51.2982x |
| Peak process RSS | 211,405,768 KiB | 675,432 KiB | 312.9934x |

**Single workload, one valid run per implementation.** Load/repetition limitations remain. These observations establish neither general scalability nor a runtime guarantee, and do not compare quantum and classical hardware. [Measurements and frozen protocol](../../reproducibility/archive/traffic_simulation/r23/audits/r23_n5_full_formal_benchmark_and_closure_review/20260913_v1/README.md).

## Remaining limitations and closure

| Limitation | Severity | Retained evidence |
|---|---|---|
| B2 six SHA mismatches; DERIVED_ARTIFACT_MISMATCH; scientific numeric impact not identified | MODERATE | [B2 assessment](../../reproducibility/archive/traffic_simulation/r23/audits/r23_n5_full_formal_benchmark_and_closure_review/20260913_v1/B2_SHA_CLOSURE_ASSESSMENT.md), [mismatch inventory](../../reproducibility/archive/traffic_simulation/r23/intermediate/r23_repository_rebaseline/20260913_v2/b2_sha_impact_assessment.json) |
| Single n=5 repetition and system load | MODERATE | [benchmark conditions](../../reproducibility/archive/traffic_simulation/r23/audits/r23_n5_full_formal_benchmark_and_closure_review/20260913_v1/SYSTEM_CONDITIONS.md) |
| Historical provenance and small instance selection | Documented limitations; see final reassessment | [findings reassessment](../../reproducibility/archive/traffic_simulation/r23/audits/r23_n5_full_formal_benchmark_and_closure_review/20260913_v1/FINDINGS_REASSESSMENT.md) |

[Accepted formal closure](../../reproducibility/outputs/traffic_simulation/r23_formal_closure/20260913_v1/R23_FORMAL_CLOSURE.md) and its [original limitations register](../../reproducibility/outputs/traffic_simulation/r23_formal_closure/20260913_v1/R23_LIMITATIONS_REGISTER.md) remain byte-identical. Scientific evidence independently reproduced, complete clean-run provenance, correct route/optimizer semantics and zero unresolved CRITICAL/MAJOR support closure with documented non-blocking limitations.

## Authority paths

- [Routing Baseline canonical specification](specifications/ROUTING_BASELINE_CANONICAL.md)
- [R23 canonical specification](specifications/R23_REDUCED_PROBLEM_CANONICAL.md)
- [Roadmap](R23_ROADMAP.md) and [next steps](R23_NEXT_STEPS.md)
- [Archive root and relocation manifest](../../reproducibility/archive/traffic_simulation/r23/README.md)

Archive records retain original paths/hashes in their contents. Use ARCHIVE_MANIFEST.csv or resolve_archived_path.py to resolve an old path; historical generators must not be run against retired output namespaces.
