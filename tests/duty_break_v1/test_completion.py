from dataclasses import replace
import copy
import json

import pytest

from kmd_toc.common.config import ROOT,read_json
from kmd_toc.termination_v1.work import Ledger
from kmd_toc.baseline_a.fixtures import artificial_problem
from kmd_toc.duty_break_v1.models import activate,RestOptions
from kmd_toc.duty_break_v1.policy import VERSION
from kmd_toc.duty_break_v1.scheduler import schedule
from kmd_toc.duty_break_v1.validation import require_valid
from .test_duty import witness


def config():return read_json(ROOT/'configs/toc_delivery/termination_rules_20261116_v1.json')


def test_CP_has_break_return_and_FCFS_inside_model_and_matches_physical_schedule(witness):
    from kmd_toc.duty_break_v1.cp import solve_completion
    p,routes,expected=witness;index={s:i for i,s in enumerate(p.od.ids)}
    pinned={k:tuple(index[s] for s in r) for k,r in routes.items()};cfg=config();before=json.dumps(cfg,sort_keys=True)
    ledger=Ledger();actual=solve_completion(p,list(pinned.values()),'B',cfg,ledger,13,pinned_assignments=pinned)
    assert actual.trips==expected.trips and actual.breaks==expected.breaks
    assert actual.method_settings['CP_wait_s']==round(require_valid(p,actual)['W_total_loading_min']*60)
    assert cfg==json.loads(before)
    assert ledger.counts['CP_calls']==1


def test_CP_mismatch_is_not_hidden_by_feasible_incumbent(witness,monkeypatch):
    import kmd_toc.duty_break_v1.cp as cp
    p,routes,_=witness;index={s:i for i,s in enumerate(p.od.ids)}
    pinned={k:tuple(index[s] for s in r) for k,r in routes.items()}
    def bad(*a,**kw):raise cp.CompletionMismatch('intentional inconsistency')
    monkeypatch.setattr(cp,'solve_completion',bad)
    with pytest.raises(cp.CompletionMismatch):cp.complete(p,list(pinned.values()),'B',config(),Ledger(),13,pinned_assignments=pinned)


@pytest.mark.parametrize('method',['B','C'])
def test_existing_classical_algorithms_new_common_completion_no_condition_or_seed_change(method):
    from kmd_toc.duty_break_v1.methods import generate
    p=activate(artificial_problem(4,2,1),version=VERSION,rest_options=RestOptions(allow_assumed_locations=True))
    cfg=config();seeds={'solver_seed':13,'quantum_seed':17};before=copy.deepcopy((cfg,seeds))
    plan=generate(p,method,cfg,Ledger(),seeds)
    assert require_valid(p,plan)['model_feasible']
    assert (cfg,seeds)==before
    assert plan.method_settings['duty_version']==VERSION


def test_quantum_assignment_order_and_nonselected_order_preserved_without_quantum_replacement(monkeypatch):
    from kmd_toc.d_local_design.completion import extract,preserves
    from kmd_toc.d_local_design.model import Decision
    from kmd_toc.duty_break_v1.local import complete,evaluate
    import kmd_toc.common.adapters as adapters
    def legacy_forbidden(*a,**kw):raise AssertionError('legacy Q bridge would bypass new constraints')
    monkeypatch.setattr(adapters,'to_vehicle_day',legacy_forbidden)
    p=activate(artificial_problem(4,2,1),version=VERSION,rest_options=RestOptions(allow_assumed_locations=True))
    original=schedule(p,{('v0',1):('c0001','c0002'),('v1',1):('c0003','c0004')},'D')
    local=extract(p,original,(('v0',1),('v1',1)),('c0002','c0004'),seed=17)
    decision=Decision(('c0004',),('c0002',));provenance={'kind':'TEST_DOUBLE_NOT_QUANTUM_PERFORMANCE'}
    proposal=complete(p,original,local,decision,quantum_provenance=provenance)
    assert preserves(proposal,local,decision,original)
    assert require_valid(p,proposal)['model_feasible']
    selected,ledger=evaluate(p,original,local,decision,quantum_provenance=provenance)
    if ledger['status']=='ACCEPT':assert ledger['delta_D_km']<=0 and ledger['delta_W_total_min']<=0
    else:assert selected is original


def test_Q_pool_completion_requires_explicit_assignment_and_no_full_Q_fallback():
    from kmd_toc.duty_break_v1.master import complete_supplied_routes
    from kmd_toc.duty_break_v1.cp import complete,solve_completion
    from kmd_toc.duty_break_v1.methods import generate
    p=activate(artificial_problem(4,2,1),version=VERSION,rest_options=RestOptions(allow_assumed_locations=True))
    with pytest.raises(ValueError,match='EXPLICITLY_PINNED'):complete_supplied_routes(p,[(1,2,3,4)],'Q',config(),Ledger(),13)
    for entry in (complete,solve_completion):
        with pytest.raises(ValueError,match='EXPLICITLY_PINNED'):entry(p,[(1,2,3,4)],'Q',config(),Ledger(),13)
    with pytest.raises(ValueError,match='NO_CLASSICAL_SUBSTITUTION'):generate(p,'Q',config(),Ledger(),{'solver_seed':13,'quantum_seed':17})


def test_pinned_Q_common_master_retains_supplied_full_assignment():
    from kmd_toc.duty_break_v1.master import complete_supplied_routes
    p=activate(artificial_problem(4,2,1),version=VERSION,rest_options=RestOptions(allow_assumed_locations=True))
    pinned={('v0',1):(2,1),('v1',1):(4,3)}
    plan=complete_supplied_routes(p,list(pinned.values()),'Q',config(),Ledger(),13,pinned_assignments=pinned)
    assert {(t.vehicle_id,t.trip_no):tuple(p.od.ids.index(v.stop_id) for v in t.visits) for t in plan.trips}==pinned


def test_infeasible_quantum_proposal_keeps_valid_incumbent_without_repair(witness):
    from kmd_toc.d_local_design.completion import extract
    from kmd_toc.d_local_design.model import Decision
    from kmd_toc.duty_break_v1.local import evaluate
    p,_,original=witness
    local=extract(p,original,(('v0',1),('v1',2)),('c0001','c0004'),seed=17)
    selected,ledger=evaluate(p,original,local,Decision(('c0004',),('c0001',)),
                             quantum_provenance={'kind':'TEST_DOUBLE_NOT_QUANTUM_PERFORMANCE'})
    assert selected is original and ledger['status']=='REJECT_DUTY_COMPLETION'
    assert ledger['invalid_candidate_never_adopted'] and not ledger['quantum_decision_used_as_classical_seed']
