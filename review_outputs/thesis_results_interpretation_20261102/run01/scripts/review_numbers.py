"""Light aggregation of saved outputs and exact waiting-accounting identities."""
from evidence import *
from fractions import Fraction as Q
import numpy as np
def main():
 t=time.monotonic();checks=[]
 def ck(label,e,a,tol=0):
  ok=abs(float(e)-float(a))<=tol if isinstance(e,(int,float,Q)) and isinstance(a,(int,float,Q)) else e==a;checks.append({'check':label,'expected':str(e),'actual':str(a),'status':'PASS' if ok else 'FAIL','tolerance':tol})
 policy=rows(F/'A_POLICY_DECISIONS_2808.csv');arms=rows(F/'A_MECHANISM_COMPARISON.csv');stops=rows(F/'A_DELIVERY_COMPLETION_BY_STOP.csv');pairs=rows(F/'A_PAIRED_PER_PROBLEM.csv');ck('A policies',2808,len(policy));ck('A mechanisms',9216,len(arms));ck('A acquisitions',64,len({x['problem_id'] for x in policy if x['acquired']=='True'}));ck('A unacquired',14,len({x['problem_id'] for x in policy if x['acquired']=='False'}));ck('A all ontime',True,all(x['F_PE']=='1.0' and x['F_count']=='1.0' for x in policy));ck('A adoption',1344,sum(x['adopted_method']=='QUANTUM' for x in policy));ck('A positive departures',936,sum(Q(x['departure_s'])>0 for x in policy))
 grouped=collections.defaultdict(list)
 for x in stops:
  if x['comparison_scope']=='MECHANISM64' and x['arm'] in ['CC','CQ','QC']:grouped[(x['condition_id'],x['problem_id'],x['arm'])].append(x)
 wait=[];case=[]
 for (cond,pid,arm),xx in sorted(grouped.items()):
  if arm!='CC':continue
  cc=sorted(xx,key=lambda x:int(x['stop_order']));cq=sorted(grouped[(cond,pid,'CQ')],key=lambda x:int(x['stop_order']));delta=Q(cq[0]['previous_departure_s'])-Q(cc[0]['previous_departure_s']);cum=Q(0)
  for a,b in zip(cc,cq):
   ck('A same route task',a['task_id'],b['task_id']);absorb=Q(a['waiting_s'])-Q(b['waiting_s']);cum+=absorb;diff=Q(b['complete_s'])-Q(a['complete_s']);ck('A waiting identity',delta-cum,diff);ck('A no negative absorption',True,absorb>=0);wait.append({'condition_id':cond,'problem_id':pid,'parent_id':a['parent_id'],'input_sha256':a['input_sha256'],'task_id':a['task_id'],'stop_order':a['stop_order'],'departure_change_s':float(delta),'CC_arrival_s':float(Q(a['arrival_s'])),'CQ_arrival_s':float(Q(b['arrival_s'])),'CC_wait_s':float(Q(a['waiting_s'])),'CQ_wait_s':float(Q(b['waiting_s'])),'absorbed_at_stop_s':float(absorb),'cumulative_absorbed_s':float(cum),'completion_change_s':float(diff),'positive_departure_case':delta>0,'deadline_s':float(Q(a['deadline_s'])),'CC_completion_s':float(Q(a['complete_s'])),'CQ_completion_s':float(Q(b['complete_s'])),'status':'PASS_MODEL_EVENT_ACCOUNTING','source_key':f'MECHANISM64|{cond}|{pid}|CC/CQ|{a["task_id"]}'})
  case.append({'condition_id':cond,'problem_id':pid,'departure_change_s':float(delta),'total_wait_reduction_s':float(cum),'final_completion_change_s':float(diff),'status':'PASS_FIXED_OD_IDENTICAL_ROUTE'})
 table('tables/A_WAIT_ABSORPTION_BY_STOP.csv',wait);table('tables/A_WAIT_ABSORPTION_BY_CASE.csv',case)
 amap={(x['condition_id'],x['problem_id'],x['arm']):x for x in arms};decomp=[];changed=[]
 for (cond,pid,arm),cc in sorted(grouped.items()):
  if arm!='CC':continue
  qc=grouped[(cond,pid,'QC')];c=amap[(cond,pid,'CC')];q=amap[(cond,pid,'QC')]
  def totals(task,summary):
   last=max(task,key=lambda x:int(x['stop_order']));travel=sum((Q(x['OD_travel_s']) for x in task),Q(0))+Q(summary['return_s'])-Q(last['complete_s']);waiting=sum((Q(x['waiting_s']) for x in task),Q(0));return travel,waiting
  tc,wc=totals(cc,c);tq,wq=totals(qc,q);dd=Q(q['departure_s'])-Q(c['departure_s']);dr=Q(q['return_s'])-Q(c['return_s']);ck('A route return accounting',dd+tq-tc+wq-wc,dr);ischange=c['route']!=q['route'];decomp.append({'condition_id':cond,'problem_id':pid,'parent_id':c['parent_id'],'input_sha256':c['input_sha256'],'route_changed':ischange,'OD_travel_change_s':float(tq-tc),'waiting_change_s':float(wq-wc),'departure_change_s':float(dd),'return_change_s':float(dr),'status':'PASS_SUM_OF_SAVED_EVENTS'})
  if ischange and cond=='D10-01':
   cm={x['task_id']:x for x in cc}
   for x in qc:
    y=cm[x['task_id']];changed.append({'condition_id':cond,'problem_id':pid,'parent_id':c['parent_id'],'input_sha256':c['input_sha256'],'task_id':x['task_id'],'C_visit_order':y['stop_order'],'Q_visit_order':x['stop_order'],'C_arrival_s':y['arrival_s'],'Q_arrival_s':x['arrival_s'],'C_wait_s':y['waiting_s'],'Q_wait_s':x['waiting_s'],'C_completion_s':y['complete_s'],'Q_completion_s':x['complete_s'],'completion_change_s':float(Q(x['complete_s'])-Q(y['complete_s'])),'deadline_s':x['deadline_s'],'C_slack_s':y['slack_s'],'Q_slack_s':x['slack_s'],'status':'CONDITIONAL_FIXED_OD;20_TASKS_5_CHANGED_ROUTES'})
 table('tables/A_ROUTE_RETURN_DECOMPOSITION.csv',decomp);table('tables/A_ROUTE_CHANGED_TASK_EVENTS_20.csv',changed)
 ws=[]
 for order in range(1,5):
  rr=[x for x in wait if int(x['stop_order'])==order and x['positive_departure_case']];ws.append({'stop_order':order,'positive_departure_cases':len(rr),'fully_absorbed_cases':sum(abs(x['completion_change_s'])<1e-9 for x in rr),'partly_or_unabsorbed_cases':sum(x['completion_change_s']>1e-9 for x in rr),'mean_retained_delay_s':np.mean([x['completion_change_s'] for x in rr]),'mean_cumulative_absorbed_s':np.mean([x['cumulative_absorbed_s'] for x in rr]),'mean_original_departure_change_s':np.mean([x['departure_change_s'] for x in rr])})
 table('tables/A_WAIT_ABSORPTION_SUMMARY.csv',ws)
 margin=[]
 for pid in sorted({x['problem_id'] for x in policy}):
  rr=[x for x in policy if x['problem_id']==pid];margin.append({'problem_id':pid,'parent_id':rr[0]['parent_id'],'input_sha256':rr[0]['input_sha256'],'min_slack_over36_s':min(float(x['min_slack_s']) for x in rr),'rate_all36_percent':100,'conditions':36})
 table('tables/A_MIN_DEADLINE_SLACK_78.csv',margin);ck('A minimum policy slack',3133.461531014295,min(x['min_slack_over36_s'] for x in margin),1e-8)
 plan=rows(F/'B_PLAN_REFERENCES_36800.csv');initial={x['problem_id']:json.loads(x['initial_route']) for x in rows(F/'B_CLASSICAL_INITIAL_BASELINES.csv')};bp=[];fitcheck=[];seen=set()
 for x in plan:
  value=Q(x['objective_fraction']);base=Q(x['classical_initial_fraction']);quality='IMPROVED' if value<base else 'EQUAL' if value==base else 'WORSE';same=json.loads(x['route_indices'])==initial[x['problem_id']];bp.append({'problem_id':x['problem_id'],'parent_id':x['parent_id'],'input_sha256':x['input_sha256'],'scale':x['scale'],'config_id':x['config_id'],'measurement_rep':x['measurement_rep'],'quality_class':quality,'same_route_as_initial':same,'delta_s':float(value-base),'status':'PASS_SAVED_SCALAR_AND_ROUTE_READBACK'})
  if x['family']=='mirror_family' and x['source_path'] not in seen:
   seen.add(x['source_path']);raw=js(use(x['source_path'],x['source_sha256']));orb=Q(raw['orbit_optimum_seconds']);ini=Q(raw['records'][0]['initial_seconds']);ck('B mirror exact initial equals orbit',ini,orb);fitcheck.append({'problem_id':x['problem_id'],'config_id':x['config_id'],'input_sha256':x['input_sha256'],'initial_fraction':str(ini),'orbit_min_fraction':str(orb),'exactly_equal':ini==orb,'source_path':str(use(x['source_path'])),'source_sha256':x['source_sha256']})
 table('tables/B_PLAN_QUALITY_CLASSES.csv',bp);table('tables/B_MIRROR_SUPPORT_EXACT_CHECK.csv',fitcheck);summary=[]
 for scale in [f'R{i}' for i in range(6)]+['ALL']:
  for cfg in sorted({x['config_id'] for x in bp}):
   rr=[x for x in bp if x['config_id']==cfg and (scale=='ALL' or x['scale']==scale)];summary.append({'scale':scale,'config_id':cfg,'physical_inputs':len({x['problem_id'] for x in rr}),'plan_references':len(rr),'improved_refs':sum(x['quality_class']=='IMPROVED' for x in rr),'equal_refs':sum(x['quality_class']=='EQUAL' for x in rr),'worse_refs':sum(x['quality_class']=='WORSE' for x in rr),'same_route_refs':sum(x['same_route_as_initial'] for x in rr),'mean_delta_s':math.fsum(x['delta_s'] for x in rr)/len(rr),'scope':'saved best plan;10 measurement reps per physical input'})
 table('tables/B_IMPROVE_EQUAL_WORSE_COUNTS.csv',summary);ck('B references',36800,len(plan));six={x['config_id'] for x in summary if x['scale']=='ALL' and x['equal_refs']==4600};ck('B equal settings',6,len(six));active=rows(F/'B_ACTIVE_GRID_SELECTION.csv');ck('B active selected zero',460,sum(float(x['selected_t'])==0 for x in active));coverage=rows(F/'B_EXACT_REFERENCE_COVERAGE.csv');ck('B exact available',407,sum(x['exact_reference_available']=='True' for x in coverage))
 ener=rows(F/'C_T08_ENERGY_FULL.csv');lp={(x['physical_instance_id'],x['rolling_case']):x for x in ener if x['dataset']=='CLASSICAL' and x['scenario_id']=='COND_LP_REF'};cc=[]
 for roll in ['CRR_LOWER_BOUND','CRR_UPPER_BOUND']:
  rr=[x for x in ener if x['dataset']=='CLASSICAL' and x['scenario_id']=='COND_S200_REF' and x['rolling_case']==roll];baseWh=math.fsum(float(lp[(x['physical_instance_id'],roll)]['recomputed_DC_Wh']) for x in rr);saveWh=math.fsum(float(lp[(x['physical_instance_id'],roll)]['recomputed_DC_Wh'])-float(x['recomputed_DC_Wh']) for x in rr);cc.append({'rolling_case':roll,'trajectories':len(rr),'mass_reduction_kg':float(next(iter(lp.values()))['pack_mass_kg'])-float(rr[0]['pack_mass_kg']),'baseline_Wh':baseWh,'saving_Wh':saveWh,'weighted_percent':100*saveWh/baseWh})
 ck('C T08 mass',5.448297415,cc[0]['mass_reduction_kg'],1e-9);ck('C lower DC saving',5941.5559753816215,cc[0]['saving_Wh'],1e-8);ck('C lower weighted percent',.4125790100606282,cc[0]['weighted_percent'],1e-10);table('tables/C_T08_INDEPENDENT_SUMMARY.csv',cc);pack=rows(F/'C_T09_COMPONENTS_183.csv');ck('C183 pack missing',183,sum(x['complete_pack_mass_kg']=='' for x in pack));ck('C footprint FAIL',1,sum(x['overlap_condition']=='FAIL_IF_SAME_STACK_FOOTPRINT' for x in pack));table('REVIEW_NUMERICAL_CHECKS.csv',checks)
 failed=[x for x in checks if x['status']=='FAIL'];finish('REVIEW',t,{'checks':len(checks),'failures':len(failed),'A_positive_mechanism_cases':sum(x['departure_change_s']>0 for x in case),'A_wait_stages':ws,'B_equal_settings':sorted(six),'B_equal_objective_but_different_route_refs':sum(x['quality_class']=='EQUAL' and not x['same_route_as_initial'] for x in bp),'C_review':cc,'new_scientific_runs':0})
 if failed:raise RuntimeError('Review mismatch; do not draft as PASS')
if __name__=='__main__':main()
