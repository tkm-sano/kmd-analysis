"""Read-only provenance and input diagnostics; does not generate demand or routes."""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src'))
import numpy as np
from kmd_toc.frozen_demand import load_frozen_demand

UPSTREAM = ROOT / '03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1'
FROZEN = ROOT / '03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1'
INPUTS = ROOT / 'output/toc_delivery/ad_pipeline_20261112_route_v2/roads/inputs'
RAW = ROOT / '03_data/raw'
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
RADIUS_M = 6371008.8
READ_INPUTS = {}


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def register(path):
    key = str(path.relative_to(ROOT))
    READ_INPUTS[key] = {'sha256': digest(path), 'bytes': path.stat().st_size}
    return path


def rows(path, encoding='utf-8'):
    with register(path).open(encoding=encoding, newline='') as stream:
        return list(csv.DictReader(stream))


def read_json(path):
    return json.loads(register(path).read_text())


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def worksheet(path):
    """Extract first worksheet cells without executing formulas or changing XLSX."""
    with zipfile.ZipFile(register(path)) as archive:
        shared = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            shared = [''.join(x.itertext()) for x in ET.fromstring(
                archive.read('xl/sharedStrings.xml')).findall('m:si', NS)]
        cells = {}
        for cell in ET.fromstring(archive.read('xl/worksheets/sheet1.xml')).findall('.//m:c', NS):
            value = cell.find('m:v', NS)
            if cell.get('t') == 's' and value is not None:
                text = shared[int(value.text)]
            elif value is not None:
                text = value.text
            else:
                inline = cell.find('m:is', NS)
                text = ''.join(inline.itertext()) if inline is not None else ''
            if text:
                cells[cell.get('r')] = text
        return cells


def stats(values):
    values = np.asarray(values, dtype=float)
    assert values.size and np.isfinite(values).all()
    q = np.quantile(values, [0, .1, .5, .9, 1])
    return dict(zip(['min', 'p10', 'median', 'p90', 'max'], map(float, q))) | {
        'mean': float(values.mean()), 'n': int(values.size)}


def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(np.radians, (lon1, lat1, lon2, lat2))
    a = np.sin((lat2-lat1)/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin((lon2-lon1)/2)**2
    return 2 * RADIUS_M * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def hull_area_km2(lon, lat):
    # Equirectangular local approximation, not administrative/residential land area.
    x = RADIUS_M * np.radians(lon - lon.mean()) * math.cos(math.radians(float(lat.mean())))
    y = RADIUS_M * np.radians(lat - lat.mean())
    points = sorted(set(zip(map(float, x), map(float, y))))
    def cross(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lower, upper = [], []
    for p in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    polygon = lower[:-1] + upper[:-1]
    return abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(polygon, polygon[1:]+polygon[:1]))) / 2e6


def protected_snapshot():
    paths = [ROOT/'AGENTS.md', ROOT/'README.md', ROOT/'.gitignore']
    for folder in ['src/kmd_toc', 'configs/toc_delivery', 'tests/toc_baseline_a']:
        paths += [p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(set(paths)) if p.exists()}


def run(output):
    start = time.perf_counter()
    initial = protected_snapshot()
    write_json(output/'INITIAL_STATE.json', {'head': subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), 'protected_sha256': initial})
    (output/'INITIAL_GIT_STATUS.txt').write_text(subprocess.check_output(
        ['git', 'status', '--short'], cwd=ROOT, text=True))
    households = rows(UPSTREAM/'synthetic_households.csv')
    hh_types = Counter(r['household_size_class'] for r in households)
    # Recover and independently compare every cited census row/category.
    census_path = RAW/'external_statistics/census_2020_tokyo_small_area/census_000032163278.csv'
    census = list(csv.reader(register(census_path).read_text(encoding='cp932').splitlines()))
    cited = Counter((r['source_row'], r['household_size_class']) for r in households)
    mismatches = []
    # '-' denotes no count in the cited cells; never replace suppressed 'X'.
    def census_count(value):
        return 0 if value == '-' else int(value)
    for (source_row, category), count in cited.items():
        c = census[int(source_row)-1]
        expected = {'1人': census_count(c[12]), '2人': census_count(c[13]),
                    '3～4人': census_count(c[14])+census_count(c[15]),
                    '5人以上': sum(census_count(x) for x in c[16:19])}[category]
        if count != expected:
            mismatches.append({'row': source_row, 'category': category, 'generated': count, 'raw': expected})
        assert c[1] == '13111'
    assert not mismatches, mismatches[:10]
    propensity = rows(UPSTREAM/'relative_parcel_propensity.csv')
    receipt = worksheet(RAW/'traffic_simulation/demand_proxy/mlit_tokyo_metropolitan_goods_movement_survey_2024_20260823/ss521_r06a.xlsx')
    cell_by_type = {'1人': 'E7', '2人': 'E15', '3～4人': 'E22', '5人以上': 'E29'}
    for row in propensity:
        assert abs(float(receipt[cell_by_type[row['household_type']]]) - float(row['conditional_frequency_weekly'])) < 1e-12
    weighted_reference = sum(hh_types[r['household_type']]*float(r['conditional_frequency_weekly']) for r in propensity)/len(households)
    assert all(abs(weighted_reference-float(r['reference_frequency_weekly'])) < 1e-12 for r in propensity)
    housing = worksheet(RAW/'external_statistics/housing_land_2023/housing_000040209857.xlsx')
    housing_cells = {k: housing[k] for k in ['E4989','E4990','E4993','E4996','E5001']}
    assigned_housing = Counter(r['housing_type'] for r in rows(UPSTREAM/'synthetic_households_with_housing_type.csv'))
    original = {r['stop_id']: r for r in rows(UPSTREAM/'building_delivery_stops_scoped.csv')}
    candidates = defaultdict(list)
    for row in rows(UPSTREAM/'plateau_residential_building_candidates.csv'):
        candidates[row['building_id']].append(row)
    conditions = read_json(ROOT/'configs/toc_delivery/common_conditions_v1_1.json')
    # Pin the complete frozen bundle and source pin/config before deriving summaries.
    for p in sorted(FROZEN.iterdir()):
        register(p)
    register(ROOT/'configs/toc_delivery/frozen_demand_v1.json')
    register(ROOT/'src/kmd_toc/frozen_demand_pin.py')
    profiles = []
    for scenario in ['S1','S2','S3']:
        demand = load_frozen_demand(scenario, method_id='A')
        inp = read_json(INPUTS/scenario/'input.json')
        manifest = read_json(INPUTS/scenario/'od/manifest.json')
        arrays = {}
        for name, expected in manifest['files'].items():
            path = register(INPUTS/scenario/'od'/name)
            assert READ_INPUTS[str(path.relative_to(ROOT))]['sha256'] == expected
            arrays[name] = np.load(path, mmap_mode='r', allow_pickle=False)
        n = demand.N
        ids = [inp['depot']['depot_id']] + [s['stop_id'] for s in inp['stops']]
        assert ids == manifest['ids']
        assert [s.stop_id for s in demand.stops] == ids[1:]
        assert all(a.shape == (n+1,n+1) for a in arrays.values())
        dm, ts, reachable = (arrays[k] for k in ['distance_m.npy','duration_s.npy','reachable.npy'])
        assert manifest['metadata']['table_distances_used'] is False
        assert 'Route per ordered pair' in manifest['metadata']['matrix_service']
        assert np.isfinite(dm).all() and np.isfinite(ts).all() and (dm >= 0).all() and (ts >= 0).all()
        assert reachable.all()
        lon = np.array([float(s.longitude) for s in demand.stops])
        lat = np.array([float(s.latitude) for s in demand.stops])
        assert np.allclose(lon, [s['longitude'] for s in inp['stops']], rtol=0, atol=1e-12)
        assert np.allclose(lat, [s['latitude'] for s in inp['stops']], rtol=0, atol=1e-12)
        nearest_geo = np.full(n, np.inf)
        nearest_road = np.full(n, np.inf)
        for first in range(0, n, 128):
            last = min(first+128, n)
            geo = haversine(lon[first:last,None], lat[first:last,None], lon[None,:], lat[None,:])
            road = np.array(dm[first+1:last+1,1:], dtype=float)
            rr = np.arange(last-first)
            geo[rr, np.arange(first,last)] = np.inf
            road[rr, np.arange(first,last)] = np.inf
            nearest_geo[first:last] = geo.min(axis=1)
            nearest_road[first:last] = road.min(axis=1)
        area = hull_area_km2(lon, lat)
        usage, compatibility, heights, floors = Counter(), Counter(), [], []
        missing, ambiguous, source_pe, source_requests = [], [], [], []
        for stop in demand.stops:
            src = original[stop.stop_id]
            assert src['building_id'] == stop.building_id and src['chocho_code'] == stop.chocho_code
            source_pe.append(int(src['parcel_equivalent']))
            source_requests.append(int(src['request_count']))
            matched = candidates.get(stop.building_id, [])
            if not matched:
                missing.append(stop.building_id)
                continue
            if len(matched) != 1:
                ambiguous.append(stop.building_id)
                continue
            row = matched[0]
            usage[row['building_usage']] += 1
            compatibility[row['housing_type_compatibility']] += 1
            for key, dest in [('height_m',heights),('floors',floors)]:
                try:
                    value = float(row[key])
                    if math.isfinite(value) and 0 < value < 9999:
                        dest.append(value)
                except (ValueError,TypeError):
                    pass
        depot = inp['depot']
        profiles.append({
            'scenario':scenario, 'n':n, 'vehicles':len(inp['vehicles']), 'berths':len(inp['berths']),
            'stops_per_vehicle': n/len(inp['vehicles']),
            'minimum_trips_from_total_capacity_only': math.ceil(n/inp['vehicles'][0]['capacity']),
            'maximum_trips':sum(v['max_trips'] for v in inp['vehicles']),
            'active_chocho':len(set(s.chocho_code for s in demand.stops)),
            'bbox_west_south_east_north':[float(lon.min()),float(lat.min()),float(lon.max()),float(lat.max())],
            'convex_hull_area_approx_km2':area,
            'selected_stops_per_convex_hull_km2':n/area,
            'depot_haversine_km':stats(haversine(depot['longitude'],depot['latitude'],lon,lat)/1000),
            'depot_outbound_road_km':stats(dm[0,1:]/1000),
            'depot_inbound_road_km':stats(dm[1:,0]/1000),
            'depot_outbound_road_minutes':stats(ts[0,1:]/60),
            'nearest_other_stop_haversine_m':stats(nearest_geo),
            'nearest_other_stop_directed_outbound_road_m':stats(nearest_road),
            'zero_distance_nearest_other_stop_count':int((nearest_road==0).sum()),
            'source_building_attributes_matched':n-len(missing)-len(ambiguous),
            'source_building_attributes_missing':missing,
            'source_building_attributes_ambiguous':ambiguous,
            'source_building_usage':dict(usage), 'source_housing_compatibility':dict(compatibility),
            'source_height_m':stats(heights) if heights else None,
            'source_floors_excluding_sentinels':stats(floors) if floors else None,
            'upstream_pe_at_selected_stops':sum(source_pe),
            'upstream_requests_at_selected_stops':sum(source_requests),
            'current_controlled_parcels':sum(s.parcel_count for s in demand.stops),
            'operator_zone_ids_available':False, 'actual_sequence_available':False,
            'package_time_windows_available':False,
            'unreachable_ordered_pairs':int((~reachable.astype(bool)).sum()),
            'od_hashes_verified':True,
        })
    write_json(output/'DATA_LINEAGE_CHECKS.json', {
        'synthetic_households':len(households), 'household_size_counts':dict(hh_types),
        'cited_census_row_category_groups':len(cited),
        'cited_census_rows':len(set(k[0] for k in cited)),
        'census_cited_category_count_mismatches':mismatches,
        'receipt_weekly_frequency_cells':{k:{'cell':v,'value':receipt[v]} for k,v in cell_by_type.items()},
        'receipt_note_cells':{k:receipt[k] for k in ['A41','A42','A43','A44']},
        'reference_weighted_by_synthetic_households':weighted_reference,
        'raw_receipt_total_E39':receipt['E39'],
        'housing_source_cells':housing_cells, 'housing_source_unit':'住宅数, not observed households',
        'synthetic_housing_type_counts':dict(assigned_housing),
        'upstream_unique_stops':len(original),
        'original_generator_recovered':False,
        'common_conditions_read_only':conditions,
    })
    write_json(output/'INPUT_PROFILES.json', profiles)
    write_json(output/'INPUT_HASHES.json', READ_INPUTS)
    # Small independent sanity checks for units/formulas, not solver experiments.
    assert abs(float(haversine(0,0,0,0))) < 1e-12
    assert abs(float(haversine(0,0,1,0))-RADIUS_M*math.pi/180) < 1e-6
    square_lon = np.array([0,1,1,0.0]); square_lat = np.array([0,0,1,1.0])
    expected_area = (RADIUS_M*math.pi/180)**2*math.cos(math.pi/360)/1e6
    assert abs(hull_area_km2(square_lon,square_lat)-expected_area) < 1e-6
    assert sum(hh_types.values()) == 384353
    final = protected_snapshot()
    changed = [p for p,h in initial.items() if final.get(p) != h]
    changed_inputs = [p for p,v in READ_INPUTS.items() if digest(ROOT/p) != v['sha256']]
    write_json(output/'VALIDATION.json', {
        'protected_files':len(initial), 'changed_protected_files':changed,
        'input_files':len(READ_INPUTS), 'changed_input_files':changed_inputs,
        'elapsed_wall_seconds':time.perf_counter()-start,
        'python':sys.version, 'numpy':np.__version__, 'platform':platform.platform(),
        'scope':'read_only_descriptive_audit_no_demand_generation_no_route_optimization',
        'timestamp_utc':datetime.now(timezone.utc).isoformat(),
        'all_checks_passed':not changed and not changed_inputs})
    assert not changed and not changed_inputs
    print(json.dumps({'output':str(output.relative_to(ROOT)), 'profiles':len(profiles),
                      'input_files':len(READ_INPUTS), 'protected_files':len(initial)},ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    try:
        run(output)
    except Exception as error:
        write_json(output/'FAILURE.json', {'type':type(error).__name__, 'message':str(error)})
        raise
