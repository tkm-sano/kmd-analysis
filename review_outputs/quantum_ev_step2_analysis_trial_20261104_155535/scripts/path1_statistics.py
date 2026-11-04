from common import *
from scipy.stats import norm

def wilson(k,n):
 if n==0:return None,None
 z=1.959963984540054;p=k/n;den=1+z*z/n;mid=(p+z*z/(2*n))/den;h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den;return max(0.,mid-h),min(1.,mid+h)
def descr(a,prefix):
 a=np.asarray(a,float);a=a[np.isfinite(a)]
 if not len(a):return {prefix+k:None for k in ['mean','median','sd','q25','q75','iqr','min','max']}
 q=np.quantile(a,[.25,.75],method='linear');return dict(zip([prefix+k for k in ['mean','median','sd','q25','q75','iqr','min','max']],[float(a.mean()),float(np.median(a)),float(a.std(ddof=1)) if len(a)>1 else None,float(q[0]),float(q[1]),float(q[1]-q[0]),float(a.min()),float(a.max())]))

def main():
 t=time.perf_counter();plans=frame(P/'B_PLAN_REFERENCES_36800.csv',dtype=str);aux=frame(P/'B_AUXILIARY_CLASSICAL_IMPROVEMENTS.csv',dtype=str);refs=frame(O/'EXACT_REFERENCE_STATUS.csv',dtype=str);ref={x['problem_id']:x for x in refs.to_dict('records')};am={(x['problem_id'],x['method']):x for x in aux.to_dict('records')};meta={x['run_id']:x for x in js(S/'mirror_family/MANIFEST.json')};raw={};arrays={};rows=[]
 ck('B36800 unique PK',len(plans)==36800 and not plans.duplicated(['problem_id','config_id','measurement_rep']).any())
 for pid in plans.problem_id.unique():
  m=meta[pid];arrays[pid]=arr(pin(m['instance_path'],'B original NPZ',m['instance_sha256']))
 for x in plans.to_dict('records'):
  pid=x['problem_id'];rid=int(x['measurement_rep']);source=x['source_path']
  if source not in raw:
   d=js(pin(source,'B original measurement',x['source_sha256']));raw[source]={int(v['rep']):v for v in d['records'] if v.get('mode','OPTIMIZED')=='OPTIMIZED'}
  rec=raw[source][rid];route=json.loads(x['route_indices']);cost=objective(arrays[pid],route);ck('B raw route and score match',route==rec['route_indices'] and cost==F(x['objective_fraction'])==F(str(rec.get('sampled_best_seconds',rec.get('road_seconds')))),source)
  ok=feasible(arrays[pid],route);ck('B saved selected plan feasible',ok,pid);oldex=F(x['exact_optimum_fraction']) if x['exact_optimum_fraction'] else None;ex=F(ref[pid]['exact_fraction']) if ref[pid]['exact_fraction'] else None
  for method in ['ITERATED_GREEDY_ADJACENT_SWAP','DEPHASED_RANDOM_SWAP']:
   a=am[(pid,method)];jc=F(a['classical_best_seconds']);initial=F(x['classical_initial_fraction']);delta=jc-cost;adopt=min(initial,cost)
   rows.append(dict(problem_id=pid,input_sha256=x['input_sha256'],parent_id=x['parent_id'],group_id=x['group_id'],scale=x['scale'],n_customers=int(x['n_customers']),config_id=x['config_id'],family=x['family'],fit_id=x['fit_id'],measurement_rep=rid,measurement_seed_entropy=x['measurement_seed_entropy'],classical_method=method,primary_comparison=method=='ITERATED_GREEDY_ADJACENT_SWAP',JQ_fraction=str(cost),JC_fraction=str(jc),initial_fraction=str(initial),JQ_s=float(cost),JC_s=float(jc),delta_J_fraction=str(delta),delta_J_s=float(delta),relative_improvement_percent=100*float(delta/jc),delta_initial_s=float(initial-cost),adopted_delta_J_s=float(jc-adopt),acquired=True,feasible=ok,improves=delta>0,equal=delta==0,worsens=delta<0,exact_available=ex is not None,exact_fraction=str(ex) if ex is not None else '',optimal_match=cost==ex if ex is not None else None,quantum_gap_percent=100*float((cost-ex)/ex) if ex is not None else None,classical_gap_percent=100*float((jc-ex)/ex) if ex is not None else None,legacy_exact_available=oldex is not None,legacy_quantum_gap_percent=100*float((cost-oldex)/oldex) if oldex is not None else None,legacy_optimal_match=cost==oldex if oldex is not None else None,raw_invalid_samples=x['raw_invalid_samples'],raw_source=source))
 paired=pd.DataFrame(rows);table('PATH1_PAIRED_COMPARISONS.csv',paired);inputs=[];success=[]
 for (pid,cfg,method),g in paired.groupby(['problem_id','config_id','classical_method'],sort=True):
  x=g.iloc[0];k=int(g.improves.sum());lo,hi=wilson(k,len(g));row={k:x[k] for k in ['problem_id','input_sha256','parent_id','group_id','scale','n_customers','config_id','family','classical_method','primary_comparison','JC_s','exact_available']};row.update(measurement_reps=len(g),mean_JQ_s=g.JQ_s.mean(),median_JQ_s=g.JQ_s.median(),within_measurement_sd_s=0. if g.JQ_fraction.nunique()==1 else g.JQ_s.std(ddof=1),within_measurement_iqr_s=g.JQ_s.quantile(.75)-g.JQ_s.quantile(.25),mean_delta_J_s=g.delta_J_s.mean(),median_delta_J_s=g.delta_J_s.median(),mean_relative_improvement_percent=g.relative_improvement_percent.mean(),mean_delta_initial_s=g.delta_initial_s.mean(),mean_adopted_delta_J_s=g.adopted_delta_J_s.mean(),improve_fraction=k/len(g),feasible_fraction=g.feasible.mean(),exact_gap_percent=g.quantum_gap_percent.mean() if bool(x.exact_available) else None,optimal_match_fraction=g.optimal_match.mean() if bool(x.exact_available) else None,mean_classical_gap_percent=g.classical_gap_percent.mean() if bool(x.exact_available) else None,any_improvement=k>0);inputs.append(row)
  success.append({**{k:x[k] for k in ['problem_id','scale','config_id','classical_method','fit_id']},'measurement_reps':len(g),'improving_reps':k,'improve_rate':k/len(g),'Wilson95_lower':lo,'Wilson95_upper':hi,'feasible_reps':int(g.feasible.sum()),'raw_invalid_saved_reps':int(g.raw_invalid_samples.ne('').sum()),'interval_scope':'10 independent measurement streams conditional on fixed input and learned fit; not learning stability'})
 ip=pd.DataFrame(inputs);table('PATH1_INPUT_CONFIG_STATISTICS.csv',ip);table('PATH1_SUCCESS_RATE_ANALYSIS.csv',success)
 summaries=[];unc=[];groups=sorted(ip.group_id.unique());gi={g:i for i,g in enumerate(groups)};weights=np.random.default_rng(20261102).multinomial(len(groups),np.full(len(groups),1/len(groups)),size=10000);configs=sorted(ip.config_id.unique())
 for scale in sorted(ip.scale.unique())+['ALL']:
  for cfg in configs:
   for method in ['ITERATED_GREEDY_ADJACENT_SWAP','DEPHASED_RANDOM_SWAP']:
    h=ip[(ip.config_id==cfg)&(ip.classical_method==method)&((ip.scale==scale) if scale!='ALL' else True)];g=paired[(paired.config_id==cfg)&(paired.classical_method==method)&((paired.scale==scale) if scale!='ALL' else True)];ex=g[g.exact_available];row=dict(scale=scale,config_id=cfg,classical_method=method,primary_comparison=method=='ITERATED_GREEDY_ADJACENT_SWAP',physical_inputs=len(h),groups=h.group_id.nunique(),parents=h.parent_id.nunique(),scheduled_measurement_reps=10*len(h),valid_reps=len(g),acquired_reps=int(g.acquired.sum()),feasible_reps=int(g.feasible.sum()),feasible_percent=100*g.feasible.mean(),improving_reps=int(g.improves.sum()),improve_percent=100*h.improve_fraction.mean(),inputs_with_any_improvement=int(h.any_improvement.sum()),exact_inputs=int(h.exact_available.sum()),exact_reps=len(ex),optimal_match_reps=int(ex.optimal_match.sum()) if len(ex) else None,optimal_match_percent=100*ex.optimal_match.mean() if len(ex) else None,mean_quantum_gap_percent=h.exact_gap_percent.mean(),mean_classical_gap_percent=h.mean_classical_gap_percent.mean(),mean_relative_improvement_percent=h.mean_relative_improvement_percent.mean(),mean_delta_initial_s=h.mean_delta_initial_s.mean(),mean_adopted_delta_J_s=h.mean_adopted_delta_J_s.mean(),mean_within_measurement_sd_s=h.within_measurement_sd_s.mean(),max_within_measurement_sd_s=h.within_measurement_sd_s.max(),mean_rep_median_objective_s=h.median_JQ_s.mean(),mean_rep_median_delta_J_s=h.median_delta_J_s.mean(),missing_policy='exact missing excluded only from exact metrics; no imputation',runtime_matched=False)
    row.update(descr(h.mean_JQ_s,'input_mean_JQ_'));row.update(descr(h.mean_delta_J_s,'input_mean_delta_J_'));row.update(descr(g.JQ_s,'all_rep_JQ_'));row.update(descr(g.delta_J_s,'all_rep_delta_J_'));summaries.append(row)
    for metric,col in [('mean_delta_J_s','mean_delta_J_s'),('improve_fraction','improve_fraction'),('mean_gap_percent','exact_gap_percent'),('optimal_match_fraction','optimal_match_fraction')]:
     nums=np.zeros(len(groups));dens=np.zeros(len(groups))
     for v in h.to_dict('records'):
      if pd.isna(v[col]):continue
      j=gi[v['group_id']];nums[j]+=float(v[col]);dens[j]+=1
     den=weights@dens;boot=np.divide(weights@nums,den,out=np.full(10000,np.nan),where=den>0);good=boot[np.isfinite(boot)];unc.append(dict(scale=scale,config_id=cfg,classical_method=method,metric=metric,kind='GROUP_RESAMPLING_SENSITIVITY_NOT_REAL_FLEET_CI',point=nums.sum()/dens.sum() if dens.sum() else None,lower95=np.quantile(good,.025) if len(good) else None,upper95=np.quantile(good,.975) if len(good) else None,resamples=10000,seed=20261102,unit='25 demand groups; all within-group inputs/settings/reps retained',clusters_present=int((dens>0).sum()),undefined_resamples=int((den==0).sum())))
    # Measurement-only resampling: fixed inputs/fits and classical results. Reuse identical stream for both classical contrasts.
    matrices={key:g.pivot(index='problem_id',columns='measurement_rep',values=col).astype(float).to_numpy() for key,col in [('mean_delta_J_s','delta_J_s'),('improve_fraction','improves')]};seed=[20261104,6 if scale=='ALL' else int(scale[1:]),configs.index(cfg)];rg=np.random.default_rng(np.random.SeedSequence(seed));boots={k:[] for k in matrices};vary=np.any(np.ptp(matrices['mean_delta_J_s'],axis=1)>0)
    if vary:
     for start in range(0,10000,100):
      counts=rg.multinomial(10,np.full(10,.1),size=(100,len(h)))
      for key,mat in matrices.items():boots[key].extend(((counts*mat[None,:,:]).sum(axis=(1,2))/(10*len(h))).tolist())
    else:
     for key,mat in matrices.items():boots[key]=[float(mat.mean())]*10000
    for key,bb in boots.items():unc.append(dict(scale=scale,config_id=cfg,classical_method=method,metric=key,kind='MEASUREMENT_RESAMPLING_FIXED_INPUT_FIT',point=float(matrices[key].mean()),lower95=float(np.quantile(bb,.025)),upper95=float(np.quantile(bb,.975)),resamples=10000,seed=json.dumps(seed),unit='10 measurement reps resampled separately inside each fixed input/fit',clusters_present=len(h),undefined_resamples=0))
 table('PATH1_STATISTICAL_RESULTS.csv',summaries);table('PATH1_UNCERTAINTY_INTERVALS.csv',unc)
 # Legacy indicators explicitly reconstructed for impact audit.
 legacy=[]
 for (sc,cfg),g in paired[paired.primary_comparison].groupby(['scale','config_id']):
  old=g[g.legacy_exact_available];new=g[g.exact_available];legacy.append(dict(scale=sc,config_id=cfg,legacy_exact_inputs=old.problem_id.nunique(),audited_exact_inputs=new.problem_id.nunique(),legacy_gap_percent=old.legacy_quantum_gap_percent.mean(),audited_gap_percent=new.quantum_gap_percent.mean(),legacy_optimal_match_percent=100*old.legacy_optimal_match.mean(),audited_optimal_match_percent=100*new.optimal_match.mean()))
 table('EXACT_REFERENCE_STATISTICAL_IMPACT.csv',legacy)
 # All figure values are saved in input/summary/pair CSVs above.
 plt=plotting();primary=ip[ip.primary_comparison];summary=pd.DataFrame(summaries);primary_s=summary[summary.primary_comparison & summary.scale.ne('ALL')];short={c:c.replace('_P2','').replace('ACTIVE_ADJACENT_P3_GRID','ACTIVE').replace('GROVER_P3','GROVER3') for c in configs}
 fig,ax=plt.subplots(figsize=(10,5))
 for cfg,h in primary_s.groupby('config_id'):ax.plot(h.scale,h.input_mean_delta_J_mean,'o-',label=short[cfg])
 ax.axhline(0,color='black',lw=.7);ax.set(xlabel='B scale (R4=100 customers)',ylabel='Mean Delta J vs greedy (s)',title='Input-first means; saved budgets unmatched');ax.legend(fontsize=7,ncol=2);savefig(fig,'PATH1_STATISTICAL_FIGURES','F1_quality_by_scale');plt.close(fig)
 fig,axs=plt.subplots(2,3,figsize=(12,7),sharey=True)
 for ax,sc in zip(axs.flat,sorted(primary.scale.unique())):
  h=primary_s[primary_s.scale==sc].set_index('config_id').loc[configs];ax.bar(range(len(configs)),h.improve_percent);ax.set_title(sc);ax.set_xticks(range(len(configs)),[short[c] for c in configs],rotation=65,ha='right');ax.set_ylabel('Improving measurement reps (%)')
 savefig(fig,'PATH1_STATISTICAL_FIGURES','F2_improvement_rates');plt.close(fig)
 fig,axs=plt.subplots(2,3,figsize=(12,7))
 for ax,sc in zip(axs.flat,sorted(primary.scale.unique())):
  h=primary[primary.scale==sc];ax.boxplot([h[h.config_id==c].exact_gap_percent.dropna() for c in configs],tick_labels=[short[c] for c in configs],showfliers=False);ax.tick_params(axis='x',rotation=65);ax.set(title=sc,ylabel='Input mean global gap (%)')
 savefig(fig,'PATH1_STATISTICAL_FIGURES','F3_global_gap_distribution');plt.close(fig)
 fig,axs=plt.subplots(2,3,figsize=(11,7))
 for ax,sc in zip(axs.flat,sorted(primary.scale.unique())):
  h=primary[primary.scale==sc]
  for cfg in configs:
   z=h[h.config_id==cfg];ax.scatter(z.JC_s,z.mean_JQ_s,s=9,alpha=.5,label=short[cfg])
  lo=min(h.JC_s.min(),h.mean_JQ_s.min());hi=max(h.JC_s.max(),h.mean_JQ_s.max());ax.plot([lo,hi],[lo,hi],color='black',lw=.7);ax.set(title=sc,xlabel='Classical greedy J (s)',ylabel='Quantum mean J (s)')
 axs[0,0].legend(fontsize=6);savefig(fig,'PATH1_STATISTICAL_FIGURES','F4_paired_objectives');plt.close(fig)
 fig,axs=plt.subplots(2,3,figsize=(12,7))
 for ax,sc in zip(axs.flat,sorted(primary.scale.unique())):
  h=primary[primary.scale==sc];ax.boxplot([h[h.config_id==c].within_measurement_sd_s for c in configs],tick_labels=[short[c] for c in configs],showfliers=False);ax.tick_params(axis='x',rotation=65);ax.set(title=sc,ylabel='Within-fit measurement SD (s)')
 savefig(fig,'PATH1_STATISTICAL_FIGURES','F5_measurement_variation');plt.close(fig)
 finish('PATH1_STATISTICS',t,dict(plan_rows=len(plans),paired_rows=len(paired),input_config_contrasts=len(ip),summary_rows=len(summaries),interval_rows=len(unc),exact_inputs=sum(bool(x['exact_fraction']) for x in ref.values()),raw_sources=len(raw)))
if __name__=='__main__':main()
