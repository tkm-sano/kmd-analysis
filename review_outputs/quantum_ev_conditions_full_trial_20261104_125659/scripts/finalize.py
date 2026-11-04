from pathlib import Path
import sys,json,csv,hashlib,datetime
import pandas as pd
O=Path(__file__).resolve().parents[1];R=O.parents[1]
def write(n,s):(O/n).write_text(s.strip()+'\n')
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
write('README.md',f'''# KMD量子計算・EV配送　独立統合trial

本trialは2026年11月4日の依頼に基づく1回の試行である。全変更案はtrial提案であり、正式採用・研究成果への統合・公開・commit・pushは実施していない。

保存先：`{O}`

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
''')
if '--prepare' in sys.argv:
 print('README prepared before closure checks');sys.exit(0)
result=json.loads((O/'FINAL_VERIFICATION.json').read_text());run=json.loads((O/'ANALYSIS_RUN.json').read_text());render=json.loads((O/'render_final/RENDER_RUN.json').read_text());vis=pd.read_csv(O/'VISUAL_REVIEW.csv');assert len(vis)==render['pages'] and set(vis.status)=={'PASS_WITH_WORD_HOLD'}
checks=pd.read_csv(O/'NUMERICAL_CHECKS.csv');ti=pd.read_csv(O/'T09_INDEPENDENT_COMPONENT_CHECKS.csv');fin=pd.read_csv(O/'FINAL_INDEPENDENT_CHECKS.csv');assert set(checks.status)=={'PASS'} and set(fin.status)=={'PASS'}
cm=pd.read_csv(O/'CLAIM_EVIDENCE_MATRIX.csv');t=pd.read_csv(O/'TASK_COMPLETION_MATRIX.csv');counts=cm.status.value_counts().to_dict()
write('REPRODUCIBILITY_REPORT.md',f'''# 再現性報告

科学的再実験と保存データの再計算を区別した。新規QAOA、学習、経路探索、SUMO、実車・材料実験は0である。分析は決定論的で新規乱数seedは非適用。元B測定seedは保存計画行の出典を維持した。

## 実施した再計算

- B全36,800参照：460原NPZと保存測定、順列・ODコスト・初期差・可行性・gapを照合。厳密参照の数値と証明メタデータを元証明ファイルで照合した。solver証明の再生成ではない。
- A旧保存行14,832：率、分母・分子、時刻を元NPZから独立有理数式で再生。計算内容は旧固定OD会計で、主定時率分析を追加しない。
- T08全4,464行のmassを再計算。主の古典460速度×2CrrのLP/S端点で凍結kernel照合、49連続q点45,080行と利用率49点を生成。
- T09 183×8=1,464成分を独立Fraction式で検算し、bridge25,760行の質量・成分分解会計を確認。完成mass NULLと対向FAILを保持。
- 追加感度の3代表速度×2Crr×5点=30内部点を別途凍結kernelで確認。最大差{result['C_internal_kernel_max_error_Wh']:.3g}Wh。

主計算検査{run['checks']:,}項目、T09成分検査{len(ti):,}項目、最終分離検査{result['checks']:,}項目で算術不一致0である。検査項目数は実験標本数ではない。

## 計算環境と所要時間

Python {run['python']}。NumPy {run['numpy']}、pandas {run['pandas']}、{run['platform']}。主分析wall {run['wall_s']:.3f}秒、CPU累積{run['CPU_s']:.3f}秒、最大RSS {run['peak_RSS_bytes']:,}bytes。これは今回の監査・追加分析費用であり、元の量子求解費用ではない。当時の旧分析NumPy2.2.5と今回2.4.6も区別する。環境をインストール・改変していない。

scripts/analyze.py、literature_and_models.py、verify_final.pyは式の順序を分けて検証する。全ファイルのコードhashはOUTPUT_SHA256_MANIFEST.csv、入力hashはSOURCE_BASELINE_EXTENDED.csvである。元PDFの再抽出もPRIMARY_PDF_SOURCES.csvで追跡できる。

## 再現の限界

外部保全のNPZ・測定JSON・速度と、既存の読取り専用レンダラに依存する。公開clone単独・原公的資料からの全入力再生成・実機量子再現・実車Validationは未達である。今回のtrial全体を別プロセスで完全再生成して全出力byte一致を確認したとは主張しない。数値の独立式照合と実行手順・hashを提供した到達状態である。PDFのバイト完全一致はフォント・レンダラに依存する。

## 失敗と修正

Fraction文字列の解析、欠けていた表示用ライブラリ依存（tabulateを追加せず内部Markdown表へ置換）、元DOCXにないstyle名を修正した。同一目的値の丸め擬似差は正確な差を使って修正した。初回PDFの行重なりは段落の直接行間を指定して解消した。いずれもtrial内の実装・編集修正で、元結果・物理モデル・入力は不変である。
''')
write('FINAL_AUDIT_REPORT.md',f'''# 総合監査

**総合判定：TRIAL COMPLETE。研究解釈はCONDITIONAL、重要HOLD/FAILを保持する。**

全32小課題に、実施内容、成果物、実施完了度、科学的判定、未解決理由を記録した。HOLDを解消したふりをして全研究完了とは扱わない。重要主張27件の内訳は{json.dumps(counts,ensure_ascii=False)}である。FAILは不適切な断定または既存条件違反を識別したものであり、元結果の削除はしていない。

## 学術・数値監査

|項目|判定と根拠|
|---|---|
|RQと結論|RQ0/RQ1/RQ2/RQIに7章で暫定回答。品質条件、適用時間、mass相殺、未接続を分離|
|方法と結果|B時間窓なし／旧A時間窓あり、B現460／C旧460を分離。目的はOD時間で省電力最適化ではない|
|算術・単位|主計算{run['checks']:,}＋成分1,464＋分離検査{result['checks']:,}、不一致0。秒・Wh・kg・Ah/kg・%を区別|
|統計|入力内10測定rep→規模内等重み、exact407と全460を分ける。擬似独立・有意性判定・実世界CIを追加しない|
|図表|図1–4、表1–4、式(1)–(7)。CSV、原稿、図の生成コードと対応を確認|
|条件付き性|T08/09、共通速度、量子帰属、任意目標を明示。A/B/C分類を保持|
|因果解釈|技術→適用→結果は概念的trial提案。量子材料改善・実車寄与の実証へ昇格しない|
|文献|重点12件の一次照合範囲を記録。Papachristos元引用と旧全引用精読はHOLD|
|研究境界|新規SUMO/QAOA/経路探索0、凍結Controlled-DCの回生・補機・勾配・積載条件を維持|

## 原稿・表示監査

THESIS_SECTIONS_TRIAL.mdは約15,000文字の7章・要旨・参考文献・付録草案である。元DOCXのバイト複製から独立本文へ編集したTHESIS_TRIAL.docxを作成した。旧本文を変更履歴で表示する差分文書ではなく、元原稿と節対応表を併記する方式である。DOCX zip/XMLの完全性、本文140段落・表4・画像4、全段落とMarkdown・PDFの文字一致を確認した。

LibreOfficeで{render['pages']}ページのPDFを作成した。全ページのcontact sheetと3ページ目の拡大を目視し、図表・相殺式・本文・参考文献に行重なりや切れを認めなかった。ページ番号を保存している。最初のrender/は修正前表示、採用判断対象はrender_final/である。Microsoft Word実機・大学指定様式・最終提出組版はHOLDである。

本文の数式は番号付きの一行算式として記述した。元DOCXの旧数式・図表・参考文献はsourcesの複製へ保全した。既存引用の意図を推測して新本文の根拠にしない。

## 保全

読取入力・旧成果{result['source_files_preserved']:,}ファイルの台帳取得時／終了SHA256と、追跡対象{result['tracked_files_preserved']}ファイルの開始／終了SHA256は一致した。追跡差分は開始時と同一である。一方、trial外のGit状態には未追跡ファイル{result['outside_trial_added_untracked']}件の開始後追加があり、Git状態全体の不変は成立しない。追加はポスターrun03領域であり、本trialの書込み対象には含まれない。発生主体の断定は行わず、CONCURRENT_WORKSPACE_CHANGES.jsonに全追加を保存した。元Word SHA256は53a3abac8d8e62db6442f92d850eb2f3bb58e876606a84f61f6fe3de1763f99fである。SOURCE_PRESERVATION_CHECKS.csv、TRACKED_PRESERVATION_CHECKS.csv、GIT_STATUS_START/FINAL.txtに記録する。保全主張は台帳にピン留めした入力・旧成果と追跡ファイルの範囲であり、ワークスペースの未読全バイトの監査ではない。

成果物の書込み先は本trial配下のみで、元データ・コード・原稿の上書き、Git commit/push、外部公開、既存研究への正式統合は実施していない。

## 採用上の制約

公平なend-to-end時間、compiled／実機資源、厳密53、T09完成pack、量子対象物性改善、B→走行DC、地域・実車妥当性、引用・Word実機を未解決として残す。道路受入と対向条件のFAILを保持する。ADOPTION_REVIEW.mdは同一エージェントによる分離監査であり、外部第三者査読を受けたとはしない。

研究者の採否判断を待つ成果物であり、採用を決定していない。
''')
# Update actual render evidence into build metadata, without claiming native Word verification.
build=json.loads((O/'THESIS_BUILD.json').read_text());build['visual_status']='LIBREOFFICE_VISUALLY_REVIEWED_WORD_HOLD';build['rendered_pages']=render['pages'];(O/'THESIS_BUILD.json').write_text(json.dumps(build,ensure_ascii=False,indent=2))
write('FINAL_CLOSURE.json',json.dumps({'verdict':'TRIAL COMPLETE','closed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'task_count':32,'claim_count':27,'unresolved_count':15,'scientific_scope':'CONDITIONAL_WITH_HOLD_AND_FAIL','Word_native':'HOLD','formal_adoption':False,'integration':False,'git_commit_push':False,'third_party_review':False},ensure_ascii=False,indent=2))
# Manifest excludes itself and transient renderer profile/cache (not research deliverables).
files=[]
for p in sorted(O.rglob('*')):
 if not p.is_file() or p.name in ['OUTPUT_SHA256_MANIFEST.csv','OUTPUT_SHA256_MANIFEST.sha256']:continue
 rel=p.relative_to(O)
 if any(k in rel.parts for k in ['profile','cache','config','matplotlib']):continue
 files.append({'path':str(rel),'bytes':p.stat().st_size,'sha256':sha(p)})
pd.DataFrame(files).to_csv(O/'OUTPUT_SHA256_MANIFEST.csv',index=False)
write('OUTPUT_SHA256_MANIFEST.sha256','\n'.join(x['sha256']+'  '+x['path'] for x in files))
print('TRIAL COMPLETE',len(files),'manifest files,',render['pages'],'pages,',counts)
