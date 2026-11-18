import copy
from dataclasses import asdict, replace
import json
from pathlib import Path
import subprocess
import sys
import pytest

from kmd_toc.baseline_a.fixtures import artificial_problem
from kmd_toc.pipeline.completion import assemble, greedy_assignment
from kmd_toc.dwt.parallel import cpu_profile, branch_seeds, enabled, select_candidate, quantum_use_state

CONFIG = json.loads(Path('configs/toc_delivery/dwt_balance_v1_4_cpu_parallel.json').read_text())


def test_parallel_default_and_single_external_trial():
    profile = cpu_profile(CONFIG)
    assert profile['workers'] == 4 and len(set(profile['cpu_ids'])) == 4
    assert profile['native_threads_per_branch'] == 1 and profile['statistical_trial_count'] == 1
    assert enabled({'method': 'D', 'config': CONFIG})
    assert not enabled({'method': 'A', 'config': CONFIG})


@pytest.mark.parametrize('change', ['single', 'native', 'duplicate', 'insufficient', 'reserve'])
def test_bad_parallel_resource_policy_is_rejected(change):
    cfg = copy.deepcopy(CONFIG)
    allowed = cpu_profile(CONFIG)['cpu_ids']
    if change == 'single': cfg['cpu_parallel']['workers'] = 1
    if change == 'native': cfg['cpu_parallel']['native_threads_per_branch'] = 4
    if change == 'duplicate': cfg['cpu_parallel']['cpu_ids'] = [allowed[0]] * 4
    if change == 'insufficient': allowed = allowed[:1]
    if change == 'reserve': cfg['cpu_parallel']['coordinator_reserve_fraction'] = 1
    with pytest.raises(ValueError):
        cpu_profile(cfg, available=allowed)


def test_branch_streams_are_reproducible_distinct_and_not_root_reuse():
    root = {'solver_seed': 17, 'quantum_seed': 23, 'validation_seed': None}
    a = branch_seeds(root, 4)
    assert a == branch_seeds(root, 4)
    assert len({r['solver_seed'] for r in a}) == len({r['quantum_seed'] for r in a}) == 4
    assert all(r['solver_seed'] != 17 and r['quantum_seed'] != 23 for r in a)
    assert a != branch_seeds({**root, 'solver_seed': 18}, 4)


def test_invalid_low_metrics_and_deadline_failure_cannot_win_selection():
    p = artificial_problem(6, 2, 1)
    plan = assemble(p, greedy_assignment(p, [(1, 2, 3, 4, 5, 6)]), 'B', {})
    row = {'status': 'VALIDATED', 'feasible': True, 'budget_met': True, 'epsilon_met': True,
           'input_hash': p.fingerprint, 'OD_hash': p.od.fingerprint, 'plan': asdict(plan),
           'D_km': sum(t.distance_m for t in plan.trips) / 1000, 'W_min': sum(t.waiting_s for t in plan.trips) / 60}
    forged = {**row, 'D_km': 0.0}
    timeout = {**row, 'status': 'TIME_BUDGET_EXCEEDED', 'budget_met': False}
    selected, audit = select_candidate(p, [forged, timeout, row], 30)
    assert selected[1] == 2 and [x['accepted'] for x in audit] == [False, False, True]
    assert select_candidate(p, [forged, timeout], 30)[0] is None


def test_candidates_are_rejected_for_actual_schedule_violation():
    p = artificial_problem(6, 2, 1)
    plan = assemble(p, greedy_assignment(p, [(1, 2, 3, 4, 5, 6)]), 'B', {})
    bad = replace(plan, trips=(replace(plan.trips[0], load_start_s=plan.trips[0].ready_s - 1),))
    row = {'status': 'VALIDATED', 'feasible': True, 'budget_met': True, 'epsilon_met': True,
           'input_hash': p.fingerprint, 'OD_hash': p.od.fingerprint, 'plan': asdict(bad), 'D_km': 0, 'W_min': 0}
    assert select_candidate(p, [row], 30)[0] is None


def test_serial_cli_requires_explicit_historical_reproduction_flag():
    r = subprocess.run([sys.executable, '-B', 'scripts/run_dwt.py', 'register', '--config',
                        'configs/toc_delivery/dwt_balance_v1_3_1.json'], capture_output=True, text=True)
    assert r.returncode == 2 and 'historical serial reproduction must be explicit' in r.stderr


def test_actual_serial_registration_cannot_bypass_parallel_cli_policy(tmp_path):
    old = {'method': 'B', 'config': {'threads': 1}}
    path = tmp_path / 'old.json'
    path.write_text(json.dumps({'specs': [old]}))
    r = subprocess.run([sys.executable, '-B', 'scripts/run_dwt.py', 'run', '--registration', str(path)],
                       capture_output=True, text=True)
    assert r.returncode == 2 and 'Actual registration is historical serial' in r.stderr


def test_incomplete_quantum_accounting_is_unknown_not_falsely_zero():
    unknown = {'quantum_seed_used': None, 'quantum_accounting_complete': False}
    assert quantum_use_state('D', [unknown]) is None
    assert quantum_use_state('B', [unknown]) is False
    assert quantum_use_state('D', [unknown, {'quantum_seed_used': True}]) is True


def test_real_worker_dispatch_routes_new_methods_to_parallel(monkeypatch, tmp_path):
    from kmd_toc.dwt import worker, parallel
    called = []
    monkeypatch.setattr(parallel, 'execute_parallel', lambda spec, out, **kw: called.append((spec['method'], kw)) or 'parallel')
    monkeypatch.setattr(worker, 'execute', lambda spec, out: 'serial')
    for method in ['B', 'C', 'D', 'D_CLASSICAL_CONTROL']:
        assert worker.execute_trial({'method': method, 'config': CONFIG}, tmp_path, allow_import_only_fork=True) == 'parallel'
    assert worker.execute_trial({'method': 'A', 'config': CONFIG}, tmp_path) == 'serial'
    assert len(called) == 4 and all(r[1]['allow_import_only_fork'] for r in called)
