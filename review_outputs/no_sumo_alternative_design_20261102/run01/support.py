"""Read-only source registry; outputs confined to this new review."""
from pathlib import Path
import json,csv,hashlib,time,resource,subprocess,collections,math
from fractions import Fraction as F
R=Path('/home/takuma/kmd-analysis');U=Path('/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked');B=Path('/home/takuma/kmd-analysis-preservation-20261014-173544-a64e484c/backup');L=B.parent/'relocated';O=Path(__file__).resolve().parent
P1=R/'review_outputs/integrated_causal_audit_20261102/run01';P2=R/'review_outputs/complete_run_validation_20261102/run01';P3=R/'review_outputs/network_route_contract_20261102/run01';S=U/'review_outputs/staged_qaoa_validation_20261102';E=U/'review_outputs/causal_engineering_audit_20261027/run01'
SRC={};SCHEMAS={};CHECKS=[]
def sha(p):
 with Path(p).open('rb') as h:return hashlib.file_digest(h,'sha256').hexdigest()
def resolve(p):
 p=Path(p)
 if p.is_file():return p
 for root in [R,U,B,L]:
  if p.is_relative_to(root):
   for alt in [R,U,B,L]:
    q=alt/p.relative_to(root)
    if q.is_file():return q
 raise FileNotFoundError(p)
def use(p):
 p=resolve(p)
 if str(p) not in SRC:SRC[str(p)]={'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'storage':'WORKTREE' if p.is_relative_to(R) else 'EXTERNAL_UNTRACKED' if p.is_relative_to(U) else 'PRESERVATION'}
 return p
def js(p):return json.loads(use(p).read_text())
def rows(p,pk=None):
 p=use(p)
 with p.open() as h:a=list(csv.DictReader(h))
 cols=list(a[0]) if a else [];nulls={k:sum(x[k] in ('','null','NULL','NaN','nan') for x in a) for k in cols}
 SCHEMAS[str(p)]={'path':str(p),'rows':len(a),'columns':cols,'nulls':nulls,'PK':pk,'duplicate_PK':len(a)-len({tuple(x[k] for k in pk) for x in a}) if pk else None}
 return a
def dump(name,x):(O/name).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False,default=str)+'\n')
def table(name,a):
 with (O/name).open('w',newline='') as h:
  w=csv.DictWriter(h,fieldnames=list(a[0]) if a else ['status']);w.writeheader();w.writerows(a)
def check(label,exp,actual,tol=0,source=''):
 ok=abs(float(exp)-float(actual))<=tol if isinstance(exp,(int,float,F)) and isinstance(actual,(int,float,F)) else exp==actual
 CHECKS.append({'check':label,'expected':str(exp),'actual':str(actual),'tolerance':tol,'status':'PASS' if ok else 'FAIL','source':source})
def metrics(t):
 r=resource.getrusage(resource.RUSAGE_SELF);return {'wall_s':time.monotonic()-t,'CPU_s':r.ru_utime+r.ru_stime,'max_RSS_bytes':r.ru_maxrss*1024,'scope':'audit_of_saved_data_and_few_fixtures_not_full_outcome_evaluation'}
def finish(label,t,summary):
 summary['checks']=len(CHECKS);summary['failed']=[x['check'] for x in CHECKS if x['status']=='FAIL'];summary['metrics']=metrics(t)
 dump(label+'_SUMMARY.json',summary);table(label+'_CHECKS.csv',CHECKS);dump(label+'_SCHEMAS.json',list(SCHEMAS.values()));dump(label+'_SOURCES.json',list(SRC.values()));print(json.dumps(summary,ensure_ascii=False,default=str))
 if summary['failed']:raise RuntimeError('Audit mismatch; preserve FAIL evidence')
def baseline():
 t=time.monotonic();a=[]
 for root,name in [(P1,'REVIEW_ARTIFACT_MANIFEST.json'),(P2,'ARTIFACT_MANIFEST.json'),(P3,'ARTIFACT_MANIFEST.json')]:
  for x in js(root/name):
   p=use(root/x['path']);actual=SRC[str(p)]['sha256'];a.append({'path':str(p),'expected_sha256':x['sha256'],'actual_sha256':actual,'status':'PASS' if actual==x['sha256'] else 'FAIL'})
 # Read all prior review Markdown, not just filenames.
 reports=[]
 for root in [P1,P2,P3]:
  for p in sorted(root.glob('*.md')):
   body=use(p).read_text();reports.append({'path':str(p),'sha256':SRC[str(p)]['sha256'],'characters':len(body)})
 for p in [U/'docs/research/CPX01_D10_ADOPTION_DECISION_20261017.md',E/'verify_a.py',P1/'independent_audit.py',P2/'build_run_ledger.py']:use(p).read_text()
 table('PRIOR_ARTIFACT_HASH_CHECK.csv',a);table('PRIOR_REVIEW_DOCUMENTS_READ.csv',reports);check('prior artifact hash mismatches',0,sum(x['status']!='PASS' for x in a))
 dump('INITIAL_GIT_STATE.json',{'HEAD':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'status':subprocess.check_output(['git','status','--short'],cwd=R,text=True),'diff':subprocess.check_output(['git','diff','HEAD'],cwd=R,text=True)})
 finish('BASELINE',t,{'prior_artifacts_verified':len(a),'prior_reports_read':len(reports),'prohibited_executions':0})
if __name__=='__main__':baseline()
