from pathlib import Path
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
os.environ['PYTHONDONTWRITEBYTECODE']='1'
import sys,csv,json,time,hashlib,datetime,platform,subprocess,resource,math,re,itertools,collections
from fractions import Fraction as F
import numpy as np,pandas as pd
O=Path(__file__).resolve().parents[1];R=O.parents[1];U=Path('/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked');P=R/'review_outputs/no_sumo_full_analysis_20261102/run01';T=R/'review_outputs/quantum_ev_conditions_full_trial_20261104_125659';S1=R/'review_outputs/quantum_ev_step1_design_trial_20261104_153058';S=U/'review_outputs/staged_qaoa_validation_20261102';W=U/'review_outputs/unified_no_windows_r0_r8_20261022';T8=U/'review_outputs/material_ev_stage2_20261026/run02';T9=U/'review_outputs/t09_open_data_model_20261029/run01';BR=U/'review_outputs/t08_t09_conditional_bridge_20261030/run01';C=U/'review_outputs/cpu_matched_classical_swaps_r0_r5_20261101';BINS=U/'review_outputs/runtime/scip_exact_cli_20261022/scipoptsuite-10.0.3/bin'
SOURCES={};CHECKS=[];RELOC=[]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,role='source',expected=None):
 p=Path(p)
 if not p.is_file():
  old=p;roots=[R,U,Path('/home/takuma/kmd-analysis-preservation-20261014-173544-a64e484c/backup'),Path('/home/takuma/kmd-analysis-preservation-20261014-173544-a64e484c/relocated')];qs=[a/p.relative_to(b) for b in roots if p.is_relative_to(b) for a in roots];q=next((q for q in qs if q.is_file()),None)
  if q is None:raise FileNotFoundError(p)
  p=q;RELOC.append(dict(recorded_path=str(old),actual_path=str(p)))
 p=p.resolve();k=str(p)
 if k not in SOURCES:
  st=p.stat();SOURCES[k]=dict(path=k,sha256=sha(p),bytes=st.st_size,mtime_ns=st.st_mtime_ns,role=role,version='SHA256 content identity',storage='repository' if p.is_relative_to(R) else 'external preservation')
 if expected and SOURCES[k]['sha256']!=expected:raise AssertionError(f'hash mismatch: {p}')
 return p
def js(p):return json.loads(pin(p).read_text())
def frame(p,**kw):return pd.read_csv(pin(p),keep_default_na=False,low_memory=False,**kw)
def arr(p):
 with np.load(pin(p),allow_pickle=False) as z:return {k:z[k].copy() for k in z.files}
def dump(n,v):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2,default=str,allow_nan=False)+'\n')
def text(n,s):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s.strip()+'\n')
def table(n,v):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True);(v if isinstance(v,pd.DataFrame) else pd.DataFrame(v)).to_csv(p,index=False)
def ck(k,v,source='',detail=''):
 CHECKS.append(dict(check=k,status='PASS' if bool(v) else 'FAIL',source=str(source),detail=str(detail)))
 if not v:raise AssertionError((k,source,detail))
def finish(stage,t,extra=None):
 table(f'evidence/{stage}_SOURCES.csv',list(SOURCES.values()));table(f'evidence/{stage}_CHECKS.csv',pd.DataFrame(CHECKS,columns=['check','status','source','detail']))
 if RELOC:table(f'evidence/{stage}_RELOCATIONS.csv',RELOC)
 dump(f'evidence/{stage}_RUN.json',dict(stage=stage,wall_s=time.perf_counter()-t,CPU_s=resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,checks=len(CHECKS),failures=sum(x['status']=='FAIL' for x in CHECKS),**(extra or {})))
 print(json.dumps(json.loads((O/f'evidence/{stage}_RUN.json').read_text()),ensure_ascii=False,indent=2))
def objective(a,route):return sum((F(str(a['travel'][i,j])) for i,j in zip(route,route[1:])),F(0))
def feasible(a,route):return route is not None and route[0]==route[-1]==0 and sorted(route[1:-1])==list(range(1,len(a['travel']))) and sum(map(int,a['demand']))<=216 and objective(a,route)+102*(len(a['travel'])-1)<=32400
os.environ['MPLCONFIGDIR']=str(O/'logs/matplotlib')
def plotting():
 import matplotlib
 matplotlib.use('Agg');import matplotlib.pyplot as plt
 plt.rcParams.update({'font.size':9,'axes.grid':True,'grid.alpha':.2,'savefig.dpi':170})
 return plt
def savefig(fig,folder,name):
 for ext in ['png','pdf']:fig.savefig(O/f'{folder}/{name}.{ext}',bbox_inches='tight')
