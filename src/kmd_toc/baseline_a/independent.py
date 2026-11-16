"""Second calculation from raw matrices and schedule, with no builder imports."""
from collections import Counter
from decimal import Decimal, ROUND_CEILING


def recompute(problem, plan):
    errors=[];index={s:i for i,s in enumerate(problem.od.ids)};visits=Counter();arcs=Counter();wait=Decimal(0)
    intervals=[];by_vehicle={v.vehicle_id:[] for v in problem.vehicles}
    for t in plan.trips:
        if t.vehicle_id not in by_vehicle: errors.append('vehicle');continue
        by_vehicle[t.vehicle_id].append(t)
        nodes=[problem.depot.depot_id]+[s.stop_id for s in t.visits]+[problem.depot.depot_id]
        arcs.update(zip(nodes,nodes[1:]));visits.update(s.stop_id for s in t.visits)
        if len(t.visits)>60:errors.append('capacity')
        if (t.origin_id,t.destination_id)!=(problem.depot.depot_id,)*2:errors.append('depot')
        if t.load_end_s-t.load_start_s!=1800 or t.departure_s!=t.load_end_s:errors.append('loading')
        if not 28800<=t.load_start_s<=t.load_end_s<=72000:errors.append('hours')
        clock=t.departure_s
        for k,visit in enumerate(t.visits):
            a,b=index[nodes[k]],index[nodes[k+1]]
            clock+=int(Decimal(str(problem.od.duration_s[a,b])).to_integral_value(rounding=ROUND_CEILING))
            if (visit.arrival_s,visit.service_start_s,visit.service_end_s)!=(clock,clock,clock+120):errors.append('visit_time')
            clock+=120
        a,b=index[nodes[-2]],index[nodes[-1]]
        clock+=int(Decimal(str(problem.od.duration_s[a,b])).to_integral_value(rounding=ROUND_CEILING))
        if clock!=t.return_s or clock>72000:errors.append('return')
        intervals.append((t.berth_id,t.load_start_s,t.load_end_s))
    if visits!=Counter({s.stop_id:1 for s in problem.stops}):errors.append('coverage')
    for v in problem.vehicles:
        trips=sorted(by_vehicle[v.vehicle_id],key=lambda t:t.trip_no)
        if len(trips)>2 or [t.trip_no for t in trips]!=list(range(1,len(trips)+1)):errors.append('trip_count')
        previous=None
        for t in trips:
            ready=v.first_ready_s if previous is None else previous
            if t.ready_s!=ready or t.load_start_s<ready:errors.append('ready')
            if t.waiting_s!=t.load_start_s-ready:errors.append('wait')
            wait+=Decimal(t.load_start_s-ready)/60
            previous=t.return_s
    for b in problem.berths:
        bookings=sorted((s,e) for bid,s,e in intervals if bid==b.berth_id)
        if any(e>s2 for (s,e),(s2,e2) in zip(bookings,bookings[1:])):errors.append('berth_overlap')
    if any(bid not in {b.berth_id for b in problem.berths} for bid,s,e in intervals):errors.append('berth_id')
    distance=sum((Decimal(str(problem.od.distance_m[index[a],index[b]]))*count for (a,b),count in arcs.items()),Decimal(0))/1000
    return {'feasible':not errors,'errors':errors,'D_km':str(distance),'W_min':str(wait),'arc_count':sum(arcs.values())}
