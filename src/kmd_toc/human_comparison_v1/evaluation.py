"""One physical evaluator for A/B/C/D, independent metrics are authoritative."""
from collections import defaultdict
from .contract import require


def evaluate(problem,plan,*,human_csv=None):
 from kmd_toc.common.validation import validate_plan
 from kmd_toc.baseline_a.program_validation import audit_plan
 common=validate_plan(problem,plan).as_dict();independent=audit_plan(problem,plan)
 valid=(common['feasible'] and independent['feasible'] and
        abs(common['D_km']-float(independent['D_km']))<=1e-7 and
        abs(common['W_min']-float(independent['W_min']))<=1e-7)
 human=None
 if human_csv is not None:
  from kmd_toc.baseline_a.human_v1 import manual_groups
  from kmd_toc.baseline_a.rule_validation import audit_rule
  groups=manual_groups(problem,human_csv)
  actual=defaultdict(list)
  for trip in sorted(plan.trips,key=lambda t:(t.vehicle_id,t.trip_no)):
   actual[trip.vehicle_id].extend(v.stop_id for v in trip.visits)
  matches=all(actual[v.vehicle_id]==[problem.od.ids[n] for n in g] for v,g in zip(problem.vehicles,groups))
  fcfs=audit_rule(problem,plan)
  human={'assignment_and_order_preserved':matches,'FCFS_valid':fcfs['feasible']}
  valid=valid and matches and fcfs['feasible']
 return {'validated':bool(valid),'common':common,'independent':independent,'human_specific':human,
         'official_metrics':{'D_km':float(independent['D_km']) if valid else None,
              'W_min':float(independent['W_min']) if valid else None,
              'W_first_min':common['W1_min'] if valid else None,
              'W_reload_min':common['W2_min'] if valid else None}}


def partition(events):
 """Disjoint monotonic-nanosecond stages; only explicit activity is human time."""
 require(len(events)>=2,'INCOMPLETE_TIMELINE')
 totals={'HUMAN':0,'MACHINE':0,'OTHER':0}
 for a,b in zip(events,events[1:]):
  require(a['stage'] in totals,'TIMELINE_STAGE')
  require(type(a['ns']) is int and type(b['ns']) is int and 0<=a['ns']<=b['ns'],'TIMELINE_CLOCK')
  totals[a['stage']]+=b['ns']-a['ns']
 total=events[-1]['ns']-events[0]['ns']
 require(sum(totals.values())==total,'TIME_PARTITION_MISMATCH')
 return {'T_total_sec':total/1e9,'T_human_sec':totals['HUMAN']/1e9,
         'T_machine_sec':totals['MACHINE']/1e9,'T_other_sec':totals['OTHER']/1e9,
         'partition_complete':True,'partition_rounding_tolerance_sec':1e-8}


def union_seconds(intervals):
 if not intervals:return None
 total=0;end=None
 for a,b in sorted(intervals):
  require(type(a) is int and type(b) is int and 0<=a<=b,'COMPUTE_INTERVAL_CLOCK')
  if end is None or a>end:total+=b-a
  else:total+=max(0,b-end)
  end=b if end is None else max(end,b)
 return total/1e9
