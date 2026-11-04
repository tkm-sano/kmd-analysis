from common import *
from controlled_qaoa import data,setup,distribution
from path1_statistics import wilson,descr

def best_distribution(z,p,shots):
 order=sorted(range(len(z['costs'])),key=lambda j:z['costs'][j]);cost=np.array([float(z['costs'][j]) for j in order]);pr=np.array([p[j] for j in order]);tail=np.r_[np.cumsum(pr[::-1])[::-1],0.];mass=np.maximum(np.clip(tail[:-1],0,1)**shots-np.clip(tail[1:],0,1)**shots,0);return float(cost@mass)

def main():
 t=time.perf_counter();os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});fit=frame(O/'QAOA_CONTROLLED_EXPERIMENT_RESULTS.csv');rep=frame(O/'experiments/QAOA_MAIN_MEASUREMENTS.csv');keys=['problem_id','n_customers','support','initial_state','mixer','layers','method'];summary=[];analytic=[];coherence=[];dmap={pid:data(pid) for pid in sorted(fit.problem_id.unique())};zmap={}
 for k,g in fit.groupby(keys,sort=True):
  kmap=dict(zip(keys,k));n=len(g);k0=int(g.primary_rep0_optimal.sum());lo,hi=wilson(k0,n);rg=np.random.default_rng(np.random.SeedSequence([2026110404,int(kmap['problem_id'][1])*1000+int(kmap['problem_id'].split('_')[1]),list(fit.groupby(keys,sort=True).groups).index(k)]));idx=rg.integers(0,n,size=(10000,n));v=g.mean_delta_J_greedy_s.to_numpy();bb=v[idx].mean(axis=1);summary.append(kmap|dict(independent_learning_fits=n,measurement_reps_per_fit=10,shots_per_rep=8192,primary_optimal_rep0_count=k0,primary_optimal_rep0_rate=k0/n,primary_optimal_Wilson95_lower=lo,primary_optimal_Wilson95_upper=hi,mean_all_rep_optimal_rate=g.optimal_match_fraction.mean(),mean_improve_greedy_rate=g.improve_fraction.mean(),mean_delta_J_greedy_s=v.mean(),fit_delta_J_sd_s=v.std(ddof=1),fit_delta_J_median_s=np.median(v),fit_delta_J_bootstrap95_lower=np.quantile(bb,.025),fit_delta_J_bootstrap95_upper=np.quantile(bb,.975),mean_delta_J_initial_s=g.mean_delta_J_initial_s.mean(),mean_expected_objective_s=g.expected_objective_s.mean(),mean_total_wall_s=g.total_wall_s.mean(),mean_total_CPU_s=g.total_CPU_s.mean(),mean_within_measurement_sd_s=g.sd_objective_s.mean(),support_states=g.support_states.iloc[0],precision_scope='Wilson on rep0 per independent learning fit; fit bootstrap conditional on chosen diagnostic input'))
 for x in fit.to_dict('records'):
  pid=x['problem_id'];d=dmap[pid];zk=(pid,x['support'],x['initial_state'],x['mixer'])
  if zk not in zmap:zmap[zk]=setup(d,x['support'],x['mixer'],x['initial_state'])
  z=zmap[zk];angles=np.array(json.loads(x['selected_angles']));p=distribution(z,angles,x['method']);saved=np.array(json.loads(x['state_probabilities']));ck('controlled saved state probabilities reproduce',np.max(abs(p-saved))<1e-12,pid,f"{zk}/{x['layers']}/{x['method']}/{x['learning_rep']}")
  massopt=float(sum(p[j] for j,v in enumerate(z['costs']) if v==d['exact']));massinit=float(sum(p[j] for j,v in enumerate(z['costs']) if v<d['initial_cost']));base={k:x[k] for k in ['problem_id','support','initial_state','mixer','layers','method','learning_rep']}
  for shots in [1,8,64,8192]:
   get=lambda p:1. if p>=1 else -math.expm1(shots*math.log1p(-max(0.,p)))
   analytic.append(base|dict(shots=shots,optimal_acquisition_probability=get(massopt),initial_improvement_probability=get(massinit),expected_sampled_best_s=best_distribution(z,p,shots),exact_optimum_s=float(d['exact']),initial_s=float(d['initial_cost']),saved_greedy_s=float(d['JC']),value_type='analytic readback from simulated final-state probabilities; not new shots or new fits'))
  if x['method']=='QAOA':
   pdp=distribution(z,angles,'DEPHASED');coherence.append(base|dict(Q_expected_s=float(p@z['cost']),same_angles_dephased_expected_s=float(pdp@z['cost']),dephased_minus_Q_expected_s=float((pdp-p)@z['cost']),Q_single_shot_optimal_probability=massopt,same_angles_dephased_single_shot_optimal_probability=float(sum(pdp[j] for j,v in enumerate(z['costs']) if v==d['exact'])),comparison='same support, initial, mixer, layer and learned Q angles; diagnostic dephasing intervention'))
 su=pd.DataFrame(summary);an=pd.DataFrame(analytic);co=pd.DataFrame(coherence);table('QAOA_CONTROLLED_CELL_SUMMARY.csv',su);table('QAOA_MEASUREMENT_BUDGET_SENSITIVITY.csv',an);table('QAOA_SAME_ANGLE_DEPHASING.csv',co)
 paired=fit.pivot(index=['problem_id','support','initial_state','mixer','layers','learning_rep'],columns='method',values=['mean_objective_s','expected_objective_s','optimal_match_fraction','total_wall_s']);pairs=[]
 for key,row in paired.iterrows():pairs.append(dict(zip(['problem_id','support','initial_state','mixer','layers','learning_rep'],key))|dict(dephased_minus_Q_mean_sampled_s=row[('mean_objective_s','DEPHASED')]-row[('mean_objective_s','QAOA')],dephased_minus_Q_expected_s=row[('expected_objective_s','DEPHASED')]-row[('expected_objective_s','QAOA')],Q_minus_dephased_optimal_rate=row[('optimal_match_fraction','QAOA')]-row[('optimal_match_fraction','DEPHASED')],paired_learning_start_seed=True))
 table('QAOA_CONTROLLED_PAIRED_CONTRASTS.csv',pairs)
 # Reconstruct best from saved histograms, independently checking outcomes for every fit/measurement.
 shotfile=pin(O/'experiments/QAOA_MAIN_SHOT_COUNTS.npz','new stored shot histograms');savedreps=rep.set_index(['problem_id','support','initial_state','mixer','layers','method','learning_rep','measurement_rep'])
 with np.load(shotfile,allow_pickle=False) as zf:
  for i,x in enumerate(fit.to_dict('records')):
   z=zmap[(x['problem_id'],x['support'],x['initial_state'],x['mixer'])];counts=zf[f'f{i:05d}'];ck('8192 histogram counts per rep',counts.shape==(10,z['size']) and np.all(counts.sum(axis=1)==8192),x['problem_id'])
   for r,cnt in enumerate(counts):
    value=min(v for v,nc in zip(z['costs'],cnt) if nc>0);key=tuple(x[k] for k in ['problem_id','support','initial_state','mixer','layers','method','learning_rep'])+(r,);ck('stored sampled best from histogram',F(str(savedreps.loc[key,'objective_fraction']))==value,x['problem_id'])
 plt=plotting();q=su[su.method=='QAOA'];fig,axs=plt.subplots(1,3,figsize=(12,4),sharey=True)
 for ax,(pid,g) in zip(axs,q.groupby('problem_id')):
  labels=[f"{x.support[:1]}/{x.initial_state[:1]}/{x.mixer[:1]}/p{x.layers}" for x in g.itertuples()];ax.bar(range(len(g)),g.primary_optimal_rep0_rate);ax.set(title=pid,ylabel='Optimal acquisition rate, rep0',ylim=(0,1.05));ax.set_xticks(range(len(g)),labels,rotation=90,fontsize=6)
 savefig(fig,'QAOA_CONTROLLED_EXPERIMENT_FIGURES','F1_support_optimal_acquisition');plt.close(fig)
 fig,ax=plt.subplots(figsize=(8,4))
 for (pid,method),g in an[an.support=='FULL_PERMUTATION'].groupby(['problem_id','method']):
  v=g.groupby('shots').optimal_acquisition_probability.mean();ax.plot(v.index,v,'o-',label=pid+' '+method)
 ax.set(xscale='log',xlabel='Shots at fixed fitted state',ylabel='Mean optimal-acquisition probability',title='Measurement-budget sensitivity; same fitted states');ax.legend(fontsize=6,ncol=2);savefig(fig,'QAOA_CONTROLLED_EXPERIMENT_FIGURES','F2_shot_budget');plt.close(fig)
 fig,ax=plt.subplots(figsize=(8,4));g=co[co.problem_id=='R1_020'];labels=[];vals=[]
 for k,h in g.groupby(['support','initial_state','mixer','layers']):labels.append('/'.join(map(str,k)));vals.append(h.dephased_minus_Q_expected_s)
 ax.boxplot(vals,tick_labels=labels,showfliers=False);ax.tick_params(axis='x',rotation=90,labelsize=6);ax.axhline(0,color='black',lw=.7);ax.set(ylabel='Same-angle dephased minus Q expected OD (s)',title='Conditional dephasing diagnostic, R1_020');savefig(fig,'QAOA_CONTROLLED_EXPERIMENT_FIGURES','F3_same_angle_dephasing');plt.close(fig)
 fig,ax=plt.subplots(figsize=(8,4));ax.scatter(fit.total_CPU_s,fit.mean_delta_J_greedy_s,s=3,alpha=.15);ax.axhline(0,color='black',lw=.7);ax.set(xlabel='CPU pipeline time (s)',ylabel='Delta J vs saved greedy (s)',title='All new fits; CPU simulation only');savefig(fig,'QAOA_CONTROLLED_EXPERIMENT_FIGURES','F4_quality_time');plt.close(fig)
 finish('QAOA_ANALYSIS',t,dict(fits=len(fit),measurement_reps=len(rep),cells=len(su),histogram_fits=len(fit),same_angle_diagnostics=len(co),budget_sensitivity_rows=len(an)))
if __name__=='__main__':main()
