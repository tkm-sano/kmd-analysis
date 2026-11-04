from common import *
from concurrent.futures import ThreadPoolExecutor
import shutil

def solve_one(x):
 pid=x['problem_id'];folder=O/'experiments/exact_recheck'/pid;folder.mkdir(parents=True,exist_ok=True);start=time.perf_counter()
 model=Path(x['final_model']);target=folder/'model.lp'
 if not target.exists():shutil.copyfile(model,target)
 cpu=sorted(os.sched_getaffinity(0))[int(pid.split('_')[1])%min(4,len(os.sched_getaffinity(0)))];cmd=['/usr/bin/time','-v','-o',str(folder/'usage.txt'),'taskset','-c',str(cpu),str(BINS/'soplex'),'--readmode=1','--solvemode=2','-f0','-o0','-s0','-t30','-c',f'-X={folder}/primal.sol',f'-Y={folder}/dual.sol',str(target)]
 if not (folder/'RUN.json').exists():
  try:
   with (folder/'solve.log').open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=50)
   code=r.returncode
  except subprocess.TimeoutExpired:code='TIMEOUT'
  (folder/'RUN.json').write_text(json.dumps(dict(command=cmd,wall_s=time.perf_counter()-start,exitcode=code,source_model=str(model),CPU_affinity=cpu,threads=1),indent=2))
 return x,folder

def verify(x,folder):
 pid=x['problem_id'];meta={v['run_id']:v for v in js(S/'mirror_family/MANIFEST.json')};a=arr(meta[pid]['instance_path']);n=len(a['nodes']);raw=js(W/'REFERENCE'/pid/'result.json');cuts=raw['subtour_cuts'];log=(folder/'solve.log').read_text();run=js(folder/'RUN.json');result=dict(problem_id=pid,recheck_method='SoPlex8.0.3 rational LP -f0 -o0; independently verified dual with 0<=x<=1',source_model=x['final_model'],output_folder=str(folder),wall_s=run['wall_s'],old_upper_fraction=x['witness_upper_fraction'],status='HOLD',exact_fraction='',reason='')
 if not (folder/'primal.sol').is_file() or not (folder/'dual.sol').is_file():result['reason']='NO_RATIONAL_SOLUTION';return result
 primal={k:F(v) for k,v in re.findall(r'^(x_\d+_\d+)\s+(\S+)',(folder/'primal.sol').read_text(),re.M)};dt=(folder/'dual.sol').read_text();y={k:F(v) for k,v in re.findall(r'^((?:out|in|sec)_\d+|horizon)\s+(\S+)',dt,re.M)};eq=sum((v for k,v in y.items() if k.startswith(('out_','in_'))),F(0));ys=y.get('horizon',F(0));lower=eq+ys*(32400-102*(n-1));valid=ys<=0
 for k,subset in enumerate(cuts):
  v=y.get(f'sec_{k}',F(0));valid=valid and v<=0;lower+=v*(len(subset)-1)
 # All SECs are proper nonempty subsets: universally valid for a Hamiltonian tour.
 ck('recheck subtour cuts universally valid',all(1<len(s)<n and len(set(s))==len(s) and all(0<=j<n for j in s) for s in cuts),pid)
 sets=[(set(s),y.get(f'sec_{k}',F(0))) for k,s in enumerate(cuts) if y.get(f'sec_{k}',0)!=0];primal_obj=F(0);reduced_bound=F(0);max_violation=F(0)
 for i in range(n):
  for j in range(n):
   if i==j:continue
   c=F(str(a['travel'][i,j]));aty=y.get(f'out_{i}',F(0))+y.get(f'in_{j}',F(0))+ys*c+sum((v for s,v in sets if i in s and j in s),F(0));rc=c-aty;reduced_bound+=min(F(0),rc);primal_obj+=c*primal.get(f'x_{i}_{j}',F(0))
 lower+=reduced_bound;ck('dual inequality signs valid',valid,pid)
 integral=all(v in (0,1) for v in primal.values());succ={int(k.split('_')[1]):int(k.split('_')[2]) for k,v in primal.items() if v==1};route=[0]
 for _ in range(n):
  if route[-1] not in succ:break
  route.append(succ[route[-1]])
  if route[-1]==0:break
 full=integral and feasible(a,route);uv=objective(a,route) if full else F(x['witness_upper_fraction']);oldub=F(x['witness_upper_fraction']);ub=min(uv,oldub);ck('rational lower <= independently feasible upper',lower<=ub,pid,lower-ub)
 proved=lower==ub;result.update(rational_LP_objective_fraction=str(primal_obj),certified_lower_fraction=str(lower),feasible_upper_fraction=str(ub),reduced_cost_bound_fraction=str(reduced_bound),LP_primal_integral=integral,LP_primal_single_tour=full,new_route=json.dumps(route) if full else '',status='PASS_EXACT_INDEPENDENT_DUAL' if proved else 'HOLD_BOUNDED',exact_fraction=str(ub) if proved else '',gap_upper_fraction=str(ub-lower),gap_upper_s=float(ub-lower),old_upper_minus_new_upper_s=float(oldub-ub),reason='exact independent dual equals verified tour' if proved else 'valid bound only; no equality; no tolerance promotion',solver_log_zero_violation='max. violation = 0' in log)
 dump(f'experiments/exact_recheck/{pid}/INDEPENDENT_CERTIFICATE.json',result);return result

def main():
 t=time.perf_counter();status=frame(O/'EXACT_REFERENCE_STATUS.csv');missing=status[status.n_customers>=100].to_dict('records');pilot='--pilot' in sys.argv
 if pilot:missing=[next(x for x in missing if x['scale']==sc and not x['old_exact_available']) for sc in ['R4','R5']]
 else:
  pilot_data=js(O/'evidence/EXACT_SEPARATION_PILOT_GATE.json');ck('valid-bound resource pilot accepted',pilot_data['proceed'],O/'evidence/EXACT_SEPARATION_PILOT_GATE.json')
 for x in missing:pin(x['final_model'],'exact relaxation source');pin(BINS/'soplex','independent LP solver')
 results=[]
 with ThreadPoolExecutor(max_workers=2 if pilot else 4) as pool:
  for x,folder in pool.map(solve_one,missing):
   results.append(verify(x,folder));print(x['problem_id'],results[-1]['status'],flush=True)
 table('evidence/EXACT_PILOT_RESULTS.csv' if pilot else 'evidence/EXACT_FULL_RESULTS.csv',results)
 if pilot:
  gate=dict(proceed=all(r['status']=='PASS_EXACT_INDEPENDENT_DUAL' and r['wall_s']<45 for r in results),targets=[r['problem_id'] for r in results],reason='Exact rational certificate independently verified; 30s solver cap excludes read; 50s subprocess cap includes read',note='Initial default1e-6 tolerances stopped with residual; f0/o0 required and used for certificate')
  dump('evidence/EXACT_PILOT_GATE.json',gate)
 else:
  by={x['problem_id']:x for x in results}
  for i,x in status.iterrows():
   if x.problem_id in by:
    q=by[x.problem_id]
    for k in ['exact_fraction','status']:status.loc[i,k]=q[k]
    status.loc[i,'exact_source']=q['output_folder']+'/INDEPENDENT_CERTIFICATE.json';status.loc[i,'new_certified_lower_fraction']=q.get('certified_lower_fraction','');status.loc[i,'new_feasible_upper_fraction']=q.get('feasible_upper_fraction','')
  table('EXACT_REFERENCE_STATUS.csv',status);existing=frame(O/'EXACT_REFERENCE_RECHECK_RESULTS.csv');table('EXACT_REFERENCE_RECHECK_RESULTS.csv',pd.concat([existing,pd.DataFrame(results)],ignore_index=True))
 finish('EXACT_PILOT' if pilot else 'EXACT_FULL',t,{'targets':len(results),'new_exact':sum(x['status']=='PASS_EXACT_INDEPENDENT_DUAL' for x in results)})
if __name__=='__main__':main()
