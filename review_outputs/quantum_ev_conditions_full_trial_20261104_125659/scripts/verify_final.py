"""Different formula order for saved A/certificates and new continuous output audit."""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal as D,localcontext
import json,csv,sys,hashlib,zipfile,re,os,time,subprocess,shutil,unicodedata
import pandas as pd,numpy as np
from docx import Document
from lxml import etree
O=Path(__file__).resolve().parents[1];R=O.parents[1];P=R/'review_outputs/no_sumo_full_analysis_20261102/run01';U=Path('/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked');B=Path('/home/takuma/kmd-analysis-preservation-20261014-173544-a64e484c/backup');L=B.parent/'relocated'
sys.path.insert(0,str(R/'src'));from kmd_quantitative.energy.controlled_dc import evaluate
checks=[];extra={}
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def use(p):
 p=Path(p)
 if not p.is_file():
  for root in [R,U,B,L]:
   if p.is_relative_to(root):
    for alt in [R,U,B,L]:
     q=alt/p.relative_to(root)
     if q.is_file():p=q;break
    if p.is_file():break
 if str(p) not in extra:extra[str(p)]={'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
 return p
def ck(name,ok,scope='',error=None):
 checks.append(dict(check=name,status='PASS' if bool(ok) else 'FAIL',scope=scope,error=error))
 if not ok:raise AssertionError((name,scope,error))
def near(name,a,b,tol=1e-7,scope=''):ck(name,abs(float(a)-float(b))<=tol,scope,float(a)-float(b))
def read(p):
 with use(p).open() as f:return list(csv.DictReader(f))
# A: verify old rate accounting and independently replay travel/wait/service on raw NPZ.
ledger={r['PID']:r for r in read(P/'INPUT_LEDGER.csv') if r['series_id']=='A_OLD_TW'};arrays={};cache={}
for pid,row in ledger.items():
 path=use(row['input_path']);ck('A input SHA',sha(path)==row['input_sha256'],pid)
 with np.load(path,allow_pickle=False) as z:arrays[pid]={k:z[k] for k in z.files}
for name in ['A_POLICY_DECISIONS_2808.csv','A_CLASSICAL_BASELINE_2808.csv','A_MECHANISM_COMPARISON.csv']:
 rows=read(P/name)
 for r in rows:
  use(r['source_path']);use(r['quantum_source_path']);pid=r['problem_id'];rt=json.loads(r['route']);key=(pid,tuple(rt),r['departure_s'])
  if key not in cache:
   z=arrays[pid];ix={str(n):i for i,n in enumerate(z['nodes'])};order=[ix[n] for n in rt];now=F(r['departure_s']);total=F(0);on=F(0);count=0;com=[]
   for a,c in zip(order[:-2],order[1:-1]):
    now=max(now+F(str(z['travel'][a,c])),F(str(z['ready'][c])))+F(str(z['service'][c]));dem=F(str(z['demand'][c]));total+=dem;good=now<=F(str(z['due'][c]))+F(str(z['service'][c]));on+=dem if good else 0;count+=int(good);com.append(now)
   returned=now+F(str(z['travel'][order[-2],0]));cache[key]=(total,on,count,returned,sum(com,F(0))/len(com))
  total,on,count,returned,mean=cache[key]
  near('A PE denominator',r['denominator_PE'],total,scope=pid);near('A PE numerator',r['on_time_PE'],on,scope=pid);near('A PE rate',r['F_PE'],on/total,1e-12,pid);near('A count rate',r['F_count'],F(count,len(rt)-2),1e-12,pid);near('A returned',r['return_s'],returned,1e-7,pid);near('A mean completion',r['mean_completion_s'],mean,1e-7,pid)
# Certificate value and proof metadata, still not replaying solver proof.
for row in read(P/'B_EXACT_REFERENCE_COVERAGE.csv'):
 p=use(row['certificate_path']);d=json.loads(p.read_text());value=d.get('exact_optimum_seconds');available=row['exact_reference_available']=='True';ck('B certificate missingness',available==(value is not None),row['problem_id'])
 if available:
  ck('B certificate exact fraction',F(str(value))==F(row['exact_optimum_fraction']),row['problem_id']);ck('B certificate proof indicator',d.get('proved_optimal') is True or d.get('method')=='CLASSICAL_EXACT_MINPLUS_DP',row['problem_id'])
# Verify every new continuous mass in independent Decimal arithmetic.
sens=pd.read_csv(O/'PATH2_SENSITIVITY_RESULTS.csv');ck('C 45080 unique rows',len(sens)==45080 and not sens.duplicated(['trajectory_sha256','rolling_case','q_Ah_kg']).any())
for q,g in sens.groupby('q_Ah_kg'):
 with localcontext() as c:
  c.prec=40;qD=D(str(q));positive=D(20000)/(D('3.5')*qD*D('.75'));negative=D(20000)*D('1.1')/(D('3.5')*D(360)*D('.98'));cell=(positive+negative)/100+D('.19');pack=cell*100+15
 near('C independent Decimal pack',g.simplified_pack_mass_kg.iloc[0],pack,1e-10)
 ck('C all mass consistency',np.all(np.abs(g.simplified_pack_mass_kg-float(pack))<1e-10))
 ck('C vehicle+driver',np.all(np.abs(g.vehicle_mass_kg+55-g.running_mass_kg)<1e-9))
 ck('C rate arithmetic',np.all(np.abs(100*g.saving_Wh/g.baseline_DC_Wh-g.saving_percent)<1e-10))
 ck('C DC difference',np.all(np.abs(g.baseline_DC_Wh-g.DC_Wh-g.saving_Wh)<1e-7))
for rc,g in sens.groupby('rolling_case'):
 for q,h in g.groupby('q_Ah_kg'):
  target=pd.read_csv(O/'PATH2_SENSITIVITY_SUMMARY.csv');row=target[(target.rolling_case==rc)&(abs(target.q_Ah_kg-q)<1e-10)].iloc[0];near('C summary sum',h.DC_Wh.sum(),row.DC_sum_Wh,1e-6);near('C summary total rate',100*h.saving_Wh.sum()/h.baseline_DC_Wh.sum(),row.total_weighted_saving_percent,1e-9)
# Internal points, independently run unchanged kernel; endpoints alone cannot validate all branches.
freeze=json.loads(use(R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json').read_text());ref=read(P/'C_T08_ENERGY_FULL.csv');byhash={r['trajectory_sha256']:r for r in ref if r['dataset']=='CLASSICAL' and r['scenario_id']=='COND_LP_REF'};hashes=sorted(byhash);maxerr=0
for h in [hashes[0],hashes[len(hashes)//2],hashes[-1]]:
 row=byhash[h];d=pd.read_csv(use(row['trajectory_path']),usecols=['timestamp_s','speed_m_s']);choices=sens[sens.trajectory_sha256==h];grid=sorted(choices.q_Ah_kg.unique())
 for rc,pbar in [('CRR_LOWER_BOUND',4.5),('CRR_UPPER_BOUND',2.6)]:
  for k in [0,12,24,36,48]:
   x=choices[(choices.rolling_case==rc)&(abs(choices.q_Ah_kg-grid[k])<1e-10)].iloc[0];actual,_=evaluate(d.timestamp_s.to_numpy(),d.speed_m_s.to_numpy(),freeze,pbar,{'running_mass_kg':x.running_mass_kg});err=actual['net_DC_Wh']-x.DC_Wh;maxerr=max(maxerr,abs(err));near('C internal kernel check',actual['net_DC_Wh'],x.DC_Wh,1e-7,h)
# Original manuscript candidate version relation.
v7=R/'review_outputs/thesis_docx_integration_20261103/run01/revisions/v07_results_integrated.docx';root=R/'tmp_RsrchMstrDc_1026_results_integrated.docx';va=use(v7);ra=use(root)
with zipfile.ZipFile(va) as zz,zipfile.ZipFile(ra) as yy:
 changed_parts=[n for n in zz.namelist() if n in yy.namelist() and zz.read(n)!=yy.read(n)]
 xa=etree.fromstring(zz.read('word/document.xml'));xb=etree.fromstring(yy.read('word/document.xml'))
 ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
 keepcounts=[len(x.xpath('.//w:keepNext',namespaces=ns)) for x in [xa,xb]]
 for x in [xa,xb]:
  for el in x.xpath('.//w:keepNext',namespaces=ns):el.getparent().remove(el)
 equivalent=etree.tostring(xa)==etree.tostring(xb)
 ck('source v07 differs only in keepNext layout',changed_parts==['word/document.xml'] and equivalent)
 (O/'sources/SOURCE_DOCX_VERSION_COMPARISON.json').write_text(json.dumps({'selected_path':str(ra),'selected_sha256':sha(ra),'v07_path':str(va),'v07_sha256':sha(va),'bytes_equal':False,'different_zip_parts':changed_parts,'keepNext_counts_v07_selected':keepcounts,'document_equal_after_removing_keepNext':equivalent,'selection_reason':'selected root SHA matches Nov3 final integration and render08 record; content matches v07, layout differs'},ensure_ascii=False,indent=2))
# Portable small evidence snapshots; raw large scientific inputs remain at source-pinned paths.
folder=O/'sources/verified_original_tables';folder.mkdir(exist_ok=True)
for name in ['B_CLASSICAL_ORBIT_COMPARISON.csv','B_ACTIVE_GRID_SELECTION.csv','C_T09_COMPONENTS_183.csv']:
 p=use(P/name);shutil.copyfile(p,folder/name)
cm=pd.read_csv(O/'CLAIM_EVIDENCE_MATRIX.csv')
for name in ['B_CLASSICAL_ORBIT_COMPARISON.csv','B_ACTIVE_GRID_SELECTION.csv','C_T09_COMPONENTS_183.csv']:cm['evidence']=cm['evidence'].map(lambda x: re.sub(r'(?:sources/verified_original_tables/)*'+re.escape(name),'sources/verified_original_tables/'+name,x))
cm.to_csv(O/'CLAIM_EVIDENCE_MATRIX.csv',index=False)
for ev in cm.evidence:
 for filename in ev.split(';'):ck('claim evidence path exists',(O/filename).is_file(),filename)
# Native document package, heading/table/image, equation numbering, and source MD equality.
d=Document(O/'THESIS_TRIAL.docx');ck('DOCX tables',len(d.tables)==4);ck('DOCX figures',len(d.inline_shapes)==4)
with zipfile.ZipFile(O/'THESIS_TRIAL.docx') as z:
 ck('DOCX zip',z.testzip() is None)
 for name in z.namelist():
  if name.endswith('.xml') or name.endswith('.rels'):etree.fromstring(z.read(name))
paras=[p.text for p in d.paragraphs];md=(O/'THESIS_SECTIONS_TRIAL.md').read_text()
for para in paras:
 if para.strip():ck('DOCX paragraph in Markdown',para in md,para[:40])
for num in range(1,8):ck('equation number once',sum(f'({num})' in x and re.match(r'^(T\(|gap|T_pre|m_pack|E_DC|Δm|saving)',x) is not None for x in paras)==1,str(num))
for num in range(1,5):ck('figure caption unique',sum(x.startswith('図'+str(num)+'　') for x in paras)==1,str(num));ck('table caption unique',sum(x.startswith('表'+str(num)+'　') for x in paras)==1,str(num))
# Table cells match their canonical CSV-derived Markdown cells exactly.
for t in d.tables:
 for row in t.rows:
  for cell in row.cells:ck('DOCX cell appears in Markdown',cell.text in md,cell.text[:40])
# All plain-text citations and required holds are present, no old main rate paragraph remained.
for term in ['RQ0','RQ1','RQ2','RQI','定時配達率を主指標','量子由来','未検証','HOLD']:
 ck('thesis scope text',term in md,term)
# PDF full text coverage, normalized to ignore line wrapping.
pdf=(O/'render_final/TEXT.txt').read_text();pdf='\n'.join(line for line in pdf.splitlines() if not (('KMD' in line and '正式採用未定' in line) or re.fullmatch(r'\s*\d+\s*',line)));norm=lambda s:re.sub(r'\s+','',unicodedata.normalize('NFKC',s))
for para in paras:
 if para.strip():ck('PDF paragraph coverage',norm(para) in norm(pdf),para[:50])
# Required artifacts/tasks/claim verdicts.
required=['README.md','EXECUTIVE_SUMMARY.md','TASK_COMPLETION_MATRIX.csv','CLAIM_EVIDENCE_MATRIX.csv','RQ_REDESIGN_TRIAL.md','INDICATOR_DEFINITIONS.md','RESEARCH_BOUNDARY.md','EXPERIMENT_INVENTORY.csv','HOLD_REGISTER.md','ADDITIONAL_ANALYSIS_DECISIONS.md','PATH1_METHOD_AUDIT.md','PATH1_QUALITY_COMPARISON.csv','PATH1_RUNTIME_COMPARISON.csv','PATH1_RESOURCE_REQUIREMENTS.md','PATH1_CONTRIBUTION_CONDITIONS.md','PATH2_MATERIAL_BRIDGE_AUDIT.md','PATH2_MODEL_VALIDATION.md','PATH2_SENSITIVITY_RESULTS.csv','PATH2_BOUNDARY_RESULTS.csv','PATH2_OPERATION_INTERACTIONS.md','PATH2_CONTRIBUTION_CONDITIONS.md','INTEGRATED_CAUSAL_MODEL_TRIAL.md','CROSS_PATH_CONDITIONS_MATRIX.csv','DISCUSSION_TRIAL.md','LIMITATIONS.md','LITERATURE_CLASSIFICATION.csv','LITERATURE_EVIDENCE_MATRIX.csv','LITERATURE_REVIEW_TRIAL.md','RESEARCH_GAP.md','THESIS_TRIAL.docx','THESIS_SECTIONS_TRIAL.md','FIGURE_TABLE_INDEX.md','THESIS_CHANGELOG.md','UNRESOLVED_ITEMS.md','ADOPTION_REVIEW.md']
# Final reports written by finalize.py after this audit; their presence is checked in final closure.
for name in required:ck('required artifact', (O/name).is_file(),name)
tasks=pd.read_csv(O/'TASK_COMPLETION_MATRIX.csv');ck('tasks exactly32',len(tasks)==32 and tasks.task_id.nunique()==32)
counts=[4,4,6,6,4,3,3,2]
for step,n in enumerate(counts,1):ck('step task count',len(tasks[tasks.task_id.str.startswith(f'S{step}-')])==n,str(step))
ck('claim valid verdicts',set(cm.status)<=set(['PASS','CONDITIONAL','HOLD','FAIL']))
# Source preservation: all scientific files read by analysis, and explicitly added primary PDFs.
source=pd.read_csv(O/'SOURCE_BASELINE.csv');extra_rows=list(extra.values())+read(O/'PRIMARY_PDF_SOURCES.csv')
for item in extra_rows:
 if item['path'] not in set(source.path):source=pd.concat([source,pd.DataFrame([{k:item[k] for k in ['path','sha256','bytes']}])],ignore_index=True)
source.to_csv(O/'SOURCE_BASELINE_EXTENDED.csv',index=False)
preserve=[]
for x in source.to_dict('records'):
 path=Path(x['path']);actual=sha(path) if path.is_file() else 'MISSING';preserve.append({'path':x['path'],'before_sha256':x['sha256'],'after_sha256':actual,'status':'PASS' if actual==x['sha256'] else 'FAIL'})
ck('all read sources preserved',all(x['status']=='PASS' for x in preserve));pd.DataFrame(preserve).to_csv(O/'SOURCE_PRESERVATION_CHECKS.csv',index=False)
tracked=json.loads((O/'TRACKED_BASELINE.json').read_text());tp=[]
for x in tracked:tp.append({'path':x['path'],'start_sha256':x['sha256'],'end_sha256':sha(R/x['path']),'status':'PASS' if sha(R/x['path'])==x['sha256'] else 'FAIL'})
ck('all tracked files preserved',all(x['status']=='PASS' for x in tp));pd.DataFrame(tp).to_csv(O/'TRACKED_PRESERVATION_CHECKS.csv',index=False)
status=subprocess.check_output(['git','status','--porcelain=v1','--untracked-files=all'],cwd=R).decode();(O/'GIT_STATUS_FINAL.txt').write_text(status);(O/'GIT_DIFF_FINAL.patch').write_bytes(subprocess.check_output(['git','diff','HEAD','--binary'],cwd=R));initial=(O/'GIT_STATUS_START.txt').read_text().splitlines();filtered=[line for line in status.splitlines() if str(O.relative_to(R))+'/' not in line];added=sorted(set(filtered)-set(initial));removed=sorted(set(initial)-set(filtered))
ck('Pre-existing Git status entries retained',not removed)
ck('New outside Git entries are untracked',all(x.startswith('?? ') for x in added))
(O/'CONCURRENT_WORKSPACE_CHANGES.json').write_text(json.dumps({'outside_trial_git_unchanged':initial==filtered,'added_count':len(added),'removed_count':len(removed),'added':added,'removed':removed,'interpretation':'Start-to-end Git state differs due to untracked additions outside this trial. No attribution to an external actor is asserted; all task write paths are inside this trial. Pinned scientific sources and tracked hashes are checked separately.'},ensure_ascii=False,indent=2))
ck('Git tracked diff unchanged',(O/'GIT_DIFF_START.patch').read_bytes()==(O/'GIT_DIFF_FINAL.patch').read_bytes())
pd.DataFrame(checks).to_csv(O/'FINAL_INDEPENDENT_CHECKS.csv',index=False)
result={'status':'PASS_TECHNICAL_CHECKS_CONDITIONAL_RESEARCH','checks':len(checks),'failures':sum(x['status']=='FAIL' for x in checks),'A_unique_route_departure_replays':len(cache),'A_saved_rows_audited':2808*2+9216,'C_internal_kernel_checks':30,'C_internal_kernel_max_error_Wh':maxerr,'source_files_preserved':len(preserve),'tracked_files_preserved':len(tp),'outside_trial_git_status_changed':bool(added or removed),'outside_trial_added_untracked':len(added),'compiled_resources_recreated':False,'third_party_review':False}
(O/'FINAL_VERIFICATION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False,indent=2))
