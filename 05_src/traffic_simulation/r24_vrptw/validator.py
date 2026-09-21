"""Replay explicit depot-to-depot routes, independent of any optimization result.

Only input data and route sequences are accepted. Structural inability to replay
is represented by None / NOT_EVALUABLE, never temporal PASS. Decimal arithmetic
is exact via Fraction; any positive late amount fails the hard window.
"""
from collections import Counter
from fractions import Fraction
from .instance import InputError, array, fields, identifier, json_number, validate_input


def validate_routes(data, routes):
    """routes = [{vehicle_id: str, stops: [depot, customer, ..., depot]}].

    Omitted vehicles or an explicit empty stops list are unused. An unused depot
    self-loop is not a tour. Unknown identities and duplicate vehicle records are
    input errors; malformed depot structure, visits and overload are result FAILs.
    """
    instance = validate_input(data)
    array(routes, 'routes', allow_empty=True)
    depot = instance['depot_id']
    customers, vehicles, arcs = (instance[k] for k in ('customers', 'vehicles', 'arcs'))
    by_vehicle = {}
    for route in routes:
        fields(route, ['vehicle_id', 'stops'], label='route')
        vid = identifier(route['vehicle_id'], 'vehicle_id')
        if vid not in vehicles or vid in by_vehicle:
            raise InputError(f'unknown or duplicate route vehicle: {vid}')
        array(route['stops'], 'stops', allow_empty=True)
        for cid in route['stops']:
            identifier(cid, 'route node')
            if cid != depot and cid not in customers:
                raise InputError(f'unknown customer in route: {cid}')
        by_vehicle[vid] = tuple(route['stops'])
    served = Counter(cid for stops in by_vehicle.values() for cid in stops if cid != depot)
    visit = all(served[cid] == 1 for cid in customers)
    errors = []
    if not visit:
        errors.append({'component': 'visit', 'counts': {c: served[c] for c in customers}})
    route_ok = capacity_ok = depot_ok = True
    temporal = True
    customer_rows, vehicle_rows = [], []
    total_travel = Fraction(0)
    for vid, capacity in vehicles.items():
        stops = by_vehicle.get(vid, ())
        if not stops:
            vehicle_rows.append(dict(vehicle_id=vid, used=False, route=[], load=0,
                capacity=json_number(capacity), departure_time=None, return_time=None,
                depot_late_amount=None, temporal_feasible=None, depot_feasible=None,
                capacity_feasible=True, travel_time_seconds=0, travel_distance=0))
            continue
        inner = [cid for cid in stops if cid != depot]
        load = sum((customers[c]['demand'] for c in inner), Fraction(0))
        cap = load <= capacity
        capacity_ok &= cap
        endpoints = len(stops) >= 3 and stops[0] == stops[-1] == depot and depot not in stops[1:-1]
        structure = endpoints and len(inner) == len(set(inner))
        if not cap:
            errors.append(dict(component='capacity', vehicle_id=vid, load=json_number(load)))
        if not structure:
            route_ok = False
            if not endpoints:
                depot_ok = False
            temporal = None if temporal is True else temporal
            errors.append(dict(component='route', vehicle_id=vid, message='invalid depot tour or repeated customer'))
            vehicle_rows.append(dict(vehicle_id=vid, used=True, route=list(stops), load=json_number(load),
                capacity=json_number(capacity), capacity_feasible=cap, departure_time=None, return_time=None,
                depot_late_amount=None, temporal_feasible=None, depot_feasible=False if not endpoints else None,
                travel_time_seconds=None, travel_distance=None))
            # Return time cannot be certified for a non-replayable route.
            if endpoints and depot_ok is True:
                depot_ok = None
            continue
        clock = instance['opening']
        travel = wait_total = service = Fraction(0)
        distance = Fraction(0)
        route_temporal = True
        for position, cid in enumerate(stops[1:-1], 1):
            prev, nxt = stops[position - 1], stops[position + 1]
            duration, metres = arcs[prev, cid]
            arrival = clock + duration
            c = customers[cid]
            start = max(arrival, c['earliest'])
            wait = start - arrival
            end = start + c['duration']
            early = max(Fraction(0), c['earliest'] - arrival)
            late = max(Fraction(0), start - c['latest'])
            feasible = late == 0
            route_temporal &= feasible
            customer_rows.append(dict(vehicle_id=vid, route_position=position, customer_id=cid,
                predecessor=prev, successor=nxt, arrival_time=json_number(arrival),
                earliest_service_time=json_number(c['earliest']), latest_service_time=json_number(c['latest']),
                waiting_time=json_number(wait), service_start_time=json_number(start),
                service_duration=json_number(c['duration']), service_end_time=json_number(end),
                departure_time=json_number(end), early_amount=json_number(early), late_amount=json_number(late),
                early_service_amount=0, late_arrival_amount=json_number(max(Fraction(0), arrival-c['latest'])),
                temporal_feasible=feasible))
            if not feasible:
                errors.append(dict(component='temporal', vehicle_id=vid, customer_id=cid, late_amount=json_number(late)))
            clock = end
            travel += duration
            wait_total += wait
            service += c['duration']
            distance = distance + metres if distance is not None and metres is not None else None
        duration, metres = arcs[stops[-2], depot]
        returned = clock + duration
        travel += duration
        distance = distance + metres if distance is not None and metres is not None else None
        depot_late = max(Fraction(0), returned-instance['closing'])
        dep = depot_late == 0
        if not route_temporal:
            temporal = False
        if not dep:
            depot_ok = False
            errors.append(dict(component='depot', vehicle_id=vid, late_amount=json_number(depot_late)))
        assert returned - instance['opening'] == travel + wait_total + service
        total_travel += travel
        vehicle_rows.append(dict(vehicle_id=vid, used=True, route=list(stops), load=json_number(load),
            capacity=json_number(capacity), capacity_feasible=cap, departure_time=json_number(instance['opening']),
            return_time=json_number(returned), depot_late_amount=json_number(depot_late),
            temporal_feasible=route_temporal, depot_feasible=dep, travel_time_seconds=json_number(travel),
            travel_distance=json_number(distance), waiting_time=json_number(wait_total),
            service_time=json_number(service), elapsed_time=json_number(returned-instance['opening'])))
    components = dict(visit_feasible=visit, route_feasible=route_ok, capacity_feasible=capacity_ok,
                      temporal_feasible=temporal, depot_feasible=depot_ok)
    overall = all(v is True for v in components.values())
    return dict(**components, overall_feasible=overall,
        status='VALID_SOLUTION' if overall else 'INVALID_SOLUTION',
        component_status={k: ('NOT_EVALUABLE' if v is None else 'PASS' if v else 'FAIL') for k,v in components.items()},
        customers=customer_rows, vehicles=vehicle_rows, errors=errors,
        routing_objective_seconds=json_number(total_travel) if route_ok else None,
        time_unit='seconds', arithmetic='exact decimal rational; fractional JSON outputs are decimal strings')
