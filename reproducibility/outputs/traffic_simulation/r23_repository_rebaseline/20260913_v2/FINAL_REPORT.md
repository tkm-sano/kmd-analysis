# R23 rebaseline V2 final report

See [final authority map](final_authority_map.json) and [final verification](final_verification.json). No code-audit acceptance, R23 closure or R24 start.

1. **starting branch / commit:** main / 3e440ce319deab180c47999d25350d2a841ec76a
2. **starting working-tree state:** staged 0 / tracked modified 0; hostname hayate; user takuma; full status and ignored inventory in starting_state.json
3. **starting untracked count:** 5 entries / 6 files
4. **scientific classification:** R23_N5_SCALING_EVIDENCE_ACCEPTED_WITH_LIMITATIONS
5. **audit classification:** CODE_AUDIT_FAIL_PENDING_POST_REMEDIATION_REAUDIT
6. **remediation classification:** R23_N5_RUNTIME_OPTIMIZATION_AUDIT_REMEDIATION_COMPLETED_PENDING_INDEPENDENT_REAUDIT
7. **I03 classification:** RESOLVED / R23_I03_VALIDATION_GATE_REMEDIATION_PASSED
8. **R24 classification:** R24_NOT_STARTED_BLOCKED_PENDING_R23_POST_REMEDIATION_REAUDIT
9. **authority artifacts inspected:** 547 files / 23 role nodes; 141 ignored-local authorities explicitly pinned; 574 historical files rehashed
10. **Routing authority:** A01: R13 v18 geometry_reaccepted/routing_arcs.csv; Routing canonical specification
11. **Reduced Problem authority:** A02: R23_REDUCED_PROBLEM_CANONICAL.md; scientific model section unchanged
12. **penalty authority:** A03: R20_COMMON_GLOBAL_LAMBDA_V1 λ=3 for n=2,3,4; n5 λ=4 with i07_lambda_erratum arithmetic correction only
13. **n5 design authority:** A07: n5_scaling_authority/20260911_v1; V2 resource authorization A08
14. **exact-reference authority:** A21: n5_exact_references.json; Formal instance exact_references.json and _refs/; ignored-local dependencies pinned
15. **scientific-result authority:** A09/A10/A11: rank01/02/03 scientific_result.json and corresponding terminal/resource records; A04/A05/A06 retain Formal A/B1/B2
16. **environment authority:** A08/A17: n5 resource V2 and frozen environment authority /home/takuma/.conda/envs/evrp-quantum-temp
17. **independent-audit authority:** A16: r23_n5_runtime_optimization_code_audit/20260913_v2_independent; commit 33ae964bca0e61199621ee976a927cd4069e1723
18. **remediation authority:** A18: audit_remediation/20260913_v1 at 9cce6eb; I03 incomplete state superseded by continuation
19. **I03 authority:** A19: i03_validation_gate_remediation/20260913_v1 at 3e440ce; i03_closure_gate.json
20. **scientific facts reconstructed:** n5=3 runs; directed route/reference equality, gap0, cap1; B2=6 valid results, exact recovery6, gaps0, recorded optimizers/initializations/termination; scientific_fact_table.json and b2_scientific_facts.json
21. **optimal route recovery:** 3/3 n5; 6/6 B2
22. **optimizer reported success:** 2/3 n5; rank01 non-success. B2 Nelder-Mead 3/6 native success; all 6 retained.
23. **P_feasible range:** [0.006366971625605308, 0.007978143668511524]
24. **P_optimal range:** [5.447231886991554e-05, 6.636000200882145e-05]
25. **n≥6 status:** NOT_RECOMMENDED under current exact CPU Aer statevector methodology; 36q state alone 1 TiB
26. **current finding count:** 11 = independent I01–I10 plus one new B2 item containing six mismatches
27. **resolved I01–I10 findings:** All 10 remediation-addressed; plain RESOLVED: I01, I03, I04, I06, I07, I09, I10; I02/I05/I08 resolved with documented limitations; independent closure pending
28. **unresolved pre-existing findings:** No pre-existing remediation item remains open; provenance/resource, benchmark comparability and stopping-rule authority limitations remain for independent audit
29. **B2 SHA mismatch count:** 6
30. **B2-SHA-01:** routing_v18_n4_rank01_p2_init_fixed01_rep1_optimizer_nelder_mead.json: expected dedf511bb6c8b65e613da68aaff1422f4f63dc29304a3ace4ce8cb7394e643fe → actual dc2cd274d1fcdeeffd1562ec639f9dbeec6409c5e238c51e49c1337642cb062d; DERIVED_ARTIFACT_MISMATCH
31. **B2-SHA-02:** routing_v18_n4_rank01_p3_init_fixed01_rep1_optimizer_nelder_mead.json: expected fe28e4bf13db3cbb944e5248feb559adb8337b74ed556db37e6cb81972fe2843 → actual ca385005520d1f3d5c89d81d817790da02fc985270af8d7c233ce29929006f17; DERIVED_ARTIFACT_MISMATCH
32. **B2-SHA-03:** routing_v18_n4_rank03_p2_init_fixed01_rep1_optimizer_nelder_mead.json: expected 6695865c5651690407aeb98a489b6ea040171f49846c29571a8e6864906382db → actual ce37109912a51dcd56828ea3a1e65d52ecc61f9a56da9d3f9cc22a480e1c6a28; DERIVED_ARTIFACT_MISMATCH
33. **B2-SHA-04:** routing_v18_n4_rank03_p3_init_fixed01_rep1_optimizer_nelder_mead.json: expected aac6f8153836fb7036ed8c691fafc25ca67d937bb7b42aeebf7e06af0607ddb6 → actual 87a02d1f5c78c10160d81dd14c247e0a818b608b3da13170bcdd24acf363386f; DERIVED_ARTIFACT_MISMATCH
34. **B2-SHA-05:** routing_v18_n4_rank05_p2_init_fixed01_rep1_optimizer_nelder_mead.json: expected ab909b317c4f2ed3257249848fdf1eb41c85bc82e731c1b1e333d6471cb13fff → actual 027eba3d4cd50562219cf21b24b7a540b7f19c31e589573371005c819ea4c677; DERIVED_ARTIFACT_MISMATCH
35. **B2-SHA-06:** routing_v18_n4_rank05_p3_init_fixed01_rep1_optimizer_nelder_mead.json: expected 3d1e9b71d1222fbc7b42adc8af2ec0ffca9ab776433c52029ee8019b7e031389 → actual 0ef9ceed1ae14db085a7ba64b51ae9e26228a1a9019e113d03084141b4607a86; DERIVED_ARTIFACT_MISMATCH
36. **B2 mismatch classification summary:** 6 DERIVED_ARTIFACT_MISMATCH; flag-only reverse reconstruction matches all six expected hashes. Severity PENDING_INDEPENDENT_SEVERITY_ASSESSMENT. Finalizer wall-clock/actor UNKNOWN; no impact-category UNKNOWN remaining.
37. **B2 scientific integrity:** 6/6 VERIFIED under raw-record read-only checks; no new acceptance
38. **B2 artifact integrity:** FAILED, preserved
39. **B2 rerun preliminary assessment:** NO_RERUN_INDICATED for these flag/index mismatches alone; final decision independent audit
40. **rank01 provenance:** STRONGLY_INFERRED; original result is ignored-local evidence pinned by SHA
41. **rank02 provenance:** STRONGLY_INFERRED; NOT_REAUTHORIZED; resource/trajectory limitations retained
42. **rank03 provenance:** STRONGLY_INFERRED; NOT_REAUTHORIZED; resource/trajectory limitations retained
43. **validation architecture:** 29 implementation/report/validator entries; 54-file targeted rescan; unified six-status contract
44. **active unconditional PASS count:** 0; source SHA and matches identical to I03 sealed 54-file classification
45. **contradictions found:** 14 interpreted issues; literal search 44,457 occurrences mostly historical/numeric, not findings
46. **status-doc contradictions:** 5 correction topics; existing corrected 3/3 recovery vs 2/3 optimizer wording retained
47. **status docs corrected:** 7 tracked status documents/sources: R23_STATUS, ROADMAP, NEXT_STEPS, canonical, specification index, RESEARCH_STATUS and status-only research_stage.yml
48. **historical artifacts preserved:** 574/574 sealed history unchanged; 547/547 major authority bytes identical across cleanup
49. **R24 authority review:** No formal R24 design authority; only premature-decision review found in tracked R24 paths; OPEN R23 / BLOCKED R24
50. **artifact duplication/classification:** Keep all scientific/audit history; exact duplicate groups recorded without deletion; artifact_classification.json
51. **untracked item 1:** .tmp_patch_probe: SAFE_TO_REMOVE; 1 files / 6 bytes
52. **untracked item 2:** reproducibility/config/traffic_simulation/r23_pilot_configuration: SHOULD_COMMIT; 1 files / 9054 bytes
53. **untracked item 3:** reproducibility/outputs/research_model_workbook: SHOULD_BACKUP_AND_REMOVE; 2 files / 21143 bytes
54. **untracked item 4:** research_model_3page_ja.xlsx: SHOULD_BACKUP_AND_REMOVE; 1 files / 16908 bytes
55. **untracked item 5:** research_model_3page_ja_revised.xlsx: SHOULD_BACKUP_AND_REMOVE; 1 files / 26017 bytes
56. **additional untracked items:** 0 at start and after cleanup; new rebaseline bundle explicitly force-added under existing output ignore rule
57. **files committed:** Authority commit: 44 paths (36 rebaseline files, 7 status files/sources, 1 unchanged pilot input); receipt adds final report and verification evidence, with exact lists in Git.
58. **files backed up:** 5 files, 64,074 bytes (three distinct XLSX files, workbook validation JSON, patch probe)
59. **files removed:** Same 5 verified backup files and 2 empty workbook directories; no scientific/audit artifact removed
60. **backup path:** /home/takuma/kmd-analysis_worktree_backup/20260913_rebaseline_v2
61. **backup verification:** Source vs backup: file count5, byte count64074, per-file SHA256 all identical before deletion; backup_manifest.json outside repository
62. **cleanup manifest:** [cleanup_manifest.json](cleanup_manifest.json)
63. **scientific authority SHA before/after:** 547/547 identical including canonical, penalty, exact refs, ranks, independent audit, remediation and I03; model section unchanged from start
64. **rebaseline artifact root:** reproducibility/outputs/traffic_simulation/r23_repository_rebaseline/20260913_v2
65. **rebaseline SHA verification:** SHA256SUMS covers every bundle file except itself; verified before authority commit and resealed for cleanup receipt
66. **rebaseline commit:** 29f6048de345ebde6fcd05fcd4aabd52a862f9cb; final receipt commit is the containing commit of FINAL_REPORT.md (see git log -1 -- this file)
67. **final git status --short:** Empty after cleanup; receipt commit followed by final read-only Git check in final response
68. **final working-tree clean:** YES at measured cleanup gate; final receipt must leave staged0/unstaged0/untracked0
69. **independent re-audit readiness:** READY, with explicit B2 unresolved item and retained provenance/local-evidence limitations
70. **final classification:** R23_REPOSITORY_REBASELINE_AND_WORKTREE_CLEANUP_PASSED
71. **next task:** R23_N5_RUNTIME_OPTIMIZATION_CODE_AUDIT_POST_REMEDIATION_RERUN
