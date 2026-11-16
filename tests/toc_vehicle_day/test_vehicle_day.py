"""Sixteen requested contracts plus independent enumeration and old-AOA bridge."""
from dataclasses import replace
from itertools import permutations
import numpy as np
import pytest
from kmd_toc.column_generation.models import Route
from kmd_toc.column_generation.aoa import AOAConfig
from kmd_toc.vehicle_day.fixtures import small_problem
from kmd_toc.vehicle_day.model import ObjectiveProfile, occupied_slots
from kmd_toc.vehicle_day.generation import make_day, enumerate_days, seed_plan, grid_ceil
from kmd_toc.vehicle_day.validation import validate_day, validate_plan, assign_berths, independent_plan_oracle
from kmd_toc.vehicle_day.master import solve_lp, solve_integer, reduced_cost
from kmd_toc.vehicle_day.runner import run_day_cg


@pytest.fixture(scope='module')
def problem():
    return small_problem(4, 2)


@pytest.fixture(scope='module')
def columns(problem):
    return enumerate_days(problem)


def test_zero_one_two_trips_and_capacity(problem):
    empty = make_day(problem, 'V0', (), ())
    assert not empty.trips and empty.loading_s == empty.waiting_min == 0
    day = make_day(problem, 'V0', (Route((1, 2)), Route((3, 4))), (0, 840))
    assert len(day.trips) == 2 and day.trips[1].ready_s == 840
    assert day.trips[0].return_s == 720
    assert not validate_day(problem, day)
    with pytest.raises(ValueError, match='MAX_TWO'):
        make_day(problem, 'V0', (Route((1,)),) * 3, (0, 600, 1200))
    with pytest.raises(ValueError, match='CAPACITY'):
        make_day(problem, 'V0', (Route((1, 2, 3)),), (0,))
    with pytest.raises(ValueError, match='REPEATED'):
        make_day(problem, 'V0', (Route((1, 2)), Route((2, 3))), (0, 840))


@pytest.mark.parametrize('kind,code', [
    ('early_second', 'LOAD_BEFORE_READY_OR_PREPARATION'),
    ('wrong_ready', 'READY_TIME_MISMATCH'),
    ('early_departure', 'DEPARTURE_NOT_AT_LOADING_END'),
    ('late_return', 'SHIFT_END_EXCEEDED'),
    ('wrong_load', 'LOAD_METADATA_MISMATCH'),
    ('wrong_distance', 'DISTANCE_MISMATCH'),
    ('second_only', 'TRIP_ID_OR_SECOND_ONLY'),
])
def test_invalid_time_and_metadata(problem, kind, code):
    day = make_day(problem, 'V0', (Route((1, 2)), Route((3, 4))), (0, 840))
    a, b = day.trips
    if kind == 'early_second': b = replace(b, load_start_s=600)
    if kind == 'wrong_ready': b = replace(b, ready_s=b.load_start_s + 120)
    if kind == 'early_departure': a = replace(a, departure_s=a.load_end_s - 1)
    if kind == 'late_return': b = replace(b, return_s=1800)
    if kind == 'wrong_load': a = replace(a, parcel_count=0)
    if kind == 'wrong_distance': a = replace(a, distance_km=0)
    if kind == 'second_only': a = replace(a, trip_id=2)
    assert code in validate_day(problem, replace(day, trips=(a, b)))


def test_preparation_and_loading_cannot_be_skipped(problem):
    with pytest.raises(ValueError, match='BEFORE_READY'):
        make_day(problem, 'V0', (Route((1, 2)), Route((3, 4))), (0, 720))
    day = make_day(problem, 'V0', (Route((1, 2)),), (0,))
    assert day.trips[0].departure_s == 120
    assert day.waiting_min == 0 and day.loading_s == 120


def test_berth_exclusion_and_half_open(problem):
    plan = [make_day(problem, 'V0', (Route((1, 2)),), (0,)),
            make_day(problem, 'V1', (Route((3, 4)),), (0,))]
    assert validate_plan(problem, plan)['peak_berths'] == 2
    one = small_problem(4, 1)
    same = [make_day(one, 'V0', (Route((1, 2)),), (0,)),
            make_day(one, 'V1', (Route((3, 4)),), (0,))]
    assert 'BERTH_OVERLAP' in validate_plan(one, same)['reasons']
    sequential = [same[0], make_day(one, 'V1', (Route((3, 4)),), (120,))]
    result = validate_plan(one, sequential)
    assert result['valid'] and result['W_min'] == 2 and result['loading_work_min'] == 4
    assert [x['berth_id'] for x in assign_berths(one, sequential)] == [0, 0]
    assert 'CUSTOMER_COVERAGE' in validate_plan(one, [same[0]])['reasons']
    assert 'BERTH_OVERLAP' in validate_plan(problem, plan + [plan[0]])['reasons']


def test_coarse_grid_waiting_is_visible(problem):
    v = replace(problem.vehicles[0], ready_s=60)
    fine = replace(problem, vehicles=(v,), delta_s=60)
    coarse = replace(problem, vehicles=(v,), delta_s=120)
    a = make_day(fine, 'V0', (Route((1,)),), (60,))
    b = make_day(coarse, 'V0', (Route((1,)),), (120,))
    assert a.waiting_min == 0 and b.waiting_min == 1


def test_generation_completeness_against_permutation_cuts(problem, columns):
    # Independent ordered-subset/cut/time loops, not the route-pair generator.
    expected = {()}
    for count in range(1, 5):
        for order in permutations(problem.base.customers, count):
            for cut in range(1, count + 1):
                routes = [order[:cut]] + ([order[cut:]] if cut < count else [])
                if any(len(r) > 2 for r in routes): continue
                for first in range(0, 1680, 120):
                    end_first = first + 120 + 120 * (2 * len(routes[0]) + 1)
                    if end_first > 1680: continue
                    if len(routes) == 1:
                        expected.add(((routes[0], first),))
                    else:
                        for second in range(end_first + 120, 1680, 120):
                            if second + 120 + 120 * (2 * len(routes[1]) + 1) <= 1680:
                                expected.add(((routes[0], first), (routes[1], second)))
    observed = {tuple((t.customers, t.load_start_s) for t in c.trips)
                for c in columns if c.vehicle_id == 'V0'}
    assert observed == expected
    assert len({c.column_id for c in columns}) == len(columns)


@pytest.mark.parametrize('primary', ['D', 'W'])
def test_full_master_independent_combinations_and_duals(problem, columns, primary):
    profile = ObjectiveProfile(primary)
    lp = solve_lp(problem, columns, profile)
    ip = solve_integer(problem, columns, profile)
    independent = independent_plan_oracle(problem, columns, profile)
    assert lp['success'] and ip['success'] and independent['feasible']
    assert ip['objective'] == pytest.approx(independent['objective'])
    assert np.allclose(lp['pool_reduced_costs'], lp['solver_lower_marginals'])
    assert lp['objective'] == pytest.approx(lp['dual_objective'])
    assert validate_plan(problem, ip['selected'])['valid']


def test_complete_reduced_cost_includes_all_duals(problem):
    c = make_day(problem, 'V0', (Route((1, 2)),), (120,))
    dual = {'phase': 'II', 'customer': [1, 2, 3, 4],
            'vehicle': {'V0': -3, 'V1': 0}, 'berth': [-.5] * problem.slots, 'other': -.25}
    expected = c.distance_km - 3 + 3 + .5 + .25 * c.waiting_min
    assert reduced_cost(problem, c, dual, ObjectiveProfile('D', 10)) == pytest.approx(expected)
    assert not np.isclose(expected, c.distance_km - 3)


def test_classical_day_cg_changes_assignment_and_order(problem, columns):
    result = run_day_cg(problem, columns, ObjectiveProfile('D'))
    assert result['integer']['success'] and result['metrics']['valid']
    assert result['negative_columns_added'] > 0
    assert result['integer']['objective'] < result['initial_plan']['D_km']
    assert result['integer']['objective'] >= result['full_grid_integer']['objective'] - 1e-8
    assert result['final_full_oracle_min_rc'] >= -1e-7
    assert result['stop_reason'] == 'GRID_PRICING_CERTIFIED'


def test_phase_I_infeasibility_is_not_zero_distance(problem):
    bad = replace(problem, vehicles=(replace(problem.vehicles[0], capacity=1),))
    all_days = enumerate_days(bad)
    result = run_day_cg(bad, all_days, ObjectiveProfile('D'), use_seed=False)
    assert not result['integer']['success'] and result['metrics'] is None
    assert 'TOTAL_CAPACITY_NECESSARY_CONDITION' in result['infeasibility_causes']
    assert result['final_lp']['artificial_sum'] > 0


def test_safe_existing_aoa_bridge(problem, columns):
    cfg = AOAConfig(slots=3, max_evaluations=40, restarts=1, solver_seed=2101)
    result = run_day_cg(problem, columns, ObjectiveProfile('D'), mode='aoa', aoa_config=cfg)
    assert result['integer']['success'] and result['metrics']['valid']
    assert result['negative_columns_added'] > 0
    assert result['stop_reason'] == 'AOA_NO_IMPROVING_DAY'
    assert not result['oracle_fallback_used']
    assert all(not step['aoa']['oracle_fallback_used'] for step in result['trace'])
