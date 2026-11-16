"""Independent GeoJSON/CSV audit, scalar road-length port, no builder imports."""
from bisect import bisect_left
from collections import Counter, defaultdict
import csv
import json
import math
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'output/toc_delivery/dwt_balance_20261113_v1/revision_1_3_1')
checks, arcs = [], []


def check(name, condition):
    checks.append({'check': name, 'passed': bool(condition)})


def length(points):
    value = []
    f = 1 / 298.257223563
    e2 = f * (2 - f)
    for a, b in zip(points, points[1:]):
        a = [math.floor(x * 1e6 + .5) for x in a]
        b = [math.floor(x * 1e6 + .5) for x in b]
        avg = (a[1] + b[1]) // 2
        bucket = math.floor((abs(avg) - 1) / 50000)
        phi = math.radians((bucket + .5) * .05)
        w = math.sqrt(1 - e2 * math.sin(phi) ** 2)
        kx = math.pi / 180 * 6378137 * math.cos(phi) / w
        ky = math.pi / 180 * 6378137 * (1 - e2) / w ** 3
        value.append(math.hypot((b[0] - a[0]) / 1e6 * kx, (b[1] - a[1]) / 1e6 * ky))
    return math.fsum(value)


import numpy as np
for file in sorted((root / 'trials').glob('*/metrics.json')):
    row = json.loads(file.read_text())
    if row['status'] != 'COMPLETE':
        continue
    out = file.parent
    spec = json.loads((out / 'spec.json').read_text())
    raw = json.loads(Path(spec['input_dir'], 'input.json').read_text())
    plan = json.loads((out / 'plan.json').read_text())
    stops = json.loads((out / 'stops.geojson').read_text())
    routes = json.loads((out / 'routes.geojson').read_text())
    points = [raw['depot'], *raw['stops']]
    ids = [p.get('stop_id', p.get('depot_id')) for p in points]
    indices = {j: i for i, j in enumerate(ids)}
    distance = np.load(Path(spec['input_dir'], 'od/distance_m.npy'), mmap_mode='r')
    label = row['trial_id']
    check(label + ':GeoJSON exact point IDs', Counter(f['properties']['id'] for f in stops['features']) == Counter(ids))
    by = {f['properties']['id']: f for f in stops['features']}
    for p, ident in zip(points, ids):
        f = by[ident]
        check(label + ':original/snap:' + ident, f['geometry'] == {'type': 'Point', 'coordinates': [p['longitude'], p['latitude']]}
              and f['properties']['snap'] == p['snap'])
    with (out / 'berth_events.csv').open() as h:
        events = list(csv.DictReader(h))
    check(label + ':Gantt row count', len(events) == len(plan['trips']))
    for event, trip in zip(events, plan['trips']):
        check(label + ':Gantt exact raw fields:' + trip['vehicle_id'] + ':' + str(trip['trip_no']),
              all(event[k] == str(trip[k]) for k in event))
    for trip, feature in zip(plan['trips'], routes['features']):
        tag = label + ':' + trip['vehicle_id'] + ':' + str(trip['trip_no'])
        geometry = feature['geometry']
        check(tag + ':valid real LineString', geometry is not None and geometry['type'] == 'LineString' and len(geometry['coordinates']) >= 2)
        if not geometry:
            continue
        coordinates = geometry['coordinates']
        positions = defaultdict(list)
        for i, xy in enumerate(coordinates):
            positions[tuple(xy)].append(i)
        order = [raw['depot']['depot_id'], *[x['stop_id'] for x in trip['visits']], raw['depot']['depot_id']]
        cursor = 0
        for number, (a, b) in enumerate(zip(order, order[1:])):
            snap = points[indices[b]]['snap']
            target = (snap['longitude'], snap['latitude'])
            expected = float(distance[indices[a], indices[b]])
            available = positions.get(target, [])
            found = None
            for endpoint in available[bisect_left(available, cursor):]:
                reconstructed = length(coordinates[cursor:endpoint + 1])
                if abs(reconstructed - expected) <= .35:
                    found = endpoint
                    break
            ok = found is not None
            check(tag + ':independent arc shape:' + str(number), ok)
            arcs.append({'trial_id': label, 'vehicle_id': trip['vehicle_id'], 'trip_no': trip['trip_no'],
                         'arc': number, 'from_id': a, 'to_id': b, 'OD_distance_m': expected,
                         'shape_distance_m': reconstructed if ok else None,
                         'delta_m': reconstructed - expected if ok else None, 'passed': ok})
            if not ok:
                break
            cursor = found
        check(tag + ':all geometry consumed in visit order', cursor == len(coordinates) - 1)
    parallel_profile = row.get('cpu_parallel_profile')
    expected_cpus = (parallel_profile['cpu_ids'] if parallel_profile else
                     [spec['config']['compute_affinity']['logical_cpu']])
    check(label + ':actual same CPU affinity', row.get('cpu_affinity') == expected_cpus)
    if parallel_profile:
        branches = row.get('parallel_branches', [])
        check(label + ':one branch per allocated CPU', len(branches) == parallel_profile['workers']
              and [b['cpu_affinity'] for b in branches] == [[cpu] for cpu in expected_cpus])

with (root / 'STANDARD_GEOMETRY_AUDIT.csv').open('w', newline='') as h:
    fields = ['trial_id', 'vehicle_id', 'trip_no', 'arc', 'from_id', 'to_id', 'OD_distance_m', 'shape_distance_m', 'delta_m', 'passed']
    writer = csv.DictWriter(h, fieldnames=fields)
    writer.writeheader()
    writer.writerows(arcs)
report = {'checks': len(checks), 'passed': sum(x['passed'] for x in checks), 'failed': [x for x in checks if not x['passed']],
          'road_arcs': len(arcs), 'max_abs_shape_delta_m': max((abs(x['delta_m']) for x in arcs if x['delta_m'] is not None), default=None),
          'tolerance_m': .35, 'scope': 'raw inputs, published coordinates partitioned at ordered snap endpoints, independent scalar OSRM CheapRuler, no producer/optimizer import', 'details': checks}
(root / 'STANDARD_OUTPUT_AUDIT.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print({k: v for k, v in report.items() if k != 'details'})
if report['failed']:
    raise SystemExit(1)
