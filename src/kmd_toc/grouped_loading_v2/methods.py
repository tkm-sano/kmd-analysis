"""Directed Savings baseline and common finite reception moves."""
from collections import Counter
from types import SimpleNamespace
from kmd_toc.iterative_v3.io import decode_routes
from kmd_toc.pipeline.classical import directed_cw
from .model import ScheduleError, build_jobs, candidate_key, evaluate, group_map, vehicle_number


def route_view(plan):
    """Only slot and visit information is imported by legacy proposal builders."""
    return SimpleNamespace(trips=[SimpleNamespace(vehicle_id=r["vehicle"],trip_no=r["trip"],
        visits=[SimpleNamespace(stop_id=s) for s in r["customers"]]) for r in plan["routes"]])


def work_calls(problem, routes, loading=900):
    """One planned release per group when the first berth next has capacity."""
    members = group_map(problem.vehicles)
    counts = Counter(members[v] for v,k in routes if k==1)
    groups = len(members)//5
    free = {b.berth_id:28800 for b in problem.berths}
    calls = []
    for g in range(groups):
        lower = calls[-1]+1 if calls else 28800
        latest = 32400-(groups-g-1)
        at = min(latest,max(lower,min(free.values()))) if g else 28800
        calls.append(at)
        for _ in range(counts[g]):
            start = max(at,min(free.values()))
            b = min(b for b,t in free.items() if t<=start)
            free[b] = start+loading
    return tuple(calls)


def generate_b(p,duty):
    raw, information = directed_cw(p)
    fleet = sorted((v.vehicle_id for v in p.vehicles),key=vehicle_number)
    from kmd_toc.duty_break_v1.scheduler import route_data
    pool = [tuple(p.od.ids[i] for i in r) for r in raw]
    duration = {r:sum(route_data(p,r)[0])+duty["service_s"]*len(r) for r in pool}
    # Use the same CW partition; choose a feasible deterministic slot assignment.
    receipts = []
    orders = [sorted(pool,key=lambda r:(-duration[r],r)),sorted(pool,key=lambda r:(-len(r),-duration[r],r)),pool]
    for ordering,seq in enumerate(orders):
        for first_count in range(len(fleet), (len(pool)+1)//2-1,-1):
            first = dict(zip(fleet[:first_count],seq[:first_count]))
            first_slots = {(v,1):r for v,r in first.items()}
            calls = work_calls(p,first_slots)
            # Predict first return using just the load and drive/service lengths.
            group = group_map(p.vehicles)
            free = dict.fromkeys((b.berth_id for b in p.berths),28800)
            potential = {}
            for v,r in first.items():
                start = max(calls[group[v]],min(free.values()))
                b = min(b for b,t in free.items() if t<=start)
                free[b] = start+900
                potential[v] = start+900+duration[r]
            second_options = [sorted(first,key=lambda v:(potential[v],vehicle_number(v))),list(first)]
            for pairing,vehicles in enumerate(second_options):
                rs = first_slots | {(v,2):r for v,r in zip(vehicles,seq[first_count:])}
                report = dict(order=ordering,first_count=first_count,pairing=pairing,calls_s=list(calls))
                try:
                    plan = evaluate(p,rs,calls,duty)
                except ScheduleError as e:
                    receipts.append(report | dict(status="REJECTED",reason=str(e)))
                    continue
                receipts.append(report | dict(status="FEASIBLE",physical_hash=plan["physical_hash"]))
                return plan,dict(cw=information,receipt=receipts,rule="capacity-driven deterministic CW completion",
                                 stop="first feasible",tested=len(receipts))
    raise ScheduleError(f"NO_FEASIBLE_CW_ASSIGNMENT:{receipts}")


def call_move(p, rs, calls, iteration, *, parent_calls=None):
    """Deterministic paired time proposal on the common one-second domain."""
    current = list(calls)
    capacity = work_calls(p,rs)
    index = 1+iteration%(len(current)-1)
    lower = current[index-1]+1
    upper = (current[index+1]-1) if index+1<len(current) else 32400
    # Visit a capacity breakpoint and the endpoints with no added RNG stream.
    options = (max(lower,min(upper,capacity[index])),lower,upper)
    order = (iteration//(len(current)-1))%3
    for candidate in options[order:]+options[:order]:
        if candidate != current[index]:
            current[index] = candidate
            return tuple(current)
    return tuple(current)


def routing_pool(p, initial, config, seed):
    from kmd_toc.common_initial_v1 import engines
    from kmd_toc.iterative_d3.overlay import build_function
    # Preserve finite native Routing and remove only its old 30-minute replay.
    routing = build_function(engines,"routing_from_initial",[
        ("""    reconstructed=schedule(p,routes,'C')
    same=digest_payload(physical_payload(reconstructed))==digest_payload(physical_payload(plan))
    if not same:raise ValueError('ROUTING_PROJECTION_RECONSTRUCTION_CHANGED_PHYSICAL_INITIAL')""",
         "    reconstructed=plan\n    same=True"),
        ("digest_payload(physical_payload(reconstructed))","None"),
        ("digest_payload(physical_payload(plan))","None"),
        ("native_solution_found=solution is not None)","native_solution_found=solution is not None,generated_slots=generated)")
    ])
    pool, receipt = routing(p,route_view(initial),config,seed)
    receipt.update(reconstructed_physical_hash=None,full_reconstructed_plan_equal=None,
                   preserved_outer_incumbent_hash=initial["physical_hash"],
                   grouped_start_routes_verified=True)
    return pool,receipt
