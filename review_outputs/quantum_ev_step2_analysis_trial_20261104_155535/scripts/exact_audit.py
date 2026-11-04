from common import *
t0=time.perf_counter();cov=frame(P/'B_EXACT_REFERENCE_COVERAGE.csv');meta={x['run_id']:x for x in js(S/'mirror_family/MANIFEST.json')};status=[];recheck=[]
for p in (W/'FINAL_SOURCE_SNAPSHOT').rglob('*.py'):pin(p,'exact-reference frozen implementation')
for x in cov.to_dict('records'):
 pid=x['problem_id'];m=meta[pid];a=arr(pin(m['instance_path'],'B original NPZ',m['instance_sha256']));ref=js(pin(x['certificate_path'],'saved reference status',x['certificate_sha256']));old=str(x['exact_reference_available'])=='True';rt=ref.get('best_feasible_route_indices',ref.get('route_indices'));Uval=objective(a,rt) if rt is not None else None
 ck('reference witness feasible',feasible(a,rt),pid)
 if old:
  ck('old reference equals NPZ witness exactly',F(x['exact_optimum_fraction'])==Uval,pid)
  if 'lower_bound_fraction' in ref:ck('old exact lower equals witness',F(ref['lower_bound_fraction'])==Uval,pid)
 else:ck('unproved state retained',ref['proved_optimal']==False and ref['termination']=='EXACT_BOUND_WITNESS_MISMATCH',pid)
 row=dict(problem_id=pid,scale=x['scale'],n_customers=m['n'],input_sha256=m['instance_sha256'],source_certificate=x['certificate_path'],old_exact_available=old,old_exact_fraction=x['exact_optimum_fraction'],witness_upper_fraction=str(Uval),witness_upper_s=float(Uval),old_lower_fraction=ref.get('lower_bound_fraction',ref.get('old_certified_lower_bound','')),original_termination=ref.get('termination',ref.get('status','')),solver_binary_sha256=ref.get('solver_binary_sha256',''),old_proof=x['certificate_kind'],status='PASS_EXISTING_EXACT_WITNESS' if old else 'HOLD_EXACT_UNPROVED',exact_fraction=x['exact_optimum_fraction'] if old else '',exact_source='SAVED_REFERENCE' if old else '',independent_VIPR=False)
 if row['old_lower_fraction']:row['old_upper_minus_lower_s']=float(Uval-F(row['old_lower_fraction']))
 # Small input exact exhaustive recheck independent of stored scalar.
 if m['n']<=5:
  vals=[(objective(a,[0,*p,0]),[0,*p,0]) for p in itertools.permutations(range(1,m['n']+1))];v,rr=min(vals);ck('small exact enumeration reproduced',v==Uval,pid)
  recheck.append(dict(problem_id=pid,check='exact permutation enumeration',permutations=len(vals),result='PASS',difference_fraction=str(v-Uval)))
 if not old:
  original=W/'REFERENCE'/pid/'result.json';d=js(original);folder=original.parent;last=d['iterations'][-1];i=last['iteration'];model=pin(folder/f'model_{i:03d}.lp','unproved final original LP',last['model_sha256']);log=pin(folder/f'scip_{i:03d}.log','unproved original solver log',last['log_sha256']);sol=pin(folder/f'solution_{i:03d}.sol','unproved original solver solution',last['solution_sha256']);modeltext=model.read_text();logtext=log.read_text();soltext=sol.read_text()
  arcs={(int(i),int(j)):F(c) for c,i,j in re.findall(r'^ \+ (\S+) x_(\d+)_(\d+)$',modeltext.split('Subject To')[0],re.M)}
  ck('original LP complete directed arcs',len(arcs)==m['n']*(m['n']+1),pid)
  ck('original LP objective coefficients equal NPZ',all(c==F(str(a['travel'][i,j])) for (i,j),c in arcs.items()),pid)
  selected=[(int(i),int(j)) for i,j,v in re.findall(r'^x_(\d+)_(\d+)\s+(\S+)',soltext,re.M) if F(v)==1];score=sum((arcs[k] for k in selected),F(0));obj=F(re.search(r'^objective value:\s*(\S+)',soltext,re.M)[1]);lb=F(re.findall(r'^Exact Dual Bound\s*:\s*(\S+)',logtext,re.M)[-1]);pb=F(re.findall(r'^Exact Primal Bound\s*:\s*(\S+)',logtext,re.M)[-1])
  ck('solution header equals objective summation',score==obj,pid);ck('SCIP final logged primal-dual equal',lb==pb,pid);ck('saved mismatch nonzero',score!=lb,pid)
  # Displayed solution coefficients are exact rational input coefficients; verify them too.
  solcoeff={(int(i),int(j)):F(c) for i,j,c in re.findall(r'^x_(\d+)_(\d+)\s+1\s+.*?\(obj:(\S+)\)',soltext,re.M)}
  ck('solution coefficient annotations match LP',all(arcs[k]==v for k,v in solcoeff.items()),pid)
  row.update(final_model=str(model),final_log=str(log),final_solution=str(sol),log_primal_fraction=str(pb),log_dual_fraction=str(lb),solution_objective_fraction=str(score),solution_minus_log_bound_fraction=str(score-lb),solution_minus_log_bound_s=float(score-lb),old_refined_witness_minus_log_bound_s=float(Uval-lb),iterations=len(d['iterations']),scip_status_optimal='[optimal solution found]' in logtext,time_limit_reached=d['time_limit_reached'],reference_solver_version='SCIP10.0.3',coefficient_dtype=str(a['travel'].dtype),max_decimal_places=max(-__import__('decimal').Decimal(str(v)).as_tuple().exponent for v in a['travel'].flat),input_index_check='complete directed arcs; zero-based depot; full customer permutation')
  recheck.append(dict(problem_id=pid,check='saved LP/solution/log audit',result='PASS_MISMATCH_REPRODUCED',difference_fraction=str(score-lb),source_model=str(model),source_log=str(log),source_solution=str(sol)))
 status.append(row)
table('EXACT_REFERENCE_STATUS.csv',status);table('EXACT_REFERENCE_RECHECK_RESULTS.csv',recheck)
df=pd.DataFrame(status);missing=df[df.old_exact_available==False];dump('evidence/EXACT_BASELINE_SUMMARY.json',dict(inputs=len(df),old_exact=int(df.old_exact_available.sum()),unproved=len(missing),mismatch_min_s=float(missing.solution_minus_log_bound_s.min()),mismatch_max_s=float(missing.solution_minus_log_bound_s.max()),refined_gap_min_s=float(missing.old_refined_witness_minus_log_bound_s.min()),refined_gap_max_s=float(missing.old_refined_witness_minus_log_bound_s.max()),binary_hashes=missing.solver_binary_sha256.unique().tolist(),all_solver_status_optimal=bool(missing.scip_status_optimal.all()),all_timeout_false=bool((~missing.time_limit_reached).all())))
finish('EXACT_BASELINE',t0,{'old_exact':407,'missing':53})
