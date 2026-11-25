"""Read-only recovery of four final plans and explicit C; exclusive new output."""
from dataclasses import asdict
from fractions import Fraction
import json
from pathlib import Path
import time

from .policy import ROOT, VERSION, PINS, read, digest, require_frozen
from .ranking import Candidate, Metrics, metric_record, number, select


def exact_metrics(problem, plan):
    """Recompute from shared OD / starts-ready, never trust stored summary D/W."""
    from kmd_toc.fcfs_v1.validation import require_fcfs
    from kmd_toc.d_local_design.completion import physical
    if plan.problem_hash != problem.fingerprint or plan.od_hash != problem.od.fingerprint:
        raise ValueError('PLAN_PROBLEM_OR_OD_MISMATCH')
    check = require_fcfs(problem, plan)
    ok, independent = physical(problem, plan)
    if not ok:
        raise ValueError('INDEPENDENT_PHYSICAL_REJECTION:' + str(independent))
    index = {s: i for i, s in enumerate(problem.od.ids)}
    distance = Fraction(0)
    for trip in plan.trips:
        nodes = (problem.depot.depot_id, *(v.stop_id for v in trip.visits), problem.depot.depot_id)
        distance += sum((Fraction(str(float(problem.od.distance_m[index[a], index[b]])))
                         for a, b in zip(nodes, nodes[1:])), Fraction(0))
    wait_s = sum(t.load_start_s - t.ready_s for t in plan.trips)
    metrics = Metrics(distance / 1000, Fraction(wait_s, 60))
    if abs(float(metrics.W) - check['W_loading_min']) > 1e-12:
        raise ValueError('INDEPENDENT_WAIT_MISMATCH')
    return metrics, {'fcfs': check, 'dual_physical': independent}


def same_physical_plan(left, right):
    # method / plan ID / annotations do not turn a different route or time into C.
    canonical = lambda p: tuple(sorted(p.trips, key=lambda t: (t.vehicle_id, t.trip_no)))
    return left.problem_hash == right.problem_hash and left.od_hash == right.od_hash and canonical(left) == canonical(right)


def _load_record(record, base, trial):
    from kmd_toc.common.models import load_plan
    if record.get('outer_trial_id') != trial:
        raise ValueError('EXPLICIT_SAME_OUTER_TRIAL_BINDING_REQUIRED')
    path = (base / record['path']).resolve()
    expected = record['sha256']
    if not isinstance(expected, str) or len(expected) != 64 or digest(path) != expected:
        raise ValueError('PLAN_TRANSFER_HASH_MISMATCH:' + str(path))
    plan = load_plan(path)
    if digest(path) != expected:
        raise ValueError('PLAN_CHANGED_DURING_LOAD:' + str(path))
    return path, plan


def _write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def recover_and_select(manifest_path, output):
    """A final-collection entry point, not permission to launch a planner.

    Registration is an explicit C-to-trial assignment, not a statistical pairing
    claim. Missing / invalid C is fatal HOLD, never a distance-rule fallback.
    """
    start = time.perf_counter()
    manifest_path = Path(manifest_path).resolve()
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    audit = {'selection_version': VERSION, 'status': 'HOLD', 'main_experiment_authorized': False,
             'manifest_path': str(manifest_path), 'policy_sha256': PINS, 'candidates': [],
             'source_sha256': {str(p.relative_to(ROOT)): digest(p)
                               for p in sorted(Path(__file__).parent.glob('*.py'))}}
    try:
        require_frozen()
        manifest_hash = digest(manifest_path)
        registration = read(manifest_path)
        if registration.get('selection_version') != VERSION:
            raise ValueError('REGISTERED_SELECTION_VERSION_REQUIRED')
        trial = registration['outer_trial_id']
        if not isinstance(trial, str) or not trial.strip():
            raise ValueError('NONEMPTY_OUTER_TRIAL_ID_REQUIRED')
        if registration.get('C_reference_assignment') != 'explicit_same_problem_outer_trial':
            raise ValueError('EXPLICIT_C_REFERENCE_ASSIGNMENT_REQUIRED')
        audit.update(outer_trial_id=trial, manifest_sha256=manifest_hash,
                     C_reference_assignment=registration['C_reference_assignment'],
                     statistical_pairing='NOT_INFERRED_FROM_REFERENCE_ASSIGNMENT')
        branches = registration['branches']
        if (not isinstance(branches, list) or len(branches) != 4 or
                any(type(b.get('branch_id')) is not int for b in branches) or
                sorted(b['branch_id'] for b in branches) != list(range(4))):
            raise ValueError('EXACTLY_FOUR_FIXED_BRANCH_RECORDS_REQUIRED')
        from kmd_toc.common.models import load_problem
        problem = load_problem((manifest_path.parent / registration['problem']['path']).resolve())
        if (problem.fingerprint != registration['problem']['fingerprint'] or
                problem.od.fingerprint != registration['problem']['od_fingerprint']):
            raise ValueError('REGISTERED_PROBLEM_OR_OD_MISMATCH')
        audit['problem'] = registration['problem']
        cpath, cplan = _load_record(registration['C_reference'], manifest_path.parent, trial)
        if cplan.method_id != 'C':
            raise ValueError('C_REFERENCE_MUST_BE_METHOD_C')
        reference, ccheck = exact_metrics(problem, cplan)
        audit['C_reference'] = {**registration['C_reference'], 'resolved_path': str(cpath),
                                'metrics': metric_record(reference, reference), 'validation': ccheck}
        ipath, initial = _load_record(registration['initial'], manifest_path.parent, trial)
        initial_metrics, icheck = exact_metrics(problem, initial)
        if registration['initial'].get('compute_wall_s') is not None:
            number(registration['initial']['compute_wall_s'])
        audit['initial_is_same_physical_plan_as_C'] = same_physical_plan(initial, cplan)
        audit['initial_method_id'] = initial.method_id
        rows = [Candidate(None, initial_metrics)]
        plans = {None: initial}
        audit['candidates'].append({'branch_id': None, 'kind': 'saved_initial', 'feasible': True,
                                    'path': str(ipath), 'sha256': registration['initial']['sha256'],
                                    'compute_wall_s': registration['initial'].get('compute_wall_s'),
                                    'validation': icheck, **metric_record(initial_metrics, reference)})
        for branch in sorted(branches, key=lambda b: b['branch_id']):
            bid = branch['branch_id']
            if branch.get('outer_trial_id') != trial:
                raise ValueError('BRANCH_OUTER_TRIAL_MISMATCH')
            wall = branch.get('compute_wall_s')
            if wall is not None:
                number(wall)
            row = {**branch, 'kind': 'branch_final', 'feasible': False,
                   'D_km': None, 'W_total_loading_min': None, 'I_dual': None,
                   'I_dual_status': 'not_evaluated'}
            audit['candidates'].append(row)
            if branch.get('status') not in ('COMPLETE', 'FAILED', 'INCOMPLETE'):
                raise ValueError('EXPLICIT_BRANCH_COMPLETION_STATUS_REQUIRED')
            if branch['status'] != 'COMPLETE':
                row['excluded_reason'] = 'NOT_A_COMPLETE_FINAL_PLAN'
                continue
            # A broken transfer / trial contract is fatal; infeasible plans are excluded.
            bpath, plan = _load_record(branch, manifest_path.parent, trial)
            row['resolved_path'] = str(bpath)
            if plan.method_id != 'D':
                raise ValueError('D_BRANCH_METHOD_REQUIRED')
            try:
                metrics, checks = exact_metrics(problem, plan)
            except ValueError as error:
                row['excluded_reason'] = str(error)
                continue
            row.update(feasible=True, validation=checks, **metric_record(metrics, reference))
            rows.append(Candidate(bid, metrics))
            plans[bid] = plan
        winner, reason = select(rows, reference)
        # For audit only: the actual historical key uses stored validated distance
        # rounded to 0.1 m. It is never an alternative selector for this version.
        from kmd_toc.termination_v1.work import key as historical_key
        old = min(rows, key=lambda c: (historical_key(plans[c.branch_id]),
                                      c.branch_id is not None, c.branch_id if c.branch_id is not None else -1))
        selected = plans[winner.branch_id]
        again, final_check = exact_metrics(problem, selected)
        if again != winner.metrics:
            raise ValueError('SELECTED_PLAN_RECHECK_MISMATCH')
        # Verify every registered file again before committing a new selection.
        for record in [registration['C_reference'], registration['initial'], *branches]:
            if record.get('path') and record.get('sha256'):
                if digest((manifest_path.parent / record['path']).resolve()) != record['sha256']:
                    raise ValueError('INPUT_CHANGED_DURING_SELECTION')
        if digest(manifest_path) != manifest_hash:
            raise ValueError('REGISTRATION_CHANGED_DURING_SELECTION')
        _write(output / 'plan.json', asdict(selected))
        audit.update(status='PASS_FINAL_SELECTION_ONLY', selected_branch_id=winner.branch_id,
                     selected_kind='saved_initial' if winner.branch_id is None else 'branch_final',
                     selection=reason, selected_metrics=metric_record(winner.metrics, reference),
                     selected_plan_sha256=digest(output / 'plan.json'), selected_validation=final_check,
                     old_rule_comparison={'scope': 'same_candidate_set_including_initial_diagnostic_only',
                                          'selected_branch_id': old.branch_id,
                                          'metrics': metric_record(old.metrics, reference),
                                          'different_choice': old.branch_id != winner.branch_id,
                                          'delta_D_new_minus_old_km': float(winner.metrics.D - old.metrics.D),
                                          'delta_W_new_minus_old_min': float(winner.metrics.W - old.metrics.W)},
                     full_D_planner='HOLD_NOT_IMPLEMENTED_BY_SELECTION',
                     branch_generation_conditions='NOT_CERTIFIED_BY_POSTSELECTION')
    except (ValueError, KeyError, OSError, TypeError) as error:
        audit['error'] = f'{type(error).__name__}: {error}'
        audit['selection_wall_s'] = time.perf_counter() - start
        _write(output / 'SELECTION.json', audit)
        raise
    audit['selection_wall_s'] = time.perf_counter() - start
    _write(output / 'SELECTION.json', audit)
    return audit
