from common import *
from scipy.optimize import minimize
from scipy.linalg import expm
from statistics import NormalDist

def data(pid):
 t=time.perf_counter();c=time.process_time();m=next(x for x in js(S/'mirror_family/MANIFEST.json') if x['run_id']==pid);a=arr(m['instance_path']);base=frame(P/'B_CLASSICAL_INITIAL_BASELINES.csv',dtype=str);br=base[base.problem_id==pid].iloc[0];initial=tuple(json.loads(br.initial_route)[1:-1]);n=len(initial);perms=list(itertools.permutations(range(1,n+1)));exact=[objective(a,[0,*p,0]) for p in perms];vals=np.array(list(map(float,exact)));scale=max(float(vals.std()),1.);center=float(vals.mean());jc=frame(P/'B_AUXILIARY_CLASSICAL_IMPROVEMENTS.csv',dtype=str);jc=F(jc[(jc.problem_id==pid)&(jc.method=='ITERATED_GREEDY_ADJACENT_SWAP')].iloc[0].classical_best_seconds)
 return dict(a=a,initial=initial,n=n,perms=perms,costs=exact,scale=scale,center=center,initial_cost=objective(a,[0,*initial,0]),JC=jc,exact=min(exact),input_sha256=m['instance_sha256'],wall_s=time.perf_counter()-t,CPU_s=time.process_time()-c)

def setup(d,support,mixer,initial):
 if support=='FULL_PERMUTATION':states=d['perms']
 else:
  states=[]
  for bits in itertools.product([0,1],repeat=d['n']//2):
   p=list(d['initial'])
   for i,b in enumerate(bits):
    if b:p[i],p[-1-i]=p[-1-i],p[i]
   states.append(tuple(p))
  states=sorted(states)
 ix={p:i for i,p in enumerate(states)};costs=[objective(d['a'],[0,*p,0]) for p in states];cost=np.array(list(map(float,costs)));phase=(cost-d['center'])/d['scale'];size=len(states)
 state=np.full(size,1/math.sqrt(size),dtype=complex) if initial=='UNIFORM_SUPPORT' else np.eye(size,dtype=complex)[ix[d['initial']]]
 if mixer=='PROJECTOR':h=np.ones((size,size))/size
 else:
  h=np.zeros((size,size))
  for p,i in ix.items():
   pairs=[(j,j+1) for j in range(d['n']-1)] if support=='FULL_PERMUTATION' else [(j,d['n']-1-j) for j in range(d['n']//2)]
   for j,k in pairs:
    q=list(p);q[j],q[k]=q[k],q[j];h[ix[tuple(q)],i]+=1
 eig,v=np.linalg.eigh(h)
 return dict(states=states,costs=costs,phase=phase,state=state,h=h,eig=eig,v=v,cost=cost,size=size)

def distribution(z,angles,method):
 state=z['state'].copy();prob=abs(state)**2
 for g,b in zip(angles[::2],angles[1::2]):
  if method=='QAOA':
   state*=np.exp(-1j*g*z['phase']);state=z['v']@(np.exp(-1j*b*z['eig'])*(z['v'].conj().T@state))
  else:
   u=(z['v']*np.exp(-1j*b*z['eig']))@z['v'].conj().T;prob=abs(u)**2@prob
 p=abs(state)**2 if method=='QAOA' else prob
 assert p.min()>-1e-13 and abs(p.sum()-1)<1e-10
 return np.maximum(p,0)/p.sum()

def run_fit(pid,support,init,mixer,layers,method,learn_index,mode):
 begin=time.perf_counter();begin_c=time.process_time();d=data(pid);tt=time.perf_counter();cc=time.process_time();z=setup(d,support,mixer,init);prew=d['wall_s']+time.perf_counter()-tt;prec=d['CPU_s']+time.process_time()-cc
 sid=0 if support=='MIRROR_ORBIT' else 1;iid=0 if init=='BASIS_INITIAL' else 1;mid=0 if mixer=='PROJECTOR' else 1;pidid=int(pid[1])*1000+int(pid.split('_')[1]);entropy=[2026110402,pidid,sid,iid,mid,layers,learn_index,0 if mode=='main' else 1];seed=np.random.SeedSequence(entropy);rng=np.random.default_rng(seed);x0=np.array([rng.uniform(0,8) if k%2==0 else rng.uniform(-math.pi,math.pi) for k in range(2*layers)]);simw=simc=0.;calls=0
 def f(x):
  nonlocal simw,simc,calls
  t=time.perf_counter();c=time.process_time();p=distribution(z,x,method);value=float(p@z['phase']);simw+=time.perf_counter()-t;simc+=time.process_time()-c;calls+=1;return value
 tw=time.perf_counter();tc=time.process_time();result=minimize(f,x0,method='COBYLA',bounds=[(0,8) if k%2==0 else (-math.pi,math.pi) for k in range(2*layers)],options=dict(maxiter=64,rhobeg=.4,tol=1e-7,catol=1e-9));p=distribution(z,result.x,method);optw=time.perf_counter()-tw;optc=time.process_time()-tc
 # The shared learning-start seed is paired; each method is optimized separately.
 t=time.perf_counter();c=time.process_time();records=[];counts=[];methodid=0 if method=='QAOA' else 1
 for rep in range(10):
  mentropy=[2026110403,pidid,sid,iid,mid,layers,learn_index,methodid,rep,0 if mode=='main' else 1];g=np.random.default_rng(np.random.SeedSequence(mentropy));draws=g.multinomial(8192,p);idx=min(np.flatnonzero(draws>0),key=lambda j:z['costs'][j]);raw=z['costs'][idx];adopt=min(raw,d['initial_cost']);rt=[0,*z['states'][idx],0];counts.append(draws)
  records.append(dict(problem_id=pid,n_customers=d['n'],support=support,initial_state=init,mixer=mixer,layers=layers,method=method,learning_rep=learn_index,measurement_rep=rep,measurement_seed=json.dumps(mentropy),shots=8192,objective_fraction=str(raw),objective_s=float(raw),adopted_objective_fraction=str(adopt),adopted_objective_s=float(adopt),delta_J_greedy_s=float(d['JC']-raw),delta_J_initial_s=float(d['initial_cost']-raw),improves_greedy=raw<d['JC'],improves_initial=raw<d['initial_cost'],optimal_match=raw==d['exact'],feasible=True,route=json.dumps(rt),input_sha256=d['input_sha256']))
 samplew=time.perf_counter()-t;samplec=time.process_time()-c;t=time.perf_counter();c=time.process_time()
 for row in records:assert feasible(d['a'],json.loads(row['route'])) and objective(d['a'],json.loads(row['route']))==F(row['objective_fraction'])
 validw=time.perf_counter()-t;validc=time.process_time()-c;t=time.perf_counter();c=time.process_time();impmass=float(sum(p[j] for j,v in enumerate(z['costs']) if v<d['JC']));success=-math.expm1(8192*math.log1p(-impmass)) if 0<impmass<1 else impmass
 summary=dict(problem_id=pid,n_customers=d['n'],support=support,initial_state=init,mixer=mixer,layers=layers,method=method,learning_rep=learn_index,learning_seed=json.dumps(entropy),optimizer='COBYLA',objective_evaluations=calls,max_evaluations=64,optimizer_success=bool(result.success),optimizer_message=str(result.message),initial_angles=json.dumps(x0.tolist()),selected_angles=json.dumps(result.x.tolist()),support_states=z['size'],input_sha256=d['input_sha256'],mean_objective_s=float(np.mean([x['objective_s'] for x in records])),sd_objective_s=float(np.std([x['objective_s'] for x in records],ddof=1)),mean_delta_J_greedy_s=float(np.mean([x['delta_J_greedy_s'] for x in records])),mean_delta_J_initial_s=float(np.mean([x['delta_J_initial_s'] for x in records])),improve_fraction=float(np.mean([x['improves_greedy'] for x in records])),primary_rep0_improves=records[0]['improves_greedy'],primary_rep0_optimal=records[0]['optimal_match'],optimal_match_fraction=float(np.mean([x['optimal_match'] for x in records])),exact_success_probability_best8192=success,single_shot_improvement_probability=impmass,expected_objective_s=float(p@z['cost']),state_probabilities=json.dumps(p.tolist()),preprocessing_wall_s=prew,preprocessing_CPU_s=prec,optimization_wall_s=optw,optimization_CPU_s=optc,simulation_wall_s=simw,simulation_CPU_s=simc,optimizer_overhead_wall_s=max(0.,optw-simw),sampling_wall_s=samplew,sampling_CPU_s=samplec,verification_wall_s=validw,verification_CPU_s=validc,postprocessing_wall_s=0.,postprocessing_CPU_s=0.,transfer_s=None,hardware='CPU exact feasible-subspace simulation',threads=1,CPU_affinity=json.dumps(sorted(os.sched_getaffinity(0))),QPU_execution=False)
 summary['postprocessing_wall_s']=time.perf_counter()-t;summary['postprocessing_CPU_s']=time.process_time()-c;summary['total_wall_s']=time.perf_counter()-begin;summary['total_CPU_s']=time.process_time()-begin_c
 return summary,records,np.asarray(counts)

def main():
 t=time.perf_counter();pilot='--pilot' in sys.argv;mode='pilot' if pilot else 'main';nlearn=3 if pilot else 97;os.sched_setaffinity(0,{max(os.sched_getaffinity(0))});inputs=['R0_001','R1_001','R1_020'];conditions=list(itertools.product(inputs,['MIRROR_ORBIT','FULL_PERMUTATION'],['BASIS_INITIAL','UNIFORM_SUPPORT'],['PROJECTOR','GRAPH_SWAP'],[1,2],['QAOA','DEPHASED']))
 pin(O/'QAOA_CONTROLLED_EXPERIMENT_DESIGN.md','preregistered controlled design');pin(Path(__file__),'controlled simulation code')
 # Numerical controls independent direct expm and seed replay before fitting.
 for pid in inputs:
  d=data(pid)
  for supp in ['MIRROR_ORBIT','FULL_PERMUTATION']:
   for init in ['BASIS_INITIAL','UNIFORM_SUPPORT']:
    for mix in ['PROJECTOR','GRAPH_SWAP']:
     z=setup(d,supp,mix,init);ang=np.array([.7,.23,.5,-.31]);direct=z['state'].copy()
     for g,b in zip(ang[::2],ang[1::2]):direct=expm(-1j*b*z['h'])@(np.exp(-1j*g*z['phase'])*direct)
     ck('controlled direct expm agrees with eig implementation',np.max(abs(abs(direct)**2-distribution(z,ang,'QAOA')))<1e-12,pid,f'{supp}/{init}/{mix}')
     ck('controlled support all routes feasible',all(feasible(d['a'],[0,*s,0]) for s in z['states']),pid)
     if supp=='FULL_PERMUTATION':ck('full support exact minimum equals reference',min(z['costs'])==d['exact'],pid)
 if not pilot:ck('controlled pilot correctness/resource gate',js(O/'evidence/QAOA_PILOT_GATE.json')['proceed'])
 warm=run_fit('R0_001','FULL_PERMUTATION','BASIS_INITIAL','PROJECTOR',1,'QAOA',999,'warmup')[0];dump(f'experiments/qaoa_{mode}_warmup.json',warm)
 fits=[];reps=[];hist=[]
 for cond in conditions:
  for lr in range(nlearn):
   fit,rr,cnt=run_fit(*cond,lr,mode);fits.append(fit);reps.extend(rr);hist.append(cnt)
  print(mode,cond,'fits',len(fits),flush=True)
 table(f'experiments/QAOA_{mode.upper()}_FITS.csv',fits);table(f'experiments/QAOA_{mode.upper()}_MEASUREMENTS.csv',reps)
 # Ragged support sizes stored per-fit in an NPZ with stable order, count statistics sufficient for best extraction.
 np.savez_compressed(O/f'experiments/QAOA_{mode.upper()}_SHOT_COUNTS.npz',**{f'f{i:05d}':a for i,a in enumerate(hist)})
 if pilot:
  projected=(time.perf_counter()-t)*97/3;gate=dict(proceed=projected<1800 and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<2**31,projected_main_wall_s=projected,learning_reps_main=97,learning_reps_pilot=3,precision_target_primary_Wilson_halfwidth=.10,formula='ceil(z975^2/(4h^2))=97',cells=len(conditions),notes='all cells retained regardless of improvement; pilot and main use separate streams')
  dump('evidence/QAOA_PILOT_GATE.json',gate)
 else:table('QAOA_CONTROLLED_EXPERIMENT_RESULTS.csv',fits)
 finish('QAOA_PILOT' if pilot else 'QAOA_MAIN',t,dict(fits=len(fits),measurement_reps=len(reps),independent_learning_reps_per_cell=nlearn,measurement_reps_per_fit=10,shots_per_rep=8192))
if __name__=='__main__':main()
