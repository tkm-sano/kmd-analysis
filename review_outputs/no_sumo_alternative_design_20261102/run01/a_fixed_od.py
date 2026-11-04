"""Few-case Fraction recurrence verification, never evaluates all 2808 policies."""
from support import *
import numpy as np,itertools
def evaluate(z,rt,d):
 now=F(d);previous=rt[0];out=[]
 for order,k in enumerate(rt[1:-1],1):
  travel=F(str(z['travel'][previous,k]));arrival=now+travel;ready=F(str(z['ready'][k]));start=max(arrival,ready);service=F(str(z['service'][k]));complete=start+service;due=F(str(z['due'][k]))+service
  out.append({'task_id':str(z['nodes'][k]),'order':order,'q_PE':str(z['demand'][k]),'previous_departure_s':str(now),'OD_travel_s':str(travel),'arrival_s':str(arrival),'ready_s':str(ready),'waiting_s':str(start-arrival),'service_start_s':str(start),'service_s':str(service),'complete_s':str(complete),'deadline_D03_s':str(due),'slack_s':str(due-complete),'on_time':complete<=due})
  now=complete;previous=k
 return out,now+F(str(z['travel'][previous,rt[-1]]))
def main():
 t=time.monotonic();ops=rows(U/'review_outputs/cpx01_d11_validation_20261017/operations_2808.csv',['scenario_id','PID']);tasks=rows(U/'review_outputs/cpx01_d13_p03_d02_independent_audit_20261017/PID_TASK_DEFINITIONS.csv');taskby={x['PID']:x for x in tasks};unique={x['PID']:x for x in ops};meta={};arrays={};raw={}
 for pid,x in sorted(unique.items()):
  c=js(x['classical_source']);q=js(x['quantum_source']);raw[pid]=(c,q)
  with np.load(use(taskby[pid]['instance_path']),allow_pickle=False) as z:arrays[pid]={k:z[k].copy() for k in ['nodes','demand','ready','due','service','travel','distance']}
  check('A input hash '+pid,c['instance_sha256'],sha(resolve(taskby[pid]['instance_path'])))
  a=arrays[pid];check('A 4 tasks '+pid,4,len(a['nodes'])-1);check('A service102 '+pid,True,all(F(str(v))==102 for v in a['service'][1:]));check('A finite OD '+pid,True,bool(np.isfinite(a['travel']).all()))
  meta[pid]={'PID':pid,'parent_id':x['parent_id'],'group_id':c['group_id'],'replicate_id':x['replicate_id'],'acquired':q['final_feasible_count']>0,'same_order':c['customer_order']==(q.get('best_final_feasible_route') or {}).get('route_ids'),'input_path':str(resolve(taskby[pid]['instance_path'])),'input_sha256':c['instance_sha256']}
 table('A_INPUT_COVERAGE.csv',list(meta.values()));check('A acquisitions',64,sum(x['acquired'] for x in meta.values()));check('A operations',2808,len(ops));check('A policy conditions',36,len({x['scenario_id'] for x in ops}))
 # Select by input/policy labels only. Do not search new computed outcomes for favorable cases.
 ordered=sorted(ops,key=lambda x:(x['PID'],x['scenario_id']));selected=[]
 for label,pred in [('same_order',lambda x:meta[x['PID']]['acquired'] and meta[x['PID']]['same_order'] and int(x['t_depart'])==0),('different_order',lambda x:meta[x['PID']]['acquired'] and not meta[x['PID']]['same_order'] and int(x['t_depart'])==0),('unacquired_switch',lambda x:not meta[x['PID']]['acquired']),('positive_delay',lambda x:int(x['t_depart'])>0)]:selected.append((label,next(x for x in ordered if pred(x))))
 prior=rows(E/'A_OD_REPLAY_TASKS.csv');lookup={(x['scenario_id'],x['PID'],x['task_id']):x for x in prior};cases=[];traces=[]
 def run(label,x,route,d,basis,compare_saved=False):
  z=arrays[x['PID']];ix={str(n):i for i,n in enumerate(z['nodes'])};rt=[ix[n] for n in route];out,ret=evaluate(z,rt,d);den=sum(F(y['q_PE']) for y in out);on=sum(F(y['q_PE']) for y in out if y['on_time']);prefix=F(d)
  for k,y in enumerate(out):
   # Independent closed form: max of departure-prefix and all prior release-prefix terms.
   travelprefix=sum((F(str(z['travel'][i,j])) for i,j in zip(rt[:k+1],rt[1:k+2])),F(0));terms=[F(d)+travelprefix+(k+1)*102]
   for j in range(k+1):terms.append(F(str(z['ready'][rt[j+1]]))+(k-j+1)*102+sum((F(str(z['travel'][a,b])) for a,b in zip(rt[j+1:k+1],rt[j+2:k+2])),F(0)))
   check(label+' closed form task'+str(k),max(terms),F(y['complete_s']),1e-10)
   if compare_saved:
    old=lookup[(x['scenario_id'],x['PID'],y['task_id'])];check(label+' saved arrival '+str(k),F(old['OD_model_arrival_s']),F(y['arrival_s']),1e-8);check(label+' saved complete '+str(k),F(old['OD_model_completion_s']),F(y['complete_s']),1e-8)
   traces.append({'case_id':label,'PID':x['PID'],'scenario_id':x['scenario_id'],'basis':basis,'input_sha256':meta[x['PID']]['input_sha256'],**y})
  cases.append({'case_id':label,'PID':x['PID'],'scenario_id':x['scenario_id'],'basis':basis,'acquired':meta[x['PID']]['acquired'],'route':json.dumps(route),'departure_s':str(d),'return_s':str(ret),'denominator_PE':str(den),'on_time_PE':str(on),'F_PE':str(on/den),'on_time_tasks':sum(y['on_time'] for y in out),'tasks':len(out),'min_slack_s':str(min(F(y['slack_s']) for y in out))});return out
 for label,x in selected:
  aq=x['quantum_acquired']=='True';tc=-int(x['L'])+int(x['T_C']);tq=-int(x['L'])+int(x['T_Q']);cut=-int(x['B']);qm=aq and tq<=cut;adopt=tq if qm else max(tc,min(tq,cut));dep=max(0,adopt+int(x['T_dispatch'])+(0 if qm else int(x['T_switch'])));check(label+' policy departure',int(x['t_depart']),dep);check(label+' policy method',x['adopted_method'],'QUANTUM' if qm else 'CLASSICAL');run(label,x,json.loads(x['visit_order']),F(dep),'SAVED_POLICY_EXAMPLE',True)
 # One mechanism quartet, independent of policy adoption; successful Q route must exist.
 x=next(x for x in ordered if meta[x['PID']]['acquired'] and not meta[x['PID']]['same_order'] and int(x['t_depart'])>int(x['t_depart_C']));c,q=raw[x['PID']]
 for label,rt,d in [('CC',c['customer_order'],x['t_depart_C']),('QC',q['best_final_feasible_route']['route_ids'],x['t_depart_C']),('CQ',c['customer_order'],x['t_depart']),('QQ',q['best_final_feasible_route']['route_ids'],x['t_depart'])]:run('mechanism_'+label,x,rt,F(d),'FOUR_CONDITION_FIXTURE_NOT_NEW_COHORT_EVALUATION')
 # Exact deadline and late examples are algebraic boundary fixtures on a real frozen input.
 # They are deliberately outside D10's policy scenarios, never called observed cases.
 route=raw[x['PID']][0]['customer_order'];z=arrays[x['PID']];ix={str(n):i for i,n in enumerate(z['nodes'])};rt=[ix[n] for n in route];pref=F(0);bounds=[]
 for k,node in enumerate(rt[1:-1],1):
  pref+=F(str(z['travel'][rt[k-1],node]))+102;bounds.append(F(str(z['due'][node]))+102-pref)
 dstar=min(bounds);out=run('exact_deadline_fixture',x,route,dstar,'DERIVED_DEPARTURE_BOUNDARY_NOT_D10_POLICY');check('deadline equality exists',True,any(F(y['slack_s'])==0 for y in out));out=run('late_plus1_fixture',x,route,dstar+1,'DERIVED_DEPARTURE_BOUNDARY_NOT_D10_POLICY');check('late boundary negative',True,any(F(y['slack_s'])<0 for y in out))
 table('A_SMALL_CASES.csv',cases);table('A_SMALL_CASE_TASKS.csv',traces)
 finish('A',t,{'physical_inputs':len(meta),'parent_count':len({x['parent_id'] for x in meta.values()}),'demand_groups':len({x['group_id'] for x in meta.values()}),'acquired':sum(x['acquired'] for x in meta.values()),'unacquired':sum(not x['acquired'] for x in meta.values()),'same_order_acquired':sum(x['same_order'] for x in meta.values()),'policies':36,'potential_A2_judgments':2808,'potential_A1_mechanism_references':64*36*4,'new_evaluated_route_cases':len(cases),'new_evaluated_task_rows':len(traces),'new_full_cohort_evaluations':0,'status':'CONDITIONAL_STATIC_OD_MODEL_NOT_NATIVE_DELIVERY','boundary_examples':'derived departure fixtures, not existing policy observations'})
if __name__=='__main__':main()
