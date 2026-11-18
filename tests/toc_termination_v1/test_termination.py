import copy
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import pytest
from kmd_toc.termination_v1.work import CheckBudget,Ledger,key,WorkLimit
from kmd_toc.termination_v1.runner import CONFIG,ROOT,validate_config,select_candidates,aggregate
from kmd_toc.comparison_v1.contract import read,digest
from kmd_toc.baseline_a.fixtures import artificial_problem

@pytest.fixture
def config():return read(CONFIG)


def test_limit_boundary_counts_failures_independent_of_clock():
    a,b=CheckBudget(4),CheckBudget(4)
    assert [a() for _ in range(7)]==[False,False,False,True,True,True,True]
    assert [b() for _ in range(7)]==[False,False,False,True,True,True,True]
    assert (a.checks,a.acknowledgements)==(4,3)


def test_clock_change_preserves_frozen_A_and_routing(config):
    from kmd_toc.baseline_a.rule_v1 import generate
    from kmd_toc.pipeline.classical import directed_cw
    from kmd_toc.termination_v1.solvers import routing_pool
    p=artificial_problem(6,2,1)
    first,_=generate(p,clock=lambda:1.)
    second,_=generate(p,clock=lambda:10**12)
    assert first==second
    routes,_=directed_cw(p)
    a=Ledger(clock=lambda:1.);b=Ledger(clock=lambda:10**12)
    x,ax=routing_pool(p,routes,config,a,13);y,ay=routing_pool(p,routes,config,b,13)
    assert x==y and ax==ay and a.counts==b.counts
    end=next(e for e in a.events if e['event']=='Routing_end')
    assert end['algorithm_termination']=='WORK_BUDGET_REACHED'
    assert end['checks']==256


def test_routing_no_initial_feasible_terminates(config):
    from kmd_toc.termination_v1.solvers import routing_pool
    p=artificial_problem(3,1,1)
    p=replace(p,stops=p.stops) # actual capacity search: invalid seeded route, solver must build initial route
    ledger=Ledger();routes,_=routing_pool(p,[],config,ledger,13)
    assert routes and ledger.counts['Routing_limit_checks']<=256


def test_no_plan_completion_and_incumbent_preserved(config,monkeypatch):
    import kmd_toc.termination_v1.solvers as solvers
    p=artificial_problem(6,2,1);routes=[tuple(range(1,7))]
    def no_plan(*args,**kwargs):raise ValueError('CP_COMPLETION_UNKNOWN')
    monkeypatch.setattr(solvers,'solve_completion',no_plan)
    ledger=Ledger();plan=solvers.complete(p,routes,'B',config,ledger,13)
    assert plan.method_settings['completion_selected_source']=='verified_incumbent'
    with pytest.raises(ValueError,match='NO_VERIFIED'):solvers.complete(p,[],'B',config,Ledger(),13)


def test_actual_CP_work_callback_and_physical_conditions(config):
    from kmd_toc.termination_v1.solvers import solve_completion
    from kmd_toc.comparison_v1.execution import physical_checks
    p=artificial_problem(6,2,1);ledger=Ledger()
    config['completion']['max_improving_solutions']=1
    plan=solve_completion(p,[tuple(range(1,7))],'B',config,ledger,13)
    end=next(e for e in ledger.events if e['event']=='CP_end')
    assert end['improving_solutions']==1 and end['algorithm_termination']=='WORK_BUDGET_REACHED'
    assert physical_checks(p,plan,'B')[0]


def test_duplicate_and_infeasible_catalogues_finish(config,monkeypatch):
    from kmd_toc.common.adapters import to_vehicle_day
    from kmd_toc.pipeline.completion import assemble,greedy_assignment
    from kmd_toc.termination_v1.master import catalogue
    import kmd_toc.vehicle_day.generation as gen
    p=artificial_problem(6,2,1);day=to_vehicle_day(p,delta_s=1);routes=[tuple(range(1,7))]
    seed=assemble(p,greedy_assignment(p,routes),'D',{})
    ledger=Ledger();catalogue(p,day,routes,seed,[],config,ledger)
    assert ledger.counts['day_pattern_attempts']==6
    assert ledger.counts['day_pattern_overlap_rejections']==4
    def invalid(*args,**kwargs):raise ValueError('INFEASIBLE')
    monkeypatch.setattr(gen,'make_day',invalid)
    ledger=Ledger();assert catalogue(p,day,routes,seed,[],config,ledger)==[]
    assert ledger.counts['day_pattern_attempts']==6 and ledger.counts['day_pattern_infeasible']==2


def engine(config,ledger):
    from kmd_toc.common.adapters import to_vehicle_day
    from kmd_toc.column_generation.reduction import contract
    from kmd_toc.column_generation.aoa import AOAConfig
    from kmd_toc.termination_v1.quantum import FinitePricingAOA
    p=artificial_problem(6,2,1);day=to_vehicle_day(p,delta_s=1)
    sub=contract(day.base,[0.]*6,((1,2),(3,4),(5,6)),'test',slots=4)
    cfg=AOAConfig(slots=4,solver_seed=127,**{k:config['D'][k] for k in ('p','max_evaluations','restarts','train_shots','final_shots','tolerance','statevector_backend')})
    return FinitePricingAOA(sub.pricing,sub.dual,cfg,ledger,'test')


def test_real_shots_counts_initial_eval_cache_and_single_total_restart(config):
    ledger=Ledger();result=engine(config,ledger).run()
    n=ledger.counts['quantum_training_attempts']
    assert len(result['history'])==1 and 1<=n<=80
    assert n==len(result['history'][0]['evaluations'])==ledger.counts['quantum_training_successes']
    assert ledger.counts['quantum_training_shots']==10000*n
    assert ledger.counts['quantum_final_shots']==result['measured_shots']==10000
    assert ledger.counts['quantum_final_sampling_calls']==ledger.counts['quantum_final_circuit_calls']==1
    assert ledger.counts['quantum_optimizer_cache_hits']>=1
    assert ledger.counts['quantum_optimizer_initial_preparations']==1
    assert ledger.counts['quantum_validation_tensor_calls']==1


def test_failed_objective_is_counted_and_not_retried(config,monkeypatch):
    ledger=Ledger();e=engine(config,ledger)
    def fail(*_):raise RuntimeError('evaluation failure')
    monkeypatch.setattr(e,'tensor_state',fail)
    with pytest.raises(RuntimeError,match='evaluation failure'):e.run()
    assert ledger.counts['quantum_training_attempts']==ledger.counts['quantum_training_failures']==1
    assert 'quantum_training_shots' not in ledger.counts
    assert 'quantum_final_shots' not in ledger.counts


def test_defensive_evaluation_guard_preserves_candidate_at_80(config,monkeypatch):
    import kmd_toc.termination_v1.quantum as q
    def excessive(objective,initial,*args):
        for _ in range(81):objective(initial)
    monkeypatch.setattr(q,'measured_minimize',excessive)
    ledger=Ledger();result=engine(config,ledger).run()
    assert ledger.counts['quantum_training_attempts']==80
    assert ledger.counts['quantum_objective_requests']==81
    assert ledger.counts['quantum_training_shots']==800000
    assert result['measured_shots']==10000


def test_branch_errors_do_not_require_all_branch_success_and_ties_stable(config,tmp_path):
    from kmd_toc.pipeline.completion import assemble,greedy_assignment
    from kmd_toc.common.models import save_plan
    p=artificial_problem(6,2,1);plan=assemble(p,greedy_assignment(p,[tuple(range(1,7))]),'B',{})
    branches=[{'branch_id':0,'adoptable':False,'execution_state':'ERROR'}]
    for i in [3,2,1]:
        out=tmp_path/f'branch_{i:02d}';out.mkdir();save_plan(plan,out/'plan.json')
        branches.append({'branch_id':i,'adoptable':True,'plan_sha256':digest(out/'plan.json')})
    selected,checks=select_candidates(p,'B',branches,tmp_path)
    assert selected[1]==1 and len(checks)==4


def test_unstarted_failures_and_main_gate_preserved(tmp_path):
    runs=[{'run_id':'a','case_id':'x','method':'A'},{'run_id':'d','case_id':'x','method':'D'}]
    (tmp_path/'REGISTERED.json').write_text(json.dumps({'cases':[{'case_id':'x'}],'runs':runs}))
    rows=aggregate(tmp_path)
    assert len(rows)==2 and all(r['D'] is None and not r['adoptable'] for r in rows)
    assert all(r['execution_state']=='NOT_STARTED' for r in rows)


def test_new_config_rejects_time_or_missing_work_budget(config):
    validate_config(config)
    for key in ('time_limit','max_deterministic_time','timeout'):
        bad=copy.deepcopy(config);bad['D'][key]=10**12
        with pytest.raises(ValueError,match='TIME_STOP'):validate_config(bad)
    bad=copy.deepcopy(config);bad['D']['max_evaluations']=None
    with pytest.raises(ValueError):validate_config(bad)


def test_legacy_sources_unchanged():
    baseline=read(ROOT/'docs/research/termination_rules_20261116_v1/BASELINE.json')
    files=baseline['files']
    for name in ('src/kmd_toc/baseline_a/rule_v1.py','src/kmd_toc/dwt/methods.py','src/kmd_toc/comparison_v1/execution.py','README.md'):
        expected=files[name]
        # The user explicitly authorized the 2026-11-17 D/W README revision.
        # Preserve this historical checksum against the original document,
        # while the actual algorithm sources must still match in place.
        path=(ROOT/'docs/audits/dw_policy_20261117_v1/before/README.md'
              if name=='README.md' else ROOT/name)
        assert digest(path)==(expected['sha256'] if isinstance(expected,dict) else expected)


def test_routing_no_feasible_solution_is_finite(config,monkeypatch):
    from ortools.constraint_solver import pywrapcp
    from kmd_toc.termination_v1.solvers import routing_pool
    original=pywrapcp.RoutingModel.AddDimensionWithVehicleCapacity
    def infeasible(self,callback,slack,capacities,fix,name):
        return original(self,callback,slack,[0]*len(capacities),fix,name)
    monkeypatch.setattr(pywrapcp.RoutingModel,'AddDimensionWithVehicleCapacity',infeasible)
    ledger=Ledger();routes,_=routing_pool(artificial_problem(3,1,1),[],config,ledger,13)
    assert routes==[]
    event=next(e for e in ledger.events if e['event']=='Routing_end')
    assert event['algorithm_termination'] in ('WORK_BUDGET_REACHED','SEARCH_EXHAUSTED')
    assert event['checks']<=256


def test_C_preserves_valid_seed_if_expanded_pool_solve_has_no_plan(config,monkeypatch):
    import kmd_toc.termination_v1.methods as methods
    import kmd_toc.termination_v1.solvers as solvers
    from kmd_toc.comparison_v1.execution import physical_checks
    p=artificial_problem(6,2,1)
    def expanded(p,initial,*args):
        r=initial[0]
        return sorted(set(initial+[tuple(reversed(r)),r[1:]+r[:1],r[2:]+r[:2],r[3:]+r[:3]])),{}
    def no_plan(*args,**kwargs):raise ValueError('CP_COMPLETION_UNKNOWN')
    monkeypatch.setattr(methods,'routing_pool',expanded)
    monkeypatch.setattr(solvers,'solve_completion',no_plan)
    result=methods.generate(p,'C',config,Ledger(),{'solver_seed':13,'quantum_seed':None})
    assert result.method_settings['completion_selected_source']=='verified_incumbent'
    assert physical_checks(p,result,'C')[0]
