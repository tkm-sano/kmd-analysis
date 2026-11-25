"""Independent physical reconstruction and event-queue FCFS; never schedules."""
from collections import Counter,defaultdict
import heapq
import math

from .models import DutyProblem,DutyPlan
from .policy import VERSION,load_policy,policy_hash


def validate(p,plan):
    errors=[];vehicle_rows=[];trip_rows=[]
    def fail(code,context='',detail=None):errors.append({'code':code,'context':context,'detail':detail})
    def result(D=None,W=None):
        unverified=[b.location_id for b in getattr(plan,'breaks',()) if b.location_status!='caller_confirmed']
        for row in vehicle_rows:
            vid=row['vehicle_id']
            row['violation_codes']=[e['code'] for e in errors if e['context']==vid or e['context'].startswith(vid+'/')]
            row['duty_exceeded']=any(k in row['violation_codes'] for k in ('RETURN_AFTER_1900','ACTIVITY_OUTSIDE_SHIFT','NONBREAK_WORK_WINDOW_EXCEEDED'))
            row['break_violation']=any('BREAK' in k and k!='NONBREAK_WORK_WINDOW_EXCEEDED' for k in row['violation_codes'])
            row['berth_or_FCFS_violation']=any('BERTH' in k or 'FCFS' in k for k in row['violation_codes'])
        return {'feasible':not errors,'model_feasible':not errors,'version':VERSION,
                'violations':errors,'D_km':D if not errors else None,
                'W_total_loading_min':W if not errors else None,
                'diagnostic_D_km':D,'diagnostic_W_total_loading_min':W,
                'primary_W_definition':'sum_all_active_trip_start_minus_ready_div_60',
                'vehicles':vehicle_rows,'trips':trip_rows,
                'unverified_break_locations':sorted(set(unverified)),
                'stopping_site_feasibility':'NOT_ESTABLISHED_INVALID_MODEL' if errors else
                    'HOLD_UNVERIFIED_LOCATIONS' if unverified else 'CALLER_EVIDENCE_SUPPLIED_NOT_A_SITE_AUDIT',
                'main_experiment':'HOLD'}
    if not isinstance(p,DutyProblem) or not isinstance(plan,DutyPlan):
        fail('DO_NOT_MIX_LEGACY_AND_DUTY');return result()
    try:p.validate_duty()
    except ValueError as error:fail('INPUT_INVALID',detail=str(error));return result()
    c=load_policy();vehicles={v.vehicle_id:v for v in p.vehicles};stops={s.stop_id:s for s in p.stops}
    berths={b.berth_id:b for b in p.berths};index={s:i for i,s in enumerate(p.od.ids)}
    if plan.schema_version!='duty-break-plan-v1' or plan.method_id not in ('B','C','D'):
        fail('DUTY_PLAN_METADATA')
    if plan.execution_kind!=('quantum_circuit_simulator' if plan.method_id=='D' else 'classical'):
        fail('EXECUTION_KIND')
    if plan.problem_hash!=p.fingerprint or plan.od_hash!=p.od.fingerprint:
        fail('INPUT_OR_OD_HASH')
    if (plan.method_settings.get('duty_version')!=VERSION or
            plan.method_settings.get('duty_policy_sha256')!=policy_hash() or
            plan.method_settings.get('rest_options')!=p.rest_options.payload()):
        fail('DUTY_SETTINGS_OR_LOCATION_MODE')
    counts=Counter(v.stop_id for t in plan.trips for v in t.visits)
    if counts!=Counter({s:1 for s in stops}):fail('DELIVER_EACH_CUSTOMER_EXACTLY_ONCE')
    if any(type(t.trip_no) is not int or t.trip_no not in (1,2) for t in plan.trips):
        fail('TRIP_NUMBER_MUST_BE_INTEGER_1_OR_2');return result()
    breaks=defaultdict(list)
    for b in plan.breaks:
        breaks[b.vehicle_id].append(b)
        if b.vehicle_id not in vehicles:fail('UNKNOWN_BREAK_DRIVER',b.vehicle_id)
        if b.trip_no is not None and (type(b.trip_no) is not int or b.trip_no not in (1,2)):
            fail('BREAK_TRIP_NUMBER',b.vehicle_id)
        if any(type(x) is not int for x in (b.start_s,b.end_s)):
            fail('BREAK_INTEGER_SECONDS',b.vehicle_id);continue
        if b.end_s-b.start_s!=3600:fail('BREAK_NOT_CONTINUOUS_60_MIN',b.vehicle_id)
        if not 43200<=b.start_s<=46800 or b.end_s>50400:fail('BREAK_WINDOW',b.vehicle_id)
        if not p.rest_options.eligible(b.location_id):fail('BREAK_LOCATION_NOT_ALLOWED',b.vehicle_id)
        if (b.location_status,b.evidence)!=p.rest_options.evidence(b.location_id):
            fail('BREAK_LOCATION_EVIDENCE_MISMATCH',b.vehicle_id)
    groups=defaultdict(list);load_intervals=[];durations={};distances=[];total_wait=0
    for t in plan.trips:
        groups[t.vehicle_id].append(t)
        if t.vehicle_id not in vehicles:fail('UNKNOWN_VEHICLE',t.vehicle_id)
    for vid,v in vehicles.items():
        ts=sorted(groups.get(vid,()),key=lambda t:t.trip_no)
        br=breaks[vid][0] if len(breaks[vid])==1 else None
        if br is not None and any(type(x) is not int for x in (br.start_s,br.end_s)):br=None
        if ts and len(breaks[vid])!=1:fail('EXACTLY_ONE_BREAK_PER_ACTIVE_DRIVER',vid)
        if not ts and breaks[vid]:fail('UNUSED_VEHICLE_MUST_BE_RECORDED_WITHOUT_PLAN_BREAK',vid)
        if len(ts)>2 or [t.trip_no for t in ts]!=list(range(1,len(ts)+1)):
            fail('AT_MOST_TWO_CONTIGUOUS_TRIPS',vid)
        previous=None;activities=[];drive_s=0;service_s=0;loading_s=0;waiting_s=0;earliest=None;rest_hits=0
        for t in ts:
            key=(vid,t.trip_no);context=f'{vid}/{t.trip_no}'
            fields=(t.ready_s,t.load_start_s,t.load_end_s,t.departure_s,t.return_s,t.waiting_s)
            if any(type(x) is not int or x<0 for x in fields):
                fail('TRIP_INTEGER_SECONDS',context);continue
            ready=v.first_ready_s if t.trip_no==1 else previous
            if ready is None or t.ready_s!=ready or t.load_start_s<t.ready_s:
                fail('READY_OR_SECOND_TRIP_CONNECTION',context)
            if t.ready_s<28800 or t.load_start_s<28800:fail('START_BEFORE_0800',context)
            if t.load_end_s!=t.load_start_s+1800:fail('LOAD_30_MIN',context)
            if t.departure_s!=t.load_end_s:fail('IMMEDIATE_DEPARTURE',context)
            if t.berth_id not in berths:fail('UNKNOWN_BERTH',context)
            else:
                b=berths[t.berth_id]
                if t.load_start_s<b.opening_s or t.load_end_s>b.closing_s:fail('BERTH_HOURS',context)
            load_intervals.append((t.load_start_s,t.load_end_s,t.berth_id,context))
            if t.origin_id!=p.depot.depot_id or t.destination_id!=p.depot.depot_id:fail('DEPOT_ROUND_TRIP',context)
            if not t.visits:fail('EMPTY_ACTIVE_TRIP',context)
            if any(z.stop_id not in stops for z in t.visits):fail('UNKNOWN_CUSTOMER',context);continue
            if sum(stops[z.stop_id].demand for z in t.visits)>v.capacity:fail('CAPACITY',context)
            expected_wait=t.load_start_s-t.ready_s
            if t.waiting_s!=expected_wait:fail('W_DEFINITION',context)
            total_wait+=expected_wait;waiting_s+=expected_wait;loading_s+=1800
            activities.extend([(t.ready_s,t.load_start_s,'FCFS_wait'),(t.load_start_s,t.load_end_s,'loading')])
            clock=t.departure_s;node=p.depot.depot_id;distance=[];trip_drive=0;trip_rest=0
            for visit in t.visits:
                secs=math.ceil(float(p.od.duration_s[index[node],index[visit.stop_id]]))
                distance.append(float(p.od.distance_m[index[node],index[visit.stop_id]]))
                activities.append((clock,clock+secs,'driving'));clock+=secs;drive_s+=secs;trip_drive+=secs
                arrival=clock
                if earliest is None and p.rest_options.eligible(visit.stop_id) and 43200<=clock<=46800:
                    earliest=(t.trip_no,visit.stop_id,clock)
                if br is not None and br.trip_no==t.trip_no and br.location_id==visit.stop_id and br.placement=='before_delivery_service':
                    if (br.start_s,br.end_s)!=(clock,clock+3600):fail('BREAK_NOT_AT_STOP_ARRIVAL',context)
                    activities.append((br.start_s,br.end_s,'break'));clock+=3600;rest_hits+=1;trip_rest+=3600
                if (visit.arrival_s!=arrival or visit.service_start_s!=clock or visit.service_end_s!=clock+120 or
                        any(type(x) is not int for x in (visit.arrival_s,visit.service_start_s,visit.service_end_s))):
                    fail('VISIT_TIMES_OR_SERVICE_120S',context,visit.stop_id)
                activities.append((clock,clock+120,'service'));clock+=120;service_s+=120
                if earliest is None and p.rest_options.eligible(visit.stop_id) and 43200<=clock<=46800:
                    earliest=(t.trip_no,visit.stop_id,clock)
                if br is not None and br.trip_no==t.trip_no and br.location_id==visit.stop_id and br.placement!='before_delivery_service':
                    if br.placement!='after_delivery_service' or (br.start_s,br.end_s)!=(clock,clock+3600):
                        fail('BREAK_NOT_AT_RECORDED_STOP_SERVICE_END',context)
                    activities.append((br.start_s,br.end_s,'break'));clock+=3600;rest_hits+=1;trip_rest+=3600
                node=visit.stop_id
            secs=math.ceil(float(p.od.duration_s[index[node],0]));distance.append(float(p.od.distance_m[index[node],0]))
            activities.append((clock,clock+secs,'driving'));clock+=secs;drive_s+=secs;trip_drive+=secs
            previous=clock;d=math.fsum(distance);distances.append(d)
            if t.return_s!=clock:fail('RETURN_TIME_RECONSTRUCTION',context)
            if t.return_s>68400 or clock>68400:fail('RETURN_AFTER_1900',context)
            if type(t.distance_m) not in (int,float) or not math.isfinite(t.distance_m) or abs(d-t.distance_m)>1e-6:
                fail('OD_DISTANCE',context)
            durations[key]=trip_drive+120*len(t.visits)+trip_rest
            trip_rows.append({'vehicle_id':vid,'trip_no':t.trip_no,'customers':len(t.visits),
                              'ready_s':t.ready_s,'load_start_s':t.load_start_s,'load_end_s':t.load_end_s,
                              'departure_s':t.departure_s,'return_s':t.return_s,'driving_s':trip_drive,
                              'service_s':120*len(t.visits),'break_s':trip_rest,'W_s':expected_wait,'D_m':d})
        if br is not None:
            if earliest is not None:
                if (br.trip_no,br.location_id,br.start_s)!=earliest:fail('COMMON_EARLIEST_BREAK_RULE',vid)
                if rest_hits!=1:fail('BREAK_NOT_ONCE_IN_ROUTE',vid)
            else:
                final=previous if previous is not None else 28800
                if (not p.rest_options.allow_post_final_depot_break or br.trip_no is not None or
                        br.location_id!=p.depot.depot_id or br.placement!='after_final_return_by_noon' or
                        br.start_s!=43200 or br.end_s!=46800 or final>43200):
                    fail('NO_ALLOWED_ROUTE_BREAK_OR_POST_FINAL_PLACEMENT',vid)
                if rest_hits:fail('DUPLICATED_ROUTE_AND_DEPOT_BREAK',vid)
                activities.append((br.start_s,br.end_s,'break'))
        ordered=sorted((s,e,kind) for s,e,kind in activities if e>s)
        for (a,b,kind),(s,e,nextkind) in zip(ordered,ordered[1:]):
            if s<b:fail('DRIVER_ACTIVITY_OVERLAP',vid,[kind,nextkind,a,b,s,e])
        if any(s<28800 or e>68400 for s,e,_ in ordered):fail('ACTIVITY_OUTSIDE_SHIFT',vid)
        work=drive_s+service_s+loading_s+waiting_s
        if work>36000:fail('NONBREAK_WORK_WINDOW_EXCEEDED',vid)
        vehicle_rows.append({'vehicle_id':vid,'used':bool(ts),'break_constraint_applicable':bool(ts),
                             'customers':sum(len(t.visits) for t in ts),'active_trips':len(ts),
                             'first_ready_s':v.first_ready_s,'trip1_departure_s':ts[0].departure_s if ts else None,
                             'trip1_return_s':ts[0].return_s if ts else None,
                             'trip2_ready_s':ts[1].ready_s if len(ts)>1 else None,
                             'break_start_s':br.start_s if br else None,'break_end_s':br.end_s if br else None,
                             'break_s':br.end_s-br.start_s if br else None,'driving_s':drive_s,
                             'service_s':service_s,'loading_s':loading_s,'W_s':waiting_s,
                             'final_return_s':previous,'return_deadline_s':v.return_deadline_s,
                             'activity_work_s':work,'nonbreak_window_s':36000,'duty_span_s':39600,
                             'pre_shift_tasks_s':0,'post_return_tasks_s':0,
                             'unused_nonbreak_window_s':36000-work,'activities':ordered,
                             'break_location_status':br.location_status if br else None})
    for bid in berths:
        prev=-1;owner=''
        for s,e,b,context in sorted(x for x in load_intervals if x[2]==bid):
            if s<prev:
                fail('BERTH_OVERLAP',context,{'other_trip':owner,'berth':bid})
                fail('BERTH_OVERLAP',owner,{'other_trip':context,'berth':bid})
            if e>prev:prev=e;owner=context
    # Separate event-driven FCFS oracle: uses reconstructed OD+service+break
    # duration and input first-ready, never calls the release-order scheduler.
    trips={(t.vehicle_id,t.trip_no):t for t in plan.trips}
    if len(trips)!=len(plan.trips):fail('DUPLICATE_TRIP_KEYS')
    events=[];queue=[];idle=set();seen=set()
    for vid,v in vehicles.items():
        if (vid,1) in trips:heapq.heappush(events,(v.first_ready_s,1,vid,1))
    for b in p.berths:heapq.heappush(events,(b.opening_s,0,b.berth_id,0))
    while events:
        now=events[0][0]
        while events and events[0][0]==now:
            stamp,kind,identifier,k=heapq.heappop(events)
            if kind==0:idle.add(identifier)
            else:heapq.heappush(queue,(stamp,identifier,k))
        while idle and queue:
            ready,vid,k=heapq.heappop(queue);bid=min(idle);idle.remove(bid);key=(vid,k)
            if key not in durations:continue
            t=trips[key];ret=now+1800+durations[key];seen.add(key)
            if (t.ready_s,t.load_start_s,t.berth_id,t.return_s)!=(ready,now,bid,ret):
                fail('INDEPENDENT_FCFS_QUEUE',f'{vid}/{k}',{'ready':ready,'start':now,'berth':bid,'return':ret})
            heapq.heappush(events,(now+1800,0,bid,0))
            if k==1 and (vid,2) in trips:heapq.heappush(events,(ret,1,vid,2))
        if len(seen)==len(trips):break
    if len(seen)!=len(trips):fail('UNSCHEDULED_FCFS_TRIPS')
    return result(math.fsum(distances)/1000,total_wait/60)


def require_valid(p,plan):
    report=validate(p,plan)
    if not report['model_feasible']:raise ValueError('DUTY_BREAK_REJECTION:'+str(report['violations']))
    return report
