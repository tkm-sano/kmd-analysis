# R23 remediation final report

判定: `R23_N5_RUNTIME_OPTIMIZATION_AUDIT_REMEDIATION_INCOMPLETE`。

原監査のI01–I10と依頼本文のI05–I10は同じfindingを指していない。原ID・severityを変更せず、`finding_authority.json`に対応表を保存した。以下の番号3–42は依頼本文の項目順、closure表は原監査IDである。

1. Starting branch/commit: main / 33ae964bca0e61199621ee976a927cd4069e1723。host=hayate、user=takuma、shell Python=/opt/miniconda/bin/python、開始conda=/home/takuma/kmd-analysis/.conda。既存untracked5項目を保持。
2. Primary authority: r23_n5_runtime_optimization_code_audit/20260913_v2_independent。v1より原独立findingを優先。
3. I01: zero/wrong-norm/overflowを通常のprobability metricsとして返していた。
4. I01修正: float64/complex128、有限性、unit norm、計算後range/sumを既存1e-12でfail closed。renormalize、clip、補正なし。
5. Zero norm: V4InputErrorでreject、VERIFIED。
6. Wrong norm: norm4、0.999をreject、VERIFIED。
7. NaN: reject、VERIFIED。
8. Inf: reject、VERIFIED。
9. Finite1e308からのoverflow: reject、VERIFIED。計算途中の負値/NaN/inf注入もreject。
10. Valid domain: before/after expectation、P_total/P_feasible/P_optimal/P_invalid、route一致。比較tolerance1e-12。固定初期点とbasis fixtureの検証であり全optimizer trajectoryではない。
11. I02: 記録HEADに実行runner/V4 wiringがない。
12. Rank01 lineage: STRONGLY_INFERRED。実行直前のrunner作成ログとlaunchを復元。実行時full-source SHA/traceなし。
13. Rank02 lineage: STRONGLY_INFERRED。実行前FileChange patchをreplayし、後日commit0e149edのrunner/qaoaに完全一致。
14. Rank03 lineage: STRONGLY_INFERRED。同runner/wiringとprocess records。署名付き実行attestationではない。
15. Contradiction: EXECUTION_PROVENANCE_METADATA_INCONSISTENCY。source_commitはHEADのみでdirty sourceを表さない。rank02/03のru_maxrssは同時期ps RSSとも不整合。原因未確定。
16. Rank02/03: RERUN_REQUIRED_FOR_FORMAL_ACCEPTANCE。旧record保持・未再承認。新しいrunは開始していない。
17. I03: n5 legacy generatorの無条件PASS・実helper未実行・coverage誤記。
18. 無条件PASS: n5対象4本をarchive後retire。全repository検索で旧B1/B2/provenanceの6箇所が残る。validation_pass_search.json参照。
19. Gate変更: required test IDの完全一致、非空、実行済みassertion、数値比較、evidenceを要求。9種のgate mutationをreject。
20. Validation manifest: 16/16 VERIFIED。ただし全repositoryの無条件PASS除去はPARTIAL。ローカルtest成功をglobal closureと混同しない。
21. I04: convergence3/3はrank01 native success=falseと矛盾。
22. Current status/next steps/roadmap/canonical/dashboardを修正。旧scientific artifactsは書き換えず現在の説明で訂正。
23. 正式表現: optimal route recovered3/3、relative route objective gap0 for3/3、optimizer reported success2/3（false/true/true）。rank02/03 provenance制約付き。
24. 依頼I05: 300 cap/maxiter/optionsの事前authority不足。
25. Cap authority: VERIFIED_PRE_FIXEDは実行前FileChangeの宣言に限定。maxiter300、cap300、options=None、wall_time=None。実行processへの帰属はSTRONGLY_INFERRED。
26. Stopping risk: HIGH→MEDIUM。新しい実行前source証拠に基づく。manifestのoptions不足やprocess attestation不足は残る。
27. 依頼I06: COBYLA decisionのB2非依存を過剰断定しない。
28. Timeline: B2 evidence reviewは2026-09-11 21:17 JSTまでに存在、n5 authorityは22:18:24、rank01開始22:32:21。baseline continuityとB2 evidence availabilityを区別。
29. Optimizer-selection risk: MEDIUM。n5 post-result変更の証拠なし、B2影響なしとは断言不可。
30. 依頼I07／原I09: λ十分条件のmargin算術誤記。
31. Erratum: n5ではλ>3、4−3=1、2×4−6=2。元artifact不変、独立erratumとcanonicalで訂正。
32. λ4.0はstrict sufficient conditionを満たす。scientific parameter変更なし。
33. 依頼I08／原I05,I10: timing/memory境界不一致とP_optimal_lookup誤ラベル。
34. Runtime: PRELIMINARY_ONLY。33.7倍をformal/scientific speedupとしない。
35. Memory: original observed absolute peak201.6GiBとcandidate incremental約0.615GiBは直接比較不可。327倍reductionを否定。
36. Formal benchmark未実行。host/CPU/threads/affinity/OMP/BLAS/Aer/warmup/repetitions/boundaries/memoryのprospective contractを定義。全setup/eval/final費用と全repetitionを保持する。
37. 依頼I09: 不利な結果と監査FAIL/provenance制約を正式statusで明示する必要。
38. rank01 false/cap、P_feasible<1%、P_optimal約5.45e-5〜6.64e-5、42.62h、201.58GiB、rank02/03制約、独立FAIL/NOT_REPRODUCED、preliminary benchmark、n≥6非推奨を保持。
39. Global convergence、robustness/scaling law、optimizer superiority、quantum advantage/speedup、正式倍率をNOT_SUPPORTEDとして否定。履歴claimは不変かつsuperseded扱い。
40. 依頼I10／原I02,I06,I08: 実行metadata不足とcompact reporting schemaの不明確さ。
41. Metadata contract: commit、source/runner/helper/authority SHA、source manifest、env/versions、host/CPU/threads、command、start/end、effective options、seed、termination、resources、final params/trace hashを要求。
42. 欠落時FORMAL_RUN_PROVENANCE_INCOMPLETE、formal evidenceへ昇格禁止。構造validatorをtest済み。実hashをarchiveと結び付ける実行側integration/attestationは次の正式run前に必要。
43. Frozen env: 指定pathの全expected version一致、変更なし、pytest追加なし。
44. n2: synthetic subset fixture（λ4、p1）のbefore/after regression VERIFIED。歴史的Formal Aの再実行ではない。
45. n3: 同synthetic subset fixtureのregression VERIFIED。
46. n4: 同synthetic subset fixtureのregression VERIFIED。歴史的n2–4のλ3 authorityは変更していない。
47. n5: 3 rankの固定点でVERIFIED。
48. Rank01 bit ordering: 120 routes、120 unique indices、120/120 roundtrip。
49. Rank02 bit ordering: 120 routes、120 unique indices、120/120 roundtrip。
50. Rank03 bit ordering: 120 routes、120 unique indices、120/120 roundtrip。
51. Multiple optimum: independent synthetic mass0.25+0.75=1をactual helperで確認。unique optimum前提なし。
52. Invalid input: 17 invalid cases＋3計算異常注入をreject。wrong dimension、dtype、empty、invalid/duplicate/missing optimum含む。
53. Independence: referenceはcandidate aggregation helper不使用。n2–4 full one-hot mask、n5独立permutation indices＋full numeric mass、独立diagonal expectation。歴史的final optimizer点は再現していない。
54. Source分類: SAFETY_GUARD_ONLY、VALIDATION_ONLY、DOCUMENTATION_ONLY、PROVENANCE_ONLY。全path/hunk/diff/SHAをsource_change_classification.jsonに保存。
55. SCIENTIFIC_SEMANTICS変更: 0。QUBO/Hamiltonian/schema/optimizer/initialization/runner不変、objective/run_single AST不変。
56. Immutable: 162 protected filesを比較。scientific result/manifest/exact/history/両audit不変。歴史directory内の旧generator2本のみsourceとして停止、元bytesを別archiveで保持。
57. LOW arbitrariness: 6。
58. MEDIUM arbitrariness: 9。
59. HIGH arbitrariness: 0。cap評価の新証拠と残存制約を明示。
60. Unresolved CRITICAL: 0。
61. Unresolved MAJOR: 1（原I03のrepository-wide残存）。
62. I01–I10 closure: 下表。原severityを保存し、resolved-with-limitationを完全証明と扱わない。
63. Classification: R23_N5_RUNTIME_OPTIMIZATION_AUDIT_REMEDIATION_INCOMPLETE。
64. R23: REMEDIATION_INCOMPLETE。CODE_AUDIT_FAIL / CODE_AUDIT_RESULT_NOT_REPRODUCED維持。旧limited scientific evidenceは保持。
65. R24: NOT_AUTHORIZED_PENDING_R23_REMEDIATION。Full-EVRP R20 BLOCKED、R21 NOT_STARTED。
66. Artifact: reproducibility/outputs/traffic_simulation/r23_n5_runtime_optimization_audit_remediation/20260913_v1/。
67. SHA: SHA256SUMSで全artifactをseal。source SHAはsource_change_classification.jsonで照合。最終検証結果はfinal_verification.json。
68. Commit: このreportを導入したcommit（自己参照hashは埋め込まない）。`git log -1 --format=%H -- <artifact-root>/FINAL_REPORT.md`で特定。
69. Final git status: handoff時に確認。初期untracked5項目は変更せず保持。commit後の正確な状態は対話最終報告に記載。
70. Next: I03残存6箇所の修正・検証でremediationを閉じる。その後のみ別task R23_N5_RUNTIME_OPTIMIZATION_CODE_AUDIT_POST_REMEDIATION_RERUN。独立PASS後にphase closure→R24。

| Original ID | Original severity | Closure | Residual severity |
|---|---|---|---|
| I01 | MAJOR | RESOLVED | NONE |
| I02 | MAJOR | RESOLVED_WITH_DOCUMENTED_PROVENANCE_LIMITATION | MODERATE |
| I03 | MAJOR | PARTIAL | MAJOR |
| I04 | MAJOR | RESOLVED | NONE |
| I05 | MODERATE | RESOLVED_WITH_DOCUMENTED_LIMITATION | MODERATE |
| I06 | MODERATE | RESOLVED | NONE |
| I07 | MODERATE | RESOLVED | NONE |
| I08 | MODERATE | RESOLVED_WITH_DOCUMENTED_PROVENANCE_LIMITATION | MODERATE |
| I09 | MINOR | RESOLVED | NONE |
| I10 | MODERATE | RESOLVED | NONE |
