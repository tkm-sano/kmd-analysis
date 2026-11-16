# Step 5 基準と保全

作業日：2026年11月5日（Asia/Tokyo）。作業ディレクトリは `/home/takuma/kmd-analysis/review_outputs/quantum_ev_step5_20261105` である。元実験を再実行せず、保存データの読取・再集計・独立原稿作成を実施した。

## 開始状態

HEADは `8605d5412f6af62229a83095c35ab04c8c7dd9b1` である。開始時はmainがorigin/mainより7commit先行し、多数の既存未追跡成果物が存在した。未追跡ファイルを今回の生成物と誤認しない。Git状態の全行と既存tracked差分は `evidence/GIT_STATUS_START.txt` と `evidence/GIT_DIFF_START.patch` に保存した。commit/pushは実施しない。

`evidence/REPOSITORY_FILE_INVENTORY.csv` に既存研究ディレクトリのパス・容量・mtime_nsを記録した。`.conda`等の環境や`.git`を全件hashする監査ではない。`evidence/BASELINE_SHA256.csv` は既存review成果物、研究設計、コード、ルート原稿等を開始時にhashした台帳である。03_dataの大きなrawデータ群は一覧を保全し、実際に用いる入力は別途SHA256で固定した。外部保全ディレクトリのNPZ、候補MEASUREMENTS、greedy RESULT、protocolは読取前の `evidence/ANALYSIS_INPUT_SHA256.csv` で固定した。終了時照合結果は `evidence/PRESERVATION_RESULT.json` に保存する。

## 原稿の基準選定

基準は `/home/takuma/kmd-analysis/review_outputs/quantum_ev_step4_thesis_integration_trial_20261104_184043/THESIS_STEP4_INTEGRATED_TRIAL.docx` および同名PDFである。採用根拠は同ディレクトリの `SOURCE_THESIS_AUTHORITY.md`、`FINAL_AUDIT_REPORT.md`、`STEP5_HANDOFF.md`、`THESIS_PRESERVED_CONTENT_AUDIT.csv` にある。Step3後の科学的採用判断を反映し、11月3日内容基準版の86OMML・27表・19画像を本文/保全付録に保持した、114頁の来歴確認済み統合版である。ファイルのmtimeや名前の新しさだけから選んでいない。後日のポスターevidence内コピーを独立の論文改訂版とは扱わない。研究者が承認した最終提出版であることを示す決裁記録は未確認であり、今回の改訂入力としての選定である。

元内容保全基準 `/home/takuma/kmd-analysis/tmp_RsrchMstrDc_1026_results_integrated.docx` の既存記録hashは `53a3abac8d8e62db6442f92d850eb2f3bb58e876606a84f61f6fe3de1763f99f` である。Step5の実hashは開始台帳に記録した。新原稿 `THESIS_STEP5_REVISED.docx` を作成し、基準原稿を上書きしない。

## 科学的判断の優先順位

今回の明示指示、`/home/takuma/kmd-analysis/review_outputs/quantum_ev_step4_evidence_decisions_20261104_183654/STEP4_EVIDENCE_DECISIONS.md` と `CLAIM_EVIDENCE_MATRIX.csv`、補正後Step3、Step2/1・原実験の順で解釈を照合する。Step4の35判断（PASS9、CONDITIONAL18、HOLD5、NOT CLAIMED3）を変更しない。Step4統合台帳の31採用推奨とは件数/目的の異なる台帳である。

## 確認した資料群

|資料|入口・役割|
|---|---|
|Step1|`/home/takuma/kmd-analysis/review_outputs/quantum_ev_step1_design_trial_20261104_153058`：主対照・時間/統計/材料範囲の仕様|
|Step2|`/home/takuma/kmd-analysis/review_outputs/quantum_ev_step2_analysis_trial_20261104_155535`：73,600対照行のうち主対照36,800、支持460、QAOA診断、時間、材料感度|
|Step3|`/home/takuma/kmd-analysis/review_outputs/quantum_ev_step3_synthesis_trial_20261104_174309`：414/46/41、Chen訂正、二経路の採用整理|
|Step3別統合|`review_outputs/quantum_ev_thesis_step3_integration_20261104_173959`：文献と旧全文trial。全文代替にしない|
|Step4科学判断|`/home/takuma/kmd-analysis/review_outputs/quantum_ev_step4_evidence_decisions_20261104_183654`：Chen実用入力HOLD・主/参考の分離|
|Step4全文|`/home/takuma/kmd-analysis/review_outputs/quantum_ev_step4_thesis_integration_trial_20261104_184043`：DOCX/PDF・全文・文献・保全対応|
|B保存計画|`/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01/B_PLAN_REFERENCES_36800.csv`：ルート/入力/seed/source hash|
|原実行|外部保全 `staged_qaoa_validation_20261102` と `cpu_matched_classical_swaps_r0_r5_20261101`：CPU模擬/古典の分離|
|材料/DC|T07/T08/T09の来歴はStep2 SOURCE_MAP/Step4科学台帳。凍結DCは `01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json`|

SHA256の全文はCSVを正本とし、最終時点で照合する。既存HOLD・道路受入FAIL・T09_ROW183対向FAILを削除しない。
