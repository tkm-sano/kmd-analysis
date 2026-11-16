"""External component check, not an adapter for the full Ota delivery problem.

Amazon provides historical time matrices, not road-distance matrices. Both NN
projections below remain explicitly different from the full A2 distance policy.
"""
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace
import time

import numpy as np
from .construction import _nearest

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / 'configs/toc_delivery/a_sequence_external_v1.json'
CONFIG_SHA256 = 'cede2761a8bf75e19e30a4c49a8d48543303993c630125e6733bcbc81305dd6d'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def dump(path, value):
    with Path(path).open('x') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')


def settings():
    if digest(CONFIG) != CONFIG_SHA256:
        raise ValueError('SEQUENCE_PROTOCOL_HASH')
    return json.loads(CONFIG.read_text())


def iter_json_object(path, chunk_size=1024 * 1024):
    """Stream one top-level value at a time; reject truncated or trailing input."""
    decoder = json.JSONDecoder()
    with Path(path).open() as stream:
        buf, pos, eof = '', 0, False
        def refill():
            nonlocal buf, pos, eof
            block = stream.read(chunk_size)
            buf, pos = buf[pos:] + block, 0
            eof = not block
        def ws():
            nonlocal pos
            while True:
                while pos < len(buf) and buf[pos].isspace():
                    pos += 1
                if pos < len(buf) or eof:
                    return
                refill()
        def token(expected):
            nonlocal pos
            ws()
            if pos >= len(buf) or buf[pos] != expected:
                raise ValueError('STREAM_JSON_EXPECTED_' + expected)
            pos += 1
        def value():
            nonlocal pos
            ws()
            while True:
                try:
                    result, end = decoder.raw_decode(buf, pos)
                    if end == len(buf) and not eof:
                        refill()
                        continue
                    if end < len(buf) and not (buf[end].isspace() or buf[end] in ',}:'):
                        if eof:
                            raise ValueError('STREAM_JSON_INVALID_DELIMITER')
                        refill()
                        continue
                    pos = end
                    return result
                except json.JSONDecodeError:
                    if eof:
                        raise ValueError('STREAM_JSON_TRUNCATED_OR_INVALID')
                    refill()
        token('{')
        ws()
        first = True
        while pos >= len(buf) or buf[pos] != '}':
            if not first:
                token(',')
            key = value()
            if not isinstance(key, str):
                raise ValueError('STREAM_JSON_KEY')
            token(':')
            ws()
            yield key, value()
            first = False
            ws()
        token('}')
        ws()
        if pos < len(buf):
            raise ValueError('STREAM_JSON_TRAILING_DATA')


def ranked(seed, *parts):
    return hashlib.sha256('|'.join(map(str, (seed, *parts))).encode()).hexdigest()


def route_ids(route):
    stops = route['stops']
    station = [s for s, row in stops.items() if row['type'] == 'Station']
    if len(station) != 1 or any(r['type'] not in ('Station', 'Dropoff') for r in stops.values()):
        raise ValueError('ONE_STATION_AND_DROPOFF_TYPES_REQUIRED')
    if len(stops) < 3:
        raise ValueError('AT_LEAST_TWO_DROPOFFS')
    for stop in stops.values():
        if not (math.isfinite(stop['lat']) and math.isfinite(stop['lng']) and
                -90 <= stop['lat'] <= 90 and -180 <= stop['lng'] <= 180):
            raise ValueError('COORDINATES')
    return [station[0], *sorted(set(stops) - set(station))]


def select_routes(metadata, config):
    groups = defaultdict(lambda: defaultdict(list))
    excluded = []
    for rid, route in metadata.items():
        try:
            route_ids(route)
            groups[route['station_code']][route['date_YYYY_MM_DD']].append(rid)
        except (ValueError, KeyError, TypeError) as error:
            excluded.append({'route_id': rid, 'reason': str(error)})
    seed, policy = config['root_seed'], config['evaluation']
    selected = []
    for station in sorted(groups, key=lambda s: ranked(seed, s))[:policy['max_stations']]:
        for date in sorted(groups[station], key=lambda d: ranked(seed, station, d))[:policy['dates_per_station']]:
            selected += sorted(groups[station][date], key=lambda r: ranked(seed, r))[:policy['routes_per_station_date']]
    return selected, excluded


def time_matrix(ids, raw):
    if set(raw) != set(ids) or any(set(raw[s]) != set(ids) for s in ids):
        raise ValueError('MATRIX_IDS')
    matrix = np.array([[raw[a][b] for b in ids] for a in ids], dtype='float64')
    # Amazon aggregates package-location pairs within stops; even self-stop
    # averages can be positive. Preserve them, including for official scoring.
    if not np.isfinite(matrix).all() or (matrix < 0).any():
        raise ValueError('MATRIX_INVALID_OR_UNREACHABLE')
    if matrix.std() == 0:
        raise ValueError('OFFICIAL_SCORE_UNDEFINED_CONSTANT_MATRIX')
    return matrix


def geographic_matrix(ids, route):
    xy = np.array([[route['stops'][s]['lat'], route['stops'][s]['lng']] for s in ids])
    phi, lam = np.radians(xy[:, 0]), np.radians(xy[:, 1])
    a = np.sin((phi[:, None] - phi[None, :]) / 2)**2 + np.cos(phi[:, None]) * np.cos(phi[None, :]) * np.sin((lam[:, None] - lam[None, :]) / 2)**2
    return 6371008.8 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def nearest_projection(ids, costs):
    p = SimpleNamespace(od=SimpleNamespace(distance_m=costs),
                        stops=[SimpleNamespace(stop_id=s) for s in ids[1:]])
    return [ids[0], *[ids[i] for i in _nearest(range(1, len(ids)), p)]]


def validate_order(ids, sequence):
    if (len(sequence) != len(ids) or len(set(sequence)) != len(ids) or
            set(sequence) != set(ids) or sequence[0] != ids[0]):
        raise ValueError('VISIT_EXACTLY_ONCE_STATION_FIRST')


def actual_order(raw, ids):
    positions = raw['actual']
    if set(positions) != set(ids) or any(type(v) is not int for v in positions.values()) or sorted(positions.values()) != list(range(len(ids))):
        raise ValueError('ACTUAL_POSITIONS_NOT_PERMUTATION')
    order = sorted(positions, key=positions.__getitem__)
    validate_order(ids, order)
    return order


def sequence_deviation(actual, candidate):
    # Both lists include the station once, at the beginning, without a repeated end.
    rank = {s: i for i, s in enumerate(actual[1:])}
    positions = [rank[s] for s in candidate[1:]]
    n = len(positions)
    return 2 * sum(abs(b-a)-1 for a, b in zip(positions, positions[1:])) / (n*(n-1))


def official_normalization(matrix):
    standardized = (matrix - np.mean(matrix)) / np.std(matrix)
    return standardized - np.min(standardized)


def amazon_score(actual, candidate, ids, normalized):
    """Independent iterative ERP implementing the published challenge definition.

    Match the official suffix recursion's tie order: substitute, delete, insert.
    The official normalizer mutates nested dictionaries; this array version is pure.
    """
    validate_order(ids, actual)
    validate_order(ids, candidate)
    index = {s: i for i, s in enumerate(ids)}
    a = [index[s] for s in [*actual, actual[0]]]
    b = [index[s] for s in [*candidate, candidate[0]]]
    n, m, gap = len(a), len(b), 1000.
    following = [(m-j)*gap for j in range(m+1)]
    counts_next = [m-j for j in range(m+1)]
    costs = normalized.tolist()
    for i in range(n-1, -1, -1):
        row, counts = [0.] * (m+1), [0] * (m+1)
        row[m], counts[m] = (n-i)*gap, n-i
        for j in range(m-1, -1, -1):
            sub = following[j+1] + costs[a[i]][b[j]]
            delete, insert = following[j] + gap, row[j+1] + gap
            if sub <= delete and sub <= insert:
                row[j], counts[j] = sub, counts_next[j+1] + (a[i] != b[j])
            elif delete <= insert:
                row[j], counts[j] = delete, counts_next[j] + 1
            else:
                row[j], counts[j] = insert, counts[j+1] + 1
        following, counts_next = row, counts
    erp = following[0] / counts_next[0] if counts_next[0] else 0.
    return sequence_deviation(actual, candidate) * erp


def metrics(ids, sequence, actual, matrix, route, normalized):
    validate_order(ids, sequence)
    validate_order(ids, actual)
    index = {s: i for i, s in enumerate(ids)}
    def edges(order):
        return list(zip(order, [*order[1:], order[0]]))
    observed_edges, proposed_edges = edges(actual), edges(sequence)
    travel = math.fsum(float(matrix[index[a], index[b]]) for a, b in proposed_edges)
    actual_travel = math.fsum(float(matrix[index[a], index[b]]) for a, b in observed_edges)
    zones = []
    missing = 0
    for sid in sequence[1:]:
        zone = route['stops'][sid].get('zone_id')
        if not isinstance(zone, str) or not zone:
            missing += 1
        else:
            zones.append(zone)
    runs = [z for k, z in enumerate(zones) if k == 0 or z != zones[k-1]]
    reentries = len(runs) - len(set(runs)) if zones else None
    rank = {s: i for i, s in enumerate(actual[1:])}
    values = [rank[s] for s in sequence[1:]]
    inversions = sum(a > b for i, a in enumerate(values) for b in values[i+1:])
    return {'amazon_score': amazon_score(actual, sequence, ids, normalized),
            'sequence_deviation': sequence_deviation(actual, sequence),
            'directed_edge_agreement': len(set(observed_edges) & set(proposed_edges)) / len(observed_edges),
            'zone_reentries': reentries, 'known_zone_stop_count': len(zones), 'missing_zone_stop_count': missing,
            'zone_reentries_per_dropoff': reentries / (len(ids)-1) if reentries is not None else None,
            'matrix_travel_time_s_closed_route': travel,
            'matrix_travel_time_ratio_to_actual': travel / actual_travel if actual_travel > 0 else None,
            'normalized_Kendall_inversions': inversions / (len(values)*(len(values)-1)/2)}


def summarize(rows, config):
    successful = [r for r in rows if r['status'] == 'SCORED']
    methods = sorted({r['method'] for r in successful})
    columns = ('amazon_score', 'sequence_deviation', 'directed_edge_agreement', 'zone_reentries',
               'zone_reentries_per_dropoff', 'matrix_travel_time_ratio_to_actual', 'normalized_Kendall_inversions')
    result = {'attempted_rows': len(rows), 'failed_rows': len(rows)-len(successful), 'methods': {}, 'contrasts': {}}
    result['attempts_by_method'] = {method: {'attempted': sum(r['method']==method for r in rows),
        'failed': sum(r['method']==method and r['status']!='SCORED' for r in rows)} for method in {r['method'] for r in rows}}
    for method in methods:
        subset = [r for r in successful if r['method'] == method]
        result['methods'][method] = {'rows': len(subset), 'unique_routes': len({r['route_id'] for r in subset})}
        for col in columns:
            vals = [r[col] for r in subset if r.get(col) is not None]
            result['methods'][method][col] = {'n': len(vals), 'mean': float(np.mean(vals)) if vals else None,
                'median': float(np.median(vals)) if vals else None,
                'p10': float(np.quantile(vals, .1)) if vals else None, 'p90': float(np.quantile(vals, .9)) if vals else None}
    by_route = defaultdict(list)
    for r in successful:
        by_route[r['route_id']].append(r)
    for method in ['NN_time', 'NN_geodesic']:
        clusters = defaultdict(list)
        for values in by_route.values():
            nn = [r for r in values if r['method'] == method]
            random = [r['amazon_score'] for r in values if r['method'] == 'Random']
            if nn and len(random) == config['controls']['random_permutations_per_route']:
                r = nn[0]
                clusters[(r['station_code'], r['date'])].append(r['amazon_score'] - float(np.mean(random)))
        means = np.array([np.mean(v) for v in clusters.values()])
        if len(means) > 1:
            rng = np.random.default_rng(config['root_seed'])
            samples = rng.choice(means, size=(config['inference']['bootstrap_repetitions'], len(means)), replace=True).mean(axis=1)
            low, high = np.quantile(samples, [.025, .975])
            result['contrasts'][method] = {'clusters': len(means), 'routes': sum(map(len, clusters.values())),
                'mean_cluster_effect': float(means.mean()), 'bootstrap_95_interval': [float(low), float(high)],
                'better_than_random_on_sample': bool(high < 0), 'equivalent_to_drivers': None,
                'equivalence_margin': None, 'primary': method == 'NN_time'}
    result.update(full_A_representativeness='NOT_ESTABLISHED', original_A2_distance_validation='NOT_TESTED',
                  D_km=None, W_min=None, T_A_human_reference=None)
    return result


def run(data_directory, output):
    cfg = settings()
    out, data = Path(output), Path(data_directory)
    out.mkdir(parents=True, exist_ok=False)
    import os
    import platform
    import sys
    dump(out/'ENVIRONMENT.json', {'python': sys.version, 'executable': sys.executable,
        'platform': platform.platform(), 'numpy': np.__version__, 'affinity': sorted(os.sched_getaffinity(0)),
        'native_threads_environment': {k: os.environ.get(k) for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']},
        'T_scope': 'analysis wall; NOT A_program or human planning time'})
    begin = time.perf_counter()
    def bound():
        if time.perf_counter()-begin > cfg['limits']['analysis_wall_s']:
            raise TimeoutError('SEQUENCE_ANALYSIS_LIMIT')
    source_paths = [Path(__file__), ROOT/'scripts/validate_a_sequences.py',
                    ROOT/'src/kmd_toc/baseline_a/construction.py', CONFIG]
    source_hashes = {str(p.relative_to(ROOT)): digest(p) for p in source_paths}
    dump(out/'REGISTRATION.json', {'registered_at': datetime.now(timezone.utc).isoformat(),
        'protocol': cfg, 'protocol_sha256': CONFIG_SHA256, 'source_files': source_hashes,
        'actual_order_parsed': False, 'actual_file_bytes_hashed_for_integrity': True,
        'earlier_pilot_actual_order_parsed': False})
    rows = []
    try:
        manifest = json.loads((data/'MANIFEST.json').read_text())
        if manifest['status'] != 'COMPLETE' or set(manifest['files']) != {
                f'{s}_{k}.json' for s in ['pilot','eval'] for k in ['routes','times','actual']}:
            raise ValueError('DATA_MANIFEST_INCOMPLETE')
        for name, record in manifest['files'].items():
            if digest(data/name) != record['sha256']:
                raise ValueError('DATA_HASH: '+name)
            bound()
        dump(out/'INPUT_MANIFEST.json', manifest)
        metadata = {s: json.loads((data/f'{s}_routes.json').read_text()) for s in ['pilot', 'eval']}
        pilot = sorted(metadata['pilot'], key=lambda r: ranked(cfg['root_seed'], r))[:cfg['pilot']['routes']]
        evaluation, excluded = select_routes(metadata['eval'], cfg)
        if set(pilot) & set(evaluation):
            raise ValueError('PILOT_EVAL_ID_OVERLAP')
        selection = {'pilot': pilot, 'eval': evaluation, 'excluded_metadata': excluded,
                     'outcome_parsed': False, 'outcome_based_exclusions': False}
        dump(out/'SELECTION.json', selection)
        problems, proposals = {}, {}
        for split in ['pilot', 'eval']:
            selected = set(selection[split])
            found = set()
            for rid, raw in iter_json_object(data/f'{split}_times.json'):
                bound()
                if rid not in selected:
                    continue
                found.add(rid)
                route = metadata[split][rid]
                ids = route_ids(route)
                matrix = time_matrix(ids, raw)
                problems[rid] = (split, ids, matrix, route)
                generated = {'NN_time': nearest_projection(ids, matrix),
                             'NN_geodesic': nearest_projection(ids, geographic_matrix(ids, route)), 'Random': []}
                seed = int(ranked(cfg['root_seed'], rid)[:16], 16)
                rng = np.random.default_rng(seed)
                for _ in range(cfg['controls']['random_permutations_per_route']):
                    generated['Random'].append([ids[0], *rng.permutation(ids[1:]).tolist()])
                for method, sequences in generated.items():
                    for sequence in sequences if method == 'Random' else [sequences]:
                        validate_order(ids, sequence)
                proposals[rid] = generated
            if found != selected:
                raise ValueError('MISSING_SELECTED_MATRIX')
        dump(out/'PROPOSED_SEQUENCES.json', proposals)
        dump(out/'PROPOSALS_FROZEN.json', {'sha256': digest(out/'PROPOSED_SEQUENCES.json'),
            'actual_order_parsed': False, 'elapsed_s': time.perf_counter()-begin,
            'claim': 'all selected sequences committed before parsing any actual order; raw bytes only hashed earlier'})
        for split in ['pilot', 'eval']:
            actuals = json.loads((data/f'{split}_actual.json').read_text())
            for rid in selection[split]:
                _, ids, matrix, route = problems[rid]
                actual = actual_order(actuals[rid], ids)
                normalized = official_normalization(matrix)
                candidates = {'Actual': [actual], 'NN_time': [proposals[rid]['NN_time']],
                              'NN_geodesic': [proposals[rid]['NN_geodesic']], 'Random': proposals[rid]['Random']}
                for method, sequences in candidates.items():
                    for repetition, sequence in enumerate(sequences):
                        bound()
                        row = {'split': split, 'route_id': rid, 'station_code': route['station_code'],
                               'date': route['date_YYYY_MM_DD'], 'dropoffs': len(ids)-1,
                               'method': method, 'repetition': repetition}
                        try:
                            row.update(metrics(ids, sequence, actual, matrix, route, normalized), status='SCORED')
                        except Exception as error:
                            row.update(status='FAILED', error={'type': type(error).__name__, 'message': str(error)})
                        rows.append(row)
        dump(out/'ROUTE_METRICS.json', rows)
        dump(out/'SUMMARY.json', {s: summarize([r for r in rows if r['split'] == s], cfg) for s in ['pilot','eval']})
        import csv
        fields = sorted({k for r in rows for k in r})
        with (out/'ROUTE_METRICS.csv').open('x', newline='') as stream:
            writer = csv.DictWriter(stream, fields)
            writer.writeheader()
            writer.writerows(rows)
        dump(out/'RUN_STATUS.json', {'status': 'COMPLETE' if all(r['status']=='SCORED' for r in rows) else 'FAILED_ROWS',
            'elapsed_s': time.perf_counter()-begin, 'row_count': len(rows),
            'source_stability': all(digest(ROOT/p)==h for p,h in source_hashes.items()),
            'original_A2_not_modified': True})
    except Exception as error:
        dump(out/'FAILURE.json', {'status': 'FAILED', 'type': type(error).__name__, 'message': str(error),
            'elapsed_s': time.perf_counter()-begin, 'partial_scored_rows': len(rows)})
        if rows:
            dump(out/'PARTIAL_ROUTE_METRICS.json', rows)
        raise
    finally:
        dump(out/'OUTPUT_HASHES.json', {p.name: digest(p) for p in out.iterdir() if p.is_file()})
    return json.loads((out/'SUMMARY.json').read_text())
