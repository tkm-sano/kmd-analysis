# R23 I03 validation gate contract

This is an I03-only continuation of remediation commit `9cce6eb`. It changes validation/reporting, not scientific execution parameters or historical evidence. Old authorization/report writers now call a read-only validator and print JSON; they no longer issue authorizations or overwrite historical namespaces. The two B2 execution scripts change preflight validation records only. Their scientific calls/options are AST-compared against the starting commit; no run is started.

## Status and aggregation

`VERIFIED`: an executed condition succeeded; `FAILED`: an executed condition failed; `BLOCKED`: required evidence is missing/unreadable; `NOT_TESTED`: not executed; `PARTIAL`: only part of applicable checks completed. Historical guarded `PASS` maps to VERIFIED only for the specific executed preflight/assertion it represents. Artifact existence and declared historical statuses are not scientific revalidation.

Each check declares REQUIRED, OPTIONAL or NOT_APPLICABLE. An empty gate is NOT_TESTED. Among REQUIRED checks, FAILED takes priority over BLOCKED; otherwise all VERIFIED gives VERIFIED, all NOT_TESTED gives NOT_TESTED, and a mixture gives PARTIAL. No REQUIRED checks gives PARTIAL. OPTIONAL outcomes remain visible but do not decide required integrity. NOT_APPLICABLE checks are not failures. The n5 compatibility gate follows these statuses while retaining its `passed` boolean and exact required-ID/evidence contract.

## Dimensions

Execution completeness compares the nonempty planned manifest run set with every actual run file, retaining optimizer failures. Artifact integrity compares actual bytes with declared manifest/terminal/baseline hashes. Scientific validity checks conditions, initialization vectors, native termination metadata and independently recomputed directed route cost/gap. Feasibility checks customer permutation, bits and Qiskit ordering. Probability integrity recomputes raw full-basis total/feasible/optimal/invalid masses at 1e-12 without candidate helpers. Exact references are checked by independently enumerating permutations over the frozen R20 normalized matrix.

Exact optimum recovery and native optimizer convergence/success are OPTIONAL outcomes, not scientific-integrity prerequisites. A valid non-optimal route is not inherently corrupt. A well-recorded success=false run remains in the scientific dataset. A missing success field is BLOCKED; malformed success is FAILED. COBYLA numeric `nit` and a stored B1 route-gap field are NOT_APPLICABLE where absent: the native API permits `nit=None`, and B1 gap is derived instead of invented as zero.

Provenance verification means **recorded authority SHA consistency**, not attestation of process memory or proof that every imported file matched at historical runtime. Source-attestation limitations remain outside this I03 repair. R21/R22 lineage verifies pinned result/manifest hashes, manifest binding and declared per-instance check consistency; fresh scientific revalidation is explicitly NOT_TESTED. The lineage admission check refuses an empty or incomplete check set even if a caller writes `status=VERIFIED`.

## Dataset failures versus validator correctness

The B2 v2 terminal index contains six stale run-file hashes. The new validator must report artifact integrity FAILED; this task does not rewrite the index or raw runs. B2 v1 failure records remain included in a separate profile and cannot obtain overall scientific integrity VERIFIED. These detections do not mean the validator must be adjusted to reproduce a previous successful classification.

A successful I03 remediation verifies that the gates correctly distinguish valid, invalid, missing and untested evidence. It does **not** accept B2 evidence whose artifact integrity fails. The newly exposed B2 mismatch must accompany the independent re-audit and be reviewed separately before scientific acceptance. No self-issued CODE_AUDIT_PASS, no R24 authorization, and no repair of other findings occurs here.

Regression uses the unchanged `/home/takuma/.conda/envs/evrp-quantum-temp` environment and direct assertions. Negative fixtures modify in-memory copies or isolated temporary directories only. Run the I03 harness, not historical generators that wrote evidence. Reports and SHA manifests are stored in the new I03 namespace; previous remediation artifacts stay immutable.
