"""Explicit input, event and energy adapters; frozen scientific kernel unchanged."""
import math
from decimal import Decimal as D
import numpy as np
from common import canon,digest

REQUIRED=('series_id','input_sha256','vehicle','vtype_sha256','road_sha256','road_edges','stops','traffic','simulation','environment_sha256','generator_sha256')
def complete_id(payload):
 missing=[k for k in REQUIRED if k not in payload or payload[k] is None]
 if not payload.get('road_edges'):missing.append('road_edges_not_materialized')
 if payload.get('unbound'):missing.extend(payload['unbound'])
 if missing:return None,sorted(set(missing))
 return 'RUN-'+digest(payload),[]
def operation_policy(L,TQ,B,acquired,TC=120,switch=600,dispatch=120):
 tc=-D(str(L))+D(str(TC));tq=-D(str(L))+D(str(TQ));cut=-D(str(B))
 if acquired and tq<=cut:return {'method':'QUANTUM','availability_s':tq,'cutoff_s':cut,'switch_s':None,'adopt_s':tq,'departure_s':max(D(0),tq+dispatch),'reason':'AVAILABLE_BY_DEADLINE'}
 fallback=min(tq,cut) if not acquired else cut
 return {'method':'CLASSICAL','availability_s':tc,'cutoff_s':cut,'switch_s':fallback,'adopt_s':max(tc,fallback),'departure_s':max(D(0),max(tc,fallback)+switch+dispatch),'reason':'FAILURE_KNOWN' if not acquired and tq<=cut else 'DEADLINE_NO_AVAILABLE_QUANTUM'}
def delivery_event(*,stop_start,stop_end,ready,service,deadline,observation_complete=True,physical_arrival=None,resume=None):
 vals=[x for x in [stop_start,stop_end,ready,service,deadline,physical_arrival,resume] if x is not None]
 if any(not math.isfinite(float(x)) for x in vals) or service<=0:raise ValueError('Invalid event values')
 if stop_start is None:
  return {'physical_arrival_s':physical_arrival,'stop_start_s':None,'work_start_model_s':None,'work_complete_model_s':None,'stop_end_s':stop_end,'resume_s':resume,'outcome':'NOT_COMPLETED' if observation_complete else 'INDETERMINATE','formal_outcome':'HOLD','model_status':'NO_STOP_OBSERVED'}
 start=max(D(str(stop_start)),D(str(ready if ready is not None else 0)));end=start+D(str(service))
 if stop_end is not None and D(str(stop_end))<D(str(stop_start)):raise ValueError('Stop end precedes stop start')
 if resume is not None and (stop_end is None or D(str(resume))<D(str(stop_end))):raise ValueError('Resume precedes stop end')
 status=('ON_TIME' if end<=D(str(deadline)) else 'LATE') if deadline is not None else 'COMPLETED_NO_CUSTOMER_DEADLINE'
 if stop_end is None:status='NOT_COMPLETED' if observation_complete else 'INDETERMINATE'
 elif D(str(stop_end))<end:raise ValueError('Native hold shorter than defined work')
 return {'physical_arrival_s':physical_arrival,'stop_start_s':float(stop_start),'work_start_model_s':float(start),'work_complete_model_s':float(end),'stop_end_s':float(stop_end) if stop_end is not None else None,'resume_s':resume,'outcome':status,'formal_outcome':'HOLD','model_status':'MODEL_SERVICE_NOT_REAL_OBSERVATION','extra_hold_s':float(D(str(stop_end))-end) if stop_end is not None else None}
def rates(tasks):
 denom=sum(x['q_PE'] for x in tasks)
 if not tasks or denom<=0:raise ValueError('Fixed demand required')
 known=sum(x['q_PE'] for x in tasks if x['outcome']=='ON_TIME');unknown=sum(x['q_PE'] for x in tasks if x['outcome']=='INDETERMINATE')
 return {'demand_PE':denom,'task_count':len(tasks),'F_PE':known/denom if not unknown else None,'F_PE_lower':known/denom,'F_PE_upper':(known+unknown)/denom,'F_count':sum(x['outcome']=='ON_TIME' for x in tasks)/len(tasks) if not unknown else None}
def validate_trace(t,v,mass,pressure,arrival=None):
 t=np.asarray(t,dtype=float);v=np.asarray(v,dtype=float)
 if t.ndim!=1 or v.ndim!=1 or len(t)!=len(v) or len(t)<2:raise ValueError('Need >=2 paired 1D samples')
 if not np.isfinite(t).all() or not np.isfinite(v).all() or (v<0).any() or not (np.diff(t)==1).all():raise ValueError('Finite, nonnegative speed and exact 1s required')
 if not math.isfinite(mass) or mass<=0 or not math.isfinite(pressure) or pressure<=0:raise ValueError('Explicit positive mass and pressure required')
 if arrival is not None and (not math.isfinite(arrival) or arrival<t[-1]):raise ValueError('Arrival precedes last observation')
 return t,v
def scalar_dc(t,v,mass,pressure,arrival=None):
 t,v=validate_trace(t,v,mass,pressure,arrival);parts=[[],[],[],[]];dc=[]
 for i in range(1,len(t)):
  ds=v[i]*(t[i]-t[i-1]);dvsq=v[i]**2-v[i-1]**2
  W=[mass*9.80665*(.005+(.01+.0095*(3.6*v[i]/100)**2)/pressure)*ds,.5*1.2041*1.175*v[i]**2*ds,.5*mass*dvsq,.5*61*dvsq]
  for p,w in zip(parts,W):p.append(float(w)/3600)
  dc.append(max(math.fsum(W),0)/(.9*3600))
 return {'observed_distance_m':math.fsum(float(v[i]) for i in range(1,len(t))),'W1_Wh':math.fsum(parts[0]),'W2_Wh':math.fsum(parts[1]),'W3_Wh':math.fsum(parts[2]),'W4_Wh':math.fsum(parts[3]),'DC_Wh':math.fsum(dc),'terminal_gap_s':float(arrival-t[-1]) if arrival is not None else None,'terminal_gap_energy_Wh':None,'boundary':'OBSERVED_WINDOW_CONTROLLED_DC','running_mass_kg':mass,'pressure_bar':pressure}
