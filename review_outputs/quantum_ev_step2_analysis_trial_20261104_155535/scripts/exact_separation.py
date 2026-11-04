from common import *
from concurrent.futures import ThreadPoolExecutor

def mincut(cap,n,sink):
 # Exact Edmonds-Karp with early exit at1: only cuts<1 matter.
 residual={i:{} for i in range(n)}
 for (i,j),v in cap.items():
  if v>0:residual[i][j]=residual[i].get(j,F(0))+v;residual[j].setdefault(i,F(0))
 flow=F(0)
 while flow<1:
  parent={0:None};queue=collections.deque([0])
  while queue and sink not in parent:
   i=queue.popleft()
   for j,v in residual[i].items():
    if v>0 and j not in parent:parent[j]=i;queue.append(j)
  if sink not in parent:return flow,set(parent)
  amount=1-flow;j=sink
  while j:amount=min(amount,residual[parent[j]][j]);j=parent[j]
  j=sink
  while j:i=parent[j];residual[i][j]-=amount;residual[j][i]=residual[j].get(i,F(0))+amount;j=i
  flow+=amount
 return flow,None

def independent_verify(a,cuts,y,primal,oldub):
 n=len(a['travel']);h=y.get('horizon',F(0));valid=h<=0 and all(y.get(f'sec_{k}',F(0))<=0 for k in range(len(cuts)));assert valid
 lower=sum((v for k,v in y.items() if k.startswith(('out_','in_'))),F(0))+h*(32400-102*(n-1))+sum((y.get(f'sec_{k}',F(0))*(len(s)-1) for k,s in enumerate(cuts)),F(0));sets=[(set(s),y.get(f'sec_{k}',F(0))) for k,s in enumerate(cuts) if y.get(f'sec_{k}',0)!=0]
 for i in range(n):
  for j in range(n):
   if i==j:continue
   c=F(str(a['travel'][i,j]));rc=c*(1-h)-y.get(f'out_{i}',F(0))-y.get(f'in_{j}',F(0))-sum((v for s,v in sets if i in s and j in s),F(0));lower+=min(F(0),rc)
 integral=all(v in (0,1) for v in primal.values());succ={i:j for (i,j),v in primal.items() if v==1};rt=[0]
 for _ in range(n):
  if rt[-1] not in succ:break
  rt.append(succ[rt[-1]])
  if rt[-1]==0:break
 full=integral and feasible(a,rt);up=min(oldub,objective(a,rt)) if full else oldub
 assert lower<=up,(lower-up)
 return lower,up,rt if full else None

def case(x):
 pid=x['problem_id'];folder=O/'experiments/exact_separation'/pid;folder.mkdir(parents=True,exist_ok=True);start=time.perf_counter();m=json.loads((S/'mirror_family/MANIFEST.json').read_text());m=next(q for q in m if q['run_id']==pid);a=arr(m['instance_path']);n=len(a['travel']);ref=js(W/'REFERENCE'/pid/'result.json');cuts=[list(s) for s in ref.get('subtour_cuts',[])];seen={tuple(sorted(s)) for s in cuts};oldub=F(x['witness_upper_fraction']);up=oldub;oldmodel=Path(x['final_model']).read_text();base=oldmodel.split('Bounds')[0];base=re.sub(r'^ sec_\d+:.*\n','',base,flags=re.M);tail=oldmodel[oldmodel.index('Bounds'):];steps=[];lastL=F(x.get('old_lower_fraction') or 0);cert=None;reason='ITERATION_LIMIT';cpu=sorted(os.sched_getaffinity(0))[int(pid.split('_')[1])%min(4,len(os.sched_getaffinity(0)))];memory_max=0
 for it in range(8):
  if time.perf_counter()-start>180:reason='CASE_WALL_LIMIT';break
  trial=folder/f'iter{it:02d}';trial.mkdir(exist_ok=True);lp=trial/'model.lp';extras=''.join(' sec_'+str(k)+': '+' + '.join(f'x_{i}_{j}' for i in s for j in s if i!=j)+f' <= {len(s)-1}\n' for k,s in enumerate(cuts));lp.write_text(base+extras+tail)
  cmd=['/usr/bin/time','-v','-o',str(trial/'usage.txt'),'taskset','-c',str(cpu),str(BINS/'soplex'),'--readmode=1','--solvemode=2','-f0','-o0','-s0','-t30','-c',f'-X={trial}/primal.sol',f'-Y={trial}/dual.sol',str(lp)];t=time.perf_counter()
  try:
   with (trial/'solve.log').open('w') as f:proc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=50)
   code=proc.returncode
  except subprocess.TimeoutExpired:code='TIMEOUT'
  if not (trial/'dual.sol').is_file() or not (trial/'primal.sol').is_file():reason='NO_RATIONAL_SOLUTION';break
  ps={(int(i),int(j)):F(v) for i,j,v in re.findall(r'^x_(\d+)_(\d+)\s+(\S+)',(trial/'primal.sol').read_text(),re.M)};ys={k:F(v) for k,v in re.findall(r'^((?:out|in|sec)_\d+|horizon)\s+(\S+)',(trial/'dual.sol').read_text(),re.M)}
  lower,up,route=independent_verify(a,cuts,ys,ps,up);lastL=max(lastL,lower);usage=(trial/'usage.txt').read_text();rss=re.search(r'Maximum resident set size \(kbytes\): (\d+)',usage);memory_max=max(memory_max,int(rss[1])*1024 if rss else 0)
  step=dict(iteration=it,wall_s=time.perf_counter()-t,returncode=code,lower_fraction=str(lower),upper_fraction=str(up),gap_fraction=str(up-lower),cuts=len(cuts),primal_integer=all(v in (0,1) for v in ps.values()),single_tour=route is not None,route=route,model_sha256=sha(lp));steps.append(step);(trial/'VERIFIED.json').write_text(json.dumps(step,indent=2));(trial/'CUTS.json').write_text(json.dumps(cuts))
  if lower==up:reason='EXACT_DUAL_EQUALS_FEASIBLE_TOUR';cert=trial;break
  fresh=[]
  for sink in range(1,n):
   flow,side=mincut(ps,n,sink)
   if side is not None and flow<1:
    s=set(range(n))-side if len(side)>n/2 else side;key=tuple(sorted(s))
    if 1<len(s)<n and key not in seen:seen.add(key);fresh.append(list(key))
  if not fresh:reason='FRACTIONAL_DFJ_NO_VIOLATED_SEC';break
  cuts.extend(fresh)
 result=dict(problem_id=pid,method='exact rational DFJ LP separation plus independently verified dual',status='PASS_EXACT_INDEPENDENT_DUAL' if cert else 'HOLD_BOUNDED',exact_fraction=str(up) if cert else '',certified_lower_fraction=str(lastL),feasible_upper_fraction=str(up),gap_upper_s=float(up-lastL),gap_upper_fraction=str(up-lastL),old_upper_minus_new_upper_s=float(oldub-up),iterations=len(steps),final_cuts=len(cuts),wall_s=time.perf_counter()-start,peak_RSS_bytes=memory_max,reason=reason,certificate_path=str(cert/'VERIFIED.json') if cert else str(folder/'RESULT.json'),steps=steps)
 (folder/'RESULT.json').write_text(json.dumps(result,indent=2));return result

def main():
 t=time.perf_counter();status=frame(O/'EXACT_REFERENCE_STATUS.csv');target=status[status.old_exact_available==False].to_dict('records');pilot='--pilot' in sys.argv
 if pilot:target=[next(x for x in target if x['scale']==sc) for sc in ['R4','R5']]
 else:ck('separation pilot approved',js(O/'evidence/EXACT_SEPARATION_PILOT_GATE.json')['proceed'])
 results=[]
 with ThreadPoolExecutor(max_workers=2 if pilot else 4) as pool:
  for q in pool.map(case,target):results.append(q);print(q['problem_id'],q['status'],q['iterations'],flush=True)
 table('evidence/EXACT_SEPARATION_PILOT.csv' if pilot else 'evidence/EXACT_SEPARATION_FULL.csv',[{k:v for k,v in q.items() if k!='steps'} for q in results])
 if pilot:dump('evidence/EXACT_SEPARATION_PILOT_GATE.json',dict(proceed=all(q['wall_s']<180 and q['peak_RSS_bytes']<2**31 for q in results),results=[{k:v for k,v in q.items() if k!='steps'} for q in results]))
 else:
  by={q['problem_id']:q for q in results}
  for i,x in status.iterrows():
   if x.problem_id in by:
    q=by[x.problem_id]
    for k in ['status','exact_fraction']:status.loc[i,k]=q[k]
    status.loc[i,'exact_source']=q['certificate_path'];status.loc[i,'new_certified_lower_fraction']=q['certified_lower_fraction'];status.loc[i,'new_feasible_upper_fraction']=q['feasible_upper_fraction']
  table('EXACT_REFERENCE_STATUS.csv',status);table('EXACT_REFERENCE_RECHECK_RESULTS.csv',pd.concat([frame(O/'EXACT_REFERENCE_RECHECK_RESULTS.csv'),pd.DataFrame([{k:v for k,v in q.items() if k!='steps'} for q in results])],ignore_index=True))
 finish('EXACT_SEPARATION_PILOT' if pilot else 'EXACT_SEPARATION_FULL',t,dict(targets=len(results),new_exact=sum(q['status']=='PASS_EXACT_INDEPENDENT_DUAL' for q in results)))
if __name__=='__main__':main()
