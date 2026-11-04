# KMD量子計算・EV配送　独立統合trial

本trialは2026年11月4日の依頼に基づく1回の試行である。全変更案はtrial提案であり、正式採用・研究成果への統合・公開・commit・pushは実施していない。

保存先：`/home/takuma/kmd-analysis/review_outputs/quantum_ev_conditions_full_trial_20261104_125659`

## 読む順序

1. EXECUTIVE_SUMMARY.md：主要結果・到達状態。
2. ADOPTION_REVIEW.md：追加価値、推奨A/B/C/D、リスク、元原稿との差分。
3. THESIS_SECTIONS_TRIAL.md または THESIS_TRIAL.docx：7章、要旨、参考文献、付録の独立草案。
4. FINAL_AUDIT_REPORT.md／REPRODUCIBILITY_REPORT.md：検算・出典・保全・表示監査と適用限界。
5. HOLD_REGISTER.md／UNRESOLVED_ITEMS.md：未解決の理由・影響・次作業。

## S1–S8と成果物の対応

|工程|成果物|
|---|---|
|初期監査|SOURCE_AUTHORITY_AND_CONFLICTS.md、SOURCE_DISCOVERY_INVENTORY.csv、START.json、GIT_STATUS_START.txt、TRACKED_BASELINE.json|
|S1|RQ_REDESIGN_TRIAL.md、INDICATOR_DEFINITIONS.md/csv、RESEARCH_BOUNDARY.md|
|S2|EXPERIMENT_INVENTORY.csv、CLAIM_EVIDENCE_MATRIX.csv、SOURCE_CLAIM_CANDIDATES.csv、HOLD_REGISTER.md、ADDITIONAL_ANALYSIS_DECISIONS.md|
|S3|PATH1_METHOD_AUDIT.md、PATH1_QUALITY_COMPARISON.csv、PATH1_INPUT_SEED_STATISTICS.csv、PATH1_RUNTIME_COMPARISON.csv、PATH1_RESOURCE_REQUIREMENTS.md、PATH1_CONTRIBUTION_CONDITIONS.md、PATH1_FIGURES/|
|S4|PATH2_MATERIAL_BRIDGE_AUDIT.md、PATH2_MODEL_VALIDATION.md、PATH2_SENSITIVITY_RESULTS.csv、PATH2_SENSITIVITY_SUMMARY.csv、PATH2_UTILIZATION_CONTINUOUS.csv、PATH2_BOUNDARY_RESULTS.csv、PATH2_OPERATION_INTERACTIONS.md/csv、PATH2_OPERATION_SUMMARY.csv、PATH2_CONTRIBUTION_CONDITIONS.md、PATH2_FIGURES/|
|S5|INTEGRATED_CAUSAL_MODEL_TRIAL.md、CROSS_PATH_CONDITIONS_MATRIX.csv、DISCUSSION_TRIAL.md、LIMITATIONS.md|
|S6|LITERATURE_CLASSIFICATION.csv、LITERATURE_EVIDENCE_MATRIX.csv、LITERATURE_EXISTING_BIBLIOGRAPHY.csv、LITERATURE_REVIEW_TRIAL.md、RESEARCH_GAP.md、PRIMARY_PDF_SOURCES.csv|
|S7|THESIS_TRIAL.docx、THESIS_SECTIONS_TRIAL.md、THESIS_BUILD.json、FIGURE_TABLE_INDEX.md、THESIS_CHANGELOG.md、render_final/THESIS_TRIAL.pdf|
|S8|FINAL_AUDIT_REPORT.md、REPRODUCIBILITY_REPORT.md、FINAL_VERIFICATION.json、FINAL_INDEPENDENT_CHECKS.csv、NUMERICAL_CHECKS.csv、T09_INDEPENDENT_COMPONENT_CHECKS.csv、SOURCE_PRESERVATION_CHECKS.csv、TRACKED_PRESERVATION_CHECKS.csv|
|総括|TASK_COMPLETION_MATRIX.csv（32小課題）、EXECUTIVE_SUMMARY.md、UNRESOLVED_ITEMS.md/csv、ADOPTION_REVIEW.md、OUTPUT_SHA256_MANIFEST.csv|

図はPNGとPDF、数値はCSVで保存した。原稿の元ファイルはsources/にバイト複製した。THESIS_TRIALは元複製のbodyを独立した新構成に置き換えた版であり、旧本文への全変更履歴を表示するWord差分文書ではない。原稿の旧全図表・数式はsource DOCXに保全した。採用判断用の節対応はADOPTION_REVIEWにある。

## データ・版・根拠

主系列Bは時間窓なし460入力、旧Aは時間窓あり。BのR4は100顧客、旧凍結系列の99顧客とは別である。Cは旧保存速度を使い、Bの同じ460問題と同一母集団としない。定時配達率は主指標から外すが旧データは削除しない。

終了時、trial外のポスターrun03に開始後の未追跡追加114件を検出した。Git状態全体の不変は成立しない。追跡対象・台帳にピン留めした元データ・原稿は個別ハッシュで保全を確認し、追加はCONCURRENT_WORKSPACE_CHANGES.jsonに記録する。run03の方針記録も条件中心・A/B/C分離を維持しており、今回の科学結果には統合していない。

入力の絶対パス・SHA256はSOURCE_BASELINE.csvとSOURCE_BASELINE_EXTENDED.csv、元のDOCX選定理由はSOURCE_AUTHORITY_AND_CONFLICTS.md、文献の照合範囲はLITERATURE_EVIDENCE_MATRIX.csvを参照する。外部保全領域の大きなNPZ・測定・速度は全量複製していない。公開Git cloneだけで全研究を再現できるとは主張しない。重点文献12件の確認と旧文献一覧全体の精読を区別する。

## 再実行

既存成果を上書きしないため、別の新規trialで再実行する。scripts/bootstrap_replay.pyに一意の新規保存先を渡すと、コードと新しいGit初期台帳だけを用意する。Pythonはこの環境の`.conda/bin/python`（-B指定）を使用する。外部保全入力と旧レンダラへの読み取り権限が必要である。

実行順：analyze.py → literature_and_models.py → write_reports.py → build_thesis.py → render_thesis.py → finalize.py --prepare → verify_final.py → finalize.py。

最後にPDFを目視確認し、その確認記録を新しい実行のVISUAL_REVIEW.csvとして保存する。目視未実施の再実行を自動PASSにしない。科学的結論は算術PASSだけで昇格させない。初回の失敗・修正ログはlogs/とrender/に保持し、採用候補の最終表示はrender_final/である。

## 判定の意味

TRIAL COMPLETEは32課題の実施状況、可能な分析、草案、監査、未解決の記録が揃ったという作業上の判定である。完成pack、公平な総求解時間、compiled資源、量子材料改善、地域・実車妥当性、引用・Word実機のHOLD/FAILを残す。採否は研究者が判断する。

採用判断レビューは同一エージェントの分離監査であり、外部第三者査読ではない。
