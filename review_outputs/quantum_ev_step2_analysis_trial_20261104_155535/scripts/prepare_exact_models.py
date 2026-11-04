from common import *
t=time.perf_counter();d=frame(O/'EXACT_REFERENCE_STATUS.csv',dtype=str);links=[];meta={v['run_id']:v for v in js(S/'mirror_family/MANIFEST.json')}
for i,x in d.iterrows():
 if int(x.n_customers)<100:continue
 p=pin(W/'REFERENCE'/x.problem_id/'result.json','original MIP final model linkage');r=js(p);last=r['iterations'][-1];j=int(last['iteration']);model=pin(p.parent/f'model_{j:03d}.lp','model source for independent LP',last['model_sha256']);log=pin(p.parent/f'scip_{j:03d}.log','original final MIP log',last['log_sha256']);sol=pin(p.parent/f'solution_{j:03d}.sol','original final MIP solution',last['solution_sha256']);a=arr(meta[x.problem_id]['instance_path']);coeff={(int(i),int(j)):F(c) for c,i,j in re.findall(r'^ \+ (\S+) x_(\d+)_(\d+)$',model.read_text().split('Subject To')[0],re.M)};ck('large original model coefficients/index match original NPZ',len(coeff)==len(a['nodes'])*(len(a['nodes'])-1) and all(v==F(str(a['travel'][i,j])) for (i,j),v in coeff.items()),x.problem_id);ck('large original reference problem ID matches',r['run_id']==x.problem_id,x.problem_id);links.append(dict(problem_id=x.problem_id,final_model=str(model),final_log=str(log),final_solution=str(sol)))
 if '--check-only' not in sys.argv:
  for k,v in links[-1].items():
   if k!='problem_id':d.loc[i,k]=v
if '--check-only' not in sys.argv:table('EXACT_REFERENCE_STATUS.csv',d)
table('evidence/EXACT_MODEL_LINKS.csv',links);finish('EXACT_MODEL_LINKS',t,{'large_models':len(links),'check_only':'--check-only' in sys.argv})
