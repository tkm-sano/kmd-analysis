"""Independent read-only reanalysis; deterministic, all output under this trial."""
from pathlib import Path
import os,sys,csv,json,hashlib,datetime,time,platform,shutil,subprocess,resource
os.environ['PYTHONDONTWRITEBYTECODE']='1'
O=Path(__file__).resolve().parents[1];R=O.parents[1]
os.environ['MPLCONFIGDIR']=str(O/'logs/matplotlib')
sys.path.insert(0,str(R/'src'))
import numpy as np,pandas as pd
from fractions import Fraction
from docx import Document
from kmd_quantitative.energy.controlled_dc import evaluate
P=R/'review_outputs/no_sumo_full_analysis_20261102/run01'
U=Path('/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked')
B=Path('/home/takuma/kmd-analysis-preservation-20261014-173544-a64e484c/backup');L=B.parent/'relocated'
S=U/'review_outputs/staged_qaoa_validation_20261102';T8=U/'review_outputs/material_ev_stage2_20261026/run02';T9=U/'review_outputs/t09_open_data_model_20261029/run01'
SRC={};checks=[];start=time.monotonic()
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def use(p,expected=None):
 p=Path(p)
 if not p.is_file():
  old=p
  for root in [R,U,B,L]:
   if p.is_relative_to(root):
    for alt in [R,U,B,L]:
     q=alt/p.relative_to(root)
     if q.is_file():p=q;break
    if p.is_file():break
  if not p.is_file():raise FileNotFoundError(old)
 k=str(p)
 if k not in SRC:SRC[k]={'path':k,'sha256':sha(p),'bytes':p.stat().st_size,'mtime_utc':datetime.datetime.fromtimestamp(p.stat().st_mtime,datetime.timezone.utc).isoformat()}
 if expected is not None:ck('source_hash',SRC[k]['sha256']==expected,k)
 return p
def js(p):return json.loads(use(p).read_text())
def df(p):return pd.read_csv(use(p),keep_default_na=False,low_memory=False)
def write(n,x):
 p=O/n;p.parent.mkdir(exist_ok=True,parents=True)
 if isinstance(x,pd.DataFrame):x.to_csv(p,index=False)
 elif n.endswith('.json'):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,default=str,allow_nan=False)+'\n')
 else:p.write_text(x)
def table(n,x):write(n,pd.DataFrame(x))
def ck(name,ok,scope='',err=None):
 checks.append({'check':name,'status':'PASS' if bool(ok) else 'FAIL','scope':scope,'error':err})
 if not ok:raise AssertionError((name,scope,err))
def near(name,a,b,tol=1e-7,scope=''):ck(name,abs(float(Fraction(str(a)))-float(Fraction(str(b))))<=tol,scope,float(Fraction(str(a)))-float(Fraction(str(b))))
# Pin existing research and prior review products, without trusting prior conclusions.
for base in [P,R/'review_outputs/integrated_causal_audit_20261102/run01',R/'review_outputs/thesis_results_interpretation_20261102/run01',R/'review_outputs/thesis_docx_integration_20261103/run01']:
 for p in base.iterdir():
  if p.is_file():use(p)
for base in [R/'docs',R/'01_research_design',R/'src/kmd_quantitative',R/'02_literature']:
 for p in base.rglob('*'):
  if p.is_file() and p.suffix in ['.md','.json','.py','.csv','.bib'] and '__pycache__' not in p.parts:use(p)
for p in [R/'README.md',T8/'SCENARIOS.json',T8/'SENSITIVITY_INPUTS.json',T8/'T08.json',T9/'model.py',T9/'CELL_MASS_ACCOUNTING_MODEL.md',T9/'ELECTRODE_GEOMETRY_MODEL.md',T9/'PARAMETER_SOURCES.csv',T9/'VERIFICATION_REPORT.md',R/'review_outputs/poster_policy_revision_20261104/run02/01_POLICY_AND_SCOPE.txt']:use(p)
for p in R.glob('*.docx'):
 use(p);shutil.copyfile(p,O/'sources'/p.name)
 doc=Document(p);write('sources/'+p.stem+'_TEXT.md','\n'.join(f'{i}\t{x.style.name}\t{x.text}' for i,x in enumerate(doc.paragraphs)))
# Source discovery inventory, not just timestamps.
inv=[]
for base in [R/'docs',R/'01_research_design',R/'review_outputs',R/'02_literature',R/'src']:
 for root,dirs,files in os.walk(base):
  dirs[:]=[d for d in dirs if d not in ['rendering_tools','tools','__pycache__','.git'] and Path(root)/d!=O and not d.startswith('render')]
  for n in files:
   p=Path(root)/n
   inv.append({'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'mtime_utc':datetime.datetime.fromtimestamp(p.stat().st_mtime,datetime.timezone.utc).isoformat(),'type':p.suffix})
table('SOURCE_DISCOVERY_INVENTORY.csv',inv)
# B: independently recompute travel objective from raw NPZ, sampling records, and certificates.
plans=df(P/'B_PLAN_REFERENCES_36800.csv');fits=df(P/'B_RESOURCES_PER_FIT.csv');cov=df(P/'B_EXACT_REFERENCE_COVERAGE.csv');base=df(P/'B_CLASSICAL_INITIAL_BASELINES.csv')
meta={x['run_id']:x for x in js(S/'mirror_family/MANIFEST.json')};arrays={};raw={};records={}
for rid in sorted(plans.problem_id.unique()):
 m=meta[rid];p=use(m['instance_path'],m['instance_sha256'])
 with np.load(p,allow_pickle=False) as z:arrays[rid]={k:z[k].copy() for k in z.files}
for x in cov.to_dict('records'):use(x['certificate_path'],x['certificate_sha256'])
for row in plans.to_dict('records'):
 key=row['source_path']
 if key not in raw:
  d=js(use(key,row['source_sha256']));raw[key]=d;records[key]={int(v['rep']):v for v in d['records'] if v.get('mode','OPTIMIZED')=='OPTIMIZED'}
 rec=records[key][int(row['measurement_rep'])];rt=json.loads(row['route_indices']);a=arrays[row['problem_id']]
 ck('B saved route identity',rt==rec['route_indices'],row['problem_id'])
 ck('B route permutation',rt[0]==rt[-1]==0 and sorted(rt[1:-1])==list(range(1,len(a['travel']))),row['problem_id'])
 cost=sum((Fraction(str(a['travel'][i,j])) for i,j in zip(rt,rt[1:])),Fraction(0))
 near('B raw NPZ cost',row['objective_s'],cost,scope=row['problem_id'])
 near('B raw measurement cost',cost,rec.get('sampled_best_seconds',rec.get('road_seconds')),scope=row['problem_id'])
 near('B delta initial',row['delta_objective_vs_initial_s'],float(cost)-float(row['classical_initial_s']),scope=row['problem_id'])
 ck('B feasibility',sum(a['demand'])<=216 and float(cost)+102*int(row['n_customers'])<=32400,row['problem_id'])
 if row['exact_optimum_s']!='':near('B gap arithmetic',row['global_gap_percent'],100*(float(cost)-float(row['exact_optimum_s']))/float(row['exact_optimum_s']),scope=row['problem_id'])
 else:ck('B missing gap retained',row['global_gap_percent']=='' and row['optimal_match']=='',row['problem_id'])
for x in fits.to_dict('records'):use(x['fit_source_path'],x['fit_source_sha256'])
ck('B references',len(plans)==36800);ck('B inputs',len(arrays)==460);ck('B unique fits',fits.fit_id.nunique()==3680)
q=[]
for (sc,cfg),g in plans.groupby(['scale','config_id'],sort=True):
 per=[]
 for rid,h in g.groupby('problem_id'):
  vals=h.objective_s.astype(float).to_numpy();ex=h.exact_optimum_s.iloc[0];ci=float(h.classical_initial_s.iloc[0]);refs=len(h)
  per.append({'problem_id':rid,'mean':float(vals.mean()),'sd':(0.0 if np.all(vals==vals[0]) else float(vals.std(ddof=1))),'gap':np.mean(h.global_gap_percent.astype(float)) if ex!='' else None,'match':np.mean(h.optimal_match.astype(str)=='True') if ex!='' else None,'delta':float(h.delta_objective_vs_initial_s.astype(float).mean()),'improve':np.mean(h.improves_initial.astype(str)=='True'),'worsen':np.mean(h.worsens_initial.astype(str)=='True')})
 a=pd.DataFrame(per);n=int(g.n_customers.iloc[0]);row={'series':'B_NO_CUSTOMER_WINDOWS','scale':sc,'n_customers':n,'config_id':cfg,'physical_inputs':len(a),'measurement_reps_per_input':10,'plan_references':len(g),'exact_inputs':int(a.gap.notna().sum()),'exact_missing_inputs':int(a.gap.isna().sum()),'mean_OD_travel_s':a['mean'].mean(),'mean_delta_vs_initial_s':a.delta.mean(),'mean_global_gap_percent':a.gap.mean(),'optimal_match_percent':100*a['match'].mean(),'improve_initial_percent':100*a.improve.mean(),'worsen_initial_percent':100*a.worsen.mean(),'mean_within_input_sd_s':a.sd.mean(),'max_within_input_sd_s':a.sd.max(),'feasible_plan_percent':100*np.mean(g.feasible.astype(str)=='True'),'status':'CONDITIONAL_FIXED_OD_CPU_SIMULATIONS'}
 q.append(row)
quality=pd.DataFrame(q);write('PATH1_QUALITY_COMPARISON.csv',quality)
old=df(P/'B_SUMMARY_BY_SCALE_AND_METHOD.csv')
for row in quality.to_dict('records'):
 z=old[(old.scale==row['scale'])&(old.config_id==row['config_id'])].iloc[0]
 for new,prior in [('mean_OD_travel_s','mean_objective_s'),('mean_delta_vs_initial_s','mean_delta_objective_s'),('mean_global_gap_percent','mean_global_gap_percent'),('optimal_match_percent','optimal_match_percent')]:near('B old aggregate verification '+new,row[new],z[prior],1e-6,sc+cfg)
# Runtime records: unique fits; no pooling across measurement scopes.
runtime=[]
for (sc,cfg,scope),g in fits.groupby(['scale','config_id','resource_scope']):
 for col in ['fit_wall_s','fit_CPU_s']:
  v=pd.to_numeric(g[col],errors='coerce').dropna();runtime.append({'series':'B','scale':sc,'config_id':cfg,'component':col,'scope':scope,'unit':'s','records':len(v),'mean_s':v.mean(),'median_s':v.median(),'min_s':v.min(),'max_s':v.max(),'measurement_type':'SAVED_CPU_SIMULATOR','direct_speedup_comparable':False})
for sc,g in base.groupby('scale'):
 for col in ['wall_seconds','CPU_seconds']:
  v=g[col].astype(float);runtime.append({'series':'B','scale':sc,'config_id':'CLASSICAL_INITIAL_CONSTRUCTION','component':col,'scope':'INITIAL_ONLY_NOT_MATCHED_TOTAL_BUDGET','unit':'s','records':len(v),'mean_s':v.mean(),'median_s':v.median(),'min_s':v.min(),'max_s':v.max(),'measurement_type':'SAVED_CPU_CLASSICAL','direct_speedup_comparable':False})
reslong=df(P/'B_SAVED_RESOURCES_LONG.csv')
for (sc,cfg,scope,field),g in reslong.groupby(['scale','config_id','scope','resource_field']):
 if scope not in ['FINAL_VALIDATION','SELECTED_STATE'] or 'seconds' not in field:continue
 v=g.value.astype(float);runtime.append({'series':'B','scale':sc,'config_id':cfg,'component':field,'scope':scope,'unit':'s','records':len(v),'mean_s':v.mean(),'median_s':v.median(),'min_s':v.min(),'max_s':v.max(),'measurement_type':'SAVED_CPU_SIMULATOR','direct_speedup_comparable':False})
write('PATH1_RUNTIME_COMPARISON.csv',pd.DataFrame(runtime))
# Pair-level and pooled input-first data, kept as supplemental finite cohort description.
write('PATH1_INPUT_SEED_STATISTICS.csv',plans.groupby(['problem_id','scale','config_id']).agg(n=('objective_s','size'),mean_objective_s=('objective_s','mean'),sd_objective_s=('objective_s',lambda x: 0.0 if x.nunique()==1 else x.std(ddof=1)),min_objective_s=('objective_s','min'),max_objective_s=('objective_s','max')).reset_index())
# Current no-window B and old window A kept separate. Legacy indicators never promoted.
for name in ['A_POLICY_DECISIONS_2808.csv','A_CLASSICAL_BASELINE_2808.csv','A_RAW_COMPUTATION_RESOURCES_78.csv','B_ACTIVE_GRID_SELECTION.csv','C_BOUNDARY_SIGN_VALIDATION.csv']:use(P/name)
# C original T08 mass budget using exact decimal-rational order.
scenarios=js(T8/'SCENARIOS.json')['scenarios'];p0={k:v['value'] for k,v in scenarios[0]['parameters'].items()};p1={k:v['value'] for k,v in scenarios[1]['parameters'].items()}
def mass(q,u=1,V=3.5,delta=0):
 Q=20000/V;pos=Q/q/u/.75;neg=Q*1.1/360/.98;cell=(pos+neg)/100+.19
 return cell,100*cell+15+delta
cellLP,mLP=mass(p0['q_ref']);cellS,mS=mass(p1['q_ref']);b08=mLP-mS
energy=df(P/'C_T08_ENERGY_FULL.csv');t9=df(P/'C_T09_COMPONENTS_183.csv');bridge=df(P/'C_BRIDGE_MASS_DC_FULL.csv')
for row in energy.to_dict('records'):
 p=next(s for s in scenarios if s['scenario_id']==row['scenario_id'])['parameters'];near('T08 mass arithmetic',row['pack_mass_kg'],mass(p['q_ref']['value'])[1],1e-8)
for row in t9.to_dict('records'):
 parts=['positive_coating_kg','negative_coating_kg','Al_mass_kg','Cu_mass_kg','separator_dry_mass_kg','liquid_mass_kg'];near('T09 known component sum',row['known_cell_components_sum_kg'],sum(float(row[k]) for k in parts),1e-8,row['condition_id']);ck('T09 complete mass null',row['complete_pack_mass_kg']=='',row['condition_id'])
ck('T09 physical failure retained',sum(t9.overlap_condition=='FAIL_IF_SAME_STACK_FOOTPRINT')==1)
for row in bridge.to_dict('records'):
 near('T09 bridge net mass',row['net_mass_saving_probe_kg'],float(row['known_mass_boundary_kg'])-float(row['unknown_mass_difference_probe_kg']),1e-8)
 near('T09 decomposition W1-W4 plus branch',row['DC_saving_Wh'],sum(float(row[k]) for k in ['W1_baseline_mask_DC_saving_Wh','W2_baseline_mask_DC_saving_Wh','W3_baseline_mask_DC_saving_Wh','W4_baseline_mask_DC_saving_Wh','branch_correction_Wh']),1e-7)
# Continuous q in closed interval of preserved T08 inputs; u or delta equivalent paths.
freeze=js(R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json')
for path in [R/'src/kmd_quantitative/energy/controlled_dc.py',R/'src/kmd_quantitative/energy/frozen_sources/run_full_controlled_dc.py']:use(path)
reference=energy[(energy.dataset=='CLASSICAL')&(energy.scenario_id=='COND_LP_REF')];ck('C classical reference rows',len(reference)==920)
qs=np.linspace(p0['q_ref'],p1['q_ref'],49);masses=np.array([mass(q)[1] for q in qs]);observations=[];sens=[];ops=[];cache={};maxerr=0.;maxscalar=0.;compact={};gridE={};decomp=[]
# Classifying positive branches over [mS,mLP] is algebraically exact; no trajectory regeneration.
for i,(h,rr) in enumerate(reference.groupby('trajectory_sha256'),1):
 row=rr.iloc[0];path=use(row.trajectory_path,h);traj=pd.read_csv(path,usecols=['timestamp_s','speed_m_s']);t=traj.timestamp_s.to_numpy();v=traj.speed_m_s.to_numpy();ck('C saved trajectory samples',np.all(np.diff(t)==1) and np.all(v>=0),h)
 cur=v[1:];dv=cur**2-v[:-1]**2;ds=cur;nonpack=float(row.running_mass_kg)-mLP
 near('common nonpack running mass',nonpack,1043.888888888889,1e-7)
 for rc,pressure in [('CRR_LOWER_BOUND',4.5),('CRR_UPPER_BOUND',2.6)]:
  mn=nonpack+mS;mx=nonpack+mLP;crr=.005+(.01+.0095*(3.6*cur/100)**2)/pressure
  a=(freeze['g']['value']*crr*ds+.5*dv)/3600
  b=(.5*61*dv+.5*freeze['rho']['value']*freeze['CdA']['value']*cur**2*ds)/3600
  lo=a*mn+b;hi=a*mx+b;always=(lo>0)&(hi>0);switch=(lo>0) != (hi>0)
  ca=float(np.sum(a[always]));cb=float(np.sum(b[always]));sa=a[switch].copy();sb=b[switch].copy();eta=freeze['eta_prop']
  def fun(m):return float((ca*m+cb+np.maximum(sa*m+sb,0).sum())/eta)
  compact[(h,rc)]=(ca,cb,sa,sb,nonpack)
  eLP=fun(mx);eS=fun(mn);es=np.array([fun(nonpack+m) for m in masses]);gridE[(h,rc)]=es
  rLP,zLP=evaluate(t,v,freeze,pressure,{'running_mass_kg':mx});rS,zS=evaluate(t,v,freeze,pressure,{'running_mass_kg':mn})
  near('C compact kernel baseline',eLP,rLP['net_DC_Wh']);near('C compact kernel alternate',eS,rS['net_DC_Wh']);maxerr=max(maxerr,abs(eLP-rLP['net_DC_Wh']),abs(eS-rS['net_DC_Wh']))
  srcrow=rr[rr.rolling_case==rc].iloc[0];near('C preserved T08 DC',srcrow.net_DC_Wh,eLP)
  savedS=energy[(energy.trajectory_sha256==h)&(energy.rolling_case==rc)&(energy.scenario_id=='COND_S200_REF')].iloc[0];near('C preserved T08 S DC',savedS.net_DC_Wh,eS)
  # Independent scalar kernel on first trajectory, both endpoints/cases.
  if i==1:
   for m,e in [(mx,eLP),(mn,eS)]:
    import math
    ee=math.fsum(max(math.fsum([m*9.80665*(.005+(.01+.0095*(3.6*float(v[j])/100)**2)/pressure)*float(v[j]),.5*m*(float(v[j])**2-float(v[j-1])**2),.5*61*(float(v[j])**2-float(v[j-1])**2),.5*1.2041*1.175*float(v[j])**3])/3600,0)/.9 for j in range(1,len(v)))
    near('C independent scalar',ee,e);maxscalar=max(maxscalar,abs(ee-e))
  # Convex sum of hinges: derivative nondecreasing, so minimal one-sided slope at lower endpoint.
  dslope=(ca+np.sum(sa[sa*mn+sb>0]))/eta;ck('positive DC mass slope on scanned interval',dslope>0,h)
  mask=zLP['wheel']>0;parts={k:float(np.sum((zLP[k]-zS[k])[mask]))/eta for k in ['roll','aero','translational','rotational']};corr=(eLP-eS)-sum(parts.values())
  near('C W1 physical replacement',(mx-mn)*9.80665*np.sum(crr*ds)/3600,rLP['rolling_Wh']-rS['rolling_Wh'])
  ops.append({'trajectory_sha256':h,'scale':row.scale_id,'rolling_case':rc,'distance_km':float(np.sum(ds))/1000,'restart_count':int(np.count_nonzero((v[:-1]<=1e-9)&(v[1:]>1e-9))),'moving_mean_speed_m_s':float(np.mean(v[v>0])),'positive_dv2_sum':float(np.sum(np.maximum(dv,0))),'LP_DC_Wh':eLP,'S_DC_Wh':eS,'saving_Wh':eLP-eS,'saving_percent':100*(eLP-eS)/eLP,'W1_mask_DC_Wh':parts['roll'],'W2_mask_DC_Wh':parts['aero'],'W3_mask_DC_Wh':parts['translational'],'W4_mask_DC_Wh':parts['rotational'],'branch_correction_Wh':corr,'branch_switch_count':int(np.count_nonzero((zLP['wheel']>0)!=(zS['wheel']>0))),'min_mass_slope_Wh_kg':dslope,'status':'CONDITIONAL_FIXED_OBSERVED_WINDOW'})
  for j,qv in enumerate(qs):
   cell,pack=mass(qv);sens.append({'trajectory_sha256':h,'physical_instance_id':row.physical_instance_id,'parent_id':row.parent_id,'group_id':row.group_id,'scale':row.scale_id,'rolling_case':rc,'q_Ah_kg':qv,'utilization':1.,'voltage_V':3.5,'additional_mass_kg':0.,'cell_mass_kg':cell,'simplified_pack_mass_kg':pack,'vehicle_mass_kg':nonpack-55+pack,'running_mass_kg':nonpack+pack,'DC_Wh':es[j],'baseline_DC_Wh':eLP,'saving_Wh':eLP-es[j],'saving_percent':100*(eLP-es[j])/eLP,'status':'CONDITIONAL_T08_INTERPOLATION_NOT_QUANTUM_ACHIEVEMENT'})
 if i%100==0:print('C continuous readback',i,'/460',flush=True)
write('PATH2_SENSITIVITY_RESULTS.csv',pd.DataFrame(sens));write('PATH2_OPERATION_INTERACTIONS.csv',pd.DataFrame(ops))
summary=[]
for rc in ['CRR_LOWER_BOUND','CRR_UPPER_BOUND']:
 ee=np.array([v for (h,c),v in gridE.items() if c==rc]);baseSum=float(ee[:,0].sum())
 for j,qv in enumerate(qs):summary.append({'rolling_case':rc,'q_Ah_kg':qv,'trajectories':460,'DC_sum_Wh':float(ee[:,j].sum()),'baseline_sum_Wh':baseSum,'saving_sum_Wh':baseSum-float(ee[:,j].sum()),'total_weighted_saving_percent':100*(baseSum-float(ee[:,j].sum()))/baseSum,'mean_individual_saving_percent':float(np.mean(100*(ee[:,0]-ee[:,j])/ee[:,0])),'cell_mass_kg':mass(qv)[0],'simplified_pack_mass_kg':mass(qv)[1],'status':'CONDITIONAL_FIXED_COHORT'})
write('PATH2_SENSITIVITY_SUMMARY.csv',pd.DataFrame(summary))
bounds=[{'boundary':'T08 zero mass / same V components','input_variable':'utilization_at_qS','value':p0['q_ref']/p1['q_ref'],'unit':'fraction','condition':'qS*u > qLP; equal common V, N/P and fixed masses','kind':'ZERO_EFFECT_NOT_TARGET','status':'CONDITIONAL'}, {'boundary':'T08 zero mass / qS u1','input_variable':'additional_mass_S_minus_LP','value':b08,'unit':'kg','condition':'additional mass < value for positive saving','kind':'ZERO_EFFECT_NOT_TARGET','status':'CONDITIONAL'}, {'boundary':'T08 zero mass / qS u1','input_variable':'mean_full_cell_voltage','value':3.5*((20000/3.5/p1['q_ref']/.75+20000/3.5*1.1/360/.98)/(mLP-34)),'unit':'V','condition':'other mass34kg; changing V also changes negative active mass','kind':'ZERO_EFFECT_NOT_TARGET','status':'CONDITIONAL'}]
for pair,g in bridge.groupby('pair_id'):
 vals=g.known_mass_boundary_kg.astype(float);near('T09 boundary constant within pair',vals.min(),vals.max(),1e-8)
 bounds.append({'boundary':pair+' known mass cancellation','input_variable':'unknown_S_minus_LP','value':float(vals.iloc[0]),'unit':'kg','condition':'delta < b, =b, >b gives mass saving, equality, reversal; complete pack unknown','kind':'ZERO_EFFECT_NOT_TARGET','status':'CONDITIONAL'})
# Arbitrary illustrative targets, selected before threshold evaluation, NOT research success criteria.
for rc in ['CRR_LOWER_BOUND','CRR_UPPER_BOUND']:
 cc=[v for (h,c),v in compact.items() if c==rc]
 def total_at(q):
  mm=mass(q)[1];return sum((ca*(nonpack+mm)+cb+np.maximum(sa*(nonpack+mm)+sb,0).sum())/.9 for ca,cb,sa,sb,nonpack in cc)
 E0=total_at(qs[0]);maxsave=100*(E0-total_at(qs[-1]))/E0
 for target in [.1,.25,.4,.5]:
  if target>maxsave:
   bounds.append({'boundary':'T08 '+rc,'input_variable':'q_for_'+str(target)+'pct_DC_target','value':None,'unit':'Ah/kg','condition':'Target exceeds endpoint reduction; no extrapolation','kind':'ARBITRARY_ILLUSTRATIVE_TARGET','status':'HOLD_OUTSIDE_ANALYZED_RANGE'});continue
  low,high=qs[0],qs[-1]
  for _ in range(48):
   mid=(low+high)/2
   if 100*(E0-total_at(mid))/E0<target:low=mid
   else:high=mid
  qstar=(low+high)/2
  bounds.append({'boundary':'T08 '+rc,'input_variable':'q_for_'+str(target)+'pct_DC_target','value':qstar,'unit':'Ah/kg','condition':'u=1,V=3.5,common components; 460-trajectory total-weighted target; deterministic bisection','kind':'ARBITRARY_ILLUSTRATIVE_TARGET','status':'CONDITIONAL'})
write('PATH2_BOUNDARY_RESULTS.csv',pd.DataFrame(bounds))
# Equivalent continuous utilization path; computes masses anew and reads the same exact DC functional.
urows=[]
for uv in np.linspace(p0['q_ref']/p1['q_ref'],1,49):
 for rc in ['CRR_LOWER_BOUND','CRR_UPPER_BOUND']:
  mm=mass(p1['q_ref'],uv)[1];cc=[v for (h,c),v in compact.items() if c==rc];ee=sum((ca*(nonpack+mm)+cb+np.maximum(sa*(nonpack+mm)+sb,0).sum())/.9 for ca,cb,sa,sb,nonpack in cc)
  urows.append({'q_Ah_kg':p1['q_ref'],'utilization':uv,'voltage_V':3.5,'rolling_case':rc,'pack_mass_kg':mm,'cell_mass_kg':mass(p1['q_ref'],uv)[0],'DC_sum_Wh':ee,'status':'CONDITIONAL_WITHIN_QEFF_ENDPOINTS'})
write('PATH2_UTILIZATION_CONTINUOUS.csv',pd.DataFrame(urows))
# Figures use standalone PNG+PDF and data are the exported CSVs.
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
for d in ['PATH1_FIGURES','PATH2_FIGURES']:(O/d).mkdir(exist_ok=True)
fig,ax=plt.subplots(figsize=(8,4.5))
for cfg in ['MEAN_P2','GROVER_P2','GROVER_P3','ACTIVE_ADJACENT_P3_GRID']:
 z=quality[quality.config_id==cfg];ax.plot(z.n_customers,z.mean_global_gap_percent,'o-',label=cfg)
ax.set(xlabel='Customers (B; no customer time windows)',ylabel='Mean optimality gap (%)',title='Saved exact references: 78/78/78/78/57/38 inputs');ax.legend(fontsize=8);fig.tight_layout()
for ext in ['png','pdf']:fig.savefig(O/f'PATH1_FIGURES/F1_quality.{ext}',dpi=160)
plt.close(fig)
fig,ax=plt.subplots(figsize=(8,4.5))
for cfg in ['MEAN_P2','GROVER_P2','GROVER_P3']:
 z=quality[quality.config_id==cfg];ax.plot(z.n_customers,z.mean_delta_vs_initial_s,'o-',label=cfg)
ax.axhline(0,color='grey',lw=1);ax.set(xlabel='Customers',ylabel='Sampled minus classical initial (s)',title='Input-first means; CPU simulations, finite cohort');ax.legend();fig.tight_layout()
for ext in ['png','pdf']:fig.savefig(O/f'PATH1_FIGURES/F2_initial_delta.{ext}',dpi=160)
plt.close(fig)
summ=pd.DataFrame(summary);fig,ax=plt.subplots(figsize=(8,4.5))
for rc,g in summ.groupby('rolling_case'):ax.plot(g.q_Ah_kg,g.total_weighted_saving_percent,label=rc)
ax.set(xlabel='Conditional cathode reference capacity (Ah/kg)',ylabel='Total-weighted Controlled-DC saving (%)',title='T08 interpolation; u=1, V=3.5; 460 fixed observed trajectories');ax.legend();fig.tight_layout()
for ext in ['png','pdf']:fig.savefig(O/f'PATH2_FIGURES/F3_continuous_q.{ext}',dpi=160)
plt.close(fig)
fig,ax=plt.subplots(figsize=(8,4.5))
for name,bv in [('T08 simplified',b08),('T09 B015',9.722608121107783),('T09 B051',5.977891152)]:
 xx=np.linspace(0,10,100);ax.plot(xx,bv-xx,label=name)
ax.axhline(0,color='grey',lw=1);ax.set(xlabel='Additional / unknown S minus LP mass (kg)',ylabel='Net mass saving (kg)',title='Separate design boundaries; not completed-pack comparison');ax.legend();fig.tight_layout()
for ext in ['png','pdf']:fig.savefig(O/f'PATH2_FIGURES/F4_cancellation.{ext}',dpi=160)
plt.close(fig)
write('NUMERICAL_CHECKS.csv',pd.DataFrame(checks));table('SOURCE_BASELINE.csv',list(SRC.values()))
write('ANALYSIS_RUN.json',{'status':'PASS_ARITHMETIC_CONDITIONAL_INTERPRETATION','wall_s':time.monotonic()-start,'CPU_s':resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime,'peak_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'python':sys.version,'platform':platform.platform(),'numpy':np.__version__,'pandas':pd.__version__,'checks':len(checks),'failures':sum(x['status']=='FAIL' for x in checks),'source_count':len(SRC),'B_refs':len(plans),'B_inputs':len(arrays),'C_trajectories':460,'C_sensitivity_rows':len(sens),'compact_vs_kernel_max_Wh':maxerr,'independent_scalar_max_Wh':maxscalar,'q_grid_points':49,'randomness':'NONE; deterministic saved-data arithmetic','new_QAOA':0,'new_SUMO':0,'mass_LP_kg':mLP,'mass_S_kg':mS,'T08_mass_saving_kg':b08})
print(json.dumps(json.loads((O/'ANALYSIS_RUN.json').read_text()),ensure_ascii=False,indent=2))
