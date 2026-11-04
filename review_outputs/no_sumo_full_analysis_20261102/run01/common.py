"""Read-only scientific inputs; all writes restricted to this review directory."""
from pathlib import Path
import json,csv,hashlib,time,resource,subprocess,sys,collections,math,platform
from fractions import Fraction as F
R=Path('/home/takuma/kmd-analysis');U=Path('/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked');B=Path('/home/takuma/kmd-analysis-preservation-20261014-173544-a64e484c/backup');L=B.parent/'relocated';O=Path(__file__).resolve().parent
P1=R/'review_outputs/integrated_causal_audit_20261102/run01';P2=R/'review_outputs/complete_run_validation_20261102/run01';P3=R/'review_outputs/network_route_contract_20261102/run01';P4=R/'review_outputs/no_sumo_alternative_design_20261102/run01';S=U/'review_outputs/staged_qaoa_validation_20261102';T8=U/'review_outputs/material_ev_stage2_20261026/run02';T9=U/'review_outputs/t09_open_data_model_20261029/run01';BR=U/'review_outputs/t08_t09_conditional_bridge_20261030/run01'
SRC={};CHECK=[]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def resolve(p):
 p=Path(p)
 if p.is_file():return p
 for root in [R,U,B,L]:
  if p.is_relative_to(root):
   for alt in [R,U,B,L]:
    q=alt/p.relative_to(root)
    if q.is_file():return q
 raise FileNotFoundError(p)
def use(p,expected=None):
 p=resolve(p);k=str(p)
 if k not in SRC:SRC[k]={'path':k,'sha256':sha(p),'bytes':p.stat().st_size,'storage':'WORKTREE' if p.is_relative_to(R) else 'EXTERNAL_PRESERVATION'}
 if expected and SRC[k]['sha256']!=expected:raise ValueError('HASH_MISMATCH '+k)
 return p
def js(p):return json.loads(use(p).read_text())
def rows(p):
 with use(p).open() as f:return list(csv.DictReader(f))
def dump(n,x):
 p=O/n;p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False,default=str)+'\n')
def table(n,x):
 p=O/n;p.parent.mkdir(exist_ok=True,parents=True);fields=list(dict.fromkeys(k for a in x for k in a)) if x else ['status']
 with p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(x)
def check(k,exp,act,tol=0,loc=''):
 ok=abs(float(exp)-float(act))<=tol if isinstance(exp,(int,float,F)) and isinstance(act,(int,float,F)) else exp==act
 if not ok or len(CHECK)<100000:CHECK.append({'check':k,'expected':str(exp),'actual':str(act),'tolerance':tol,'status':'PASS' if ok else 'FAIL','location':loc})
 if not ok:raise ValueError(f'{k}: expected={exp}; actual={act}; {loc}')
def fraction(x):return F(str(x))
def metric(t):
 x=resource.getrusage(resource.RUSAGE_SELF);return {'wall_s':time.monotonic()-t,'CPU_s':x.ru_utime+x.ru_stime,'max_RSS_bytes':x.ru_maxrss*1024}
def finish(label,t,extra):
 extra.update(metrics=metric(t),checks=len(CHECK),failures=sum(x['status']!='PASS' for x in CHECK));dump(label+'_RUN.json',extra);table(label+'_CHECKS.csv',CHECK);dump(label+'_SOURCES.json',list(SRC.values()));print(json.dumps(extra,ensure_ascii=False,default=str),flush=True)
def require_batch(series):
 g=js(O/'BATCH_GATE.json')
 if not g.get('full_execution_GO') or series not in g['series_PASS']:raise RuntimeError('Batch gate not passed')
def npz(p,expected=None):
 import numpy as np
 with np.load(use(p,expected),allow_pickle=False) as z:return {k:z[k].copy() for k in z.files}
def keyhash(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),default=str).encode()).hexdigest()
