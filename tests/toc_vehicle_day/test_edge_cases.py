"""Order-sensitive timing and proof-scope regression, independent artificial OD."""
from dataclasses import replace
import pytest
from kmd_toc.column_generation.models import Route
from kmd_toc.column_generation.aoa import AOAConfig
from kmd_toc.vehicle_day.fixtures import small_problem
from kmd_toc.vehicle_day.model import ObjectiveProfile
from kmd_toc.vehicle_day.generation import make_day, enumerate_days
from kmd_toc.vehicle_day.master import solve_lp
from kmd_toc.vehicle_day.runner import run_day_cg


def test_visit_order_changes_return_and_second_trip_ready():
    base = small_problem(4, 1)
    travel = ((0,120,240,120,240), (240,0,120,240,120), (120,240,0,120,240),
              (240,120,240,0,120), (120,240,120,240,0))
    p = replace(base, travel_s=travel)
    forward = make_day(p, 'V0', (Route((1, 2)),), (0,))
    backward = make_day(p, 'V0', (Route((2, 1)),), (0,))
    assert forward.trips[0].return_s == 720
    assert backward.trips[0].return_s == 1080
    good = make_day(p, 'V0', (Route((1, 2)), Route((3,))), (0, 840))
    assert good.trips[1].ready_s == 840
    with pytest.raises(ValueError, match='BEFORE_READY'):
        make_day(p, 'V0', (Route((2, 1)), Route((3,))), (0, 840))


def test_master_rejects_invalid_stored_schedule():
    p = small_problem()
    day = make_day(p, 'V0', (Route((1, 2)),), (0,))
    invalid = replace(day, trips=(replace(day.trips[0], departure_s=0),))
    with pytest.raises(ValueError, match='INVALID_DAY_COLUMN'):
        solve_lp(p, [invalid], ObjectiveProfile('D'))


def test_aoa_miss_never_becomes_grid_certificate(monkeypatch):
    p = small_problem()
    monkeypatch.setattr('kmd_toc.vehicle_day.runner.aoa_day_candidates',
                        lambda *args: ([], {'oracle_fallback_used': False}))
    r = run_day_cg(p, enumerate_days(p), ObjectiveProfile('D'), 'aoa', AOAConfig())
    assert r['stop_reason'] == 'AOA_NO_IMPROVING_DAY'
    assert r['final_full_oracle_min_rc'] < -1e-7
    assert r['metrics']['valid']


def test_auxiliary_wait_bound_can_make_phase_I_positive():
    p = small_problem(6, 1)
    r = run_day_cg(p, enumerate_days(p), ObjectiveProfile('D', 0), use_seed=False)
    assert r['final_phase'] == 'I'
    assert r['final_lp']['artificial_sum'] > 0
    assert not r['full_grid_integer']['success'] and r['metrics'] is None
