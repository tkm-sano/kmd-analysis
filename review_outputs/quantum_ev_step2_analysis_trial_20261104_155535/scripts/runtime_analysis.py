from common import *
from path1_statistics import descr

def greedy(pid,rep,mode):
 t=time.perf_counter();c=time.process_time();m=next(x for x in js(S/'mirror_family/MANIFEST.json') if x['run_id']==pid);a=arr(m['instance_path']);b=frame(P/'B_CLASSICAL_INITIAL_BASELINES.csv',dtype=str);rt=json.loads(b[b.problem_id==pid].iloc[0].initial_route)[1:-1];weights=[[F(str(v)) for v in row] for row in a['travel']];prew=time.perf_counter()-t;prec=time.process_time()-c
 def val(r):return weights[0][r[0]]+sum((weights[i][j] for i,j in zip(r,r[1:])),F(0))+weights[r[-1]][0]
 current=rt.copy();best=rt.copy();bestcost=score=val(current);seed=[2026110405,int(pid[1])*1000+int(pid.split('_')[1]),rep,0 if mode=='main' else 1];rng=np.random.default_rng(np.random.SeedSequence(seed));tw=time.perf_counter();tc=time.process_time();evals=0
 while evals<64:
  options=[]
  for j in range(len(current)-1):
   if evals>=64:break
   q=current.copy();q[j],q[j+1]=q[j+1],q[j];value=val(q);evals+=1;options.append((value,q))
  candidate=min(options,key=lambda x:(x[0],x[1]))
  if candidate[0]<score:score,current=candidate[0],candidate[1]
  elif evals<64:
   current=best.copy();j=int(rng.integers(0,len(current)-1));current[j],current[j+1]=current[j+1],current[j];score=val(current);evals+=1
  else:break
  if score<bestcost:bestcost=score;best=current.copy()
 optw=time.perf_counter()-tw;optc=time.process_time()-tc;tw=time.perf_counter();tc=time.process_time();route=[0,*best,0];assert feasible(a,route) and objective(a,route)==bestcost;vw=time.perf_counter()-tw;vc=time.process_time()-tc
 return dict(source='NEW_MATCHED_INPUT_CPU_PIPELINE',problem_id=pid,n_customers=m['n'],scale=m['scale_id'],config_id='NEW_ITERATED_ADJACENT_GREEDY64',method='CLASSICAL_GREEDY',learning_rep=rep,measurement_rep=None,seed=json.dumps(seed),objective_fraction=str(bestcost),objective_s=float(bestcost),evaluation_budget=64,actual_evaluations=evals,incumbent_kept=True,preprocessing_wall_s=prew,preprocessing_CPU_s=prec,optimization_wall_s=optw,optimization_CPU_s=optc,simulation_wall_s=None,simulation_CPU_s=None,sampling_wall_s=None,sampling_CPU_s=None,verification_wall_s=vw,verification_CPU_s=vc,postprocessing_wall_s=None,postprocessing_CPU_s=None,total_wall_s=time.perf_counter()-t,total_CPU_s=time.process_time()-c,transfer_s=None,scope='CPU input-read/preprocessing+64route-score greedy+validation; common initial route preprovided; imports excluded',CPU_affinity=json.dumps(sorted(os.sched_getaffinity(0))),threads=1,QPU_execution=False)

def main():
 t=time.perf_counter();os.sched_setaffinity(0,{max(os.sched_getaffinity(0))});fits=frame(O/'QAOA_CONTROLLED_EXPERIMENT_RESULTS.csv');new=[]
 for pid in ['R0_001','R1_001','R1_020']:
  warm=greedy(pid,999,'warmup');dump(f'experiments/runtime_greedy_{pid}_warmup.json',warm);pilot=[greedy(pid,i,'pilot') for i in range(3)];table(f'experiments/runtime_greedy_{pid}_pilot.csv',pilot)
  for i in range(97):new.append(greedy(pid,i,'main'))
 table('experiments/NEW_CLASSICAL_RUNTIME_RAW.csv',new)
 # Preserve raw rows and pipeline scope, do not combine copied per-rep fit times.
 allnew=fits.copy();allnew['source']='NEW_CONTROLLED_FIT_CPU_PIPELINE';allnew['scope']='CPU input-read/support setup+optimization(simulation inside)+10measurement reps+verification+postprocess; common initial preprovided; imports excluded';allnew['config_id']=allnew.support+'/'+allnew.initial_state+'/'+allnew.mixer+'/p'+allnew.layers.astype(str)
 raw=pd.concat([allnew,pd.DataFrame(new)],ignore_index=True);table('PATH1_RUNTIME_RESULTS.csv',raw)
 summaries=[]
 for key,g in raw.groupby(['source','problem_id','method','config_id'],dropna=False):
  row=dict(zip(['source','problem_id','method','config_id'],key));row.update(repetitions=len(g),threads=1,CPU_only=True)
  for col in ['total_wall_s','total_CPU_s','preprocessing_wall_s','optimization_wall_s','simulation_wall_s','sampling_wall_s','verification_wall_s']:row.update(descr(pd.to_numeric(g[col],errors='coerce'),col+'_'))
  summaries.append(row)
 table('PATH1_RUNTIME_SUMMARY.csv',summaries)
 oldfits=frame(P/'B_RESOURCES_PER_FIT.csv');oldbase=frame(P/'B_CLASSICAL_INITIAL_BASELINES.csv');oldaux=frame(P/'B_AUXILIARY_CLASSICAL_IMPROVEMENTS.csv');old=[]
 for (scale,cfg,scope),g in oldfits.groupby(['scale','config_id','resource_scope']):
  for col in ['fit_wall_s','fit_CPU_s']:old.append(dict(scale=scale,config_id=cfg,scope=scope,component=col,records=len(g),**descr(pd.to_numeric(g[col],errors='coerce'),'time_s_')))
 for scale,g in oldbase.groupby('scale'):
  for col in ['wall_seconds','CPU_seconds']:old.append(dict(scale=scale,config_id='OLD_CLASSICAL_INITIAL',scope='three-sweep heuristic+verification; excludes NPZ read/imports/certificate/IO',component=col,records=len(g),**descr(pd.to_numeric(g[col],errors='coerce'),'time_s_')))
 for (scale,method),g in oldaux.groupby(['scale','method']):old.append(dict(scale=scale,config_id=method,scope='OLD_SWAP_CPU_MATCH; not current staged8',component='actual_CPU_seconds',records=len(g),**descr(pd.to_numeric(g.actual_CPU_seconds,errors='coerce'),'time_s_')))
 table('PATH1_EXISTING_RUNTIME_BY_SCOPE.csv',old)
 for x in new:ck('classical evaluation budget controlled',x['actual_evaluations']<=64,x['problem_id'])
 # Timer audit: inner simulation is not added twice, wall components bounded by pipeline total.
 for x in raw.to_dict('records'):
  outer=sum(float(x[k]) for k in ['preprocessing_wall_s','optimization_wall_s','sampling_wall_s','verification_wall_s','postprocessing_wall_s'] if pd.notna(x.get(k)) and x.get(k)!='')
  ck('nonoverlapping time parts <= pipeline total',outer<=float(x['total_wall_s'])+1e-6,x['problem_id'])
  if pd.notna(x.get('simulation_wall_s')):ck('simulation time is inside optimization',float(x['simulation_wall_s'])<=float(x['optimization_wall_s'])+1e-7,x['problem_id'])
 plt=plotting();fig,axs=plt.subplots(1,3,figsize=(12,4))
 for ax,(pid,g) in zip(axs,raw.groupby('problem_id')):
  methods=['CLASSICAL_GREEDY','DEPHASED','QAOA'];ax.boxplot([g[g.method==m].total_wall_s for m in methods],tick_labels=methods,showfliers=False);ax.set(title=pid,ylabel='CPU pipeline wall (s)');ax.tick_params(axis='x',rotation=25)
 savefig(fig,'PATH1_RUNTIME_FIGURES','F1_new_pipeline_distribution');plt.close(fig)
 fig,ax=plt.subplots(figsize=(8,4))
 for method,g in raw.groupby('method'):ax.scatter(g.total_CPU_s,g.total_wall_s,s=3,alpha=.12,label=method)
 ax.set(xlabel='Process CPU time (s)',ylabel='Pipeline wall time (s)',title='Same CPU affinity; imports/shared initial construction excluded');ax.legend();savefig(fig,'PATH1_RUNTIME_FIGURES','F2_CPU_wall');plt.close(fig)
 fig,ax=plt.subplots(figsize=(10,4));cols=['preprocessing_wall_s','optimization_wall_s','sampling_wall_s','verification_wall_s'];v=raw.groupby('method')[cols].mean().fillna(0);bottom=np.zeros(len(v))
 for col in cols:ax.bar(v.index,v[col],bottom=bottom,label=col);bottom+=v[col].to_numpy()
 ax.set(ylabel='Mean non-overlapping wall components (s)',title='Simulation is an optimization subcomponent');ax.legend(fontsize=7);savefig(fig,'PATH1_RUNTIME_FIGURES','F3_scope_components');plt.close(fig)
 finish('RUNTIME',t,dict(new_greedy_repetitions=len(new),new_controlled_fit_times=len(fits),old_unique_fits=len(oldfits),runtime_records=len(raw)))
if __name__=='__main__':main()
