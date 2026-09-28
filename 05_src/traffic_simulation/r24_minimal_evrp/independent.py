"""Saved-result verifier using Decimal; imports neither EV replay nor VRPTW helpers.

Inputs are separately hash-pinned by the audit runner. Exact finite decimal
operations at precision 80 cover this fixed fixture without tolerance slack.
"""
from decimal import Decimal, localcontext


def validate_saved(instance, authority, frozen_routes, result):
    errors = []
    def check(condition, label):
        if not condition:
            errors.append(label)
    def equal(actual, expected, label):
        try:
            check(Decimal(str(actual)) == expected, label)
        except Exception:
            errors.append(label + ': nonnumeric')
    with localcontext() as ctx:
        ctx.prec = 80
        p = {r['parameter']: r['value'] for r in authority['parameters']}
        maximum = Decimal(p['model_battery_capacity'])
        initial = maximum * Decimal(p['initial_SOC'])
        reserve = maximum * Decimal(p['minimum_SOC'])
        r = Decimal(p['energy_consumption_coefficient'])
        edges = {(e['origin'], e['destination']): e for e in instance['travel']}
        check(result['routes'] == frozen_routes, 'frozen routes')
        check(result['unit_audit'] == dict(source_distance_unit='m',energy_distance_unit='km',
              conversion='d[km] = travel_distance[m] / 1000'), 'unit declaration')
        expected_arcs, expected_events = 0, 0
        totals = dict(distance_km=Decimal(0),travel_time_s=Decimal(0),energy_kwh=Decimal(0))
        minima, fleet_ok = [], True
        for route in frozen_routes:
            if not route['stops']:
                continue
            vid, nodes = route['vehicle_id'], route['stops']
            arcs = [a for a in result['arcs'] if a['vehicle_id'] == vid]
            events = [e for e in result['trajectory'] if e['vehicle_id'] == vid]
            check(len(arcs)==len(nodes)-1, 'arc count '+vid)
            check(len(events)==len(nodes), 'event count '+vid)
            expected_arcs += len(nodes)-1; expected_events += len(nodes)
            energy_sum=distance_sum=time_sum=Decimal(0)
            batteries=[initial]
            for index,(origin,destination) in enumerate(zip(nodes,nodes[1:]),1):
                edge=edges[origin,destination]
                distance=Decimal(str(edge['travel_distance']))/Decimal(1000)
                duration=Decimal(str(edge['travel_time_seconds']))
                energy=r*distance
                before=initial-energy_sum
                energy_sum+=energy; distance_sum+=distance; time_sum+=duration
                after=initial-energy_sum; batteries.append(after)
                if index > len(arcs):
                    continue
                row=arcs[index-1]
                check((row['arc_index'],row['origin'],row['destination'])==(index,origin,destination),'arc identity')
                for key, value in dict(distance_km=distance,travel_time_s=duration,energy_kwh=energy,
                    battery_before_kwh=before,battery_after_kwh=after,soc_before_pct=100*before/maximum,
                    soc_after_pct=100*after/maximum,minimum_battery_kwh=reserve,q_chg_kwh=Decimal(0),t_chg_s=Decimal(0)).items():
                    equal(row[key],value,f'{vid}/{index}/{key}')
                equal(Decimal(str(row['battery_before_kwh']))-Decimal(str(row['energy_kwh'])),
                      Decimal(str(row['battery_after_kwh'])),'saved arc conservation')
                check(row['battery_feasible'] is (reserve<=after<=maximum),'arc feasibility')
            for pos, event in enumerate(events):
                if pos >= len(nodes):
                    continue
                battery=batteries[pos]
                check((event['position'],event['node'])==(pos,nodes[pos]),'event identity')
                for key,value in dict(departure_battery_kwh=battery,soc_departure_pct=100*battery/maximum,
                                      q_chg_kwh=Decimal(0),t_chg_s=Decimal(0)).items():
                    equal(event[key],value,'event '+key)
                if pos==0:
                    check(event['arrival_battery_kwh'] is None and event['soc_arrival_pct'] is None,'no invented initial arrival')
                else:
                    equal(event['arrival_battery_kwh'],battery,'arrival battery')
                    equal(event['soc_arrival_pct'],100*battery/maximum,'arrival SOC')
                check(event['battery_feasible'] is (reserve<=battery<=maximum),'event feasibility')
            summary=next(v for v in result['vehicles'] if v['vehicle_id']==vid)
            ok=all(reserve<=b<=maximum for b in batteries)
            check(summary['nodes']==nodes and summary['used'] is True,'vehicle identity')
            check(summary['ev_feasible'] is ok,'route feasibility')
            check(summary['status']==('PASS' if ok else 'FAIL'),'route status')
            for key,value in dict(distance_km=distance_sum,travel_time_s=time_sum,energy_kwh=energy_sum,
                minimum_battery_kwh=min(batteries),minimum_soc_pct=100*min(batteries)/maximum,
                final_battery_kwh=batteries[-1],final_soc_pct=100*batteries[-1]/maximum,
                q_chg_kwh=Decimal(0),t_chg_s=Decimal(0)).items():
                equal(summary[key],value,'summary '+key)
            equal(initial-Decimal(str(summary['energy_kwh'])),Decimal(str(summary['final_battery_kwh'])),'route conservation')
            for k,v in dict(distance_km=distance_sum,travel_time_s=time_sum,energy_kwh=energy_sum).items(): totals[k]+=v
            minima.append(min(batteries));fleet_ok &= ok
        used_ids={route['vehicle_id'] for route in frozen_routes if route['stops']}
        expected_ids={v['vehicle_id'] for v in instance['vehicles']}
        check(len(result['vehicles'])==len(expected_ids) and {v['vehicle_id'] for v in result['vehicles']}==expected_ids,'fleet identities')
        for v in result['vehicles']:
            if v['vehicle_id'] not in used_ids:
                check(v==dict(vehicle_id=v['vehicle_id'],used=False,nodes=[],ev_feasible=None,
                    status='NOT_EVALUABLE',distance_km=0,travel_time_s=0,energy_kwh=0),'unused semantics')
        check(len(result['arcs'])==expected_arcs and len(result['trajectory'])==expected_events,'no extra arcs/events')
        for k,v in totals.items(): equal(result['fleet'][k],v,'fleet '+k)
        equal(result['fleet']['minimum_battery_kwh'],min(minima),'fleet minimum')
        equal(result['fleet']['q_chg_kwh'],Decimal(0),'fleet charge')
        equal(result['fleet']['t_chg_s'],Decimal(0),'fleet charge time')
        check(result['fleet']['all_vehicles_ev_feasible'] is fleet_ok,'fleet feasibility')
        check(result['combined_feasible'] is bool(result['vrptw']['overall_feasible'] and fleet_ok),'combined feasibility')
    return dict(status='PASS' if not errors else 'FAIL',errors=errors,arcs_checked=expected_arcs,
                route_energy_conservation=True if not errors else False,
                method='independent Decimal precision80; prefix energy subtraction; no replay helpers',
                exact_tolerance=0,diagnostic_energy_tolerance_kwh='1e-9',diagnostic_time_tolerance_s='1e-7')
