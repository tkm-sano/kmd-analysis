from pathlib import Path
import hashlib,json,time,subprocess,re
import pandas as pd
from docx import Document
O=Path(__file__).resolve().parents[1];R=O.parents[1]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def md(n,s):(O/n).write_text(s.strip()+'\n')
t0=time.perf_counter();checks=[]
def ck(n,v,detail=''):
 checks.append(dict(check=n,status='PASS' if v else 'FAIL',detail=detail));assert v,(n,detail)
required='STEP3_CLAIM_REGISTER.csv CLAIM_EVIDENCE_LEVELS.md CONFIRMED_VS_UNVERIFIED_FINDINGS.md STEP3_SOURCE_MANIFEST.csv PATH1_CONTRIBUTION_CONDITIONS.md PATH1_CONDITION_CLASSIFICATION.csv PATH1_THEORETICAL_VS_EMPIRICAL.md PATH1_LIMITATIONS.md PATH2_CONTRIBUTION_CONDITIONS.md PATH2_CONDITION_CLASSIFICATION.csv PATH2_MODEL_DEPENDENCE.md PATH2_LIMITATIONS.md CROSS_PATH_CONDITION_MATRIX.csv COMMON_CONTRIBUTION_FRAMEWORK.md SYNTHESIZED_RESEARCH_FINDINGS.md GENERALIZABILITY_ASSESSMENT.md RESEARCH_CONTRIBUTION_STATEMENT.md RESEARCH_OBJECTIVE_RQ_ALIGNMENT.md THESIS_RESULTS_DRAFT.md THESIS_DISCUSSION_DRAFT.md THESIS_CONCLUSION_DRAFT.md THESIS_FIGURE_TABLE_PLAN.md THESIS_CITATION_CHECK.md THESIS_STEP3_TRIAL.docx STEP3_ACADEMIC_REVIEW.md CLAIM_STRENGTH_AUDIT.csv ALTERNATIVE_EXPLANATIONS.md THESIS_STATEMENT_CORRECTIONS.md README.md EXECUTIVE_SUMMARY.md STEP3_COMPLETION_MATRIX.csv MAIN_RESEARCH_FINDINGS.md CONTRIBUTION_CONDITIONS_FINAL.csv EVIDENCE_TRACEABILITY.csv CROSS_PATH_SYNTHESIS.md VERIFIED_AND_UNVERIFIED_CAUSAL_LINKS.md UNRESOLVED_ITEMS.md STEP4_HANDOFF.md CHEN_2020_ADOPTION_CORRECTION.md PATH2_INPUT_PROVENANCE.csv PATH2_MAIN_VS_REFERENCE_RESULTS.md CHEN_DEPENDENCY_AUDIT.csv STEP3_MIDRUN_CORRECTION_LOG.md'.split()
for n in required:ck('required artifact '+n,(O/n).is_file() and (O/n).stat().st_size>0)
c=pd.read_csv(O/'STEP3_CLAIM_REGISTER.csv');ck('31 unique claims and dual axes',len(c)==31 and c.claim_id.is_unique and c.evidence_types.notna().all() and c.audit_status.isin(['PASS','CONDITIONAL','HOLD','FAIL']).all())
for n in ['CONTRIBUTION_CONDITIONS_FINAL.csv','CLAIM_STRENGTH_AUDIT.csv']:
 x=pd.read_csv(O/n);ck('claim consistency '+n,x.claim_id.tolist()==c.claim_id.tolist() and x.claim_text.tolist()==c.claim_text.tolist())
trace=pd.read_csv(O/'EVIDENCE_TRACEABILITY.csv');ck('all claim trace files exist',set(trace.claim_id)==set(c.claim_id) and all(Path(p).is_file() for p in trace.source));ck('analysis code/log paths exist',all(Path(p).is_file() for p in trace.analysis_code) and all(Path(p).is_file() for p in trace.execution_log))
ref=c[c.result_role=='条件付き参考例'];ck('Chen numeric claims reference-only',len(ref)==7 and (ref.Chen_dependency=='YES').all() and ref.claim_text.str.startswith('【未採用の条件付き参考例】').all())
for n in ['PATH2_CONTRIBUTION_CONDITIONS.md','THESIS_RESULTS_DRAFT.md']:
 t=(O/n).read_text();ck('main sensitivity precedes reference '+n,t.index('連続入力')<t.index('条件付き参考'))
fig=pd.read_csv(O/'FIGURE_INDEX.csv');ck('seven reproducible figure pairs',len(fig)==7 and all((O/p).is_file() and (O/Path(p).with_suffix('.pdf')).is_file() for p in fig.path))
doc=Document(O/'THESIS_STEP3_TRIAL.docx');ck('docx seven figures three tables',len(doc.inline_shapes)==7 and len(doc.tables)==3)
text='\n'.join(x.text for x in doc.paragraphs)+'\n'+'\n'.join(cell.text for table in doc.tables for row in table.rows for cell in row.cells)
for term in ['未採用','条件付き参考','414','46','41','H_plan','1000','58/97','78/97','5.448297','0.412579']:ck('docx retained caveat/numeric '+term,term in text)
pa=json.loads((O/'render/PAGE_AUDIT.json').read_text());ck('no empty rendered pages',min(x['characters'] for x in pa)>50);ck('no replacement characters',all(x['replacement_characters']==0 for x in pa));ck('render docx newer than build',(O/'render/THESIS_STEP3_TRIAL.pdf').stat().st_mtime>(O/'THESIS_STEP3_TRIAL.docx').stat().st_mtime)
num=pd.read_csv(O/'evidence/NUMERICAL_RECHECK.csv');ck('19 upstream numeric checks pass',len(num)==19 and num.status.eq('PASS').all())
dc=pd.read_csv(O/'data/DC_MASS_KERNEL_INDEPENDENT.csv');ck('920 independent material-free checks',len(dc)==920 and dc.Chen_capacity_input.eq('NONE').all() and (dc.right_derivative_lo_Wh_kg>0).all());ck('paired trajectories and Crr',dc.groupby('trajectory_sha256').size().eq(2).all() and dc.trajectory_sha256.nunique()==460)
# Rehash read-only inputs and tracked files, including previously untracked original documents in source inventory.
manifest=pd.read_csv(O/'STEP3_SOURCE_MANIFEST.csv');pres=[]
for x in manifest.to_dict('records'):
 p=Path(x['path']);actual=sha(p) if p.is_file() else '';pres.append(dict(path=str(p),baseline_sha256=x['sha256'],final_sha256=actual,scope='source manifest',status='PASS' if actual==x['sha256'] else 'FAIL'))
for x in json.loads((O/'evidence/TRACKED_BASELINE.json').read_text()):
 p=Path(x['path']);actual=sha(p) if p.is_file() else '';pres.append(dict(path=str(p),baseline_sha256=x['sha256'],final_sha256=actual,scope='tracked baseline',status='PASS' if actual==x['sha256'] else 'FAIL'))
pd.DataFrame(pres).to_csv(O/'evidence/PRESERVATION_RESULTS.csv',index=False);ck('all original source and tracked bytes unchanged',all(x['status']=='PASS' for x in pres),f'{len(manifest)} source records + 100 tracked baselines')
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();ck('HEAD unchanged',head==json.loads((O/'evidence/START.json').read_text())['head'])
diff=subprocess.check_output(['git','diff','--binary'],cwd=R);ck('tracked working diff unchanged',diff==(O/'evidence/GIT_DIFF_START.patch').read_bytes())
pd.DataFrame(checks).to_csv(O/'evidence/FINAL_CHECKS.csv',index=False)
summary=dict(status='TRIAL COMPLETE',scientific_judgment='CONDITIONAL; unresolved HOLD and inherited FAIL retained',claims=len(c),source_files=len(manifest),tracked=100,preservation_records=len(pres),pages=len(pa),figures=7,tables=3,checks=len(checks),failures=0,wall_s=time.perf_counter()-t0)
(O/'evidence/FINAL_RUN.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
report=f'''# Step3最終監査
総合実行判定：TRIAL COMPLETE。研究上の主張は適用範囲付きCONDITIONALを含み、HOLDと既存FAILを維持する。完了と科学的主張の確実性は別である。
Task3-1〜3-6の主張/条件/統合/三草稿/図表/独立Word/反証レビューを作成した。31主張の証拠種類A〜Fと監査判定を別軸にした。主要数値は元CSV、分析コード、実行ログへ追跡し、19件の上流数値検算を全PASSで記録した。定義からの必要条件/収支と、460入力の支持DPや保存観測を分離した。
研究者の実行中指示により、Chen逆算容量は主分析の確定材料値として未採用HOLDに戻した。主分析は連続入力の解析感度、一般相殺境界と材料非依存DC質量応答である。5.448297kg、.877094、3.193156V、約0.413%、T09具体差、49点/uV格子は条件付き参考例として保持した。新しい材料性能値を設定していない。初期草稿の履歴はevidence/pre_correctionに明示保存し、採用対象の根拠台帳と混在させない。
DC追加検算は保存460軌跡×2Crr、宣言済み1000〜1250kgの凍結式だけを用い、材料容量を入力せず920条件の正傾きを再確認した。これは実車妥当性や材料の実現確率の評価ではない。元の約0.413%の数値自体は再定義していない。
統計上、旧10repと新97fit、固定cohortと仮想group再標本化、軌跡分布と決定論的感度を区別した。Wilson区間だけでp1/p2差の有意性を主張していない。36,800計画、49点、920条件を独立実運用実験とは扱わない。
7図PNG/PDF、3表、結果/考察/結論草稿、独立DOCXを生成した。LibreOfficeで{len(pa)}ページへ変換し、置換文字0・空白ページなしを検査した。表示目視結果はrender/VISUAL_QA.mdを参照する。Word実機・大学最終様式はHOLDである。限定2件の社会技術文献の確認範囲と、Chen原著の直接報告/逆算を記録し、Papachristos同定HOLDを残した。全既存引用の全文監査完了とはしない。
残るHOLD：46未証明、41保存MIPの外部証明、旧8設定予算統制、raw-shot可行率の一部、H_plan/全時間、QPU/compiled、Chen入力適格性、独立材料範囲、設計部材/未知BOM/完成pack、実材料/実車/道路運用、文献同定。既存道路受入FAILとT09_ROW183対向条件FAILは未解消である。危険な解釈候補7件は限定表現へ修正した。最終主張の未修正FAILは採用していない。
保全：{len(manifest)}件の源ファイルと追跡100ファイルの開始/終了SHA256は一致した。HEADと既存tracked diffも一致した。既存データ・コード・Step1/2・原稿を上書きせず、commit/push/公開/正式統合は行っていない。保全は登録した入力・追跡ファイルについての確認であり、ワークスペース外の全ファイル監視という意味ではない。
Step4は研究者の採否判断後に独立コピーで統合を開始できる。HOLDを無条件に解消せず、Chen依存参考ラベル・主指標・証拠非対称性・未検証接続を保持する。今回の成果は独立したStep3 trialであり、正式採用・既存論文への統合は未実施である。
'''
for n in ['STEP3_FINAL_AUDIT.md','FINAL_AUDIT_REPORT.md']:md(n,report)
md('evidence/pre_correction/README.md','''# 修正前草稿の履歴
実行中のChen採用修正前に生成したStep3草稿の保存である。最終主張・原稿・研究成果の採用対象ではない。現在有効な分類はtrial rootの主張台帳、CHEN_2020_ADOPTION_CORRECTION.md、CHEN_DEPENDENCY_AUDIT.csvを参照する。元Step1/2を改変したファイルではない。''')
with (O/'README.md').open('a') as f:f.write('\n実行判定はTRIAL COMPLETE。図7件・表3件・独立Wordを生成し、PDF/ページPNGで確認した。経路2の主分析とChen依存参考例の再分類が本trialの実質的修正である。scripts/synthesize.py単体およびevidence/pre_correctionは修正前段階で、最終採用対象ではない。再現はREPRODUCIBILITY_REPORTの全順序を参照する。\n')
# One output inventory; omit itself to avoid circular hashes. Rendering profile/cache are non-research runtime files.
outputs=[]
for p in sorted(O.rglob('*')):
 if p.is_file() and p.name!='OUTPUT_SHA256_MANIFEST.csv' and not any(z in p.relative_to(O).parts for z in ['profile','cache','config','matplotlib']):outputs.append(dict(path=str(p.relative_to(O)),bytes=p.stat().st_size,sha256=sha(p)))
pd.DataFrame(outputs).to_csv(O/'OUTPUT_SHA256_MANIFEST.csv',index=False)
print(json.dumps(summary,ensure_ascii=False,indent=2))
