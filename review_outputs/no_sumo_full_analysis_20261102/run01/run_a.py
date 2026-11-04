"""All A fixed-OD decisions and counterfactual arms; no native simulation."""
from common import *
from decimal import Decimal as D,getcontext
getcontext().prec=60
def model(z,route,departure):
 ix={str(n):i for i,n in enumerate(z['nodes'])};rt=[ix[x] for x in route];check('A route permutation',list(range(1,len(rt)-1)),sorted(rt[1:-1]));now=D(str(departure));stops=[];prefix=D(0);bound=[]
 for order,(i,j) in enumerate(zip(rt,rt[1:-1]),1):
  leg=D(str(z['travel'][i,j]));arr=now+leg;start=max(arr,D(str(z['ready'][j])));service=D(str(z['service'][j]));check('service102',D(102)==service,True);c=start+service;deadline=D(str(z['due'][j]))+service;q=D(str(z['demand'][j]));prefix+=leg+service;bound.append(deadline-prefix)
  stops.append({'task_id':str(z['nodes'][j]),'stop_order':order,'previous_departure_s':str(now),'OD_travel_s':str(leg),'arrival_s':str(arr),'ready_s':str(z['ready'][j]),'waiting_s':str(start-arr),'service_start_s':str(start),'service_s':str(service),'complete_s':str(c),'due_start_s':str(z['due'][j]),'deadline_s':str(deadline),'slack_s':str(deadline-c),'late_s':str(max(D(0),c-deadline)),'q_PE':str(q),'on_time':c<=deadline,'outcome':'ON_TIME' if c<=deadline else 'LATE','status':'CONDITIONAL_FIXED_OD_COMPLETE','missing_reason':'','units':'seconds; q_PE=PE'});now=c
 den=sum(D(x['q_PE']) for x in stops);on=sum(D(x['q_PE']) for x in stops if x['on_time']);ret=now+D(str(z['travel'][rt[-2],rt[-1]]));due=D(str(z['due'][0]));summary={'departure_s':str(departure),'route':json.dumps(route,ensure_ascii=False),'denominator_PE':str(den),'on_time_PE':str(on),'denominator_count':len(stops),'on_time_count':sum(x['on_time'] for x in stops),'F_PE':float(on/den),'F_count':sum(x['on_time'] for x in stops)/len(stops),'mean_completion_s':float(sum(D(x['complete_s']) for x in stops)/len(stops)),'PE_mean_completion_s':float(sum(D(x['complete_s'])*D(x['q_PE']) for x in stops)/den),'return_s':str(ret),'return_deadline_s':str(due),'return_on_time':ret<=due,'not_completed':0,'indeterminate':0,'min_slack_s':str(min(D(x['slack_s']) for x in stops)),'first_late_departure_boundary_s':str(min(bound)),'status':'CONDITIONAL_FIXED_OD','missing_reason':'','units':'seconds; rates=fraction; demand=PE'};return summary,stops
def main():
 batch='--batch' in sys.argv;replay='--replay' in sys.argv;label='A_BATCH' if batch else 'A_REPLAY' if replay else 'A_FULL';t=time.monotonic()
 if not batch:require_batch('A')
 ops=rows(U/'review_outputs/cpx01_d11_validation_20261017/operations_2808.csv');met={x['PID']:x for x in rows(P4/'A_INPUT_COVERAGE.csv')};raw={};arr={};cache={}
 if batch:
  old=rows(P4/'A_SMALL_CASES.csv');choose={(x['PID'],x['scenario_id']) for x in old if x['basis']=='SAVED_POLICY_EXAMPLE'};ops=[x for x in ops if (x['PID'],x['scenario_id']) in choose]
 for pid in sorted({x['PID'] for x in ops}):
  x=next(x for x in ops if x['PID']==pid);raw[pid]=(js(x['classical_source']),js(x['quantum_source']));arr[pid]=npz(met[pid]['input_path'],met[pid]['input_sha256'])
 def eval(pid,route,d):
  key=(pid,tuple(route),str(d))
  if key not in cache:cache[key]=model(arr[pid],route,d)
  return cache[key]
 policy=[];base=[];arms=[];tasks=[];pairs=[];bounds=[]
 def add(scope,x,arm,rt,d,extra):
  pid=x['PID'];ss,tt=eval(pid,rt,d);ident={'comparison_scope':scope,'condition_id':x['scenario_id'],'problem_id':pid,'parent_id':x['parent_id'],'group_id':met[pid]['group_id'],'input_sha256':met[pid]['input_sha256'],'arm':arm,'source_path':str(use(x['classical_source'])),'source_sha256':SRC[str(use(x['classical_source']))]['sha256'],'quantum_source_path':str(use(x['quantum_source'])),'quantum_source_sha256':SRC[str(use(x['quantum_source']))]['sha256']};row={**ident,**ss,**extra}
  for y in tt:tasks.append({**ident,**y})
  return row
 for x in sorted(ops,key=lambda x:(x['scenario_id'],x['PID'])):
  pid=x['PID'];c,q=raw[pid];acq=q['final_feasible_count']>0;check('A acquisition row',x['quantum_acquired']=='True',acq);tc=-int(x['L'])+int(x['T_C']);tq=-int(x['L'])+int(x['T_Q']);cut=-int(x['B']);isq=acq and tq<=cut;adopt=tq if isq else max(tc,min(tq,cut));dep=max(0,adopt+int(x['T_dispatch'])+(0 if isq else int(x['T_switch'])));check('D11 departure',int(x['t_depart']),dep);check('D11 selected method',x['adopted_method'],'QUANTUM' if isq else 'CLASSICAL');qroute=q['best_final_feasible_route']['route_ids'] if acq else None;selected=qroute if isq else c['customer_order'];check('D11 route',json.loads(x['visit_order']),selected)
  dc=int(x['t_depart_C']);same=c['customer_order']==qroute if acq else None;common={'acquired':acq,'adopted_method':x['adopted_method'],'fallback_reason':x['fallback_reason'],'C_available_s':tc,'Q_available_s':tq,'adoption_deadline_s':cut,'adopt_s':adopt,'switch_s':x['t_fallback'],'L_s':x['L'],'T_Q_s':x['T_Q'],'B_s':x['B'],'route_changed_vs_C':selected!=c['customer_order'],'Q_route_differs_from_C':same is False,'timing_scope':'HYPOTHETICAL_POLICY_NOT_CPU_WALL'}
  p=add('POLICY78',x,'Q_PRIORITY',selected,dep,common);b=add('BASELINE78',x,'C_ONLY',c['customer_order'],dc,{'acquired':acq,'adopted_method':'CLASSICAL'});policy.append(p);base.append(b)
  pairs.append({'series_id':'A_POLICY','comparison_id':x['scenario_id'],'condition_id':x['scenario_id'],'problem_id':pid,'parent_id':x['parent_id'],'group_id':met[pid]['group_id'],'input_sha256':met[pid]['input_sha256'],'acquired':acq,'route_changed':p['route_changed_vs_C'],'delta_F_PE_pp':100*(p['F_PE']-b['F_PE']),'delta_F_count_pp':100*(p['F_count']-b['F_count']),'delta_mean_completion_s':p['mean_completion_s']-b['mean_completion_s'],'delta_return_s':float(D(p['return_s'])-D(b['return_s'])),'delta_departure_s':dep-dc,'status':'CONDITIONAL_FIXED_OD','missing_reason':''})
  if acq:
   quartet={}
   for name,rt,d,avail in [('CC',c['customer_order'],dc,tc),('QC',qroute,dc,tq),('CQ',c['customer_order'],dep,tc),('QQ',qroute,dep,tq)]:
    r=add('MECHANISM64',x,name,rt,d,{'acquired':True,'route_changed_vs_C':rt!=c['customer_order'],'plan_available_s':avail,'departure_before_plan_available':d<avail,'availability_feasible':d>=max(0,avail+int(x['T_dispatch'])),'counterfactual_scope':'MECHANISM_NOT_POLICY_ADOPTION'});arms.append(r);quartet[name]=r
   for effect,coefs in [('ROUTE_QC_CC',{'QC':1,'CC':-1}),('DEPARTURE_CQ_CC',{'CQ':1,'CC':-1}),('BOTH_QQ_CC',{'QQ':1,'CC':-1}),('INTERACTION',{'QQ':1,'QC':-1,'CQ':-1,'CC':1})]:
    pairs.append({'series_id':'A_MECHANISM','comparison_id':x['scenario_id']+'|'+effect,'condition_id':x['scenario_id'],'effect':effect,'problem_id':pid,'parent_id':x['parent_id'],'group_id':met[pid]['group_id'],'input_sha256':met[pid]['input_sha256'],'acquired':True,'route_changed':not same,'delta_F_PE_pp':100*sum(v*quartet[k]['F_PE'] for k,v in coefs.items()),'delta_F_count_pp':100*sum(v*quartet[k]['F_count'] for k,v in coefs.items()),'delta_mean_completion_s':sum(v*quartet[k]['mean_completion_s'] for k,v in coefs.items()),'delta_return_s':float(sum((D(v)*D(quartet[k]['return_s']) for k,v in coefs.items()),D(0))),'status':'CONDITIONAL_MECHANISM','missing_reason':''})
 # Monotonicity is checked at every cached route/departure, retaining waiting absorption.
 ordered=collections.defaultdict(list)
 for (pid,rt,d),(ss,tt) in cache.items():ordered[(pid,rt)].append((D(d),ss,tt))
 for (pid,rt),rr in ordered.items():
  rr.sort(key=lambda x:x[0])
  for lo,hi in zip(rr,rr[1:]):
   for aa,bb in zip(lo[2],hi[2]):check('departure monotone',True,D(bb['complete_s'])>=D(aa['complete_s']))
  ss=rr[0][1];bounds.append({'problem_id':pid,'parent_id':met[pid]['parent_id'],'input_sha256':met[pid]['input_sha256'],'route':json.dumps(rt),'first_late_departure_boundary_s':ss['first_late_departure_boundary_s'],'status':'CONDITIONAL_STATIC_OD_BOUNDARY'})
 folder='batch/' if batch else 'replay/' if replay else ''
 for name,xx in [('A_POLICY_DECISIONS_2808.csv',policy),('A_CLASSICAL_BASELINE_2808.csv',base),('A_MECHANISM_COMPARISON.csv',arms),('A_DELIVERY_COMPLETION_BY_STOP.csv',tasks),('A_PAIRED_PER_PROBLEM.csv',pairs),('A_DEPARTURE_BOUNDARIES.csv',bounds)]:table(folder+name,xx)
 # Batch includes real-input-derived boundary fixtures, never inject them into the cohort.
 if batch:
  fixture=[]
  for x in rows(P4/'A_SMALL_CASES.csv'):
   if x['case_id'] not in ['exact_deadline_fixture','late_plus1_fixture']:continue
   pid=x['PID'];d=F(x['departure_s']);ss,tt=model(arr[pid],json.loads(x['route']),D(d.numerator)/D(d.denominator));check('A boundary fixture',F(x['F_PE']),F(str(ss['F_PE'])),1e-12);fixture.append({'case_id':x['case_id'],**ss})
  table('batch/A_BOUNDARY_FIXTURES.csv',fixture)
 finish(label,t,{'policy_rows':len(policy),'mechanism_arm_rows':len(arms),'delivery_stop_rows':len(tasks),'unique_numerical_inputs':len(cache),'physical':len(arr),'acquired':sum(q['final_feasible_count']>0 for c,q in raw.values()),'native_runs':0,'input_hashes_checked':len(arr),'status':'PASS_ARITHMETIC_CONDITIONAL_MODEL'})
if __name__=='__main__':main()
