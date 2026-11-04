"""Read-only thesis review utilities; no scientific runner is imported."""
from pathlib import Path
import csv,json,hashlib,time,resource,subprocess,sys,collections,math
R=Path('/home/takuma/kmd-analysis');U=Path('/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked');B=Path('/home/takuma/kmd-analysis-preservation-20261014-173544-a64e484c/backup');L=B.parent/'relocated';O=Path(__file__).resolve().parents[1];F=R/'review_outputs/no_sumo_full_analysis_20261102/run01';D=R/'review_outputs/no_sumo_alternative_design_20261102/run01';S=U/'review_outputs/staged_qaoa_validation_20261102';DOC=R/'tmp_RsrchMstrDc_1026_revised.docx'
SOURCES={}
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
def use(p,expected=None):
 p=resolve(p)
 if str(p) not in SOURCES:SOURCES[str(p)]={'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'location':'WORKTREE' if p.is_relative_to(R) else 'EXTERNAL_PRESERVATION_NOT_PUBLIC_GIT'}
 if expected and SOURCES[str(p)]['sha256']!=expected:raise ValueError('HASH_MISMATCH '+str(p))
 return p
def js(p):return json.loads(use(p).read_text())
def rows(p):
 with use(p).open() as h:return list(csv.DictReader(h))
def dump(n,x):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False,default=str)+'\n')
def table(n,a):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True);fields=list(dict.fromkeys(k for x in a for k in x)) if a else ['status']
 with p.open('w',newline='') as h:w=csv.DictWriter(h,fieldnames=fields);w.writeheader();w.writerows(a)
def metrics(t):
 z=resource.getrusage(resource.RUSAGE_SELF);return {'wall_s':time.monotonic()-t,'CPU_s':z.ru_utime+z.ru_stime,'max_RSS_bytes':z.ru_maxrss*1024}
def finish(label,t,info):
 dump(label+'_SOURCES.json',list(SOURCES.values()));info['metrics']=metrics(t);dump(label+'_SUMMARY.json',info);print(json.dumps(info,ensure_ascii=False,default=str))
def mdtable(data,cols):
 return '|'+ '|'.join(label for key,label in cols)+'|\n|'+'|'.join('---' for _ in cols)+'|\n'+'\n'.join('|'+ '|'.join(str(x.get(key,'')) for key,label in cols)+'|' for x in data)
def doc(n,s):(O/n).write_text(s.strip()+'\n')
