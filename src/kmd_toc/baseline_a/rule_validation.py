"""Independent rule oracle: raw OD Decimal arithmetic and list-based FCFS.

Does not import rule_v1 or call generation/scheduling/metric helpers.
The legacy independent physical oracle remains a second audit of constraints.
"""
from collections import defaultdict
from decimal import Decimal, ROUND_CEILING
from .program_validation import audit_plan


def audit_rule(p, plan):
    physical = audit_plan(p,plan)
    errors = list(physical['errors'])
    by_vehicle = defaultdict(dict)
    index = {s:i for i,s in enumerate(p.od.ids)}
    for trip in plan.trips:
        by_vehicle[trip.vehicle_id][trip.trip_no] = trip
    pending = [(v.first_ready_s,i,1) for i,v in enumerate(p.vehicles) if by_vehicle[v.vehicle_id]]
    free = {b.berth_id:b.opening_s for b in p.berths}
    clocks, waiting = {}, [0,0]
    reconstructed = []
    while pending:
        ready,v,k = min(pending)
        pending.remove((ready,v,k))
        trip = by_vehicle[p.vehicles[v].vehicle_id].get(k)
        if trip is None:
            errors.append('CONTIGUOUS_TRIPS')
            break
        berth = sorted(free, key=lambda b:(free[b],b))[0]
        start = max(ready,free[berth])
        end = start+1800
        free[berth] = end
        if (trip.ready_s,trip.berth_id,trip.load_start_s,trip.load_end_s,trip.departure_s) != (ready,berth,start,end,end):
            errors.append('INDEPENDENT_FCFS')
        clock, previous = end, p.depot.depot_id
        for destination in [*(visit.stop_id for visit in trip.visits),p.depot.depot_id]:
            raw = Decimal(str(p.od.duration_s[index[previous],index[destination]]))
            if not raw.is_finite():
                errors.append('UNREACHABLE')
                break
            clock += int(raw.to_integral_value(rounding=ROUND_CEILING))
            if destination != p.depot.depot_id:
                clock += 120
            previous = destination
        if clock != trip.return_s:
            errors.append('INDEPENDENT_RETURN')
        clocks[v] = clock
        waiting[k-1] += start-ready
        reconstructed.append({'vehicle_index':v,'trip_no':k,'ready_s':ready,'berth_id':berth,
                              'load_start_s':start,'load_end_s':end,'return_s':clock})
        if k+1 in by_vehicle[p.vehicles[v].vehicle_id]:
            pending.append((clock,v,k+1))
    final = [clocks.get(i) for i in range(len(p.vehicles))]
    loads = [r-v.first_ready_s if r is not None else 0 for r,v in zip(final,p.vehicles)]
    overtime = sum(max(0,r-v.return_deadline_s) for r,v in zip(final,p.vehicles) if r is not None)
    return {**physical,'feasible':not errors,'errors':sorted(set(errors)),
            'W_first':waiting[0]/60,'W_reload':waiting[1]/60,
            'final_return_s':final,'L_s':loads,'O_s':overtime,'H_s2':sum(x*x for x in loads),
            'reconstructed_events':reconstructed}
