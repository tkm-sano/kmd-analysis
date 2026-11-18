"""Distance/wait-only research policy and read-only analysis of saved trials.

This module never calls a solver, changes a registration, or consumes timing
values. Old three-objective implementations remain available for reproduction.
"""
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
from statistics import mean, median, stdev, variance

POLICY_ID = 'ota-toc-DW-20261117-v1'
METHODS = ('A', 'B', 'C', 'D', 'D_CLASSICAL_REPLACEMENT')
SCALES = ('S1', 'S2', 'S3')
RQ = ('京浜トラックターミナルを起点とする大田区内のToC配送において、量子・古典ハイブリッド最適化は、'
      '配送実績を想定するベースライン、従来的な手法および古典最適化計算と比較して、'
      '全車両の総走行距離と積込待機時間という二目的について、どのような性能差とトレードオフを示すか。')
HYPOTHESIS = ('量子・古典ハイブリッド最適化は、同一の配送需要と運行制約の下で、'
              '配送実績を想定するベースライン、従来的な手法および古典最適化計算のいずれと比較しても、'
              '全車両の総走行距離と積込待機時間の二指標を総合した評価値が小さくなる。')


def read(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('DUPLICATE_KEY:' + key)
            result[key] = value
        return result
    def invalid(value):
        raise ValueError('NONFINITE_JSON:' + value)
    return json.loads(Path(path).read_text(), object_pairs_hook=unique, parse_constant=invalid)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def fingerprint(value):
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(',', ':'), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def load_policy(path):
    policy = read(path)
    expected = {'policy_id', 'status', 'authority', 'rq', 'hypothesis', 'objectives',
                'composite', 'analysis', 'execution', 'source', 'main'}
    if set(policy) != expected or policy['policy_id'] != POLICY_ID:
        raise ValueError('UNSUPPORTED_DW_POLICY')
    if policy['rq'] != RQ or policy['hypothesis'] != HYPOTHESIS:
        raise ValueError('RQ_HYPOTHESIS_DRIFT')
    if policy['status'] != 'ADOPTED_SCOPE_MAIN_HOLD' or policy['source'] != {
            'experiment_id': 'non_time_variance_pilot_20261117_v1', 'kind': 'saved_pilot_only'}:
        raise ValueError('SOURCE_OR_POLICY_STATUS_DRIFT')
    if policy['objectives'] != {'D': 'total_distance_km', 'W': 'total_loading_wait_min'}:
        raise ValueError('ONLY_DISTANCE_AND_WAIT_ARE_OBJECTIVES')
    if policy['composite'] != {'name': 'J_DW', 'status': 'HOLD', 'weights': None,
                                'normalization': None, 'support_rule': None}:
        raise ValueError('COMPOSITE_REQUIRES_NEW_REVIEWED_POLICY')
    if policy['main'].get('executable') is not False or policy['main'].get('runs') != []:
        raise ValueError('MAIN_EXPERIMENT_NOT_AUTHORIZED')
    if policy['execution'] != {
        'mode': 'finite_work', 'rules': 'configs/toc_delivery/termination_rules_20261116_v1.json',
        'BCD_branches': 4, 'native_threads_per_branch': 1,
        'outer_execution': 'sequential', 'timing_logs': 'preserve_as_execution_metadata_only',
        'launch_authorized': False,
    }:
        raise ValueError('EXECUTION_POLICY_DRIFT')
    if policy['analysis'] != {'metrics': ['D', 'W'], 'dominance_dimensions': 2,
                               'saved_pilot_role': 'post_policy_exploratory_reanalysis',
                               'primary_contrast_candidate': 'S2:D_minus_C:distance',
                               'confirmatory_primary_adopted': False,
                               'include_all_registered_attempts': True}:
        raise ValueError('ANALYSIS_POLICY_DRIFT')
    return policy


def finite(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def describe(values):
    if any(not finite(v) for v in values):
        raise ValueError('INVALID_QUALITY_VALUE')
    return {'n_recorded': len(values), 'mean': mean(values) if values else None,
            'median': median(values) if values else None,
            'sample_SD': stdev(values) if len(values) > 1 else None,
            'variance': variance(values) if len(values) > 1 else None,
            'min': min(values) if values else None, 'max': max(values) if values else None}


def difference(left, right, deterministic_left=False):
    """Right minus left; independent trial means, fixed A quality reference.

    A's repeated checks never become independent quality samples. Zero observed
    stochastic variance does not yield an artificial zero-width interval.
    """
    a, b = describe(left), describe(right)
    delta = b['mean'] - a['mean'] if left and right else None
    reason = None
    half = df = None
    if not left or not right:
        reason = 'NO_ACCEPTED_PLAN'
    elif len(right) < 2 or (not deterministic_left and len(left) < 2):
        reason = 'INSUFFICIENT_INDEPENDENT_ATTEMPTS'
    else:
        if deterministic_left:
            if len(set(left)) != 1:
                raise ValueError('A_REFERENCE_QUALITY_MISMATCH')
            se2 = b['variance'] / len(right)
            df = len(right) - 1
        else:
            va, vb = a['variance'] / len(left), b['variance'] / len(right)
            se2 = va + vb
            df = se2**2 / (va**2 / (len(left)-1) + vb**2 / (len(right)-1)) if se2 else None
        if se2 == 0:
            reason = 'ZERO_OBSERVED_STOCHASTIC_VARIANCE_UNIDENTIFIED'
        else:
            from scipy.stats import t
            half = float(t.ppf(.975, df)) * math.sqrt(se2)
    return {'mean_difference': delta, 'CI95': [delta-half, delta+half] if half is not None else None,
            'null_reason': reason, 'degrees_of_freedom': df,
            'left_quality_units': 1 if deterministic_left and left else len(left),
            'right_quality_units': len(right), 'simultaneous_coverage_claimed': False,
            'interpretation': 'conditional on successful trials and this fixed demand; exploratory'}


def quality_relation(candidate, baseline):
    from .contracts import compare_objectives
    return compare_objectives([candidate['D'], candidate['W']], [baseline['D'], baseline['W']])


def rate(successes, settled, pending):
    if pending or not settled:
        return {'numerator': successes, 'denominator': settled + pending,
                'estimate': None, 'Wilson95': None, 'Clopper_Pearson95': None,
                'reason': 'UNRESOLVED_STARTED_TRIALS' if pending else 'NO_STARTED_TRIALS'}
    from scipy.stats import beta
    k, n = successes, settled
    p, z = k/n, 1.959963984540054
    center = (p + z*z/(2*n)) / (1 + z*z/n)
    half = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / (1+z*z/n)
    exact = [0.0 if k == 0 else float(beta.ppf(.025, k, n-k+1)),
             1.0 if k == n else float(beta.ppf(.975, k+1, n-k))]
    return {'numerator': k, 'denominator': n, 'estimate': p,
            'Wilson95': [max(0., center-half), min(1., center+half)],
            'Clopper_Pearson95': exact, 'reason': None}


def analyze_rows(rows):
    """Whitelist projection: timing/J fields cannot affect any research result."""
    groups = defaultdict(list)
    projected = []
    seen = set()
    for row in rows:
        rid = row['run_id']
        if rid in seen or row['method'] not in METHODS or row['case_id'] not in SCALES:
            raise ValueError('DUPLICATE_OR_UNKNOWN_TRIAL')
        seen.add(rid)
        if type(row.get('adoptable')) is not bool:
            raise ValueError('INVALID_ADOPTABILITY')
        state = row['execution_state']
        if state not in ('NORMAL', 'ERROR', 'RESOURCE_STOP', 'USER_CANCELLED',
                         'EXTERNAL_INTERRUPTION', 'INCOMPLETE', 'NOT_STARTED'):
            raise ValueError('UNKNOWN_EXECUTION_STATE')
        if row['adoptable']:
            if (state != 'NORMAL' or row.get('input_state') != 'VALID'
                    or row.get('validation_state') != 'VALIDATED'
                    or row.get('plan_state') != 'VALID'
                    or not finite(row.get('D')) or not finite(row.get('W'))):
                raise ValueError('UNVALIDATED_ADOPTED_QUALITY:' + rid)
        elif row.get('D') is not None or row.get('W') is not None:
            raise ValueError('REJECTED_TRIAL_HAS_QUALITY:' + rid)
        item = {k: row.get(k) for k in ('run_id', 'case_id', 'method', 'repeat_id',
                'input_hash', 'OD_hash', 'physical_hash', 'config_hash',
                'execution_state', 'input_state', 'validation_state', 'adoptable', 'D', 'W')}
        projected.append(item)
        groups[(row['case_id'], row['method'])].append(item)
    summaries, comparisons, fronts = [], [], []
    for scale in SCALES:
        identities = {(r.get('input_hash'), r.get('OD_hash'), r.get('physical_hash'), r.get('config_hash'))
                      for r in projected if r['case_id'] == scale and r['execution_state'] != 'NOT_STARTED'}
        if len(identities) > 1:
            raise ValueError('INPUT_OR_CONDITION_MISMATCH:' + scale)
        for method in METHODS:
            own = groups[(scale, method)]
            accepted = [r for r in own if r['adoptable']]
            pending = sum(r['execution_state'] == 'INCOMPLETE' for r in own)
            settled = sum(r['execution_state'] not in ('INCOMPLETE', 'NOT_STARTED') for r in own)
            if method == 'A' and len({(r['D'], r['W']) for r in accepted}) > 1:
                raise ValueError('A_REFERENCE_QUALITY_MISMATCH:' + scale)
            summaries.append({'scale': scale, 'method': method, 'registered': len(own),
                'state_counts': dict(Counter(r['execution_state'] for r in own)),
                'adopted_run_ids': [r['run_id'] for r in accepted],
                'quality_units': min(1, len(accepted)) if method == 'A' else len(accepted),
                'D': describe([r['D'] for r in accepted]), 'W': describe([r['W'] for r in accepted]),
                'A_repeated_checks_are_not_quality_replicates': method == 'A',
                'validated_plan_rate': rate(len(accepted), settled, pending)})
        for left, right in [('A','B'), ('A','C'), ('A','D'), ('B','D'), ('C','D'),
                            ('D_CLASSICAL_REPLACEMENT','D')]:
            a = [r for r in groups[(scale,left)] if r['adoptable']]
            b = [r for r in groups[(scale,right)] if r['adoptable']]
            comparisons.append({'scale': scale, 'left': left, 'right': right,
                'direction': 'right_minus_left', 'paired_seed_analysis': False,
                **{key: difference([r[key] for r in a], [r[key] for r in b], left == 'A')
                   for key in ('D','W')}})
        candidates = [r for r in projected if r['case_id'] == scale and r['adoptable']]
        dominated = []
        for candidate in candidates:
            parents = [r['run_id'] for r in candidates
                       if r['run_id'] != candidate['run_id'] and quality_relation(r, candidate)['relation'] == 'DOMINATES']
            if parents:
                dominated.append({'run_id': candidate['run_id'], 'dominated_by': parents})
        dominated_ids = {r['run_id'] for r in dominated}
        fronts.append({'scale': scale, 'observed_nondominated_run_ids':
                       [r['run_id'] for r in candidates if r['run_id'] not in dominated_ids],
                       'dominance': dominated, 'claim': 'observed plans only; no global optimality or population dominance'})
    return {'policy_id': POLICY_ID, 'objectives': ['D','W'], 'units': {'D':'km', 'W':'min'},
            'role': 'exploratory reanalysis after policy change; not a preregistered main result',
            'independent_demand_families': 1, 'M_per_scale': 1,
            'nested_scales_are_not_independent_families': True,
            'rows': projected, 'summaries': summaries, 'comparisons': comparisons,
            'observed_fronts': fronts, 'J_DW': None,
            'hypothesis_status': 'NOT_TESTABLE_UNTIL_COMPOSITE_AND_SUPPORT_RULE_ARE_REGISTERED'}


def load_saved_pilot(root, policy):
    """Verify immutable registration, inputs and accepted saved-plan bytes."""
    root = Path(root).resolve()
    lock = read(root/'REGISTRATION_LOCK.json')
    for name in ('REGISTERED.json', 'PILOT_MANIFEST.json'):
        if digest(root/name) != lock[name]:
            raise ValueError('REGISTRATION_CHANGED:' + name)
    manifest = read(root/'REGISTERED.json')
    if (manifest['experiment_id'] != policy['source']['experiment_id']
            or fingerprint(manifest) != lock['manifest_fingerprint']
            or fingerprint(manifest['runs']) != manifest['run_list_hash']
            or manifest['run_list_hash'] != lock['run_list_hash']):
        raise ValueError('SOURCE_REGISTRATION_IDENTITY_MISMATCH')
    if digest(root/'SOURCE_SNAPSHOT.tar.gz') != manifest['snapshot_sha256']:
        raise ValueError('SOURCE_SNAPSHOT_CHANGED')
    cases = {c['case_id']: c for c in manifest['cases']}
    provenance = {str(root/'REGISTERED.json'): digest(root/'REGISTERED.json')}
    for case in cases.values():
        for name, expected in case['input']['files'].items():
            path = Path(case['input']['directory'])/name
            if digest(path) != expected:
                raise ValueError('FROZEN_INPUT_CHANGED:' + str(path))
            provenance[str(path)] = expected
    rows = []
    expected_ids = {r['run_id'] for r in manifest['runs']}
    if len(expected_ids) != len(manifest['runs']):
        raise ValueError('DUPLICATE_REGISTERED_ID')
    if (root/'runs').exists() and any(p.is_dir() and p.name not in expected_ids for p in (root/'runs').iterdir()):
        raise ValueError('UNREGISTERED_RUN_DIRECTORY')
    for run in manifest['runs']:
        directory = root/'runs'/run['run_id']
        path = directory/'RESULT.json'
        if path.exists():
            row = read(path)
            for key in ('run_id','case_id','method','repeat_id','attempt_id','seeds'):
                if row.get(key) != run.get(key):
                    raise ValueError('RESULT_IDENTITY_CHANGED:' + key)
            case = cases[run['case_id']]['input']
            for key, expected in [('experiment_id', manifest['experiment_id']),
                    ('contract_id',manifest['contract_id']), ('input_hash',case['input_hash']),
                    ('OD_hash',case['OD_hash']), ('physical_hash',manifest['physical_hash']),
                    ('config_hash',manifest['config_hash'])]:
                if row.get(key) != expected:
                    raise ValueError('RESULT_CONDITIONS_CHANGED:' + key)
            if row.get('adoptable'):
                plan_path = directory/'plan.json'
                if digest(plan_path) != row['plan_sha256']:
                    raise ValueError('SAVED_PLAN_CHANGED:' + run['run_id'])
                plan = read(plan_path)
                if plan['problem_hash'] != case['input_hash'] or plan['od_hash'] != case['OD_hash']:
                    raise ValueError('SAVED_PLAN_INPUT_CHANGED:' + run['run_id'])
                checks_path = directory/'PHYSICAL_CHECKS.json'
                checks = read(checks_path)
                selected = [c['checks'] for c in checks
                            if c.get('selected_repeat_check') == row['selected_branch_id']]
                if not selected:
                    raise ValueError('MISSING_SAVED_DOUBLE_CHECKS')
                checks = selected[-1]
                for name in ('common_physical', 'independent_physical'):
                    check = checks[name]
                    if (check['feasible'] is not True
                            or not math.isclose(float(check['D_km']), row['D'], rel_tol=0, abs_tol=1e-7)
                            or not math.isclose(float(check['W_min']), row['W'], rel_tol=0, abs_tol=1e-7)):
                        raise ValueError('SAVED_DOUBLE_CHECKS_MISMATCH')
                provenance[str(plan_path)] = digest(plan_path)
                provenance[str(checks_path)] = digest(checks_path)
            provenance[str(path)] = digest(path)
        else:
            case = cases[run['case_id']]['input']
            row = {**run, 'execution_state': 'INCOMPLETE' if directory.exists() else 'NOT_STARTED',
                   'input_hash': case['input_hash'], 'OD_hash': case['OD_hash'],
                   'physical_hash': manifest['physical_hash'], 'config_hash': manifest['config_hash'],
                   'adoptable': False, 'D': None, 'W': None}
        rows.append(row)
    return rows, provenance


def write_analysis(source, output, policy_path):
    policy = load_policy(policy_path)
    source, output = Path(source).resolve(), Path(output).resolve()
    if output == source or source in output.parents or output in source.parents:
        raise ValueError('ANALYSIS_OUTPUT_MUST_BE_SEPARATE_FROM_SOURCE')
    if output.exists():
        raise FileExistsError('EXISTING_OUTPUT_PRESERVED:' + str(output))
    rows, provenance = load_saved_pilot(source, policy)
    report = analyze_rows(rows)
    # Detect a source update during collection before publishing any analysis.
    if any(digest(Path(path)) != h for path,h in provenance.items()):
        raise ValueError('SOURCE_CHANGED_DURING_ANALYSIS')
    output.mkdir(parents=True, exist_ok=False)
    def save(name, value):
        with (output/name).open('x') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n')
    save('DW_ANALYSIS.json', report)
    save('SOURCE_HASHES.json', provenance)
    save('POLICY.json', policy)
    lines = ['# D・W二目的の既存予備試行再分析', '',
             '2026-11-17の方針変更後の探索的再分析。本実験の結果ではない。', '',
             '同じ凍結需要familyのS1〜S3。Aの反復は品質標本を増やさない。', '',
             '|規模|手法|取得／登録|平均D km|平均W 分|', '|---|---|---:|---:|---:|']
    for row in report['summaries']:
        values = [f"{row[k]['mean']:.4f}" if row[k]['mean'] is not None else '未取得' for k in ('D','W')]
        lines.append(f"|{row['scale']}|{row['method']}|{len(row['adopted_run_ids'])}/{row['registered']}|{'|'.join(values)}|")
    lines += ['', '総合評価の重み・正規化・支持規則が未決定のためJ_DWと研究仮説の検証は保留。',
              '全比較は成功条件付き・探索的。0観測分散に0幅の信頼区間を付けず、非有意を同等性と解釈しない。',
              '方式全体の差と量子候補生成の寄与を区別し、古典置換対照を併記する。', '']
    (output/'REPORT.md').write_text('\n'.join(lines))
    return report
