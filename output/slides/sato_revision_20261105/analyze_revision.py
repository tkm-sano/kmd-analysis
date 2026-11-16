"""Read-only evidence audit and new descriptive summaries for the Sato consultation."""
from pathlib import Path
from fractions import Fraction
import os,sys,json,hashlib,csv
sys.dont_write_bytecode=True
os.environ['OPENBLAS_NUM_THREADS']='1'
import numpy as np
import pandas as pd

O=Path(__file__).resolve().parent
R=O.parents[2]
sys.path.insert(0,str(R/'src'))
from kmd_quantitative.energy.controlled_dc import evaluate, scalar_check, EXPECTED_SHA256
S5=R/'review_outputs/quantum_ev_step5_20261105'
S4=R/'review_outputs/quantum_ev_step4_evidence_decisions_20261104_183654'
S3=R/'review_outputs/quantum_ev_thesis_step3_integration_20261104_173959'
S2=R/'review_outputs/quantum_ev_step2_analysis_trial_20261104_155535'
T=R/'review_outputs/t08_t09_final_adoption_20261105'
I=R/'review_outputs/t08_t09_interaction_boundaries_20261105/run01'
for d in ['data','evidence','render','reports']: (O/d).mkdir(exist_ok=True)
pins={};checks=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pin(p):
 p=Path(p).resolve()
 if str(p) not in pins:pins[str(p)]={'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
 return p
def read(p,**kw):return pd.read_csv(pin(p),**kw)
def ck(name,v,detail=''):
 checks.append(dict(check=name,status='PASS' if bool(v) else 'FAIL',detail=str(detail)))
 assert v,(name,detail)
def dump(name,obj):
 (O/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')

# Record reviewed decisions without changing any source artifact.
for p in [R/'研究紹介_佐野巧馬.pptx', R/'output/slides/研究紹介_佐野巧馬_詳細説明15枚.pptx',R/'output/slides/研究紹介_佐野巧馬_詳細説明15枚.pdf',
 S3/'EXECUTIVE_SUMMARY.md',S3/'ADOPTION_REVIEW.md',S3/'CLAIM_EVIDENCE_LEDGER.csv',S4/'STEP4_EVIDENCE_DECISIONS.md',S4/'CLAIM_EVIDENCE_MATRIX.csv',
 S5/'THESIS_FULL_TEXT.md',S5/'STEP5_ACADEMIC_CONTRIBUTIONS.md',S5/'STEP5_PATHWAY1_CONDITIONS.md',S5/'STEP5_OPERATIONAL_IMPACT.md',S5/'STEP5_PATHWAY2_EVIDENCE.md',S5/'STEP5_CLAIM_EVIDENCE_AUDIT.md',S5/'evidence/CLAIM_EVIDENCE_MAP.csv',
 T/'FINAL_REPORT_JA.md',T/'data/PARAMETER_ADOPTION.csv',T/'data/BOUNDARIES.csv',I/'FINAL_REPORT_JA.md',I/'scripts/analyze.py',
 R/'docs/research/RESEARCH_DESIGN_SUMMARY.md',R/'src/kmd_quantitative/energy/controlled_dc.py',R/'src/kmd_quantitative/energy/frozen_sources/run_full_controlled_dc.py']:
 pin(p)

b=read(S5/'data/B_PLAN_GAPS_36800.csv',low_memory=False)
conditions=read(S5/'data/B_INPUT_CONDITIONS_460.csv')
published=read(S5/'data/GAP_DESCRIPTIVE_STATISTICS.csv')
published_input=read(S5/'data/INPUT_UNIT_STATISTICS.csv')
pub_summary=json.loads(pin(S5/'data/SUMMARY.json').read_text())
ck('B 460 inputs 8 configs 10 measurements',len(b)==36800 and b.problem_id.nunique()==460 and b.config_id.nunique()==8 and b.groupby(['problem_id','config_id']).size().eq(10).all())
ck('B all 36800 fraction differences exact',all(Fraction(x.J_candidate_fraction)-Fraction(x.J_greedy_fraction)==Fraction(x.delta_fraction) for x in b.itertuples()))
ck('B all saved plans feasible',b.feasible.all())
ck('B return difference equals objective difference',np.max(abs(b.return_difference_s-b.delta_s))<1e-7)
ck('B last-customer vs return separated',b.last_delivery_difference_s.lt(-1e-9).sum()==180)
ck('B horizon service origin capacity',conditions.common_horizon_s.eq(32400).all() and conditions.service_per_customer_s.eq(102).all() and conditions.ready_s.eq(0).all() and conditions.capacity_PE.eq(216).all())
def stats(v):
 a=np.asarray(v,dtype=float)
 return dict(n=len(a),mean=float(a.mean()),median=float(np.median(a)),sd=float(a.std(ddof=1)),min=float(a.min()),max=float(a.max()),q25=float(np.quantile(a,.25)),q75=float(np.quantile(a,.75)))
bstat=stats(b.delta_s)
for col in ['mean','median','sd','min','max']:
 expected=float(published[(published.level=='all_plans')&(published.metric=='delta_s')].iloc[0][col]);ck('B published '+col,abs(bstat[col]-expected)<1e-8)
ic=b.groupby(['problem_id','scale','config_id'],as_index=False).delta_s.mean()
ip=b.groupby('problem_id').delta_s.mean()
scale=[]
for (sc,c),g in ic.groupby(['scale','config_id']):
 ss=stats(g.delta_s);scale.append(dict(scale=sc,n_customers=int(b.loc[b.scale==sc,'n_customers'].iloc[0]),config_id=c,**ss))
pd.DataFrame(scale).to_csv(O/'data/B_scale_setting_statistics.csv',index=False)
setstat=b.groupby('config_id').delta_s.agg(['mean','median','min','max','std']).reset_index()
setstat.to_csv(O/'data/B_setting_statistics.csv',index=False)
support=read(S2/'PATH1_SUPPORT_AUDIT.csv')
ck('matching support minimum equals initial all 460',len(support)==460 and all(Fraction(x.exact_matching_orbit_fraction)==Fraction(x.initial_fraction) for x in support.itertuples()))
bresult=dict(all_outputs=bstat,input_means=stats(ip),counts={k:int((b.classification==k).sum()) for k in ['improved','equal','worsened']},groups=int(b.group_id.nunique()),parents=int(b.parent_id.nunique()),min_return_slack_s=float(b.candidate_return_slack_s.min()),last_delivery_earlier_count=int(b.last_delivery_difference_s.lt(-1e-9).sum()),scale_settings=scale,settings=setstat.to_dict('records'))
dump('data/B_summary.json',bresult)

freeze=json.loads(pin(R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json').read_text())
ck('frozen model unchanged',sha(R/'src/kmd_quantitative/energy/frozen_sources/run_full_controlled_dc.py')==EXPECTED_SHA256)
k=read(S5/'data/DC_MASS_KERNEL_INDEPENDENT.csv')
oldmetrics=read(I/'data/TRAJECTORY_METRICS.csv').set_index('trajectory_sha256')
ck('C 460 trajectories paired in two rolling cases',len(k)==920 and k.trajectory_sha256.nunique()==460 and k.groupby('trajectory_sha256').size().eq(2).all())
rows=[]
for ni,(h,g) in enumerate(k.groupby('trajectory_sha256',sort=True)):
 path=pin(g.iloc[0].trajectory_path);ck('C trajectory sha '+h,sha(path)==h)
 df=pd.read_csv(path,usecols=['timestamp_s','speed_m_s']);t=df.timestamp_s.to_numpy();v=df.speed_m_s.to_numpy();dt=np.diff(t);cur=v[1:];dv2=cur**2-v[:-1]**2;ds=cur*dt
 ck('C native one-second sampling '+h,np.all(dt==1) and np.isfinite(v).all() and np.all(v>=0))
 moving=cur>.1;stop=v<=.1
 metrics=dict(trajectory_sha256=h,distance_km=float(ds.sum()/1000),observed_duration_s=float(t[-1]-t[0]),moving_duration_s=float(dt[moving].sum()),stop_fraction=float(stop.mean()),restarts=int(np.count_nonzero(stop[:-1]&~stop[1:])),positive_dv2=float(np.maximum(dv2,0).sum()),rms_acceleration=float(np.sqrt(np.mean((np.diff(v)/dt)**2))),group_id=str(oldmetrics.loc[h,'group_id']),parent_id=str(oldmetrics.loc[h,'parent_id']))
 ck('C stored distance and stop metrics '+h,abs(metrics['distance_km']-oldmetrics.loc[h,'distance_km'])<1e-7 and abs(metrics['stop_fraction']-oldmetrics.loc[h,'stop_fraction'])<1e-10)
 for rc,pressure in [('CRR_LOWER_BOUND',4.5),('CRR_UPPER_BOUND',2.6)]:
  lo,a=evaluate(t,v,freeze,pressure,{'running_mass_kg':1000})
  mid,_=evaluate(t,v,freeze,pressure,{'running_mass_kg':1100})
  hi,_=evaluate(t,v,freeze,pressure,{'running_mass_kg':1250})
  ref=g[g.rolling_case==rc].iloc[0]
  ck('C adopted endpoints reproduced '+h+rc,max(abs(lo['net_DC_Wh']-ref.DC_lo_Wh),abs(hi['net_DC_Wh']-ref.DC_hi_Wh))<1e-7)
  if ni in [0,230,459]:scalar_check(t,v,freeze,pressure,{'running_mass_kg':1100},mid)
  # Components are signed works on the positive TOTAL-wheel-work mask, divided by eta.
  # This sums exactly to DC. It is a bookkeeping convention, not identified causal shares.
  mask=a['wheel']>0
  parts={name+'_positive_mask_DC_Wh':float(a[key][mask].sum()/.9) for name,key in [('rolling','roll'),('aero','aero'),('translation','translational'),('rotation','rotational')]}
  ck('C positive-mask component identity '+h+rc,abs(sum(parts.values())-lo['net_DC_Wh'])<1e-7)
  row=dict(**metrics,rolling_case=rc,p_bar=pressure,mass_baseline_kg=1000,mass_changed_kg=1100,DC_1000_Wh=lo['net_DC_Wh'],DC_1100_Wh=mid['net_DC_Wh'],DC_1250_Wh=hi['net_DC_Wh'],delta_100kg_Wh=mid['net_DC_Wh']-lo['net_DC_Wh'],delta_100kg_percent=100*(mid['net_DC_Wh']-lo['net_DC_Wh'])/lo['net_DC_Wh'],dE_dm_1000_Wh_kg=float(ref.right_derivative_lo_Wh_kg),negative_wheel_work_magnitude_Wh=lo['wheel_negative_Wh'],**parts)
  rows.append(row)
 if ni%100==0:print('C reviewed',ni+1,'/ 460',flush=True)
c=pd.DataFrame(rows);c.to_csv(O/'data/C_trajectory_model_results.csv',index=False)
cresult={};corr=[]
for rc,g in c.groupby('rolling_case'):
 cresult[rc]={name:stats(g[name]) for name in ['DC_1000_Wh','distance_km','moving_duration_s','observed_duration_s','stop_fraction','restarts','positive_dv2','delta_100kg_Wh','delta_100kg_percent','dE_dm_1000_Wh_kg']}
 parts=[x for x in c if x.endswith('positive_mask_DC_Wh')]
 cresult[rc]['component_sum_share_percent']={x:float(100*g[x].sum()/g.DC_1000_Wh.sum()) for x in parts}
 for factor in ['distance_km','moving_duration_s','observed_duration_s','stop_fraction','restarts','positive_dv2','rms_acceleration']:
  val=float(g[[factor,'DC_1000_Wh']].rank().corr().iloc[0,1]);corr.append(dict(rolling_case=rc,factor=factor,outcome='DC_1000_Wh',spearman=val,interpretation='fixed-cohort descriptive; no independence or causal inference'))
pair=c.pivot(index='trajectory_sha256',columns='rolling_case',values='DC_1000_Wh')
delta=pair.CRR_UPPER_BOUND-pair.CRR_LOWER_BOUND
cresult['Crr_paired_absolute_Wh']=stats(delta)
cresult['Crr_paired_relative_percent']=stats(100*delta/pair.CRR_LOWER_BOUND)
cresult['correlations']=corr
cresult['interpretation']='NEW_DESCRIPTIVE_REANALYSIS_ADOPTED_FROZEN_MODEL; no new SUMO or material experiment; observed windows; independent samples not assumed'
dump('data/C_summary.json',cresult)
pd.DataFrame(corr).to_csv(O/'data/C_descriptive_correlations.csv',index=False)

# Explicit provenance for any material-specific illustration; never promote to main effect.
bound=read(T/'data/BOUNDARIES.csv');bound.to_csv(O/'data/material_reference_boundaries.csv',index=False)
read(S5/'data/PATH2_ANALYTICAL_SENSITIVITY.csv').to_csv(O/'data/adopted_analytical_sensitivity.csv',index=False)
pd.DataFrame(checks).to_csv(O/'evidence/numerical_checks.csv',index=False)
pd.DataFrame(pins.values()).to_csv(O/'evidence/source_manifest.csv',index=False)
pres=[dict(path=p,unchanged=sha(p)==v['sha256']) for p,v in pins.items()]
pd.DataFrame(pres).to_csv(O/'evidence/source_preservation.csv',index=False)
ck('all read sources preserved',all(x['unchanged'] for x in pres))
dump('evidence/analysis_audit.json',dict(checks=len(checks),failures=0,sources=len(pins),B=bresult['all_outputs'],C=cresult,source_files_unchanged=True,new_analysis='descriptive aggregation and frozen DC evaluation at 1000,1100,1250kg only'))
print(json.dumps(dict(B=bstat,C=cresult,checks=len(checks),sources=len(pins)),ensure_ascii=False,indent=2))
