"""Third calculation from raw JSON/NPY, independent of generators and evaluator."""
from collections import Counter, defaultdict
import csv
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_EVEN
import hashlib
import json
from pathlib import Path
import numpy as np


def audit(root):
    root = Path(root)
    checks = []
    def check(name, value):
        checks.append({'check': name, 'passed': bool(value)})
    records = []
    for file in sorted((root / 'trials').glob('*/metrics.json')):
        row = json.loads(file.read_text())
        records.append(row)
        out = file.parent
        spec = json.loads((out / 'spec.json').read_text())
        if row['status'] != 'COMPLETE':
            check(row['trial_id'] + ':failure_retained', (out / 'validation.json').exists() and (out / 'manifest.json').exists())
            continue
        raw = json.loads(Path(spec['input_dir'], 'input.json').read_text())
        plan = json.loads((out / 'plan.json').read_text())
        manifest = json.loads((out / 'manifest.json').read_text())
        ids = [raw['depot']['depot_id'], *[s['stop_id'] for s in raw['stops']]]
        index = {j: i for i, j in enumerate(ids)}
        d = np.load(Path(spec['input_dir'], 'od/distance_m.npy'), mmap_mode='r')
        t = np.load(Path(spec['input_dir'], 'od/duration_s.npy'), mmap_mode='r')
        all_seen = Counter()
        distance, waiting = Decimal(0), Decimal(0)
        vehicles = {v['vehicle_id']: v for v in raw['vehicles']}
        previous, counts, berths = {}, Counter(), defaultdict(list)
        stop_demand = {s['stop_id']: s['demand'] for s in raw['stops']}
        geometry = json.loads((out / 'routes.geojson').read_text())['features']
        check(row['trial_id'] + ':same_input_hash', row['input_hash'] == plan['problem_hash'] == raw['problem_hash'])
        check(row['trial_id'] + ':same_OD_hash', row['OD_hash'] == plan['od_hash'] == raw['od_hash'])
        check(row['trial_id'] + ':geometry_trip_count', len(geometry) == len(plan['trips']))
        for trip, feature in zip(plan['trips'], geometry):
            label = row['trial_id'] + ':' + trip['vehicle_id'] + ':' + str(trip['trip_no'])
            v = trip['vehicle_id']
            counts[v] += 1
            seen = [s['stop_id'] for s in trip['visits']]
            all_seen.update(seen)
            nodes = [raw['depot']['depot_id'], *seen, raw['depot']['depot_id']]
            length = sum((Decimal(str(d[index[a], index[b]])) for a, b in zip(nodes, nodes[1:])), Decimal(0))
            distance += length
            check(label + ':depot', trip['origin_id'] == trip['destination_id'] == nodes[0])
            check(label + ':load_capacity', sum(stop_demand[s] for s in seen) <= vehicles[v]['capacity'])
            ready = vehicles[v]['first_ready_s'] if counts[v] == 1 else previous[v]
            check(label + ':trip_ready', trip['ready_s'] == ready and trip['trip_no'] == counts[v])
            check(label + ':nonnegative_wait', trip['load_start_s'] >= ready)
            wait = trip['load_start_s'] - ready
            waiting += Decimal(wait) / 60
            check(label + ':reported_wait', trip['waiting_s'] == wait)
            check(label + ':load_and_depart', trip['load_end_s'] - trip['load_start_s'] == 1800 and trip['departure_s'] == trip['load_end_s'])
            clock = trip['departure_s']
            for a, visit in zip(nodes, trip['visits']):
                clock += int(Decimal(str(t[index[a], index[visit['stop_id']]])).to_integral_value(rounding=ROUND_CEILING))
                check(label + ':arrival:' + visit['stop_id'], (visit['arrival_s'], visit['service_start_s'], visit['service_end_s']) == (clock, clock, clock + 120))
                clock += 120
            clock += int(Decimal(str(t[index[nodes[-2]], 0])).to_integral_value(rounding=ROUND_CEILING))
            check(label + ':return_and_shift', clock == trip['return_s'] <= vehicles[v]['return_deadline_s'])
            previous[v] = clock
            berths[trip['berth_id']].append((trip['load_start_s'], trip['load_end_s']))
            check(label + ':distance', abs(length - Decimal(str(trip['distance_m']))) < Decimal('0.000001'))
            check(label + ':GeoJSON_same_route', feature['properties']['stop_order'] == seen and feature['properties']['vehicle_id'] == v)
            if feature['geometry'] is not None:
                snap = raw['depot']['snap']
                check(label + ':geometry_closes_at_real_depot', feature['geometry']['coordinates'][0] == feature['geometry']['coordinates'][-1] == [snap['longitude'], snap['latitude']])
        for v, n in counts.items():
            check(row['trial_id'] + ':max2:' + v, n <= 2)
        for b, intervals in berths.items():
            a = sorted(intervals)
            check(row['trial_id'] + ':berth:' + b, all(x[1] <= y[0] for x, y in zip(a, a[1:])))
        check(row['trial_id'] + ':exact_coverage', all_seen == Counter({s['stop_id']: 1 for s in raw['stops']}))
        check(row['trial_id'] + ':D', abs(distance / 1000 - Decimal(str(row['D_km']))) < Decimal('0.0000001'))
        check(row['trial_id'] + ':W', abs(waiting - Decimal(str(row['W_min']))) < Decimal('0.0000001'))
        check(row['trial_id'] + ':epsilon', row['epsilon_W_min'] is None or waiting <= Decimal(str(row['epsilon_W_min'])) + Decimal('1e-9'))
        check(row['trial_id'] + ':total_T_budget', 0 < row['T_program_s'] <= row['tau_s'])
        events = row['timing_events']
        check(row['trial_id'] + ':T_boundaries', events[0]['name'] == 'input_load_start' and events[0]['elapsed_s'] == 0
              and events[-1]['name'] == 'final_validation_end' and events[-1]['elapsed_s'] == row['T_program_s'])
        check(row['trial_id'] + ':output_hashes', all(hashlib.sha256((out / p).read_bytes()).hexdigest() == h for p, h in manifest['files'].items()))
        check(row['trial_id'] + ':all_standard_products', all((out / name).exists() for name in
              ['plan.json', 'routes.geojson', 'stops.geojson', 'berth_events.csv', 'metrics.json', 'manifest.json', 'validation.json']))
        with (out / 'berth_events.csv').open() as f:
            event_rows = list(csv.DictReader(f))
        check(row['trial_id'] + ':Gantt_W', sum(int(e['load_start_s']) - int(e['ready_s']) for e in event_rows) / 60 == row['W_min'])
    evaluation = root / 'THREE_OBJECTIVE_EVALUATION.json'
    if evaluation.exists():
        published = json.loads(evaluation.read_text())
        valid = [r for r in records if r['phase'] == 'limited' and r['status'] == 'COMPLETE' and r['method'] in ('B', 'C', 'D')]
        def vec(row):
            return [Decimal(str(row[k])).quantize(Decimal(q), rounding=ROUND_HALF_EVEN) for k, q in
                    zip(['D_km', 'W_min', 'T_program_s'], ['1e-7', '1e-7', '1e-6'])]
        independent_front = []
        for q in valid:
            y = vec(q)
            if not any(p['input_hash'] == q['input_hash'] and all(a <= b for a, b in zip(vec(p), y))
                       and any(a < b for a, b in zip(vec(p), y)) for p in valid):
                independent_front.append(q['trial_id'])
        check('independent_full_3D_front', set(independent_front) == set(published['front_trial_ids']))
        by_id = {r['trial_id']: r for r in records}
        for sensitivity in published['weight_reference_sensitivity']:
            if sensitivity['J'] is not None:
                row = by_id[sensitivity['trial_id']]
                raw_score = sum(Decimal(str(w)) * Decimal(str(row[k])) / Decimal(str(sensitivity['reference'][k]))
                                for w, k in zip(sensitivity['weights'], ['D_km', 'W_min', 'T_program_s']))
                check('independent_J:' + sensitivity['trial_id'], abs(Decimal(str(sensitivity['J'])) - raw_score) < Decimal('1e-12'))
    seedpairs = [(r.get('solver_seed'), r.get('quantum_seed')) for r in records if r['method'] in ('B', 'C', 'D')]
    check('distinct_registered_trial_streams', len(seedpairs) == len(set(seedpairs)))
    report = {'checks': len(checks), 'passed': sum(c['passed'] for c in checks),
              'failed': [c for c in checks if not c['passed']], 'details': checks,
              'scope': 'raw JSON/NPY Decimal/events/GeoJSON output identities/full pairwise Pareto; imports no generator or main evaluator'}
    (root / 'INDEPENDENT_DWT_VALIDATION.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    if report['failed']:
        raise ValueError(report['failed'][:5])
    return report
