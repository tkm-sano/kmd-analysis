from pathlib import Path
import os,sys,csv,json,hashlib,time,itertools,math,collections,shutil
from fractions import Fraction as F
for name in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[name]='1'
O=Path(__file__).resolve().parents[1];R=O.parents[1];S2=R/'review_outputs/quantum_ev_step2_analysis_trial_20261104_155535';S1=R/'review_outputs/quantum_ev_step1_design_trial_20261104_153058';P=R/'review_outputs/no_sumo_full_analysis_20261102/run01';U=Path('/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked');T8=U/'review_outputs/material_ev_stage2_20261026/run02';T9=U/'review_outputs/t09_open_data_model_20261029/run01';S=U/'review_outputs/staged_qaoa_validation_20261102'
import numpy as np,pandas as pd
sources={};checks=[];t0=time.perf_counter()
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,role='保存証拠',expected=None):
 p=Path(p)
 if not p.is_file():
  roots=[R,U,Path('/home/takuma/kmd-analysis-preservation-20261014-173544-a64e484c/backup'),Path('/home/takuma/kmd-analysis-preservation-20261014-173544-a64e484c/relocated')]
  old=p
  for src in roots:
   if old.is_relative_to(src):
    for dest in roots:
     q=dest/old.relative_to(src)
     if q.is_file():p=q;break
    if p.is_file():break
 if not p.is_file():raise FileNotFoundError(p)
 k=str(p.resolve())
 if k not in sources:sources[k]=dict(path=k,sha256=sha(p),bytes=p.stat().st_size,role=role,adoptable_result='ファイル同一性・定義・算術の確認',conditional_result='シミュレーション／固定モデルの解釈',HOLD='実運用・量子実機・完成品への一般化は別判定')
 if expected is not None:ck('input SHA',sources[k]['sha256']==expected,k)
 return p
def frame(p):return pd.read_csv(pin(p),keep_default_na=False,low_memory=False)
def js(p):return json.loads(pin(p).read_text())
def ck(name,ok,scope='',error=''):
 checks.append(dict(check=name,status='PASS' if bool(ok) else 'FAIL',scope=scope,error=error))
 if not ok:raise AssertionError((name,scope,error))
def near(name,a,b,tol=1e-7,scope=''):ck(name,abs(float(a)-float(b))<=tol,scope,float(a)-float(b))
def out(name,rows):pd.DataFrame(rows).to_csv(O/name,index=False)
def objective(a,route):return sum((F(str(a['travel'][i,j])) for i,j in zip(route,route[1:])),F(0))
# Input inventory is saved before numeric checks; existing outputs are pinned at their final hashes.
for base,role in [(S1,'Step1設計・指標と主対照'),(S2,'Step2確定成果・一次出力')]:
 for p in sorted(base.rglob('*')):
  if p.is_file() and not any(x in p.parts for x in ['__pycache__','matplotlib']):pin(p,role)
for p in [R/'tmp_RsrchMstrDc_1026_results_integrated.docx',R/'tmp_RsrchMstrDc_1026_revised.docx',R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json',R/'src/kmd_quantitative/energy/frozen_sources/run_full_controlled_dc.py',R/'src/kmd_quantitative/energy/controlled_dc.py',T8/'SCENARIOS.json',T8/'T08.json',T8/'MATERIAL_ENERGY.csv',T9/'model.py',T9/'PACK_20KWH_SENSITIVITY.csv',T9/'PARAMETER_SOURCES.csv']:pin(p,'原稿または凍結材料・物理仕様')
out('INPUT_FILE_LEDGER.csv',list(sources.values()))
manifest=frame(S2/'OUTPUT_SHA256_MANIFEST.csv')
for row in manifest.to_dict('records'):
 p=pin(S2/row['path']);ck('Step2 final manifest',sha(p)==row['sha256'],str(p))
# Original input and source measurement binding for all primary B rows.
paired=frame(S2/'PATH1_PAIRED_COMPARISONS.csv');rawplans=frame(P/'B_PLAN_REFERENCES_36800.csv');summary=frame(S2/'PATH1_STATISTICAL_RESULTS.csv');unc=frame(S2/'PATH1_UNCERTAINTY_INTERVALS.csv');refs=frame(S2/'EXACT_REFERENCE_STATUS.csv');meta={m['run_id']:m for m in js(S/'mirror_family/MANIFEST.json')};arrays={};raw={};rrmap={}
for pid in rawplans.problem_id.unique():
 m=meta[pid];p=pin(m['instance_path'],'B原NPZ',m['instance_sha256'])
 with np.load(p,allow_pickle=False) as z:arrays[pid]={k:z[k].copy() for k in z.files}
for row in rawplans.to_dict('records'):
 p=row['source_path']
 if p not in raw:
  d=js(pin(p,'原量子保存測定',row['source_sha256']));raw[p]={int(x['rep']):x for x in d['records'] if x.get('mode','OPTIMIZED')=='OPTIMIZED'}
 rt=json.loads(row['route_indices']);q=raw[p][int(row['measurement_rep'])];cost=objective(arrays[row['problem_id']],rt)
 ck('B NPZ and saved measurement',rt==q['route_indices'] and cost==F(row['objective_fraction'])==F(str(q.get('sampled_best_seconds',q.get('road_seconds')))),row['problem_id']);rrmap[(row['problem_id'],row['config_id'],int(row['measurement_rep']))]=cost
aux=frame(P/'B_AUXILIARY_CLASSICAL_IMPROVEMENTS.csv');jc={(r['problem_id'],r['method']):F(r['classical_best_seconds']) for r in aux.to_dict('records')}
for row in paired.to_dict('records'):
 cost=rrmap[(row['problem_id'],row['config_id'],int(row['measurement_rep']))];cl=jc[(row['problem_id'],row['classical_method'])];dj=cl-cost
 ck('B paired exact delta',cost==F(row['JQ_fraction']) and cl==F(row['JC_fraction']) and dj==F(row['delta_J_fraction']),row['problem_id']);near('B paired float delta',dj,row['delta_J_s']);ck('B improvement flag',(dj>0)==bool(row['improves']))
primary=paired[paired.primary_comparison==True];ck('B primary367? count',len(primary)==36800);ck('B 460 inputs',primary.problem_id.nunique()==460);ck('B all best feasible',primary.feasible.all());ck('B zero primary improvement',sum(primary.improves)==0)
per=primary.groupby(['problem_id','scale','config_id','group_id']).delta_J_s.mean().reset_index();r5=per[(per.scale=='R5')&(per.config_id=='GROVER_P2')];target=summary[(summary.scale=='R5')&(summary.config_id=='GROVER_P2')&(summary.primary_comparison==True)].iloc[0]
near('R5 mean',r5.delta_J_s.mean(),target.input_mean_delta_J_mean,1e-8);near('R5 input SD',r5.delta_J_s.std(ddof=1),target.input_mean_delta_J_sd,1e-8)
# Recreate group sensitivity from the prescribed RNG without a new experiment.
groups=sorted(primary.group_id.unique());weights=np.random.default_rng(20261102).multinomial(25,np.full(25,1/25),size=10000);num=np.array([r5[r5.group_id==g].delta_J_s.sum() for g in groups]);den=np.array([sum(r5.group_id==g) for g in groups]);boot=(weights@num)/(weights@den);interval=unc[(unc.scale=='R5')&(unc.config_id=='GROVER_P2')&(unc.classical_method=='ITERATED_GREEDY_ADJACENT_SWAP')&(unc.metric=='mean_delta_J_s')&unc.kind.str.startswith('GROUP')].iloc[0]
near('R5 group lower',np.quantile(boot,.025),interval.lower95,1e-8);near('R5 group upper',np.quantile(boot,.975),interval.upper95,1e-8)
# Distinct evidence strengths and 7 additions; no solver launch.
counts=refs.reference_evidence_class.value_counts().to_dict();ck('exact reference evidence classes',counts=={'RECHECKED_ENUMERATION':234,'SAVED_EXACT_INTEGER_HELD_KARP_DP':78,'INDEPENDENT_RATIONAL_DUAL':61,'UNPROVED_VALID_BOUNDS':46,'SAVED_EXACT_MIP_EQUALITY_NO_EXTERNAL_VIPR':41});ck('accepted references414',sum(refs.accepted_exact_available==True)==414)
new=refs[(refs.accepted_exact_available==True)&(refs.old_exact_available==False)];ck('7 added reference proofs',len(new)==7)
for row in new.to_dict('records'):
 cert=js(row['exact_source']);ck('new exact certificate equality',F(cert['certified_lower_fraction'])==F(cert['feasible_upper_fraction'])==F(row['exact_fraction']),row['problem_id'])
missingold=refs[refs.old_exact_available==False];ck('old53 optimal not timeout',len(missingold)==53 and all(missingold.scip_status_optimal.astype(str).str.lower()=='true') and not any(missingold.time_limit_reached.astype(str).str.lower()=='true'))
# Controlled raw measurements and histogram minima; independent of fit summary flags.
fits=frame(S2/'experiments/QAOA_MAIN_FITS.csv');measure=frame(S2/'experiments/QAOA_MAIN_MEASUREMENTS.csv');public=frame(S2/'QAOA_CONTROLLED_EXPERIMENT_RESULTS.csv');cells=frame(S2/'QAOA_CONTROLLED_CELL_SUMMARY.csv');base=frame(P/'B_CLASSICAL_INITIAL_BASELINES.csv');initial={r['problem_id']:tuple(json.loads(r['initial_route'])[1:-1]) for r in base.to_dict('records')};support={}
for pid in measure.problem_id.unique():
 n=len(initial[pid]);full=list(itertools.permutations(range(1,n+1)));mirror=[]
 for bits in itertools.product([0,1],repeat=n//2):
  rt=list(initial[pid])
  for j,bit in enumerate(bits):
   if bit:rt[j],rt[-1-j]=rt[-1-j],rt[j]
  mirror.append(tuple(rt))
 for typ,states in [('FULL_PERMUTATION',full),('MIRROR_ORBIT',sorted(mirror))]:support[(pid,typ)]=(states,[objective(arrays[pid],[0,*rt,0]) for rt in states])
ck('controlled9312fit',len(fits)==9312);ck('controlled93120measure',len(measure)==93120);histfile=pin(S2/'experiments/QAOA_MAIN_SHOT_COUNTS.npz');hist=np.load(histfile);mrows=measure.to_dict('records')
for i,row in enumerate(fits.to_dict('records')):
 states,cost=support[(row['problem_id'],row['support'])];h=hist[f'f{i:05d}'];ck('controlled histogram shape/shots',h.shape==(10,len(states)) and np.all(h.sum(axis=1)==8192),str(i))
 for rep in range(10):
  rr=mrows[10*i+rep];chosen=min(np.flatnonzero(h[rep]>0),key=lambda j:cost[j]);v=cost[chosen];route=[0,*states[chosen],0];ck('controlled histogram best fraction and route',v==F(rr['objective_fraction']) and route==json.loads(rr['route']),str(i));ck('controlled optimal flag',(v==min(support[(row['problem_id'],'FULL_PERMUTATION')][1]))==rr['optimal_match'])
# Wilson recomputed directly from raw rep0.
ctrl=[]
for layer in [1,2]:
 g=measure[(measure.problem_id=='R1_020')&(measure.support=='FULL_PERMUTATION')&(measure.initial_state=='BASIS_INITIAL')&(measure.mixer=='GRAPH_SWAP')&(measure.layers==layer)&(measure.method=='QAOA')&(measure.measurement_rep==0)];k=int(g.optimal_match.sum());n=len(g);z=1.959963984540054;ph=k/n;center=(ph+z*z/(2*n))/(1+z*z/n);half=z*math.sqrt(ph*(1-ph)/n+z*z/(4*n*n))/(1+z*z/n);a=cells[(cells.problem_id=='R1_020')&(cells.support=='FULL_PERMUTATION')&(cells.initial_state=='BASIS_INITIAL')&(cells.mixer=='GRAPH_SWAP')&(cells.layers==layer)&(cells.method=='QAOA')].iloc[0];near('controlled Wilson lower',center-half,a.primary_optimal_Wilson95_lower,1e-12);near('controlled Wilson upper',center+half,a.primary_optimal_Wilson95_upper,1e-12);ck('controlled stated k',k==(58 if layer==1 else 78));ctrl.append(dict(layers=layer,successes=k,fits=n,rate=ph,lower=center-half,upper=center+half))
# Timing is read from raw pipeline; do not measure anything anew.
rt=frame(S2/'PATH1_RUNTIME_RESULTS.csv');ck('runtime9603',len(rt)==9603);cfg='FULL_PERMUTATION/UNIFORM_SUPPORT/PROJECTOR/p2';tim=[]
for method in ['QAOA','DEPHASED']:
 g=rt[(rt.problem_id=='R1_001')&(rt.config_id==cfg)&(rt.method==method)];ck('fixed runtime97',len(g)==97);tim.append(dict(problem_id='R1_001',config_id=cfg,method=method,n=97,median_wall_ms=g.total_wall_s.median()*1000,median_CPU_ms=g.total_CPU_s.median()*1000))
# C summary recomputed from all saved parameter rows; thresholds from source budget.
cs=frame(S2/'PATH2_SENSITIVITY_RESULTS.csv');csummary=frame(S2/'PATH2_SENSITIVITY_SUMMARY.csv');ck('C rows132480',len(cs)==132480)
end=cs[(cs.model=='T08')&(cs.case_id=='Q48')];ce=[]
for rc,g in end.groupby('rolling_case'):
 s=csummary[(csummary.case_id=='Q48')&(csummary.rolling_case==rc)].iloc[0];total=100*g.delta_DC_Wh.sum()/g.baseline_DC_Wh.sum();mean=g.individual_saving_percent.mean();sd=g.individual_saving_percent.std(ddof=1);near('C total ratio',total,s.total_weighted_saving_percent,1e-9);near('C individual mean',mean,s.mean_individual_saving_percent,1e-9);near('C individual sample SD',sd,s.sd_individual_saving_percent,1e-9);ce.append(dict(rolling_case=rc,trajectories=len(g),total_weighted_percent=total,mean_percent=mean,sd_percentage_points=sd,saving_Wh=g.delta_DC_Wh.sum()))
for row in cs[cs.axis=='additional_mass'].to_dict('records'):
 b=float(row['baseline_pack_or_probe_kg'])-(float(row['alternate_pack_or_probe_kg'])-float(row['additional_or_unknown_delta_kg']));near('C mass delta identity',row['delta_mass_kg'],b-float(row['additional_or_unknown_delta_kg']),1e-8)
# Exact decimal T08 boundaries in independent rational order.
sc=js(T8/'SCENARIOS.json')['scenarios'];a={k:F(str(v['value'])) for k,v in sc[0]['parameters'].items()};b={k:F(str(v['value'])) for k,v in sc[1]['parameters'].items()};mass=lambda x:x['gross_energy']/x['voltage']*(1/(x['q_ref']*x['utilization']*x['f_positive'])+x['np_ratio']/(x['q_negative']*x['f_negative']))+100*x['cell_other_mass']+x['pack_other_mass']+x['additional_mass'];massb=mass(a)-mass(b);ustar=a['q_ref']/b['q_ref'];vstar=b['gross_energy']*(1/(b['q_ref']*b['f_positive'])+b['np_ratio']/(b['q_negative']*b['f_negative']))/(mass(a)-34)
t9=frame(T9/'PACK_20KWH_SENSITIVITY.csv');ck('T09 all complete pack null',len(t9)==183 and all(t9.complete_pack_mass_kg==''))
# Derived manuscript-ready tables retain source identities.
out('tables/CONTROLLED_VERIFIED.csv',ctrl);out('tables/RUNTIME_FIXED_EXAMPLE.csv',tim);out('tables/C_DC_VERIFIED.csv',ce);out('tables/EXACT_STRENGTH_COUNTS.csv',[dict(evidence_class=k,inputs=v) for k,v in counts.items()]);out('tables/PRIMARY_QUALITY_SUMMARY.csv',summary[(summary.primary_comparison==True)&(summary.scale!='ALL')]);out('INPUT_FILE_LEDGER.csv',list(sources.values()));out('NUMERICAL_AUDIT_CHECKS.csv',checks)
result=dict(checks=len(checks),failures=sum(x['status']=='FAIL' for x in checks),wall_s=time.perf_counter()-t0,B_primary_rows=len(primary),B_primary_improvements=int(sum(primary.improves)),R5_Grover_p2_mean_DeltaJ_s=r5.delta_J_s.mean(),R5_Grover_p2_input_SD_s=r5.delta_J_s.std(ddof=1),R5_group_lower=np.quantile(boot,.025),R5_group_upper=np.quantile(boot,.975),reference_classes=counts,new7=new.problem_id.tolist(),controlled_fits=len(fits),controlled_measurements=len(measure),runtime_records=len(rt),timing_fixed_example=tim,T08_mass_boundary_kg=float(massb),T08_utilization_boundary=float(ustar),T08_voltage_boundary_V=float(vstar),C_endpoint=ce,new_scientific_experiments=0,source_count=len(sources))
(O/'NUMERICAL_AUDIT_RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False,indent=2))
