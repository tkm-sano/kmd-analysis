from pathlib import Path
from fractions import Fraction as F
import hashlib,json,collections,sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parents[1]; R=O.parents[1]
S2=R/'review_outputs/quantum_ev_step2_analysis_trial_20261104_155535'
S4=R/'review_outputs/quantum_ev_step4_thesis_integration_trial_20261104_184043'
P=R/'review_outputs/no_sumo_full_analysis_20261102/run01'
U=Path('/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs')
S=U/'staged_qaoa_validation_20261102';C=U/'cpu_matched_classical_swaps_r0_r5_20261101'
pins={};checks=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p,role,expected=None):
 p=Path(p)
 if not p.exists() and str(p).startswith(str(R/'review_outputs')):
  p=U/p.relative_to(R/'review_outputs')
 h=sha(p)
 if expected:assert h==expected,(p,h,expected)
 pins[str(p)]=dict(path=str(p),sha256=h,bytes=p.stat().st_size,role=role)
 return p

def ck(name,ok,detail=''):
 checks.append(dict(check=name,status='PASS' if ok else 'FAIL',detail=str(detail)))
 if not ok:raise AssertionError((name,detail))

def csv(p):return pd.read_csv(pin(p,'analysis input'),keep_default_na=False)
def js(p,role='saved record',expected=None):return json.loads(pin(p,role,expected).read_text())
plans=csv(P/'B_PLAN_REFERENCES_36800.csv'); paired=csv(S2/'PATH1_PAIRED_COMPARISONS.csv');aux=csv(P/'B_AUXILIARY_CLASSICAL_IMPROVEMENTS.csv')
paired=paired[paired.primary_comparison].copy()
ck('460x8x10 unique',len(plans)==36800 and not plans.duplicated(['problem_id','config_id','measurement_rep']).any())
ck('complete balanced cells',plans.groupby(['problem_id','config_id']).size().eq(10).all() and plans.groupby('problem_id').size().eq(80).all())
meta={x['run_id']:x for x in js(S/'mirror_family/MANIFEST.json')}
for p in [S/'mirror_family/PROTOCOL.json',S/'grover_depth/PROTOCOL.json',S/'active_adjacent_p3/PROTOCOL.json',C/'PROTOCOL.json',C/'SOURCE_SNAPSHOT/scripts/run_cpu_matched_classical_swaps.py',C/'SOURCE_SNAPSHOT/src/kmd_quantitative/routing/classical_swap_baselines.py']:
 pin(p,'frozen protocol or algorithm')
rawcache={};rows=[];inputs=[];greedys={};routecache={};
# Exact decimal rational arithmetic on the actual stored directed edges.
for pid,g in plans.groupby('problem_id',sort=True):
 m=meta[pid];a=dict(np.load(pin(m['instance_path'],'B NPZ',m['instance_sha256']),allow_pickle=False))
 n=len(a['nodes'])-1; assert np.all(a['ready']==0) and np.all(a['due']==32400)
 assert np.all(a['service'][1:]==102) and a['service'][0]==0
 gr=js(C/'RUNS'/pid/'ITERATED_GREEDY_ADJACENT_SWAP/RESULT.json','greedy saved selected route')
 assert gr['instance_sha256']==m['instance_sha256']
 edge={};cache={}
 def cost(route):
  route=tuple(route)
  if route not in cache:
   total=F(0)
   for i,j in zip(route,route[1:]):
    if (i,j) not in edge:edge[i,j]=F(str(a['travel'][i,j]))
    total+=edge[i,j]
   cache[route]=total
  return cache[route]
 def route_ok(route):return route[0]==route[-1]==0 and sorted(route[1:-1])==list(range(1,n+1))
 def last_time(route):return float(cost(route))-float(a['travel'][route[-2],0])+102*n
 def complete(route):
  t=0.;out={}
  for i,j in zip(route,route[1:]):
   t=max(t+float(a['travel'][i,j]),float(a['ready'][j]))+float(a['service'][j]);out[j]=t
  return out
 gj=cost(gr['route_indices']);greedys[pid]=gj;gc=complete(gr['route_indices']);retg=float(gj)+102*n
 ar=aux[(aux.problem_id==pid)&(aux.method=='ITERATED_GREEDY_ADJACENT_SWAP')].iloc[0]
 ck('greedy exact cost and input',route_ok(gr['route_indices']) and gj==F(ar.classical_best_seconds) and ar.input_sha256==m['instance_sha256'],pid)
 cap=int(a['demand'].sum());ck('greedy capacity and return feasible',cap<=216 and retg<=32400,pid)
 inputs.append(dict(problem_id=pid,input_path=str(pin(m['instance_path'],'B NPZ',m['instance_sha256'])),input_sha256=m['instance_sha256'],n_customers=n,demand_PE=cap,capacity_PE=216,service_per_customer_s=102,total_service_s=102*n,ready_s=0,common_horizon_s=32400,greedy_J_s=float(gj),greedy_return_s=retg,greedy_last_delivery_s=last_time(gr['route_indices']),greedy_return_slack_s=32400-retg,greedy_source=str(C/'RUNS'/pid/'ITERATED_GREEDY_ADJACENT_SWAP/RESULT.json'),greedy_seed=gr['seed'],greedy_evaluations=gr['details']['exact_delta_evaluations']))
 for x in g.to_dict('records'):
  src=x['source_path']
  if src not in rawcache:
   raw=js(src,'candidate CPU simulation measurements',x['source_sha256']);rawcache[src]={int(v['rep']):v for v in raw['records'] if v.get('mode','OPTIMIZED')=='OPTIMIZED'}
  rec=rawcache[src][int(x['measurement_rep'])];route=json.loads(x['route_indices']);j=cost(route);delta=j-gj
  ck('candidate raw route, rational cost, feasibility',route==rec['route_indices'] and j==F(x['objective_fraction'])==F(str(rec.get('sampled_best_seconds',rec.get('road_seconds')))) and route_ok(route) and float(j)+102*n<=32400 and cap<=216,pid+'|'+x['config_id']+'|'+str(x['measurement_rep']))
  cc=complete(route);diffs=[cc[k]-gc[k] for k in range(1,n+1)]
  rows.append({**{k:x[k] for k in ['problem_id','parent_id','group_id','scale','n_customers','input_sha256','config_id','family','measurement_rep','measurement_seed_entropy','fit_id','source_path','source_sha256','shots']},'generation':'CPU_SIMULATION_OF_QUANTUM_ALGORITHM','J_candidate_fraction':str(j),'J_greedy_fraction':str(gj),'delta_fraction':str(delta),'J_candidate_s':float(j),'J_greedy_s':float(gj),'delta_s':float(delta),'abs_delta_s':float(abs(delta)),'relative_gap_percent':float(100*delta/gj) if gj else np.nan,'classification':'improved' if delta<0 else 'equal' if delta==0 else 'worsened','feasible':True,'total_service_s':102*n,'candidate_return_s':float(j)+102*n,'greedy_return_s':retg,'return_difference_s':float(delta),'candidate_last_delivery_s':last_time(route),'greedy_last_delivery_s':last_time(gr['route_indices']),'last_delivery_difference_s':last_time(route)-last_time(gr['route_indices']),'candidate_return_slack_s':32400-float(j)-102*n,'greedy_return_slack_s':32400-retg,'customer_horizon_within_fraction_candidate':np.mean([cc[k]<=32400 for k in range(1,n+1)]),'customer_horizon_within_fraction_greedy':np.mean([gc[k]<=32400 for k in range(1,n+1)]),'mean_customer_completion_difference_s':np.mean(diffs),'min_customer_completion_difference_s':min(diffs),'max_customer_completion_difference_s':max(diffs),'strict_greedy_adoption_delta_s':float(min(j,gj)-gj),'initial_fallback_delta_s':float(min(j,F(x['classical_initial_fraction']))-gj),'actual_start_time_s':np.nan,'contractual_on_time_rate':np.nan})
 print(pid,flush=True) if pid.endswith('_078') or pid=='R5_070' else None
d=pd.DataFrame(rows)
old=paired.set_index(['problem_id','config_id','measurement_rep']);new=d.set_index(['problem_id','config_id','measurement_rep']);
ck('Step2 paired sign converted exactly',all(F(x.delta_fraction)==-F(old.loc[k,'delta_J_fraction']) for k,x in new.iterrows()))
ck('no zero greedy denominators',d.J_greedy_s.gt(0).all())
d.to_csv(O/'data/B_PLAN_GAPS_36800.csv',index=False);pd.DataFrame(inputs).to_csv(O/'data/B_INPUT_CONDITIONS_460.csv',index=False)
metrics=['delta_s','abs_delta_s','relative_gap_percent']
stats=[]
def stats_block(frame,level,keys):
 group=[((),frame)] if not keys else frame.groupby(keys,sort=True,dropna=False)
 for key,g in group:
  if not isinstance(key,tuple):key=(key,)
  ids=dict(zip(keys,key))
  for metric in metrics:
   a=g[metric].dropna();q=a.quantile([.05,.25,.5,.75,.95],interpolation='linear')
   stats.append(dict(level=level,**ids,metric=metric,n=len(a),mean=a.mean(),median=a.median(),sd=a.std(ddof=1),min=a.min(),max=a.max(),q1=q[.25],q3=q[.75],p05=q[.05],p95=q[.95],inputs=g.problem_id.nunique(),unit='percent' if metric=='relative_gap_percent' else 's'))
for level,keys in [('all_plans',[]),('by_input',['problem_id']),('by_config',['config_id']),('by_measurement_rep',['measurement_rep']),('by_input_config',['problem_id','config_id']),('by_scale_config',['scale','config_id'])]:stats_block(d,level,keys)
pd.DataFrame(stats).to_csv(O/'data/GAP_DESCRIPTIVE_STATISTICS.csv',index=False)
# Input-first descriptions: each input has the same 8x10 design; no statistical independence assumed.
ip=d.groupby(['problem_id','parent_id','group_id','scale'],as_index=False)[metrics+['J_candidate_s','J_greedy_s']].mean()
ic=d.groupby(['problem_id','parent_id','group_id','scale','config_id'],as_index=False)[metrics].mean()
ip.to_csv(O/'data/INPUT_MEANS_460.csv',index=False);ic.to_csv(O/'data/INPUT_CONFIG_MEANS_3680.csv',index=False)
stats=[]
for frame,level,keys in [(ip,'input_mean_all',[]),(ip,'input_mean_by_scale',['scale']),(ic,'input_mean_by_config',['config_id']),(ic,'input_mean_by_scale_config',['scale','config_id'])]:stats_block(frame,level,keys)
pd.DataFrame(stats).to_csv(O/'data/INPUT_UNIT_STATISTICS.csv',index=False)
counts=[]
for level,keys in [('all_plans',[]),('by_config',['config_id']),('by_input',['problem_id']),('by_rep',['measurement_rep']),('by_input_config',['problem_id','config_id'])]:
 for key,g in ([((),d)] if not keys else d.groupby(keys)):
  if not isinstance(key,tuple):key=(key,)
  for label in ['improved','equal','worsened']:counts.append(dict(level=level,**dict(zip(keys,key)),classification=label,count=int(g.classification.eq(label).sum()),percent=100*g.classification.eq(label).mean(),denominator=len(g)))
pd.DataFrame(counts).to_csv(O/'data/IMPROVED_EQUAL_WORSENED.csv',index=False)
# Fixed-cohort influence diagnostics, not resampling inference.
sort=ip.sort_values('delta_s',ascending=False);total=ip.delta_s.sum()
summary=dict(n_plans=len(d),n_inputs=len(ip),n_settings=d.config_id.nunique(),n_reps=d.measurement_rep.nunique(),n_groups=ip.group_id.nunique(),n_parents=ip.parent_id.nunique(),mean_delta_s=d.delta_s.mean(),median_delta_s=d.delta_s.median(),mean_absolute_delta_s=d.abs_delta_s.mean(),mean_relative_gap_percent=d.relative_gap_percent.mean(),ratio_of_means_percent=100*(d.J_candidate_s.mean()-d.J_greedy_s.mean())/d.J_greedy_s.mean(),greedy_mean_s=d.J_greedy_s.mean(),candidate_mean_s=d.J_candidate_s.mean(),max_input_contribution_percent=100*sort.iloc[0].delta_s/total,top5_input_contribution_percent=100*sort.head(5).delta_s.sum()/total,top23_input_contribution_percent=100*sort.head(23).delta_s.sum()/total,mean_without_top23_inputs_s=sort.iloc[23:].delta_s.mean(),leave_one_out_mean_min_s=(total-ip.delta_s.max())/(len(ip)-1),leave_one_out_mean_max_s=(total-ip.delta_s.min())/(len(ip)-1),improved=int(d.classification.eq('improved').sum()),equal=int(d.classification.eq('equal').sum()),worsened=int(d.classification.eq('worsened').sum()),input_mean_min_s=ip.delta_s.min(),input_mean_max_s=ip.delta_s.max(),last_completion_diff_negative_plans=int(d.last_delivery_difference_s.lt(-1e-9).sum()),min_return_slack_s=d.candidate_return_slack_s.min(),max_return_slack_s=d.candidate_return_slack_s.max(),min_greedy_slack_s=d.greedy_return_slack_s.min(),max_greedy_slack_s=d.greedy_return_slack_s.max(),seed_interpretation='rep index 0..9; entropy input/config-specific, not 10 shared global seeds')
(O/'data/SUMMARY.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False))
sort.assign(contribution_percent=100*sort.delta_s/total).to_csv(O/'data/INPUT_INFLUENCE.csv',index=False)
op=d.groupby('config_id').agg(n=('problem_id','size'),mean_return_difference_s=('return_difference_s','mean'),mean_last_delivery_difference_s=('last_delivery_difference_s','mean'),min_last_delivery_difference_s=('last_delivery_difference_s','min'),max_last_delivery_difference_s=('last_delivery_difference_s','max'),min_candidate_slack_s=('candidate_return_slack_s','min'),median_candidate_slack_s=('candidate_return_slack_s','median'),max_candidate_slack_s=('candidate_return_slack_s','max'),mean_customer_completion_difference_s=('mean_customer_completion_difference_s','mean'),within_common_horizon_candidate=('customer_horizon_within_fraction_candidate','mean'),within_common_horizon_greedy=('customer_horizon_within_fraction_greedy','mean')).reset_index();op.to_csv(O/'data/OPERATIONAL_SUMMARY.csv',index=False)
# Supplementary ratio of means by setting (not average relative gap).
ro=d.groupby('config_id')[['J_candidate_s','J_greedy_s','relative_gap_percent']].mean();ro['ratio_of_means_percent']=100*(ro.J_candidate_s-ro.J_greedy_s)/ro.J_greedy_s;ro.to_csv(O/'data/RELATIVE_GAP_VS_RATIO_OF_MEANS.csv')
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'savefig.dpi':300})
colors=plt.cm.tab10(np.arange(8));configs=sorted(d.config_id.unique());
def save(fig,name):
 fig.savefig(O/'figures'/f'{name}.png',bbox_inches='tight');fig.savefig(O/'figures'/f'{name}.pdf',bbox_inches='tight');plt.close(fig)
fig,ax=plt.subplots(figsize=(7.6,5.3))
for c,color in zip(configs,colors):
 h=d[d.config_id==c];ax.scatter(h.J_greedy_s,h.J_candidate_s,s=7,alpha=.3,label=c,color=color,rasterized=True)
m=max(d.J_candidate_s.max(),d.J_greedy_s.max());ax.plot([0,m],[0,m],color='black',lw=1,label='Equal objective');ax.set(xlabel='Greedy directed round-trip travel J (s)',ylabel='Candidate directed round-trip travel J (s)',title='B: 36,800 saved plans; paired by 460 inputs');ax.legend(fontsize=6,loc='upper left',ncol=2);fig.text(.5,.005,'8 settings x 10 measurement reps/input; descriptive points, dependent repeats; CPU simulations',ha='center',fontsize=7);save(fig,'F1_paired_objectives')
fig,axs=plt.subplots(1,2,figsize=(10,4.1))
for ax,col,label in zip(axs,['delta_s','relative_gap_percent'],['Candidate minus greedy (s)','Relative gap vs greedy (%)']):
 ax.hist(d[col],bins=50,color='#236785',alpha=.85);ax.axvline(0,color='black',lw=.7);ax.set(xlabel=label,ylabel='Saved plans (count)');ax.set_title(f'n = 36,800; median = {d[col].median():.3f}')
fig.suptitle('B: signed and relative gaps; all saved plans (dependent repetitions)');fig.tight_layout(rect=(0,.04,1,.94));fig.text(.5,.005,'Zero is equality; positive is worse. Histogram counts are descriptive, not independent sample sizes.',ha='center',fontsize=8);save(fig,'F2_gap_distributions')
fig,axs=plt.subplots(2,1,figsize=(9,7),sharex=True)
for ax,col,lab in zip(axs,metrics[::2],['Signed gap (s)','Relative gap (%)']):
 ax.boxplot([ic.loc[ic.config_id==c,col] for c in configs],tick_labels=configs,showfliers=True,flierprops={'markersize':2});ax.set_ylabel(lab);ax.axhline(0,color='black',lw=.7)
axs[1].tick_params(axis='x',rotation=28,labelsize=7);fig.suptitle('B: each box has 460 input means (10 reps/setting/input)');fig.tight_layout(rect=(0,.04,1,.95));fig.text(.5,.003,'Median / quartiles; whiskers 1.5 IQR; points beyond whiskers retained. Settings are paired, not randomized.',ha='center',fontsize=8);save(fig,'F3_setting_input_boxes')
fig,axs=plt.subplots(2,1,figsize=(9,6),sharex=True)
ordered=ip.sort_values('problem_id');x=np.arange(len(ordered));
for ax,col,lab in zip(axs,['delta_s','relative_gap_percent'],['Mean signed gap (s)','Mean relative gap (%)']):
 for sc,color in zip(sorted(ip.scale.unique()),plt.cm.Set2(np.arange(6))):
  mask=ordered.scale.eq(sc).to_numpy();ax.scatter(x[mask],ordered.loc[mask,col],s=11,label=sc,color=color)
 ax.set_ylabel(lab);ax.axhline(0,color='black',lw=.7)
axs[0].legend(ncol=6,fontsize=8);axs[1].set_xlabel('Input rank in problem_id order (460 inputs; each mean uses 8 settings x 10 reps)');fig.suptitle('B: input-level gaps vs greedy; fixed cohort, equal input weights');fig.tight_layout();save(fig,'F4_input_gaps')
# copy primary path2 evidence without rewriting Step4.
for name in ['DC_MASS_KERNEL_SUMMARY.csv','DC_MASS_KERNEL_INDEPENDENT.csv','PATH2_ANALYTICAL_SENSITIVITY.csv']:
 p=pin(S4/'data'/name,'Step4 adopted path2 evidence');(O/'data'/name).write_bytes(p.read_bytes())
for name in ['STEP4_EVIDENCE_DECISIONS.md','CLAIM_EVIDENCE_MATRIX.csv']:
 p=pin(R/'review_outputs/quantum_ev_step4_evidence_decisions_20261104_183654'/name,'scientific authority');(O/'evidence'/('STEP4_'+name if not name.startswith('STEP4_') else name)).write_bytes(p.read_bytes())
pd.DataFrame(pins.values()).to_csv(O/'evidence/ANALYSIS_INPUT_SHA256.csv',index=False);pd.DataFrame(checks).to_csv(O/'evidence/NUMERICAL_CHECKS.csv',index=False)
print(json.dumps(summary,ensure_ascii=False,indent=2))
