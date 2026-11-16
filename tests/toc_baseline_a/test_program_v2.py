from dataclasses import replace
import json
import math
import time

import numpy as np
import pytest

from kmd_toc.baseline_a.construction import create_plan
from kmd_toc.baseline_a.fixtures import artificial_problem
from kmd_toc.baseline_a.program import digest, execute, load_registered, measure, score
from kmd_toc.baseline_a.program_validation import audit_plan
from kmd_toc.common.models import load_problem, save_problem
from kmd_toc.common.validation import validate_plan


@pytest.fixture
def two_trip():
    p = artificial_problem(120, 1, 1)
    return p, create_plan(p, 'A2')


def test_small_hand_calculation_and_units():
    p = artificial_problem(2, 1, 1)
    d = np.full((3, 3), 1000., dtype='float64')
    t = np.full((3, 3), 1.2, dtype='float64')
    np.fill_diagonal(d, 0)
    np.fill_diagonal(t, 0)
    od = replace(p.od, distance_m=d, duration_s=t)
    p = replace(p, od=od, experiment=replace(p.experiment, data_hashes={'od': od.fingerprint}))
    q = create_plan(p, 'A2')
    report = audit_plan(p, q)
    assert report['feasible']
    assert float(report['D_km']) == 3
    assert float(report['W_min']) == 0
    assert q.trips[0].return_s == 30600 + 1800 + 3 * 2 + 2 * 120
    assert validate_plan(p, q).D_km == 3


@pytest.mark.parametrize('kind', ['duplicate', 'omission', 'capacity', 'trip_count', 'connection',
                                  'preload_departure', 'deadline', 'negative_wait', 'distance', 'service', 'depot'])
def test_independent_oracle_rejects_corrupt_plans(two_trip, kind):
    p, q = two_trip
    a, b = q.trips
    if kind == 'duplicate':
        a = replace(a, visits=(*a.visits, a.visits[0]))
    elif kind == 'omission':
        a = replace(a, visits=a.visits[1:])
    elif kind == 'capacity':
        a = replace(a, visits=(*a.visits, b.visits[0]))
    elif kind == 'trip_count':
        b = replace(b, trip_no=3)
    elif kind == 'connection':
        b = replace(b, ready_s=a.return_s-1, load_start_s=a.return_s-1)
    elif kind == 'preload_departure':
        a = replace(a, departure_s=a.load_end_s-1)
    elif kind == 'deadline':
        a = replace(a, return_s=72001)
    elif kind == 'negative_wait':
        a = replace(a, load_start_s=a.ready_s-60, waiting_s=-60)
    elif kind == 'distance':
        a = replace(a, distance_m=a.distance_m+1)
    elif kind == 'service':
        a = replace(a, visits=(replace(a.visits[0], service_end_s=a.visits[0].service_end_s+1), *a.visits[1:]))
    elif kind == 'depot':
        a = replace(a, destination_id='wrong')
    bad = replace(q, trips=(a, b))
    assert not validate_plan(p, bad).feasible
    assert not audit_plan(p, bad)['feasible']


def test_berth_overlap_and_valid_second_connection(two_trip):
    p, q = two_trip
    assert audit_plan(p, q)['feasible']
    assert q.trips[1].ready_s == q.trips[0].return_s
    p = artificial_problem(20, 3, 1)
    q = create_plan(p, 'A2')
    a, b, c = q.trips
    bad = replace(q, trips=(a, replace(b, load_start_s=a.load_start_s, load_end_s=a.load_end_s), c))
    assert 'BERTH_OVERLAP' in audit_plan(p, bad)['errors']


def test_full_measurement_includes_second_validation(monkeypatch):
    import kmd_toc.baseline_a.program as module
    original = module.audit_plan
    def slow_audit(p, q):
        time.sleep(.025)
        return original(p, q)
    monkeypatch.setattr(module, 'audit_plan', slow_audit)
    row, q = measure(lambda: artificial_problem())
    assert row['status'] == 'VALIDATED'
    assert row['T_program_s'] >= .025
    assert row['timing_events'][-1]['name'] == 'validation_agreement_end'
    assert row['timing_events'][-1]['elapsed_s'] == row['T_A_program']
    assert row['T_A_human_reference'] is None


def test_mismatched_or_failed_validation_has_no_accepted_metrics(monkeypatch):
    import kmd_toc.baseline_a.program as module
    def wrong(*_):
        return {'feasible': True, 'D_km': '9999', 'W_min': '0', 'errors': []}
    monkeypatch.setattr(module, 'audit_plan', wrong)
    row, q = measure(lambda: artificial_problem())
    assert q is not None and row['status'] == 'REJECTED_PLAN'
    assert row['D_km'] is row['W_min'] is row['T_program_s'] is None
    assert row['T_attempt_wall_s'] > 0


def test_hash_and_unreachable_failures(tmp_path):
    p = artificial_problem()
    directory = tmp_path / 'inputs'
    save_problem(p, directory)
    raw = json.loads((directory / 'input.json').read_text())
    raw['stops'][0]['latitude'] += .001
    (directory / 'input.json').write_text(json.dumps(raw))
    with pytest.raises(ValueError, match='INPUT_HASH'):
        load_problem(directory)
    with pytest.raises(ValueError, match='REGISTERED_INPUT_FILE_HASH'):
        load_registered(directory, {'files': {'input.json': '0'*64}}, 'S1')
    reach, d, t = (a.copy() for a in [p.od.reachable, p.od.distance_m, p.od.duration_s])
    reach[0, 1], d[0, 1], t[0, 1] = False, math.nan, math.nan
    od = replace(p.od, reachable=reach, distance_m=d, duration_s=t)
    p = replace(p, od=od, experiment=replace(p.experiment, data_hashes={'od': od.fingerprint}))
    with pytest.raises(ValueError, match='OD_UNREACHABLE'):
        p.validate()


def test_failure_saved_and_output_never_overwritten(tmp_path):
    directory = tmp_path / 'inputs'
    save_problem(artificial_problem(), directory)
    out = tmp_path / 'failed'
    row = execute(directory, 'S1', out, registration={'files': {'input.json': '0'*64}})
    assert row['status'] == 'INPUT_HOLD'
    assert row['T_program_s'] is None and row['T_attempt_wall_s'] > 0
    assert not (out / 'plan.json').exists()
    assert 'REGISTERED_INPUT_FILE_HASH' in json.loads((out / 'validation.json').read_text())['error']['message']
    before = digest(out / 'metrics.json')
    with pytest.raises(FileExistsError):
        execute(directory, 'S1', out)
    assert digest(out / 'metrics.json') == before


def test_time_limit_has_attempt_but_no_accepted_time():
    row, _ = measure(lambda: artificial_problem(), limit_s=0)
    assert row['status'] == 'TIME_LIMIT'
    assert row['T_program_s'] is row['D_km'] is row['W_min'] is None
    assert row['T_attempt_wall_s'] > 0


def test_reference_guard_and_equal_weight_score():
    m = {'status': 'VALIDATED', 'scenario_id': 'S1', 'input_hash': 'a', 'OD_hash': 'b',
         'T_kind': 'program_wall', 'T_scope': ['complete'], 'comparison_contract_id': 'same',
         'D_km': 3., 'W_min': 2., 'T_program_s': 1.}
    r = {**m, 'status': 'FROZEN'}
    assert score(m, None)['J'] is None
    assert score(m, r)['J'] == 1
    assert score(m, {**r, 'W_min': 0})['J'] is None
    assert score(m, {**r, 'T_program_s': float('inf')})['J'] is None
    assert score(m, {**r, 'scenario_id': 'S2'})['J'] is None
    assert score(m, {**r, 'T_scope': ['solver_only']})['J'] is None
