from pathlib import Path
import json,hashlib,shutil,re,zipfile
from lxml import etree
from docx import Document
import pandas as pd
O=Path(__file__).resolve().parents[1];R=O.parents[1];S3=R/'review_outputs/quantum_ev_step3_synthesis_trial_20261104_174309';OTHER=R/'review_outputs/quantum_ev_thesis_step3_integration_20261104_173959';BASE=R/'tmp_RsrchMstrDc_1026_results_integrated.docx'
sources={}
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,role,expected=None):
 p=Path(p).resolve();assert p.is_file(),p;h=sha(p)
 if expected:assert h==expected,(p,h,expected)
 sources[str(p)]=dict(path=str(p),sha256=h,bytes=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns,role=role);return p
# Revalidate frozen Step3 and its primary input identities.
for x in pd.read_csv(S3/'OUTPUT_SHA256_MANIFEST.csv').to_dict('records'):pin(S3/x['path'],'Step3 artifact',x['sha256'])
for x in pd.read_csv(S3/'STEP3_SOURCE_MANIFEST.csv').to_dict('records'):pin(x['path'],'Step3 upstream source',x['sha256'])
candidates=[R/'tmp_RsrchMstrDc_1026_revised.docx',BASE, R/'review_outputs/thesis_docx_integration_20261103/run01/revisions/v07_results_integrated.docx',OTHER/'THESIS_UPDATED_STEP3.docx',OTHER/'sources/ORIGINAL_THESIS.docx',R/'review_outputs/quantum_ev_conditions_full_trial_20261104_125659/THESIS_TRIAL.docx',S3/'THESIS_STEP3_TRIAL.docx'];rows=[]
for p in candidates:
 pin(p,'thesis candidate');d=Document(p);rows.append(dict(path=str(p),sha256=sha(p),paragraphs=len(d.paragraphs),text_characters=sum(len(x.text) for x in d.paragraphs),tables=len(d.tables),images=len(d.inline_shapes),OMML=len(d._element.xpath('.//m:oMath')),status='CONTENT_BASELINE_NOT_FORMAL_RECOGNITION' if p==BASE else 'comparison candidate'))
pd.DataFrame(rows).to_csv(O/'evidence/THESIS_CANDIDATES.csv',index=False);shutil.copyfile(BASE,O/'sources/BASELINE_THESIS.docx')
for p in (OTHER/'sources/literature').glob('*'):
 if p.is_file() and not p.name.startswith('REJECTED_'):pin(p,'prior retrieved primary literature/metadata')
for root in [OTHER,R/'review_outputs/thesis_docx_integration_20261103/run01',R/'review_outputs/quantum_ev_conditions_full_trial_20261104_125659']:
 for p in root.glob('*'):
  if p.is_file() and p.suffix in ['.md','.csv','.json']:pin(p,'prior authority/change/audit record')
d=Document(BASE);pindex={id(x._p):i for i,x in enumerate(d.paragraphs)};structure=[];pno=0;tno=0;full=[];chapter='front';section=''
for j,el in enumerate(d._element.body):
 typ=etree.QName(el).localname
 if typ=='sectPr':continue
 txt=''.join(el.itertext()) if False else ''.join(el.xpath('.//w:t/text() | .//m:t/text()'))
 if typ=='p':
  p=d.paragraphs[pno];style=p.style.name
  if style=='Heading 1':chapter=p.text
  if style.startswith('Heading'):section=p.text
  ix=pno;pno+=1
 else:style='Table';ix=tno;tno+=1
 structure.append(dict(block_id=f'SRC{j:04d}',body_index=j,element=typ,paragraph_index=ix if typ=='p' else '',table_index=ix if typ=='tbl' else '',style=style,chapter=chapter,section=section,text=txt,text_characters=len(txt),OMML=len(el.xpath('.//m:oMath')),drawings=len(el.xpath('.//w:drawing')),xml_sha256=hashlib.sha256(etree.tostring(el)).hexdigest()))
 full.append(f'[{j} / {typ} / {ix}] {txt}')
pd.DataFrame(structure).to_csv(O/'ORIGINAL_THESIS_STRUCTURE.csv',index=False);(O/'sources/BASELINE_TEXT.txt').write_text('\n\n'.join(full))
# Preserve source relationships/styles/equations and exact baseline bytes as the recoverable origin.
for n in ['STEP4_HANDOFF.md','MAIN_RESEARCH_FINDINGS.md','CONTRIBUTION_CONDITIONS_FINAL.csv','EVIDENCE_TRACEABILITY.csv','CROSS_PATH_SYNTHESIS.md','RESEARCH_CONTRIBUTION_STATEMENT.md','VERIFIED_AND_UNVERIFIED_CAUSAL_LINKS.md','THESIS_RESULTS_DRAFT.md','THESIS_DISCUSSION_DRAFT.md','THESIS_CONCLUSION_DRAFT.md','CHEN_2020_ADOPTION_CORRECTION.md','CHEN_DEPENDENCY_AUDIT.csv','FINAL_AUDIT_REPORT.md','UNRESOLVED_ITEMS.md']:
 (O/'evidence'/('STEP3_'+n)).write_bytes((S3/n).read_bytes())
for n in ['PATH1_STATISTICAL_RESULTS.csv','QAOA_CONTROLLED_CELL_SUMMARY.csv','PATH1_RUNTIME_SUMMARY.csv','PATH2_ANALYTICAL_SENSITIVITY.csv','DC_MASS_KERNEL_INDEPENDENT.csv','DC_MASS_KERNEL_SUMMARY.csv','DC_ENDPOINT_RECHECK.csv','PATH2_T09_COMMON_INPUT_SENSITIVITY.csv']:
 shutil.copyfile(S3/'data'/n,O/'data'/n)
for n in ['CONTRIBUTION_CONDITIONS_FINAL.csv','PATH2_INPUT_PROVENANCE.csv','CHEN_DEPENDENCY_AUDIT.csv']:shutil.copyfile(S3/n,O/'data'/n)
pd.DataFrame(sources.values()).to_csv(O/'SOURCE_BASELINE_SHA256.csv',index=False)
(O/'SOURCE_THESIS_AUTHORITY.md').write_text(f'''# 統合基準と権威範囲
内容保全の基準は {BASE}、SHA256 {sha(BASE)} である。11月3日統合記録の最終出力hashに一致し、元改訂版からの挿入・保全・表示記録が残る。908段落・27表・19画像・86OMMLを持ち、既存方法と付録の保全性が候補中で最も高い。
これは正式版を新たに認定した判断ではない。現在研究者が正式承認したファイル名を証明する決裁記録は未確認である。trial作成の基準選択に限定する。日時だけで選んでいない。
11月4日17:39の別統合trialは48頁・406段落・11表・8画像・45OMMLで、旧付録44式は元DOCXだけに保全していた。文献一次資料は利用可能だが、今回のChen採用修正と全文保全の基準として自動継承しない。12:56統合trialと14頁Step3は短い独立草稿であり全文代替にしない。元改訂版ea25…とv07は来歴比較として保持する。
優先順位は今回の研究者指示→Step3修正後の主張と根拠→Step2実験記録→元原稿の有効な方法・背景・文献・付録である。現行READMEの旧定時率・面接方針は履歴資料であり、新しい研究方針へ戻す根拠にはしない。
原稿の各XML blockを一意IDへ分解し、現行本文へ再使用する内容と保存付録へ移す内容を対応付ける。主張の正式採用判断は研究者に残す。
''')
print(json.dumps(dict(trial=str(O),sources=len(sources),source_blocks=len(structure),candidates=len(rows)),ensure_ascii=False))
