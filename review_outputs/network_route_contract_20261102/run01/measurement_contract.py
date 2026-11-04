"""Accepted model definitions. These functions do not observe a real handover."""
from decimal import Decimal as D
import math
def measure_service(c):
 out={'task_id':c.get('task_id','task'),'model_version':'SERVICE102_V1','physical_arrival_s':c.get('physical_arrival_observed_s'),'native_stop_started_s':c.get('stop_started_s'),'native_resume_s':c.get('stop_ended_s'),'first_positive_speed_sample_s':c.get('first_positive_speed_sample_s'),'model_start_s':None,'model_complete_s':None,'candidate_complete_s':None,'outcome':'INDETERMINATE','status':'HOLD','interpretation':'MODEL_DELIVERY_COMPLETION_NOT_OBSERVED_HANDOVER','return_status':c.get('return_status','UNKNOWN')}
 if c.get('known_unreachable') or c.get('absence_proven'):
  out.update(outcome='NOT_COMPLETED',status='CONDITIONAL',reason='PROVEN_UNREACHED_OR_UNSERVED');return out
 started=c.get('stop_started_s')
 if started is None:out['reason']='MISSING_STOP_RECORD_IS_NOT_PROOF_OF_NO_SERVICE';return out
 a=D(str(started));r=D(str(c.get('ready_s',0))) if c.get('series')=='A' else D(0);s=max(a,r);finish=s+D(102);out['candidate_complete_s']=float(finish)
 if c.get('service_s',102)!=102:out.update(status='FAIL',reason='SERVICE_DURATION_DEFINITION_MISMATCH');return out
 if not c.get('task_binding_verified'):
  out['reason']='TASK_ORDER_OR_ACTIVITY_BINDING_NOT_VERIFIED';return out
 if c.get('planned_lane')!=c.get('observed_lane'):
  out.update(status='FAIL',reason='LOCATION_LANE_MISMATCH');return out
 if c.get('observed_pos_m') is None:out['reason']='MISSING_STOP_POSITION';return out
 end=D(str(c['planned_end_m']));start=D(str(c.get('planned_start_m',max(0,float(end)-.2))));pos=D(str(c['observed_pos_m']))
 if not start<=pos<=end:out.update(status='FAIL',reason='OUTSIDE_DECLARED_STOP_RANGE');return out
 ended=c.get('stop_ended_s');coverage=c.get('stopped_coverage_end_s');coverage=ended if ended is not None else coverage
 if coverage is None or c.get('continuous_stop_verified') is not True:out['reason']='CONTINUOUS_SERVICE_INTERVAL_NOT_PROVEN';return out
 coverage=D(str(coverage));horizon=D(str(c['observation_end_s']));coverage=min(coverage,horizon)
 if ended is not None and D(str(ended))<finish:
  out.update(status='FAIL',outcome='NOT_COMPLETED',reason='SERVICE_INTERRUPTED_BY_EARLY_DEPARTURE');return out
 if coverage<finish:
  future=c.get('series')=='A' and D(str(c['deadline_s']))>horizon
  out.update(status='CONDITIONAL',outcome='INDETERMINATE' if future else 'NOT_COMPLETED',reason='RIGHT_CENSORED_IN_PROGRESS_FUTURE_DEADLINE' if future else 'NOT_COMPLETED_BY_EVALUATION_HORIZON',service_state='IN_PROGRESS',model_start_s=float(s));return out
 out.update(status='CONDITIONAL',model_start_s=float(s),model_complete_s=float(finish),service_state='COMPLETED',reason='102S_CONTINUOUS_MODEL_SERVICE_AT_BOUND_STOP')
 out['outcome']=('ON_TIME' if finish<=D(str(c['deadline_s'])) else 'LATE') if c.get('series')=='A' else 'COMPLETED_NO_CUSTOMER_DEADLINE'
 return out
def aggregate(tasks):
 if not tasks or any(x['q_PE']<=0 for x in tasks):raise ValueError('Fixed positive demand required')
 den=sum(x['q_PE'] for x in tasks);ontime=sum(x['q_PE'] for x in tasks if x['outcome']=='ON_TIME');unknown=sum(x['q_PE'] for x in tasks if x['outcome']=='INDETERMINATE');u=any(x['outcome']=='INDETERMINATE' for x in tasks)
 return {'denominator_PE':den,'denominator_count':len(tasks),'on_time_PE':ontime,'unknown_PE':unknown,'F_PE':None if u else ontime/den,'F_count':None if u else sum(x['outcome']=='ON_TIME' for x in tasks)/len(tasks),'F_PE_lower':ontime/den,'F_PE_upper':(ontime+unknown)/den}
def energy_pair_eligible(demand,served_C,served_Q,return_C,return_Q,boundary_C,boundary_Q):
 return set(demand)==set(served_C)==set(served_Q) and return_C and return_Q and boundary_C==boundary_Q=='OBSERVED_WINDOW_CONTROLLED_DC'
def scalar_energy(t,v,m,p,arrival=None):
 if len(t)!=len(v) or len(t)<2 or any(not math.isfinite(float(x)) for x in [*t,*v,m,p]) or any(x<0 for x in v) or m<=0 or p<=0 or any(b-a!=1 for a,b in zip(t,t[1:])):raise ValueError('Invalid DC input; no repair')
 if arrival is not None and arrival<t[-1]:raise ValueError('Arrival before last sample')
 out={k:[] for k in ['W1','W2','W3','W4','DC']}
 for i in range(1,len(t)):
  ds=v[i]*(t[i]-t[i-1]);dv2=v[i]**2-v[i-1]**2
  q=[m*9.80665*(.005+(.01+.0095*(3.6*v[i]/100)**2)/p)*ds,.5*1.2041*1.175*v[i]**2*ds,.5*m*dv2,.5*61*dv2]
  for k,x in zip(['W1','W2','W3','W4'],q):out[k].append(x/3600)
  out['DC'].append(max(math.fsum(q),0)/(.9*3600))
 total={k:math.fsum(x) for k,x in out.items()};total.update(distance_m=math.fsum(v[1:]),stock_Wh=18000-total['DC'],stock_status='FAIL' if total['DC']>18000 else 'PASS',terminal_gap_s=arrival-t[-1] if arrival is not None else None,terminal_gap_Wh=None,boundary='OBSERVED_WINDOW_CONTROLLED_DC');return total
