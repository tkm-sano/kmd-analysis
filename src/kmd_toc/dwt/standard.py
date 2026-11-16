"""Standard products from validated plans. Export time is outside program T."""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import time
from .worker import dump

REQUIRED = ('plan.json', 'routes.geojson', 'stops.geojson', 'berth_events.csv',
            'metrics.json', 'manifest.json', 'validation.json')


class Geometry:
    def __init__(self, repo):
        self.repo = Path(repo)
        source = self.repo / 'output/toc_delivery/visualization_20261113_v1/data_access.py'
        spec = importlib.util.spec_from_file_location('retained_route_geometry', source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.roads = module.SavedRoads()
        self.indices = {case: {p.get('stop_id', p.get('depot_id')): i
                              for i, p in enumerate([x['depot'], *x['stops']])}
                        for case, x in self.roads.inputs.items()}
        self.cache = {}

    def leg(self, case, origin, destination):
        # Small road validation instances are ID subsets of frozen S1.
        case = case if case in self.indices else 'S1'
        key = (case, origin, destination)
        if key not in self.cache:
            row = self.roads.pair(case, self.indices[case][origin], self.indices[case][destination])
            if not row['geometry_check']['passed']:
                raise ValueError('GEOMETRY_HOLD')
            self.cache[key] = row
        return self.cache[key]


def export_standard(row, spec, out, geometry=None):
    out = Path(out)
    start = time.perf_counter()
    if row['status'] != 'VALIDATED':
        # A rejected actual candidate can be retained as a diagnostic, never as
        # a fictitious successful plan or an eligible point.
        if row.get('plan'):
            dump(out / 'rejected_plan.json', row['plan'])
        dump(out / 'validation.json', {'status': row['status'], 'common': row.get('validation'),
                                       'independent': row.get('second_validation'), 'error': row.get('error')})
        row['export_wall_s'] = time.perf_counter() - start
        dump(out / 'metrics.json', {k: v for k, v in row.items() if k != 'plan'})
        dump(out / 'manifest.json', {'status': 'NO_ACCEPTED_PLAN', 'spec': spec,
                                     'required_plan_products': 'not applicable to failed trial'})
        return row
    try:
        raw = json.loads(Path(spec['input_dir'], 'input.json').read_text())
        plan = row['plan']
        points = [raw['depot'], *raw['stops']]
        ids = [p.get('stop_id', p.get('depot_id')) for p in points]
        index = {v: i for i, v in enumerate(ids)}
        assignment = {}
        features = []
        events = []
        for trip in plan['trips']:
            path = [raw['depot']['depot_id'], *[v['stop_id'] for v in trip['visits']], raw['depot']['depot_id']]
            coords = []
            checked = 0.
            if geometry is not None:
                for u, v in zip(path, path[1:]):
                    leg = geometry.leg(row['scenario_id'], u, v)
                    coords.extend(leg['coordinates'] if not coords else leg['coordinates'][1:])
                    checked += leg['distance_m']
                if abs(checked - trip['distance_m']) > 1e-6:
                    raise ValueError('EXPORT_ROUTE_OD_DISTANCE')
                geo = {'type': 'LineString', 'coordinates': coords}
            else:
                # Artificial tests have no real road geometry. Null is honest;
                # road experiments require a functioning geometry resolver.
                if raw['experiment']['kind'] != 'synthetic_validation':
                    raise ValueError('REAL_ROAD_GEOMETRY_REQUIRED')
                geo = None
            props = {k: v for k, v in trip.items() if k != 'visits'}
            props.update(stop_count=len(trip['visits']), load=sum(points[index[v['stop_id']]]['demand'] for v in trip['visits']),
                         stop_order=[v['stop_id'] for v in trip['visits']], geometry_source='saved directed Route node annotation' if geo else 'synthetic witness; no road geometry')
            features.append({'type': 'Feature', 'geometry': geo, 'properties': props})
            for order, visit in enumerate(trip['visits'], 1):
                assignment[visit['stop_id']] = {'vehicle_id': trip['vehicle_id'], 'trip_no': trip['trip_no'], 'visit_order': order, **visit}
            events.append({k: trip[k] for k in ['vehicle_id', 'trip_no', 'berth_id', 'ready_s', 'load_start_s', 'load_end_s', 'departure_s', 'return_s', 'waiting_s']})
        stops = [{'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [p['longitude'], p['latitude']]},
                  'properties': {'id': ident, 'kind': 'depot' if i == 0 else 'delivery',
                                 'snap': p['snap'], **assignment.get(ident, {})}}
                 for i, (ident, p) in enumerate(zip(ids, points))]
        dump(out / 'plan.json', plan)
        dump(out / 'routes.geojson', {'type': 'FeatureCollection', 'features': features})
        dump(out / 'stops.geojson', {'type': 'FeatureCollection', 'features': stops})
        with (out / 'berth_events.csv').open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(events[0]))
            writer.writeheader()
            writer.writerows(events)
        dump(out / 'validation.json', {'status': 'PASS', 'common': row['validation'], 'independent': row['second_validation'],
                                       'route_geometries': 'all saved road legs checked' if geometry else 'not applicable: synthetic'})
        row.update(status='COMPLETE', standard_output_complete=True)
    except Exception as error:
        row.update(status='EXPORT_HOLD', standard_output_complete=False,
                   export_error={'type': type(error).__name__, 'message': str(error)})
        dump(out / 'validation.json', {'status': 'EXPORT_HOLD', 'error': row['export_error']})
    row['export_wall_s'] = time.perf_counter() - start
    dump(out / 'metrics.json', {k: v for k, v in row.items() if k != 'plan'})
    hashes = {name: hashlib.sha256((out / name).read_bytes()).hexdigest()
              for name in REQUIRED if name != 'manifest.json' and (out / name).exists()}
    dump(out / 'manifest.json', {'version': 'dwt-standard-v1', 'status': row['status'], 'spec': spec,
                                 'files': hashes, 'road_geometry_interpolation': False,
                                 'T_program_excludes_export': True})
    if row['status'] == 'COMPLETE' and not all((out / name).exists() for name in REQUIRED):
        row.update(status='EXPORT_HOLD', standard_output_complete=False)
        dump(out / 'metrics.json', {k: v for k, v in row.items() if k != 'plan'})
    return row
