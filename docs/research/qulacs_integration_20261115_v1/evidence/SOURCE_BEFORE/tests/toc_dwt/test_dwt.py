from dataclasses import replace
import json
from pathlib import Path
import pytest
import numpy as np
from kmd_toc.baseline_a.fixtures import artificial_problem
from kmd_toc.baseline_a.independent import recompute
from kmd_toc.common.models import save_problem
from kmd_toc.common.od import OD
from kmd_toc.common.validation import validate_plan
from kmd_toc.dwt.budget import Budget, BudgetExceeded
from kmd_toc.dwt.evaluation import dominates, eligible, pareto, score
from kmd_toc.dwt.worker import execute
from kmd_toc.dwt.standard import export_standard, REQUIRED

CONFIG = json.loads(Path('configs/toc_delivery/dwt_balance_v1_3.json').read_text())


def point(name, d, w, t, method='B'):
    return dict(trial_id=name, D_km=d, W_min=w, T_program_s=t, method=method,
                status='COMPLETE', feasible=True, budget_met=True, epsilon_met=True,
                standard_output_complete=True, T_kind='program_wall', input_hash='same')


def test_dominance_equal_grid_and_transitivity():
    a, b, c = point('a', 1, 2, 3), point('b', 2, 2, 3), point('c', 3, 3, 4)
    assert dominates(a, b) and dominates(b, c) and dominates(a, c)
    assert not dominates(a, a)
    assert not dominates(point('round', 1 + 1e-9, 2, 3), a)
    front, relations = pareto([a, b, c, point('trade', .5, 3, 2), point('same', 1, 2, 3)])
    assert {r['trial_id'] for r in front} == {'a', 'same', 'trade'}
    assert {r['dominated'] for r in relations} == {'b', 'c'}


@pytest.mark.parametrize('field,value', [('feasible', False), ('budget_met', False),
                                         ('epsilon_met', False), ('standard_output_complete', False),
                                         ('T_kind', 'human_estimate'), ('D_km', None), ('T_program_s', float('nan'))])
def test_invalid_or_missing_cannot_win(field, value):
    a = point('bad', 0, 0, 0)
    a[field] = value
    assert not eligible(a)
    assert score(a, dict(D_km=10, W_min=10, T_program_s=10), [1 / 3] * 3) is None
    assert pareto([a, point('valid', 1, 1, 1)])[0][0]['trial_id'] == 'valid'


def test_weight_reference_and_A_boundary():
    r = point('x', 10, 20, 30)
    ref = dict(D_km=10, W_min=20, T_program_s=30)
    assert score(r, ref, [.6, .2, .2]) == pytest.approx(1)
    with pytest.raises(ValueError, match='WEIGHT'):
        score(r, ref, [.6, .6, .6])
    with pytest.raises(ValueError, match='REFERENCE'):
        score(r, {**ref, 'W_min': 0}, [1 / 3] * 3)
    assert score({**r, 'method': 'A'}, ref, [1 / 3] * 3) is None


def test_time_budget_reserve_and_stopping_are_actual_clock_based():
    for bad in [float('nan'), float('inf'), -1, True]:
        with pytest.raises(ValueError):
            Budget(bad)
    now = [10.]
    budget = Budget(10, .1, clock=lambda: now[0])
    assert budget.left() == 9
    assert budget.left(3) == 3
    now[0] = 19.1
    with pytest.raises(BudgetExceeded):
        budget.left()
    assert budget.left(validation=True) == pytest.approx(.9)
    now[0] = 20.01
    with pytest.raises(BudgetExceeded):
        budget.left(validation=True)


def tradeoff_problem():
    """Two exhaustive covers: cheap3 trips needs W>=30; dear2 permits W=0.

    All trips take >6h, hence one vehicle cannot do two within 08–20.
    Three vehicle ready times are 08:10/08:30/08:50, one 30min berth.
    This deliberately artificial witness is never labelled real Ota roads.
    """
    p = artificial_problem(4, 3, 1)
    d = np.full((5, 5), 4000.)
    d[0, :] = d[:, 0] = 1000
    d[1, 2] = 100
    np.fill_diagonal(d, 0)
    t = np.full((5, 5), 500.)
    t[0, :] = t[:, 0] = 12000
    np.fill_diagonal(t, 0)
    od = OD(p.od.ids, d, t, p.od.reachable, {**p.od.metadata, 'witness': 'long trips force distinct vehicles'})
    return replace(p, od=od, experiment=replace(p.experiment, data_hashes={'od': od.fingerprint})).validate()


def test_epsilon_changes_cover_and_independently_expected_D_W():
    from kmd_toc.pipeline.completion import complete_routes
    p = tradeoff_problem()
    routes = [(1, 2), (3,), (4,), (1, 2, 3)]
    loose = complete_routes(p, routes, 'B', other_limit=30, seconds=3)
    tight = complete_routes(p, routes, 'B', other_limit=0, seconds=3)
    # Independent arithmetic for the two possible exact covers, no solver oracle.
    expected_cheap_km = (1000 + 100 + 1000 + 2000 + 2000) / 1000
    expected_dear_km = (1000 + 100 + 4000 + 1000 + 2000) / 1000
    assert expected_cheap_km == 6.1 and expected_dear_km == 8.1
    for plan, d, w in [(loose, 6.1, 30), (tight, 8.1, 0)]:
        c = validate_plan(p, plan)
        second = recompute(p, plan)
        assert c.feasible and second['feasible']
        assert c.D_km == pytest.approx(d) == pytest.approx(float(second['D_km']))
        assert c.W_min == pytest.approx(w) == pytest.approx(float(second['W_min']))
    assert len(loose.trips) == 3 and len(tight.trips) == 2


def spec_for(tmp_path, method='B', seconds=5):
    p = artificial_problem(6, 2, 1)
    save_problem(p, tmp_path / 'input')
    return {'input_dir': str(tmp_path / 'input'), 'method': method, 'config': CONFIG,
            'tau_s': seconds, 'epsilon_W_min': 30, 'trial_id': 'test', 'scenario_id': 'ART_N6',
            'instance_id': 'artificial', 'repetition_id': 0, 'phase': 'test',
            'seeds': {'solver_seed': 17, 'quantum_seed': 23, 'validation_seed': None}, 'config_sha256': 'a' * 64}


def test_worker_standard_products_and_T_boundary(tmp_path):
    spec = spec_for(tmp_path)
    out = tmp_path / 'result'
    out.mkdir()
    result = execute(spec, out)
    assert result['status'] == 'VALIDATED'
    result = export_standard(result, spec, out)
    assert result['status'] == 'COMPLETE' and eligible(result)
    assert all((out / name).exists() for name in REQUIRED)
    assert json.loads((out / 'routes.geojson').read_text())['features'][0]['geometry'] is None
    assert result['timing_events'][0] == {'name': 'input_load_start', 'elapsed_s': 0.0}
    assert result['timing_events'][-1]['name'] == 'final_validation_end'
    assert result['T_program_s'] == result['timing_events'][-1]['elapsed_s']
    assert result['dependency_setup_s'] >= 0
    assert result['export_wall_s'] > 0 and result['T_program_s'] <= spec['tau_s']
    manifest = json.loads((out / 'manifest.json').read_text())
    import hashlib
    assert all(hashlib.sha256((out / name).read_bytes()).hexdigest() == h for name, h in manifest['files'].items())


def test_tiny_total_budget_fails_without_fake_plan(tmp_path):
    spec = spec_for(tmp_path, seconds=1e-9)
    out = tmp_path / 'result'
    out.mkdir()
    result = execute(spec, out)
    assert not result['budget_met'] and not result['feasible']
    result = export_standard(result, spec, out)
    assert not (out / 'plan.json').exists() and not eligible(result)


def test_C_budget_actually_reaches_solver_setting(tmp_path):
    spec = spec_for(tmp_path, method='C', seconds=3)
    out = tmp_path / 'result'
    out.mkdir()
    result = execute(spec, out)
    assert result['status'] == 'VALIDATED'
    assert result['plan']['method_settings']['requested_routing_seconds'] == 1


def test_verified_incumbent_survives_CP_unknown(monkeypatch):
    from kmd_toc.dwt import methods
    p = artificial_problem(6, 2, 1)
    def unknown(*args, **kwargs):
        raise ValueError('CP_COMPLETION_UNKNOWN')
    monkeypatch.setattr(methods, 'complete_routes', unknown)
    plan = methods.complete(p, [(1, 2, 3, 4, 5, 6)], 'B', 30, Budget(5), 17, {})
    assert validate_plan(p, plan).feasible and recompute(p, plan)['feasible']
    assert plan.method_settings['completion_selected_source'] == 'verified_incumbent'
    assert plan.method_settings['completion_CP_error']['message'] == 'CP_COMPLETION_UNKNOWN'


def test_invalid_incumbent_is_not_rescued_by_score_or_fallback(monkeypatch):
    from kmd_toc.dwt import methods
    def unknown(*args, **kwargs):
        raise ValueError('CP_COMPLETION_UNKNOWN')
    monkeypatch.setattr(methods, 'complete_routes', unknown)
    with pytest.raises(ValueError, match='NO_VERIFIED'):
        methods.complete(tradeoff_problem(), [(1, 2), (3,), (4,)], 'B', 0, Budget(5), 17, {})


@pytest.mark.parametrize('method', ['D', 'D_CLASSICAL_CONTROL'])
def test_hybrid_budgeted_end_to_end_and_quantum_control(tmp_path, method):
    spec = spec_for(tmp_path, method=method, seconds=30)
    out = tmp_path / 'result'
    out.mkdir()
    result = execute(spec, out)
    assert result['status'] == 'VALIDATED'
    m = result['plan']['method_settings']
    assert m['quantum_enabled'] == (method == 'D')
    assert m['classical_only_control'] == (method != 'D')
    assert (m['quantum_calls'] > 0) == (method == 'D')
    assert result['quantum_seed_used'] == (m['quantum_calls'] > 0)
    assert not m['quantum_improvement_claim']
    assert result['stage_evidence_files']
    for item in m['quantum']:
        assert item['training_total_shots'] == item['training_evaluations'] * 1000
        assert sum(item['result']['history'][0]['qiskit_counts'].values()) == item['final_total_shots'] == 4096


def test_registration_input_identity_is_enforced_before_search(tmp_path):
    spec = spec_for(tmp_path)
    spec['registered_input_hash'] = '0' * 64
    out = tmp_path / 'result'
    out.mkdir()
    result = execute(spec, out)
    assert not result['feasible'] and result['plan'] is None
    assert result['error']['message'] == 'REGISTERED_INPUT_OR_OD_CHANGED'


def test_single_pinned_policy_read_in_problem_validation(monkeypatch):
    from kmd_toc.common import models
    p = artificial_problem(20, 3, 1)
    original = models.load_conditions
    calls = []
    def tracked():
        calls.append(True)
        return original()
    monkeypatch.setattr(models, 'load_conditions', tracked)
    p.validate()
    assert len(calls) == 1
    bad = replace(p, stops=(replace(p.stops[0], snap=replace(p.stops[0].snap, distance_m=101)), *p.stops[1:]))
    with pytest.raises(ValueError, match='SNAP'):
        bad.validate()
    # The public standalone check still loads and verifies its policy.
    before = len(calls)
    p.stops[0].snap.validate(p.od.metadata['graph_id'], p.od.metadata['kind'])
    assert len(calls) == before + 1


def test_adaptive_reserve_uses_measured_remaining_two_verifications():
    now = [0.]
    budget = Budget(10, .08, clock=lambda: now[0], adaptive_validation=True)
    budget.observe_validation(1.)
    assert budget.reserve == pytest.approx(2.2)
    assert budget.left() == pytest.approx(7.8)
    budget.observe_validation(.1)
    assert budget.reserve == pytest.approx(2.2)
    budget.observe_validation(2.)
    assert budget.reserve == pytest.approx(4.2)


@pytest.mark.parametrize('error_type,expected', [(BudgetExceeded, 'VALIDATED'), (ValueError, 'NO_VERIFIED_PLAN')])
def test_cooperative_stop_keeps_verified_incumbent_but_does_not_hide_bugs(tmp_path, monkeypatch, error_type, expected):
    from kmd_toc.dwt import methods
    from kmd_toc.pipeline.completion import complete_routes
    spec = spec_for(tmp_path, seconds=10)
    out = tmp_path / 'result'
    out.mkdir()
    def stop(p, method, epsilon, budget, seeds, config):
        plan = complete_routes(p, [(1, 2, 3, 4, 5, 6)], 'B', other_limit=30, seconds=1)
        assert validate_plan(p, plan).feasible and recompute(p, plan)['feasible']
        budget.incumbent = plan
        raise error_type('intentional test stop')
    monkeypatch.setattr(methods, 'generate', stop)
    result = execute(spec, out)
    assert result['status'] == expected
    if expected == 'VALIDATED':
        assert result['plan']['method_settings']['algorithm_path_incomplete']
        assert result['timing_events'][-1]['name'] == 'final_validation_end'
    else:
        assert result['plan'] is None and result['T_program_s'] is None


def test_uniform_dependency_setup_reads_no_delivery_input(monkeypatch):
    from kmd_toc.common import models
    from kmd_toc.dwt import worker
    from kmd_toc.dwt.setup import preload_dependencies
    def forbidden(*args, **kwargs):
        raise AssertionError('Input read during library-only setup')
    monkeypatch.setattr(models, 'load_problem', forbidden)
    monkeypatch.setattr(worker, 'load_problem', forbidden)
    assert preload_dependencies() >= 0


def test_single_A_preserves_human_time_boundary_and_is_not_scored(tmp_path):
    spec = spec_for(tmp_path, method='A', seconds=10)
    out = tmp_path / 'result'
    out.mkdir()
    row = execute(spec, out)
    assert row['status'] == 'VALIDATED'
    row = export_standard(row, spec, out)
    assert row['status'] == 'COMPLETE'
    assert row['plan']['method_settings']['single_A_rule']['rule'] == 'A2'
    assert row['T_human_s'] is None and row['T_program_s'] > 0
    assert row['T_human_route_episode_reference']['mapping']['full_A_T_s'] is None
    assert score(row, dict(D_km=100, W_min=100, T_program_s=10), [1 / 3] * 3) is None


def test_registered_runner_forwards_verified_import_only_launch_mode(tmp_path, monkeypatch):
    from kmd_toc.dwt import experiment, setup
    import multiprocessing
    spec = spec_for(tmp_path)
    target = tmp_path / 'registration.json'
    target.write_text(json.dumps({'phase': 'test', 'specs': [spec]}))
    monkeypatch.setattr(setup, 'preload_dependencies', lambda: 0.)
    original = Path.iterdir
    def iterdir(path):
        return iter([Path('/proc/self/task/1')]) if str(path) == '/proc/self/task' else original(path)
    monkeypatch.setattr(Path, 'iterdir', iterdir)
    monkeypatch.setattr(multiprocessing, 'get_all_start_methods', lambda: ['fork'])
    received = []
    def run(spec, root, geometry, *, import_only_fork=False):
        received.append(import_only_fork)
        return dict(trial_id=spec['trial_id'], status='test_only', D_km=None, W_min=None, T_program_s=None)
    monkeypatch.setattr(experiment, 'run_spec', run)
    experiment.run_registered(target)
    assert received == [True]
