"""Classical charging sidecar; exact rational energy/time, immutable VRPTW input.

Topology: one physical charger, optionally visited in any customer-sequence gap.
No consecutive visits to the same point or intermediate depot replenishment.
Every used vehicle serves a customer; at most n+1 charger visits per route.
"""
from fractions import Fraction as F
from itertools import product, permutations
from collections import Counter
from r24_vrptw.instance import validate_input, json_number

# Declared before execution. Exact reference uses zero tolerance; MILP audit only
# permits these numerical residuals, never changes q or clips battery values.
ENERGY_TOL = F('1e-9')
TIME_TOL = F('1e-7')
OBJECTIVE_TOL = F('1e-7')


def power_rule(q, available_seconds):
    threshold = 3600 * F(str(q)) / F(str(available_seconds))
    margin_target = F(11, 10) * threshold
    grid = -(-margin_target.numerator // margin_target.denominator)
    return threshold, F(grid)


def context(instance, od, precheck, design):
    base = validate_input(instance)
    params = {p['parameter']:p['value'] for p in design['parameters']}
    assert F(params['model_battery_capacity']) == 20
    assert F(params['minimum_SOC']) == F('.1')
    assert F(params['energy_consumption_coefficient']) == F('.127')
    assert F(params['charging_efficiency']) == 1 and params['partial_charging'] is True
    assert F(params['charging_queue_time']) == F(params['charging_setup_time']) == 0
    threshold, power = power_rule(precheck['q_required_kwh'],precheck['available_charge_time_s'])
    if power != 10:
        raise ValueError('STOP: predefined power rule no longer produces10kW')
    charger = precheck['route'][1]
    nodes = [base['depot_id'],*base['customers'],charger]
    arcs = {}
    for i,j in product(nodes,repeat=2):
        if i == j: continue
        row = od[i+'|'+j]
        if not row['reachable'] or row['validation_status'] != 'PASS':
            raise ValueError('STOP: missing/unvalidated directed OD')
        arcs[i,j] = (F(str(row['travel_time_s'])),F(str(row['distance_m']))/1000)
        if i != charger and j != charger:
            assert arcs[i,j] == (base['arcs'][i,j][0],base['arcs'][i,j][1]/1000)
    initial = F(precheck['provisional_initial_battery_kwh'])
    lo,hi = map(F,precheck['strengthened_fleet_interval_kwh'])
    assert lo < initial < hi and 100*initial/20 == F(precheck['provisional_initial_SOC_pct'])
    return dict(base=base,arcs=arcs,charger=charger,maximum=F(20),reserve=F(2),
                initial=initial,r=F('.127'),power=power,threshold=threshold)


def minimal_charges(ctx,nodes,enabled):
    """Analytic per-structure optimum for frozen WIDE windows and constant power.

    Charge just enough to reach next charger/return with reserve. Additional
    earlier charge cannot reduce total charging; no waiting absorbs durations
    in this fixture. Bounds/time checked by replay, not repaired here.
    """
    b=ctx['initial']; charges={}
    for pos,(i,j) in enumerate(zip(nodes,nodes[1:]),1):
        b -= ctx['r']*ctx['arcs'][i,j][1]
        if j == ctx['charger']:
            end=next((k for k in range(pos+1,len(nodes)) if nodes[k]==ctx['charger']),len(nodes)-1)
            remaining=sum((ctx['r']*ctx['arcs'][nodes[k],nodes[k+1]][1] for k in range(pos,end)),F(0))
            q=max(F(0),remaining+ctx['reserve']-b) if enabled else F(0)
            charges[str(pos)]=q;b+=q
    return charges


def route_replay(ctx,vid,nodes,charges,*,energy_tol=F(0),time_tol=F(0)):
    base=ctx['base'];depot=base['depot_id'];c=ctx['charger']
    if not nodes:return dict(vehicle_id=vid,used=False,nodes=[],feasible=None,events=[],arcs=[],travel_s=0,charging_s=0)
    customers=[x for x in nodes[1:-1] if x!=c]
    if (nodes[0]!=depot or nodes[-1]!=depot or depot in nodes[1:-1] or not customers
        or len(customers)!=len(set(customers)) or any(x not in base['customers'] and x!=c for x in nodes[1:-1])
        or any(i==j for i,j in zip(nodes,nodes[1:]))):raise ValueError('Invalid route structure')
    if set(charges)-{str(i) for i,x in enumerate(nodes) if x==c}:raise ValueError('Charge outside charger occurrence')
    clock=base['opening'];b=ctx['initial'];travel=distance=energy=charged=charge_time=F(0)
    load=sum((base['customers'][x]['demand'] for x in customers),F(0))
    cap=load<=base['vehicles'][vid];battery_ok=ctx['reserve']-energy_tol<=b<=ctx['maximum']+energy_tol;time_ok=True
    events=[];arcs=[];first=None;minimum=b
    for pos,(i,j) in enumerate(zip(nodes,nodes[1:]),1):
        tau,km=ctx['arcs'][i,j];e=ctx['r']*km;before=b;b-=e;arrival=clock+tau
        arrival_b=b;minimum=min(minimum,b)
        arr_ok=ctx['reserve']-energy_tol<=b<=ctx['maximum']+energy_tol
        if not arr_ok and first is None:first=dict(origin=i,destination=j,battery_before_kwh=json_number(before),arc_energy_kwh=json_number(e),battery_after_kwh=json_number(b),B_min_kwh=json_number(ctx['reserve']))
        q=F(str(charges.get(str(pos),0)));tc=3600*q/ctx['power']
        if j in base['customers']:
            data=base['customers'][j];start=max(arrival,data['earliest']);service=data['duration'];late=max(F(0),start-data['latest'])
        else:start=arrival;service=F(0);late=max(F(0),arrival-base['closing']) if j==depot else F(0)
        charge_ok=q>=-energy_tol and (j==c or q==0) and q<=ctx['maximum']-b+energy_tol
        b+=q;clock=start+service+tc
        node_time=late<=time_tol and clock<=base['closing']+time_tol
        node_b=arr_ok and charge_ok and ctx['reserve']-energy_tol<=b<=ctx['maximum']+energy_tol
        battery_ok &= node_b;time_ok &= node_time
        travel+=tau;distance+=km;energy+=e;charged+=q;charge_time+=tc
        arcs.append(dict(vehicle_id=vid,position=pos,origin=i,destination=j,distance_km=json_number(km),travel_time_s=json_number(tau),energy_kwh=json_number(e),battery_before_kwh=json_number(before),battery_after_kwh=json_number(arrival_b)))
        events.append(dict(vehicle_id=vid,position=pos,node=j,arrival_time_s=json_number(arrival),waiting_s=json_number(start-arrival),service_start_s=json_number(start),service_s=json_number(service),departure_time_s=json_number(clock),arrival_battery_kwh=json_number(arrival_b),q_chg_kwh=json_number(q),departure_battery_kwh=json_number(b),SOC_arr_pct=json_number(100*arrival_b/ctx['maximum']),SOC_dep_pct=json_number(100*b/ctx['maximum']),t_chg_s=json_number(tc),battery_feasible=bool(node_b),temporal_feasible=bool(node_time)))
    assert ctx['initial']+charged-energy==b
    return dict(vehicle_id=vid,used=True,nodes=list(nodes),charges={k:json_number(F(str(v))) for k,v in charges.items()},load=json_number(load),capacity_feasible=bool(cap),battery_feasible=bool(battery_ok),temporal_feasible=bool(time_ok),feasible=bool(cap and battery_ok and time_ok),first_reserve_violation=first,events=events,arcs=arcs,travel_s=json_number(travel),distance_km=json_number(distance),energy_kwh=json_number(energy),charged_kwh=json_number(charged),charging_s=json_number(charge_time),final_battery_kwh=json_number(b),final_SOC_pct=json_number(100*b/ctx['maximum']),minimum_battery_kwh=json_number(minimum),return_time_s=json_number(clock),diagnostic_after_failure=first is not None)


def fleet_replay(ctx,plans,**tolerances):
    ids=[p['vehicle_id'] for p in plans]
    if len(ids)!=len(set(ids)) or set(ids)!=set(ctx['base']['vehicles']):raise ValueError('Fleet identity mismatch')
    served=Counter(x for p in plans for x in p['nodes'][1:-1] if x in ctx['base']['customers'])
    visits=all(served[x]==1 for x in ctx['base']['customers'])
    routes=[route_replay(ctx,p['vehicle_id'],p['nodes'],p['charges'],**tolerances) for p in plans]
    used=[r for r in routes if r['used']]
    return dict(routes=routes,visit_feasible=visits,feasible=visits and all(r['feasible'] for r in used),primary_travel_s=json_number(sum((F(str(r['travel_s'])) for r in used),F(0))),secondary_charging_s=json_number(sum((F(str(r['charging_s'])) for r in used),F(0))))


def route_structures(ctx,assigned):
    if not assigned:return [()]
    d=ctx['base']['depot_id'];c=ctx['charger'];out=[]
    for order in permutations(assigned):
        for gaps in product((False,True),repeat=len(order)+1):
            inner=[]
            for i in range(len(order)+1):
                if gaps[i]:inner.append(c)
                if i<len(order):inner.append(order[i])
            out.append((d,*inner,d))
    return out


def exact_reference(ctx,enabled):
    # Analytic charging optimum relies on this audited WIDE property.
    assert all(x['earliest']==ctx['base']['opening'] and x['latest']==ctx['base']['closing'] for x in ctx['base']['customers'].values())
    customers=list(ctx['base']['customers']);vids=list(ctx['base']['vehicles']);results=[];best=None;witnesses=[]
    for assignment in product(range(len(vids)),repeat=len(customers)):
        options=[route_structures(ctx,[x for x,a in zip(customers,assignment) if a==k]) for k in range(len(vids))]
        for nodes_by_vehicle in product(*options):
            plans=[dict(vehicle_id=v,nodes=list(nodes),charges=minimal_charges(ctx,nodes,enabled)) for v,nodes in zip(vids,nodes_by_vehicle)]
            result=fleet_replay(ctx,plans);index=len(results)
            results.append(dict(index=index,plans=[{**p,'charges':{k:json_number(v) for k,v in p['charges'].items()}} for p in plans],result=result))
            if result['feasible']:
                obj=(F(str(result['primary_travel_s'])),F(str(result['secondary_charging_s'])))
                if best is None or obj<best:best=obj;witnesses=[index]
                elif obj==best:witnesses.append(index)
    return dict(status='PROVEN_OPTIMAL' if best is not None else 'PROVEN_INFEASIBLE',complete=True,charging_enabled=enabled,enumerated_count=len(results),feasible_count=sum(x['result']['feasible'] for x in results),objective=None if best is None else [json_number(x) for x in best],optimal_indices=witnesses,candidates=results,scope='All vehicle assignments/customer permutations/charger-gap subsets, including repeated visits separated by customers;analytic minimum charging;WIDE fixture only')
