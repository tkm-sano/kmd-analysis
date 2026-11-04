"""Independent max-plus, fsum and mass-linear DC readback. No primary evaluators."""
from common import *
import numpy as np,pandas as pd
def main():
 batch='--batch' in sys.argv;label='VERIFY_BATCH' if batch else 'VERIFY_FULL';folder='batch/' if batch else '';t0=time.monotonic();n=0;errors=[];ledger=[]
 def ck(k,e,a,tol=0,location=''):
  nonlocal n
  n+=1
  ok=abs(float(e)-float(a))<=tol if isinstance(e,(int,float,F)) and isinstance(a,(int,float,F)) else e==a
  if not ok:errors.append({'check':k,'expected':str(e),'actual':str(a),'location':location,'tolerance':tol})
 # A recurrence is independently unrolled into a maximum over release prefixes.
 aa={x['PID']:x for x in rows(P4/'A_INPUT_COVERAGE.csv')};arrays={};summaries={}
 for name in ['A_POLICY_DECISIONS_2808.csv','A_CLASSICAL_BASELINE_2808.csv','A_MECHANISM_COMPARISON.csv']:
  for x in rows(O/(folder+name)):summaries[(x['comparison_scope'],x['condition_id'],x['problem_id'],x['arm'])]=x
 arows=rows(O/(folder+'A_DELIVERY_COMPLETION_BY_STOP.csv'));by=collections.defaultdict(list)
 for x in arows:by[(x['comparison_scope'],x['condition_id'],x['problem_id'],x['arm'])].append(x)
 acache={}
 for key,xx in by.items():
  x=summaries[key];pid=x['problem_id']
  if pid not in arrays:arrays[pid]=npz(aa[pid]['input_path'],aa[pid]['input_sha256'])
  z=arrays[pid];lookup={str(v):i for i,v in enumerate(z['nodes'])};rt=[lookup[v] for v in json.loads(x['route'])];departure=F(x['departure_s']);cachekey=(pid,tuple(rt),departure)
  if cachekey not in acache:
   completions=[];starts=[];arrivals=[]
   for k,j in enumerate(rt[1:-1]):
    arrival=(departure if k==0 else completions[-1])+F(str(z['travel'][rt[k],j]));terms=[departure+sum((F(str(z['travel'][a,b])) for a,b in zip(rt[:k+1],rt[1:k+2])),F(0))+(k+1)*102]
    for q in range(k+1):terms.append(F(str(z['ready'][rt[q+1]]))+(k-q+1)*102+sum((F(str(z['travel'][a,b])) for a,b in zip(rt[q+1:k+1],rt[q+2:k+2])),F(0)))
    comp=max(terms);completions.append(comp);starts.append(comp-102);arrivals.append(arrival)
   acache[cachekey]=(arrivals,starts,completions)
  arrivals,starts,completions=acache[cachekey];on=F(0);den=F(0)
  for k,y in enumerate(sorted(xx,key=lambda x:int(x['stop_order']))):
   q=F(y['q_PE']);den+=q;due=F(str(z['due'][rt[k+1]]))+102;ont=completions[k]<=due
   for field,val in [('arrival_s',arrivals[k]),('service_start_s',starts[k]),('complete_s',completions[k]),('deadline_s',due),('late_s',max(F(0),completions[k]-due))]:ck('A '+field,val,F(y[field]),1e-9,str(key)+y['task_id'])
   ck('A deadline equality',ont,y['on_time']=='True',location=str(key));on+=q if ont else 0
  ret=completions[-1]+F(str(z['travel'][rt[-2],0]));ck('A return',ret,F(x['return_s']),1e-9,str(key));ck('A fixed denominator',den,F(x['denominator_PE']));ck('A PE numerator',on,F(x['on_time_PE']));ck('A PE fraction',float(on/den),float(x['F_PE']),1e-12)
 ck('A all summaries linked',len(summaries),len(by))
 if batch:
  for x in rows(O/'batch/A_BOUNDARY_FIXTURES.csv'):ck('A algebraic boundary '+x['case_id'],0 if x['case_id']=='exact_deadline_fixture' else -1,float(x['min_slack_s']),1e-10)
 ledger.append({'series':'A','rows':len(arows),'checks_through':n,'status':'PASS' if not errors else 'FAIL'})
 # B independent double precision fsum of original NPZ arcs + canonical rational references.
 bm={x['run_id']:x for x in js(S/'mirror_family/MANIFEST.json')};arrays={};brows=rows(O/(folder+'B_PLAN_REFERENCES_36800.csv'));initial={};bgroup=collections.Counter()
 for x in brows:
  pid=x['problem_id']
  if pid not in arrays:
   m=bm[pid];arrays[pid]=npz(m['instance_path'],m['instance_sha256']);initial[pid]=js(U/'review_outputs/whole_roster_swap_qaoa_through_r5_20261101/RUNS'/pid/'RESULT.json')
  a=arrays[pid];rt=json.loads(x['route_indices']);v=math.fsum(float(a['travel'][i,j]) for i,j in zip(rt,rt[1:]));d=math.fsum(float(a['distance'][i,j]) for i,j in zip(rt,rt[1:]));value=F(x['objective_fraction']);ci=F(x['classical_initial_fraction']);ck('B original objective',float(value),v,1e-7,pid+x['config_id']);ck('B distance',float(x['OD_distance_m']),d,1e-6);ck('B delta',float(value-ci),float(x['delta_objective_vs_initial_s']),1e-8);ck('B permutation',list(range(1,int(x['n_customers'])+1)),sorted(rt[1:-1]));ck('B acquired feasible',True,x['plan_acquired']=='True' and x['feasible']=='True')
  if x['exact_optimum_fraction']:
   ref=F(x['exact_optimum_fraction']);ck('B optimal match',ref==value,x['optimal_match']=='True');ck('B gap',float(100*(value-ref)/ref),float(x['global_gap_percent']),1e-8)
  else:ck('B missing gap retained','',x['global_gap_percent']);ck('B missing match retained','',x['optimal_match'])
  bgroup[(pid,x['config_id'])]+=1
 ck('B ten repetitions',True,all(v==10 for v in bgroup.values()));ledger.append({'series':'B','rows':len(brows),'checks_through':n,'status':'PASS' if not errors else 'FAIL'})
 # C independent linear mass coefficients, using original samples and separate summation.
 ts=rows(O/(folder+'C_T08_ENERGY_FULL.csv'));bs=rows(O/(folder+'C_BRIDGE_MASS_DC_FULL.csv'));todo=collections.defaultdict(list)
 for x in ts:todo[x['input_sha256']].append(('T08',x))
 for x in bs:todo[x['input_sha256']].append(('BRIDGE',x))
 maxerr=0.
 for h,rr in sorted(todo.items()):
  df=pd.read_csv(use(rr[0][1]['trajectory_path'],h),usecols=['timestamp_s','speed_m_s']);v=df.speed_m_s.to_numpy();tt=df.timestamp_s.to_numpy();ck('C no missing times',True,bool(np.all(np.diff(tt)==1)));current=v[1:];kin=.5*(current**2-v[:-1]**2);aero=.5*1.2041*1.175*current**3;rot=61*kin;store={}
  def independent(m,p):
   key=(m,p)
   if key not in store:
    perkg=9.80665*(.005+(.01+.0095*(3.6*current/100)**2)/p)*current+kin;store[key]=float(np.maximum(m*perkg+aero+rot,0).sum(dtype=np.float64)/(.9*3600))
   return store[key]
  for kind,x in rr:
   if kind=='T08':
    val=independent(float(x['running_mass_kg']),4.5 if x['rolling_case']=='CRR_LOWER_BOUND' else 2.6);e=abs(val-float(x['recomputed_DC_Wh']));maxerr=max(maxerr,e);ck('C independent T08 DC',val,float(x['recomputed_DC_Wh']),1e-7,x['condition_id'])
   else:
    base=independent(float(x['reference_running_mass_kg']),float(x['pressure_bar']));alt=independent(float(x['S_running_mass_probe_kg']),float(x['pressure_bar']));ck('C independent bridge saving',base-alt,float(x['recomputed_saving_Wh']),1e-7,x['condition_id']);ck('C signed boundary identity',float(x['known_mass_boundary_kg'])-float(x['unknown_mass_difference_probe_kg']),float(x['net_mass_saving_probe_kg']),1e-8);e=max(abs(base-float(x['recomputed_baseline_DC_Wh'])),abs(alt-float(x['recomputed_S_DC_Wh'])));maxerr=max(maxerr,e);ck('C independent endpoint energies',0,e,1e-7)
 pack=rows(O/(folder+'C_T09_COMPONENTS_183.csv'));fails=0
 for x in pack:
  f=lambda k:F(x[k]);Q=f('gross_design_Wh')/f('mean_voltage_design_V');mp=Q/f('q_reference_Ah_kg')/f('positive_utilization');mn=Q*f('NP_after_formation')/f('negative_q_Ah_kg')/(1-f('negative_unavailable_fraction'));fp=F('.96') if x['series'].startswith('A_') else F('.75');ap=f('positive_face_area_m2');an=f('negative_face_area_m2');ep=f('positive_porosity');en=f('negative_porosity');expected={'positive_coating_kg':mp/fp,'negative_coating_kg':mn/F('.98'),'Al_mass_kg':ap/2*f('Al_thickness_m')*2699,'Cu_mass_kg':an/2*f('Cu_thickness_m')*8960,'separator_dry_mass_kg':max(ap,an)*f('separator_areal_mass_kg_m2'),'liquid_mass_kg':(mp/fp/4458*ep/(1-ep)+mn/F('.98')/2200*en/(1-en)+max(ap,an)*F('.000025')*F('.41')+f('extra_liquid_volume_m3'))*1300}
  for k,val in expected.items():ck('T09 independent '+k,float(val),float(x[k]),1e-8,x['condition_id'])
  ck('T09 independent sum',float(sum(expected.values(),F(0))),float(x['known_sum_recalculated_kg']),1e-8);ck('T09 unknown preserved','',x['complete_pack_mass_kg']);fails+=x['overlap_condition']=='FAIL_IF_SAME_STACK_FOOTPRINT'
 ck('T09 failure retained',1,fails);ledger.append({'series':'C','rows':len(ts)+len(bs)+len(pack),'checks_through':n,'status':'PASS' if not errors else 'FAIL'})
 if not batch:
  ck('A policy count',2808,len(rows(O/'A_POLICY_DECISIONS_2808.csv')));ck('A arms count',9216,len(rows(O/'A_MECHANISM_COMPARISON.csv')));ck('B reference count',36800,len(brows));ck('B exact input count',407,len({x['problem_id'] for x in brows if x['exact_optimum_fraction']}));ck('C T08 full rows',4464,len(ts));ck('C bridge full rows',25760,len(bs));ck('C T09 full rows',183,len(pack))
 table(label+'_ERRORS.csv',errors);table(label+'_BY_SERIES.csv',ledger);summary={'checks':n,'failures':len(errors),'max_C_independent_DC_error_Wh':maxerr,'metrics':metric(t0),'code_independence':'Does not import run_a, run_b or run_c; max-plus, fsum and mass-linear DC formulas used'};dump(label+'_RUN.json',summary);dump(label+'_SOURCES.json',list(SRC.values()));print(json.dumps(summary),flush=True)
 if errors:raise RuntimeError('Independent verification mismatch; gate closed')
if __name__=='__main__':main()
