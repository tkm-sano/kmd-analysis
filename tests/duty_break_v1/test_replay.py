import json
from pathlib import Path

import pytest

from kmd_toc.baseline_a.fixtures import artificial_problem
from kmd_toc.common.models import save_problem,save_plan as save_old
from kmd_toc.common.config import digest_file
from kmd_toc.fcfs_v1.scheduler import schedule as schedule_old
from kmd_toc.duty_break_v1.models import RestOptions
from kmd_toc.duty_break_v1.__main__ import run_case


def test_replay_is_explicit_pinned_conversion_and_old_inputs_untouched(tmp_path):
    base=artificial_problem(3,2,1);save_problem(base,tmp_path/'input')
    old=schedule_old(base,{('v0',1):('c0001','c0002'),('v1',1):('c0003',)},'C')
    source=tmp_path/'old.json';save_old(old,source);before=digest_file(source)
    result=run_case(base,tmp_path/'input',source,tmp_path/'new',RestOptions(allow_assumed_locations=True))
    assert result['model_feasible'] and result['routes_assignments_and_order_preserved']
    assert result['delta_D_pinned_replay_km']==0 and digest_file(source)==before
    assert result['quantum_calls']==0 and result['full_planning_time_s'] is None
    assert all(v['return_deadline_s']==68400 for v in result['derived_vehicles'])
    assert all(b['closing_s']==72000 for b in result['berths_unchanged'])
    with pytest.raises(FileExistsError):run_case(base,tmp_path/'input',source,tmp_path/'new',RestOptions(allow_assumed_locations=True))


def test_unconfirmed_location_failure_is_not_saved_as_valid_plan(tmp_path):
    base=artificial_problem(1,1,1);old=schedule_old(base,{('v0',1):('c0001',)},'B')
    source=tmp_path/'old.json';save_old(old,source)
    result=run_case(base,tmp_path/'input',source,tmp_path/'strict',RestOptions())
    assert not result['model_feasible']
    assert result['status']=='REPLAYED_ASSIGNMENT_INFEASIBLE_NOT_GLOBAL_PROOF'
    assert (tmp_path/'strict/REJECTED_CANDIDATE.json').exists()
    assert not (tmp_path/'strict/plan.json').exists()
