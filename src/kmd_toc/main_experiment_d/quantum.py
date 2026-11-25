"""Guarded finite-shot local kernel for the new main-D contract.

Only small artificial calls are exercised by this freeze task. This is not a
full delivery planner. The full main entry point remains unconditionally HOLD.
The existing forward-v5 circuit and p2 SectorMPS are imported read-only.
"""
from dataclasses import asdict, dataclass
import importlib.util
import json
import math
import os
from pathlib import Path
import time

from .shots import ROOT, check_overrides, load_trial, same_json, _identifier
from .depth import check_depth, checked_angles
from .circuit import build_circuit, executed_layers


@dataclass(frozen=True)
class KernelSettings:
    # Required explicit inputs, NOT new protocol defaults or approvals.
    p: int
    max_evaluations: int
    initial_angles: tuple
    rhobeg: float
    tol: float
    bond: int
    cutoff: float

    def validate(self, n):
        check_depth(self.p)
        if (type(self.p) is not int or self.p < 1 or
                type(self.max_evaluations) is not int or self.max_evaluations < 1 or
                len(self.initial_angles) != 2 * self.p or
                not all(math.isfinite(x) for x in self.initial_angles) or
                not math.isfinite(self.rhobeg) or self.rhobeg <= 0 or
                not math.isfinite(self.tol) or self.tol <= 0 or
                type(self.bond) is not int or self.bond < 1):
            raise ValueError('EXPLICIT_KERNEL_SETTINGS_REQUIRED')
        if self.cutoff != 1e-18:
            raise ValueError('EXISTING_NUMERICAL_CUTOFF_MUST_BE_PRESERVED')
        if self.p == 2 and n in (10, 12) and self.bond != {10: 1024, 12: 1280}[n]:
            raise ValueError('EXISTING_P2_NUMERICAL_BOND_MUST_BE_PRESERVED')


def _module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def backend_modules():
    return (_module('_main_d_forward_v5', ROOT / 'scripts/large_n_20261119_v5/quantum.py'),
            _module('_main_d_precision_sector', ROOT / 'scripts/p2_precision_20261120/sector_mps.py'))


def _write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def run_local(manifest_path, branch_id, call_id, local, settings, *, shots=None):
    """Apply the frozen pair at EVERY sampler boundary, with exclusive call IDs.

    Each objective evaluation executes one circuit state and samples 1,000
    bitstrings. The optimized state is freshly evolved once and sampled once
    with 10,000 shots. Multiple local problems require distinct call IDs; no
    restart, retry, n-dependent allocation or reduced-shot fallback exists.
    """
    manifest = load_trial(manifest_path)
    check_overrides(shots)
    if type(branch_id) is not int or branch_id not in range(4):
        raise ValueError('BRANCH_ID_0_TO_3_REQUIRED')
    _identifier(call_id)
    settings.validate(local.n)
    if any(os.environ.get(k) != '1' for k in
           ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS')):
        raise ValueError('ONE_NATIVE_THREAD_ENV_REQUIRED')
    branch = manifest['branches'][branch_id]
    seed = branch['optimizer_seed']
    pair = manifest['qaoa_shots']
    out = Path(manifest_path).parent / 'calls' / f'branch_{branch_id}' / call_id
    out.mkdir(parents=True, exist_ok=False)
    _write(out / 'CALL.json', {
        'trial_id': manifest['trial_id'], 'scale': manifest['scale'], 'branch_id': branch_id,
        'call_id': call_id, 'qaoa_shots': pair,
        'qaoa': manifest['qaoa'], 'depth_p': settings.p,
        'depth_config_sha256': manifest['depth_config_sha256'],
        'shots_config_sha256': manifest['shots_config_sha256'],
        'optimizer_seed': seed, 'local_seed': local.seed, 'settings': asdict(settings),
        'local_payload': local.payload(),
        'numerical_threshold': 1e-6,
        'numerical_scope': 'existing truncation TV bound; floating residual estimates separately logged',
    })
    events = []
    def emit(row):
        events.append(row)
        with (out / 'EVENTS.jsonl').open('a') as stream:
            stream.write(json.dumps(row, allow_nan=False) + '\n')
            stream.flush()
    start = time.perf_counter()
    try:
        from scipy.optimize import minimize
        q, sector = backend_modules()
        _, circuit_metadata = build_circuit(local, q)
        emit({'event': 'circuit_constructed', **circuit_metadata})
        lookup = q.proxy_lookups(local)
        width, _, total_q = q.register_layout(local.n)
        history = []

        def execute(angles, phase, evaluation, sampling_seed):
            # Re-check the approved file and the complete saved branch contract
            # before each quantum call, including the final extraction.
            current = load_trial(manifest_path)
            if current != manifest:
                raise ValueError('MANIFEST_CHANGED_DURING_CALL')
            angles = checked_angles(angles)
            requested = pair['optimization' if phase == 'optimization' else 'final_extraction']
            def numerical(row):
                emit({'event': 'numerical_update', 'phase': phase, 'evaluation': evaluation, **row})
                bound = row['truncation_trace_bound']
                if not math.isfinite(bound) or not 0 <= bound <= 1e-6:
                    raise ValueError('NUMERICAL_TV_CRITERION_NOT_MET')
            state_builder = sector.SectorMPS(q.initial_order(local), 1 << width,
                                             settings.bond, settings.cutoff, numerical)
            state_builder.prepare_sweep()
            for layer in range(settings.p):
                gamma, beta = angles[2 * layer:2 * layer + 2]
                state_builder.layer = layer + 1
                state_builder.phase(lookup, float(gamma), lookup['bound_m'])
                state_builder.mixer(float(beta))
            layer_metadata = executed_layers(state_builder.logs, local.n)
            state = state_builder.state()
            bound = state['trace_distance_error_bound']
            if not math.isfinite(bound) or not 0 <= bound <= 1e-6:
                raise ValueError('NUMERICAL_TV_CRITERION_NOT_MET')
            emit({'event': 'sampling_started', 'phase': phase, 'evaluation': evaluation,
                  **layer_metadata,
                  'requested_shots': requested, 'sampling_seed': sampling_seed,
                  'angles': list(map(float, angles)), 'TV_error_bound': bound})
            counts = sector.sample(state, requested, sampling_seed, width, total_q)
            if not counts or any(type(c) is not int or c < 0 for c in counts.values()):
                raise ValueError('INVALID_SHOT_COUNTS')
            actual = sum(counts.values())
            emit({'event': 'sampling_completed', 'phase': phase, 'evaluation': evaluation,
                  **layer_metadata,
                  'requested_shots': requested, 'actual_shots': actual, 'sampling_seed': sampling_seed,
                  'counts': counts, 'TV_error_bound': bound})
            if actual != requested:
                raise ValueError('ACTUAL_SHOTS_MISMATCH')
            costs = {}
            labels = {s: i + 1 for i, s in enumerate(local.customer_ids)}
            for bits in counts:
                decision = q.decode_register(int(bits, 2), local.customer_ids)
                order = tuple(labels[s] for s in decision.trip_1) + (0,) + tuple(labels[s] for s in decision.trip_2)
                costs[bits] = q.lookup_cost(order, lookup) / lookup['bound_m']
            value = math.fsum(costs[b] * c for b, c in counts.items()) / actual
            emit({'event': 'objective_value', 'phase': phase, 'evaluation': evaluation, 'sample_mean': value})
            return value, counts

        def objective(angles):
            if len(history) >= settings.max_evaluations:
                raise ValueError('EXPLICIT_EVALUATION_CAP_EXCEEDED')
            value, _ = execute(angles, 'optimization', len(history) + 1, seed + len(history))
            history.append(value)
            return value

        fit = minimize(objective, settings.initial_angles, method='COBYLA',
                       options={'maxiter': settings.max_evaluations,
                                'rhobeg': settings.rhobeg, 'tol': settings.tol})
        _, counts = execute(fit.x, 'final_extraction', 1, seed + 100000)
        completed = [e for e in events if e['event'] == 'sampling_completed']
        result = {'status': 'MEASURED_LOCAL_CALL', 'qaoa_shots': pair,
                  'qaoa': manifest['qaoa'], 'depth_p': settings.p,
                  'depth_config_sha256': manifest['depth_config_sha256'],
                  'circuit_metadata': circuit_metadata,
                  'shots_config_sha256': manifest['shots_config_sha256'],
                  'optimizer_seed': seed, 'nfev': len(history), 'scipy_nfev': int(fit.nfev),
                  'optimizer_fun': float(fit.fun), 'optimizer_success': bool(fit.success),
                  'optimizer_message': str(fit.message), 'angles': list(map(float, fit.x)),
                  'counts': counts, 'optimization_shots_actual': sum(
                      e['actual_shots'] for e in completed if e['phase'] == 'optimization'),
                  'final_extraction_shots_actual': sum(
                      e['actual_shots'] for e in completed if e['phase'] == 'final_extraction'),
                  'total_shots_actual': sum(e['actual_shots'] for e in completed),
                  'wall_s': time.perf_counter() - start}
        _write(out / 'RESULT.json', result)
        return result
    except Exception as error:
        completed = [e for e in events if e['event'] == 'sampling_completed']
        started = [e for e in events if e['event'] == 'sampling_started']
        _write(out / 'FAILURE.json', {
            'status': 'FAILED', 'error': f'{type(error).__name__}: {error}',
            'qaoa_shots': pair, 'shots_config_sha256': manifest['shots_config_sha256'],
            'depth_p': settings.p, 'depth_config_sha256': manifest['depth_config_sha256'],
            'completed_shots_actual': sum(e['actual_shots'] for e in completed),
            'inflight_shots': None if len(started) != len(completed) else 0,
            'retry': False, 'reduced_shots_fallback': False,
        })
        raise


def audit_trial(manifest_path):
    """Re-count raw bitstrings for all branches, including failed/unselected calls."""
    manifest = load_trial(manifest_path)
    pair = manifest['qaoa_shots']
    totals = {'optimization': 0, 'final_extraction': 0}
    calls = []
    for call_path in sorted((Path(manifest_path).parent / 'calls').glob('branch_*/*/CALL.json')):
        call = json.loads(call_path.read_text())
        branch_id = call['branch_id']
        if (type(branch_id) is not int or branch_id not in range(4) or
                call_path.parent.parent.name != f'branch_{branch_id}' or
                not same_json(call.get('qaoa_shots'), pair) or
                not same_json(call.get('qaoa'), manifest['qaoa']) or
                type(call.get('depth_p')) is not int or call['depth_p'] != manifest['qaoa']['depth_p'] or
                call.get('depth_config_sha256') != manifest['depth_config_sha256'] or
                type(call.get('settings', {}).get('p')) is not int or
                call['settings']['p'] != manifest['qaoa']['depth_p'] or
                call.get('shots_config_sha256') != manifest['shots_config_sha256'] or
                call.get('trial_id') != manifest['trial_id'] or call.get('scale') != manifest['scale'] or
                call.get('optimizer_seed') != manifest['branches'][branch_id]['optimizer_seed']):
            raise ValueError('CALL_CONTRACT_MISMATCH')
        events_path = call_path.parent / 'EVENTS.jsonl'
        events = [json.loads(line) for line in events_path.read_text().splitlines()] if events_path.exists() else []
        checked_angles(call['settings']['initial_angles'])
        constructed = [e for e in events if e['event'] == 'circuit_constructed']
        starts = [e for e in events if e['event'] == 'sampling_started']
        completed = [e for e in events if e['event'] == 'sampling_completed']
        for e in starts + completed:
            phase = e['phase']
            if phase not in totals or type(e['requested_shots']) is not int or e['requested_shots'] != pair[phase]:
                raise ValueError('LEDGER_REQUESTED_SHOTS_MISMATCH')
            if not math.isfinite(e['TV_error_bound']) or not 0 <= e['TV_error_bound'] <= 1e-6:
                raise ValueError('LEDGER_NUMERICAL_CRITERION_NOT_MET')
            if (type(e.get('depth_p')) is not int or e['depth_p'] != manifest['qaoa']['depth_p'] or
                    e.get('cost_layers') != manifest['qaoa']['depth_p'] or
                    e.get('mixer_layers') != manifest['qaoa']['depth_p'] or
                    e.get('cost_layer_ids') != list(range(1, manifest['qaoa']['depth_p'] + 1)) or
                    e.get('mixer_layer_ids') != list(range(1, manifest['qaoa']['depth_p'] + 1))):
                raise ValueError('LEDGER_EXECUTED_DEPTH_MISMATCH')
        if len(completed) > len(starts):
            raise ValueError('LEDGER_SAMPLING_PAIR_MISMATCH')
        for begun, ended in zip(starts, completed):
            if any(begun[k] != ended[k] for k in ('phase', 'evaluation', 'requested_shots', 'sampling_seed')):
                raise ValueError('LEDGER_SAMPLING_PAIR_MISMATCH')
        for e in completed:
            if not e['counts'] or any(type(c) is not int or c < 0 for c in e['counts'].values()):
                raise ValueError('LEDGER_INVALID_SHOT_COUNTS')
            actual = sum(e['counts'].values())
            if actual != e['actual_shots'] or actual != pair[e['phase']]:
                raise ValueError('LEDGER_ACTUAL_SHOTS_MISMATCH')
            totals[e['phase']] += actual
        result_path = call_path.parent / 'RESULT.json'
        failure_path = call_path.parent / 'FAILURE.json'
        status = 'FAILED' if failure_path.exists() else 'INCOMPLETE'
        if result_path.exists():
            result = json.loads(result_path.read_text())
            metadata = result.get('circuit_metadata', {})
            if (len(constructed) != 1 or
                    not same_json({k: v for k, v in constructed[0].items() if k != 'event'}, metadata) or
                    type(metadata.get('depth_p')) is not int or metadata['depth_p'] != manifest['qaoa']['depth_p'] or
                    metadata.get('cost_layers') != manifest['qaoa']['depth_p'] or
                    metadata.get('mixer_layers') != manifest['qaoa']['depth_p'] or
                    metadata.get('angle_parameter_count') != 2 * manifest['qaoa']['depth_p']):
                raise ValueError('RESULT_CIRCUIT_DEPTH_MISMATCH')
            checked_angles(result['angles'])
            nopt = sum(e['phase'] == 'optimization' for e in completed)
            nfinal = sum(e['phase'] == 'final_extraction' for e in completed)
            if (failure_path.exists() or len(starts) != len(completed) or
                    nfinal != 1 or nopt != result['nfev'] or
                    not same_json(result['qaoa_shots'], pair) or
                    not same_json(result.get('qaoa'), manifest['qaoa']) or
                    type(result.get('depth_p')) is not int or result['depth_p'] != manifest['qaoa']['depth_p'] or
                    result.get('depth_config_sha256') != manifest['depth_config_sha256'] or
                    result['shots_config_sha256'] != manifest['shots_config_sha256'] or
                    result['optimization_shots_actual'] != nopt * pair['optimization'] or
                    result['final_extraction_shots_actual'] != pair['final_extraction'] or
                    result['total_shots_actual'] != sum(e['actual_shots'] for e in completed)):
                raise ValueError('RESULT_SHOTS_ACCOUNTING_MISMATCH')
            status = 'COMPLETE'
        calls.append({'branch_id': branch_id, 'call_id': call['call_id'], 'status': status,
                      'completed_shots_actual': sum(e['actual_shots'] for e in completed),
                      'inflight_shots': None if len(starts) != len(completed) else 0})
    return {'trial_id': manifest['trial_id'], 'qaoa_shots': pair,
            'qaoa': manifest['qaoa'], 'depth_config_sha256': manifest['depth_config_sha256'],
            'shots_config_sha256': manifest['shots_config_sha256'],
            'completed_shots_actual': totals, 'total_completed_shots_actual': sum(totals.values()),
            'calls': calls, 'main_experiment_authorized': False}
