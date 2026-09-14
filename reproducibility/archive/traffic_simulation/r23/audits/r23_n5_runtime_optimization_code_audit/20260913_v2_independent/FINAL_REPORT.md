# R23_N5_RUNTIME_OPTIMIZATION_CODE_AUDIT_RERUN

独立判定: `CODE_AUDIT_FAIL`。前回比較: `CODE_AUDIT_RESULT_NOT_REPRODUCED`。
以下は独立seal確定後の引継ぎ報告であり、確定済みfindingとclassificationを変更しない。

1. Starting branch / commit: `main` / `d4a8d78a04316414a9f19ff143264d96c88b3c9b`。host=`hayate`、user=`takuma`。開始時shell Python=`/opt/miniconda/bin/python` (3.13.5)、CONDA_PREFIX=`/home/takuma/kmd-analysis/.conda`。
2. Independence procedure: v1 code auditを除外してsource・git・実行artifactからscope/findingを作成。独立判定と全独立artifactのSHAを`independent_seal.json`に保存後、v1を初めて開いた。
3. Previous audit hidden during initial review: YES。status内の旧audit部分も独立判断には使用せず、scientific claim行と旧audit以前のstatus snapshotを確認した。
4. Original implementation authority: rank01 resultのcommit=`9a4ce5600a211ffb92adf3b84fe2468d70be2b26`、`qaoa.py` SHA=`6d0e26fe2f14a77cabd6d938226965479bb8ec46805efee5dcaf7af7c3a6bf67`。process snapshotから実行entrypointを確認。ただし実行時runnerのSHA/commitが欠け、完全なauthorityは未検証。
5. Candidate implementation authority: helper初版=`ff1d579`、SHA=`c0892b96e375fe2c274eaab74dfeb59cb8ec3a8a1331bb44bca3bd22dc9a9691`。現行helper SHA=`f96d76b53cda7034a4b57a6ffdea98bceed11c51a31d1218d69d8bb09cf3888f`。qaoaへの直接分岐追加＋別helper＋runner wrapper。rank02/03記録commitにはv4分岐とrunnerが存在しない。
6. Files inspected: scope125 files。path/purpose/SHA/commit/stateを`audit_scope.json`に保存。コード・artifactのプログラムによるinspectionと主要経路のline-level reviewを区別して記録。
7. Line-level changes: original snapshot比、qaoa `+42/-7`、helper `+86`、runner `+158`。全変更opcodeを保存。これは監査対象の既存差分であり、今回のsource変更ではない。
8. PERFORMANCE_ONLY: 辞書生成回避・statevector返却・dispatch等、親opcode8件。helperの制約由来index生成も詳細分類。
9. VALIDATION_ONLY: helperのdimension/type/finiteness/reference guardsを詳細分類。ただし元の確率integrity guardを完全には置換しない。
10. SCIENTIFIC_SEMANTICS: 親opcode4件。確率入力の受理範囲、出力diagnostics省略、実行runnerのscientific configuration/provenanceを保守的に分類。モデル式変更を意味しない。
11. UNKNOWN: 0。歴史的source未検証はprovenance findingとして明記し、PASSへ隠さない。独立DOCUMENTATION_ONLY opcodeは0。
12. QUBO equivalence: 3 instancesすべて、variable ordering・linear・quadratic・offsetのcanonical hashと数値が完全一致。
13. Hamiltonian equivalence: 3 instancesすべてPauli/coefficients/constant一致。各206 terms（identity含む）。travel/λ contributionsも保存。
14. Optimizer objective equivalence: 数式・sign・offset・normalizationは同一。n2/3/4実関数差0、n5独立diagonalとの差`8.526512829121202e-14`、許容`1e-12`内。
15. Bit ordering: `x[i,t]→q=i*n+t→k=sum x[q]2^q→Qiskit逆順label→route`。各rank120 routes・120 unique indices・120/120 roundtrip PASS。
16. Exact-optimum leakage: objective/circuit/parameter update/stopping/best-route selectionへの流入なし。exact reference変更時もbest route不変をfixture確認。元から存在するreference energy/gapのreporting使用は記録。
17. Hidden result hard-coding: scientific candidateへの結果値埋込みなし。runnerのn/IDsは固定scope。benchmarkの`idx[-1:]`は実際のP_optimalではなく、I10として報告。
18. n authority: n=5を`66d8d73`のmanifestでrank01開始前に固定。
19. Instance authority: 10顧客の252 combinationsをseed2301のSHAでrank付け。top3を独立再計算して一致。
20. p authority: p=1をn5実行前固定。従来n4 depth outcomesより前に選択したとは言えず、optimal depthの主張は不可。
21. λ authority: λ=4.0、strict bound `λ>(n+1)/2=3` を満たす最小整数。empirical tuningの記録なし。
22. Optimizer authority: COBYLAをn5実行前固定。B2比較結果より後なので、B2からの影響がなかったとの証明にはならない。
23. Initialization authority: fixed_0.1、`[0.1,0.1]`をn5実行前固定。初期値robustnessは未確立。
24. Evaluation-cap authority: 現行runner/schemaは300、maxiter300、optionsはNone→maxiterのみ明示。n5 manifestにはcap/optionsの明示がなく、実行時wrapper欠落のため事前固定は完全には検証できない。
25. Seed authority: simulator/transpiler/profiling17、selection2301、classical validation2501。fixed initialization/COBYLAに別RNG指定なし。n5で良いseedだけ残した証拠なし。
26. Tolerance authority: constantsと閾値は`1e-12`のまま。ただしcandidateの総和/range guard欠落は実効的な契約差。
27. Denominator authority: raw full-state massを維持、feasible条件での再正規化なし。
28. Instance-selection arbitrariness: LOW。選択規則にdifficulty/outcome項なし。単一fixture由来3例の一般化には限界。
29. Optimizer-selection arbitrariness: MEDIUM。baseline継続は合理的だがrationale追加が必要。general superiorityは支持されない。
30. p arbitrariness: MEDIUM。最小resource実験として合理的、深さの最適性は未検証。
31. λ arbitrariness: LOW。theoremの十分条件あり。authorityのmargin算術にMINOR誤記（実際は4−3=1、8−6=2）。
32. Stopping-rule arbitrariness: HIGH（authority不足）。意図的post-hoc調整を認定していない。rank01延長・途中変更・恣意的wall stopの観測証拠はなし。
33. Benchmark-condition comparability: 不十分。thread/affinity/OMP/BLAS/Aer並列設定の対応記録が欠ける。
34. Runtime metric comparability: `PRELIMINARY_ONLY`。33.7×はfull run/nfevとprototype評価の異なるboundary。scientific speedupとは呼ばない。
35. Memory metric comparability: formal reduction factor不可。absolute ru_maxrss、増分、観測RSSが混在し、workload/processも異なる。rank02/03の0.309/0.278GiB peakも0.5GiB raw vectorとの整合確認が必要。
36. Precomputation accounting: currentにはpersistent circuit/Hamiltonian/feasible cache/backend reuseなし。`T_end_to_end=T_input_setup+T_run_single`。v2 benchmarkはindex setup・simulation・guard・route reportingを除外。
37. Validation independence: 今回はactual helper＋歴史的original＋独立one-hot mask/diagonal referenceで検証。既存generatorのPASSは差分に依存せず、既存harnessはhelperを呼ばないため不十分。
38. Validation-set bias: 今回はvalid/nonoptimal/duplicate/missing/empty/malformed/known optimum/invalid index/multiple optimumを追加検証。legacy coverage表現は過大。単一初期点検証を全trajectory検証とはしない。
39. Failure-path safety: NaN/inf入力・dimension・empty/duplicate/malformed optimumはreject。zero norm・norm4・有限値overflow結果inf/nanは受理。float32/complex64演算差も`1e-12`を超えた。
40. Silent fallback findings: backend/optimizerのbroad exceptはfailureを明示。主要問題は確率integrityの無検証と無条件PASS。missing reference energyの0 defaultは現行runnerが値を供給するhistorical diagnostic limitationとして記録。
41. Artifact immutability: 今回125 scope filesのSHA不変、source diff空。rank02/03のtracked結果は追加以来不変。ignored/untracked rank01の歴史的immutabilityは完全には証明不可。
42. Git provenance: design→authorization→rank01→profiling→helper→remaining results/wiring commit→audit→guardsを復元。記録commitと実行entrypointの不一致をI02に記載。
43. Post-hoc changes: 数式・λ・p・optimizer・初期値・denominator・選択規則の変更証拠なし。postprocessing/guards/output契約の結果後変更あり。cap/optionsの完全な事前固定は未検証。
44. Selective reporting: success=false、cap、P_feasible<1%、小さいP_optimal、42.62h、201.58GiB、optimization/benchmark制約/n≥6非推奨はartifactに残る。一方、現行statusのconvergence3/3が矛盾。
45. Unsupported claims: convergence3/3、n5 robustness、formal speedup、optimizer一般優越、一般scaling law、Full-EVRP generalization、quantum advantage。
46. LOW arbitrariness count: 6（decision単位）。
47. MEDIUM arbitrariness count: 8（decision単位）。
48. HIGH arbitrariness count: 1（cap/options authority不足）。
49. CRITICAL findings: 0。
50. MAJOR findings: 4（I01 probability guard、I02 execution provenance、I03 validation gate、I04 convergence claim）。
51. MODERATE findings: 5（I05 benchmark、I06 diagnostics省略、I07 precision、I08 archival/replay不足、I10 benchmark optimum proxy）。
52. MINOR findings: 1（I09 penalty margin算術）。
53. Independent classification: `CODE_AUDIT_FAIL`。正常domainの数式等価性PASSだけでは完全gateを満たさない。
54. Previous classification: `CODE_AUDIT_PASS_WITH_REMEDIATION`。3 MODERATE、CRITICAL/MAJOR/HIGHはいずれも0。
55. Agreement/disagreement: 数式・bit ordering・raw denominator・leakageなし・formal倍率不可は一致。failure safety、validation、provenance、immutabilityの確実性、convergence、cap authorityで不一致。旧3 findingとの対応をcomparisonに保存。
56. Reproducibility classification: `CODE_AUDIT_RESULT_NOT_REPRODUCED`。旧helperでもnorm0/4を受理するため、その後のsource変更だけで差は説明できない。前回DOF集計の宣言11/5と実row9/7の不一致は比較専用注記。
57. Required remediation: finding_registerのI01–I10。source guard、実行時snapshot回収、実helperに対するfail-sensitive gate、誤ったstatus、benchmark/precision/output/archival契約、margin誤記。今回は修正せず残す。
58. rank02/rank03 scientific evidence: 既存値を保持。exact-route回収・native successは記録あり。ただしsource lineage/resource整合未解決で、今回再実行・再承認していない。
59. Artifact root: `reproducibility/outputs/traffic_simulation/r23_n5_runtime_optimization_code_audit/20260913_v2_independent/`。
60. SHA verification: `independent_seal.json`で比較前後不変確認。最終`SHA256SUMS`はartifact全体と4 audit scriptsを対象とする。検証commandはこのdirectoryで`sha256sum -c SHA256SUMS`。
61. Commit: このreportとaudit scripts/artifactsを追加したaudit-only commit（`git log -1 --format=%H -- <このファイル>`で解決）。自己参照hashをartifactに埋め込まない。commit message=`traffic-sim: independently re-audit R23 n5 runtime optimization`。
62. Final git status: tracked変更はaudit-only commitへ格納。開始時のunrelated/untracked 5 entriesをそのまま残す。最終command結果は対話の引継ぎ報告に記載。
63. Next recommended task: `R23_N5_RUNTIME_OPTIMIZATION_AUDIT_REMEDIATION`。R24を進めず、draftのauthority昇格もしない。
64. R23 overall status: 既存Reduced Problem evidenceはlimitations付きで保持。今回runtime optimization code auditはFAIL / REMEDIATION_REQUIRED。canonical documentsは監査中変更しない。
65. Full-EVRP status: R20 BLOCKED、R21 NOT_STARTED。今回capacity/time-window/battery/charging/multi-vehicle実装なし。

実験用Pythonは凍結authorityの`/home/takuma/.conda/envs/evrp-quantum-temp/bin/python`を使用し、versionsを実測した。pytestはこの環境に存在せず、環境を変更せず独立assertion scriptsで検証した。pytest suite実行成功は主張しない。scientific optimizer runは0回、n5は固定初期点の診断評価のみ。
