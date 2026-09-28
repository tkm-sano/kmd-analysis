"""Exact kWh accounting over unchanged VRPTW routes and temporal validation."""
from fractions import Fraction
from r24_vrptw.instance import InputError, number, json_number, validate_input
from r24_vrptw.validator import validate_routes


def parameters(authority):
    if (authority['MINIMAL_EVRP_DESIGN_AUTHORITY'] != 'FROZEN'
            or authority['IMPLEMENTATION_READY'] != 'YES'
            or authority['charging_availability_first_case'] != []):
        raise InputError('Frozen charger-disabled authority required')
    rows = {p['parameter']: p for p in authority['parameters']}
    keys = ('model_battery_capacity', 'initial_SOC', 'minimum_SOC',
            'energy_consumption_coefficient')
    values = tuple(number(rows[k]['value'], k) for k in keys)
    # This module implements only this frozen reference, not scenario controls.
    if values != (Fraction(20), Fraction(1), Fraction(1, 10), Fraction(127, 1000)):
        raise InputError('Frozen reference parameter mismatch')
    return values


def distance_km(value, source_unit):
    if source_unit != 'm':
        raise InputError('Explicit frozen source distance unit m required')
    value = number(value, 'distance_m')
    if value < 0:
        raise InputError('Negative distance')
    return value / 1000


def energy_kwh(distance, coefficient):
    return distance * coefficient


def battery_after(before, energy):
    return before - energy


def battery_feasible(battery, minimum, maximum):
    return minimum <= battery <= maximum


def replay(instance, routes, authority, *, source_distance_unit):
    """Return EV sidecar plus untouched base validation; never repair a route."""
    maximum, initial_soc, minimum_soc, coefficient = parameters(authority)
    initial, minimum = maximum * initial_soc, maximum * minimum_soc
    base = validate_routes(instance, routes)
    parsed = validate_input(instance)
    arc_rows, trajectory, summaries = [], [], []
    for vehicle in base['vehicles']:
        vid, nodes = vehicle['vehicle_id'], vehicle['route']
        if not vehicle['used']:
            summaries.append(dict(vehicle_id=vid, used=False, nodes=[], ev_feasible=None,
                                  status='NOT_EVALUABLE', distance_km=0,
                                  travel_time_s=0, energy_kwh=0))
            continue
        if vehicle['return_time'] is None:
            summaries.append(dict(vehicle_id=vid, used=True, nodes=nodes,
                                  ev_feasible=None, status='NOT_EVALUABLE'))
            continue
        battery = initial
        distances, times, energies = [], [], []
        trajectory.append(dict(vehicle_id=vid, position=0, node=nodes[0],
            arrival_battery_kwh=None, departure_battery_kwh=json_number(initial),
            soc_arrival_pct=None, soc_departure_pct=json_number(100*initial/maximum),
            q_chg_kwh=0, t_chg_s=0, battery_feasible=battery_feasible(initial,minimum,maximum)))
        feasible = battery_feasible(initial, minimum, maximum)
        for pos, (origin, destination) in enumerate(zip(nodes, nodes[1:]), 1):
            time, metres = parsed['arcs'][origin, destination]
            if metres is None:
                raise InputError('Missing frozen road distance')
            distance = distance_km(json_number(metres), source_distance_unit)
            energy = energy_kwh(distance, coefficient)
            after = battery_after(battery, energy)
            ok = battery_feasible(after, minimum, maximum)
            feasible &= ok
            arc_rows.append(dict(vehicle_id=vid, arc_index=pos, origin=origin,
                destination=destination, distance_km=json_number(distance),
                travel_time_s=json_number(time), energy_kwh=json_number(energy),
                battery_before_kwh=json_number(battery), battery_after_kwh=json_number(after),
                soc_before_pct=json_number(100*battery/maximum),
                soc_after_pct=json_number(100*after/maximum), minimum_battery_kwh=json_number(minimum),
                q_chg_kwh=0, t_chg_s=0, battery_feasible=ok))
            trajectory.append(dict(vehicle_id=vid, position=pos, node=destination,
                arrival_battery_kwh=json_number(after), departure_battery_kwh=json_number(after),
                soc_arrival_pct=json_number(100*after/maximum),
                soc_departure_pct=json_number(100*after/maximum), q_chg_kwh=0,t_chg_s=0,
                battery_feasible=ok))
            distances.append(distance); times.append(time); energies.append(energy)
            battery = after
        summaries.append(dict(vehicle_id=vid, used=True, nodes=nodes,
            distance_km=json_number(sum(distances)),travel_time_s=json_number(sum(times)),
            energy_kwh=json_number(sum(energies)),minimum_battery_kwh=json_number(battery),
            minimum_soc_pct=json_number(100*battery/maximum),final_battery_kwh=json_number(battery),
            final_soc_pct=json_number(100*battery/maximum),ev_feasible=feasible,
            status='PASS' if feasible else 'FAIL',q_chg_kwh=0,t_chg_s=0))
    used = [s for s in summaries if s['used']]
    evaluable = all(s['ev_feasible'] is not None for s in used)
    fleet = None
    if used and evaluable:
        fleet = {k: json_number(sum(number(s[k],k) for s in used))
                 for k in ('distance_km','travel_time_s','energy_kwh')}
        fleet.update(minimum_battery_kwh=json_number(min(number(s['minimum_battery_kwh'],'B') for s in used)),
                     all_vehicles_ev_feasible=all(s['ev_feasible'] for s in used),q_chg_kwh=0,t_chg_s=0)
    return dict(schema='minimal-evrp-zero-charge-v1', role='MODEL_VALIDATION',
                routes=routes, vrptw=base, arcs=arc_rows, trajectory=trajectory,
                vehicles=summaries, fleet=fleet, unit_audit=dict(source_distance_unit=source_distance_unit,
                energy_distance_unit='km',conversion='d[km] = travel_distance[m] / 1000'),
                combined_feasible=bool(base['overall_feasible'] and fleet and fleet['all_vehicles_ev_feasible']),
                arithmetic='exact Fraction; reserve comparison tolerance 0; diagnostic energy 1e-9 kWh/time 1e-7 s')
