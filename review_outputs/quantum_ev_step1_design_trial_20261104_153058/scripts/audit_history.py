from pathlib import Path
import pandas as pd,numpy as np,json,hashlib,datetime
from fractions import Fraction as F
O=Path(__file__).resolve().parents[1];R=O.parents[1];U=Path('/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked');P=R/'review_outputs/no_sumo_full_analysis_20261102/run01';T=R/'review_outputs/quantum_ev_conditions_full_trial_20261104_125659';S=U/'review_outputs/staged_qaoa_validation_20261102';W=U/'review_outputs/unified_no_windows_r0_r8_20261022'
prov=pd.read_csv(O/'SOURCE_PROVENANCE.csv',keep_default_na=False).to_dict('records');known={x['path'] for x in prov};checks=[]
def use(p,role):
 p=Path(p)
 if not p.is_file():
  roots=[R,U,Path('/home/takuma/kmd-analysis-preservation-20261014-173544-a64e484c/backup'),Path('/home/takuma/kmd-analysis-preservation-20261014-173544-a64e484c/relocated')];qs=[a/p.relative_to(b) for b in roots if p.is_relative_to(b) for a in roots];p=next(q for q in qs if q.is_file())
 if str(p) not in known:
  st=p.stat();prov.append(dict(path=str(p),version='saved file; hash identifies version',sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),bytes=st.st_size,mtime_utc=datetime.datetime.fromtimestamp(st.st_mtime,datetime.timezone.utc).isoformat(),role=role,reference=role,storage='repository' if p.is_relative_to(R) else 'external preservation'));known.add(str(p))
 return p
def ck(k,v,source,detail=''):checks.append(dict(check=k,status='PASS' if bool(v) else 'FAIL',source=str(source),detail=str(detail)))
ops_path=use(U/'review_outputs/cpx01_d11_validation_20261017/operations_2808.csv','A original policy table');ops=pd.read_csv(ops_path,keep_default_na=False);covered=pd.read_csv(R/'review_outputs/no_sumo_alternative_design_20261102/run01/A_INPUT_COVERAGE.csv',keep_default_na=False);acq=[];saved=[]
for pid,g in ops.groupby('PID'):
 x=g.iloc[0];mp=covered[covered.PID==pid].iloc[0];ip=use(mp.input_path,'A old time-window NPZ')
 with np.load(ip,allow_pickle=False) as z:present_windows=bool(np.any(z['ready']>0) or np.any(z['due'][1:]<32400))
 cp=use(x.classical_source,'A original classical route result');qp=use(x.quantum_source,'A original quantum result');q=json.loads(qp.read_text());available=q['final_feasible_count']>0;acq.append(available);ck('A raw acquisition matches policy',g.quantum_acquired.astype(str).eq(str(available)).all(),qp)
 saved.append(dict(series='A_OLD_TIME_WINDOWS',problem_id=pid,input_path=str(ip),input_sha256=hashlib.file_digest(ip.open('rb'),'sha256').hexdigest(),classical_source=str(cp),quantum_source=str(qp),quantum_acquired=available,has_nontrivial_time_windows=present_windows,policy_rows=len(g),policy_timing='hypothetical T_Q/T_C; not CPU measured'))
ck('A historical 78inputs/64 acquired/36 policies',len(saved)==78 and sum(acq)==64 and len(ops)==2808,ops_path)
pd.DataFrame(saved).to_csv(O/'evidence/A_ORIGINAL_SOURCE_LINKS.csv',index=False)
# Actual original initial route score and timers; input binding from already verified classical initial table.
base=pd.read_csv(P/'B_CLASSICAL_INITIAL_BASELINES.csv',keep_default_na=False,dtype=str)
for x in base.to_dict('records'):
 p=use(W/'RESULTS'/f"{x['problem_id']}.json",'original deterministic three-sweep classical initialization');d=json.loads(p.read_text());ck('B initial linked upstream route',d['route_indices']==json.loads(x['initial_route']) and d['instance_sha256']==x['input_sha256'],p)
 ck('B initial timing copied exactly',float(d['wall_seconds'])==float(x['wall_seconds']) and abs(float(d['cpu_seconds'])-float(x['CPU_seconds']))<1e-12,p)
for fam in ['mirror_family','grover_depth','active_adjacent_p3']:
 h=json.loads((S/fam/'SOURCE_HASHES.json').read_text())
 for n,sha in h.items():
  p=S/fam/'SOURCE_SNAPSHOT'/n
  if p.is_file():use(p,'frozen source identity');ck('B frozen execution snapshot hash',hashlib.file_digest(p.open('rb'),'sha256').hexdigest()==sha,p)
# Grid shape and endpoint finite-model summaries; no new inference.
sens=pd.read_csv(T/'PATH2_SENSITIVITY_SUMMARY.csv');full=pd.read_csv(T/'PATH2_SENSITIVITY_RESULTS.csv',usecols=['trajectory_sha256','rolling_case','q_Ah_kg']);ck('C49 q grid shape',len(full)==460*2*49 and full.q_Ah_kg.nunique()==49 and not full.duplicated().any(),T/'PATH2_SENSITIVITY_RESULTS.csv')
ratio=pd.read_csv(O/'evidence/C_ENDPOINT_RATIO_READBACK.csv')
for x in ratio.to_dict('records'):
 ep=sens[sens.rolling_case==x['rolling_case']].sort_values('q_Ah_kg').iloc[-1];ck('C old0.413 endpoint matches source energy sums',abs(ep.total_weighted_saving_percent-x['total_weighted_saving_percent'])<1e-10,T/'PATH2_SENSITIVITY_SUMMARY.csv',x['rolling_case'])
rt=pd.read_csv(O/'PATH1_RUNTIME_SCOPE_INVENTORY.csv',keep_default_na=False)
idx=rt.index[rt.column_or_pointer=='quantum_hardware_seconds']
for i in idx:rt.loc[i,'measurement_type']='NOT_EXECUTED bookkeeping zero; not measured QPU time';rt.loc[i,'execution_environment']='CPU simulator; QPU_execution=false';rt.loc[i,'comparison_control']='none; no QPU benchmark';rt.loc[i,'scope']='saved historical zero denotes no hardware execution; no QPU elapsed inference'
rt.to_csv(O/'PATH1_RUNTIME_SCOPE_INVENTORY.csv',index=False)
pd.DataFrame(prov).to_csv(O/'SOURCE_PROVENANCE.csv',index=False);pd.DataFrame(checks).to_csv(O/'evidence/HISTORY_CHECKS.csv',index=False)
sumry=dict(sources=len(prov),checks=len(checks),failures=sum(x['status']=='FAIL' for x in checks),A_inputs=len(saved),A_acquired=sum(acq),A_policy_rows=len(ops));(O/'evidence/HISTORY_SUMMARY.json').write_text(json.dumps(sumry,ensure_ascii=False,indent=2));print(json.dumps(sumry,indent=2));assert not any(x['status']=='FAIL' for x in checks)
