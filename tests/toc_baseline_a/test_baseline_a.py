from collections import Counter
from dataclasses import replace
import ast
import hashlib
import json
from pathlib import Path
import pytest
from kmd_toc.baseline_a.config import CONFIG, SHA256, ROOT, load_settings, settings_block
from kmd_toc.baseline_a.construction import create_plan, _two_opt, _cost
from kmd_toc.baseline_a.fixtures import artificial_problem
from kmd_toc.baseline_a.human_time import estimate_workflow, human_time_sensitivity
from kmd_toc.baseline_a.independent import recompute
from kmd_toc.baseline_a.runner import summary, run_case, frozen_preflight
from kmd_toc.common.models import save_problem, save_plan, load_plan
from kmd_toc.common.validation import validate_plan


def codes(report):return {v['code'] for v in report.violations}


def rehash(p, od):
    return replace(p,od=od,experiment=replace(p.experiment,data_hashes={'od':od.fingerprint}))


def test_preregistered_settings_document_and_sources():
    cfg=load_settings();assert cfg['random_seed'] is None
    assert cfg['angle_offsets_deg']==[0,120,240]
    assert hashlib.sha256(CONFIG.read_bytes()).hexdigest()==SHA256
    doc=(ROOT/'docs/research/toc_delivery_a/A_RULE_BASELINE_SPEC.md').read_text()
    assert doc.split('<!-- BEGIN GENERATED A RULE SETTINGS -->\n')[1].split('\n<!-- END GENERATED A RULE SETTINGS -->')[0]==settings_block()
    reg=json.loads((ROOT/'output/toc_delivery/a_rule_v1_20261112/PREREGISTRATION.json').read_text())
    assert reg['BD_performance_results_used'] is False and reg['A_solver_execution_started'] is False
    for filename,h in reg['files'].items():assert hashlib.sha256((ROOT/filename).read_bytes()).hexdigest()==h
    assert cfg['human_time']['public_Japan_Post_minutes_context_only']['reference_stop_count'] is None
    assert cfg['human_time']['public_Japan_Post_minutes_context_only']['used_for_scaling'] is False


def test_settings_drift_rejected(tmp_path):
    cfg=load_settings();cfg['methods']['A3']['two_opt_passes']=9
    path=tmp_path/'settings.json';path.write_text(json.dumps(cfg))
    with pytest.raises(ValueError,match='A_RULE_SETTINGS_HASH'):load_settings(path)


@pytest.mark.parametrize('n,v,b',[(6,2,1),(20,3,1),(120,2,1),(240,3,1)])
@pytest.mark.parametrize('condition',['A1','A2','A3'])
@pytest.mark.parametrize('offset',[0,120,240])
def test_registered_conditions_independent_coverage_time_and_cost(n,v,b,condition,offset):
    p=artificial_problem(n,v,b);plan=create_plan(p,condition,offset);common=validate_plan(p,plan);other=recompute(p,plan)
    assert common.feasible,common.violations
    assert other['feasible'],other
    assert float(other['D_km'])==pytest.approx(common.D_km,abs=1e-8)
    assert float(other['W_min'])==pytest.approx(common.W_min,abs=1e-8)
    assert Counter(s.stop_id for t in plan.trips for s in t.visits)==Counter({s.stop_id:1 for s in p.stops})
    assert plan.method_id=='A' and plan.method_settings['Sagawa_actual'] is False
    assert plan.od_hash==p.od.fingerprint and plan.problem_hash==p.fingerprint


def test_assignment_and_order_both_change_and_are_input_derived():
    p=artificial_problem(20,3,1)
    a,b,c=(create_plan(p,x) for x in ['A1','A2','A3'])
    assignment=lambda q:{s.stop_id:t.vehicle_id for t in q.trips for s in t.visits}
    order=lambda q:[tuple(s.stop_id for s in t.visits) for t in q.trips]
    assert assignment(a)!=assignment(b)!=assignment(c)
    assert order(a)!=order(b)!=order(c)
    # These witnesses lie in one quadrant: registered angle rotations can coincide.
    # Change input geography instead of falsely demanding all parameter levels differ.
    shifted=replace(p,stops=tuple(replace(s,longitude=2*p.depot.longitude-s.longitude,
        snap=replace(s.snap,longitude=2*p.depot.longitude-s.longitude)) for s in p.stops))
    assert assignment(a)!=assignment(create_plan(shifted,'A1'))
    assert b.method_settings['balance_moves'] and c.method_settings['distance_relocations']
    assert all(m['distance_delta_m']<0 for m in c.method_settings['distance_relocations'])


def test_deterministic_and_io_roundtrip(tmp_path):
    p=artificial_problem(20,3,1)
    assert create_plan(p,'A3')==create_plan(p,'A3')
    q=create_plan(p,'A2');save_plan(q,tmp_path/'plan.json');loaded=load_plan(tmp_path/'plan.json')
    assert q==loaded and validate_plan(p,loaded).feasible
    with pytest.raises(ValueError,match='UNREGISTERED'):create_plan(p,'A4')
    with pytest.raises(ValueError,match='UNREGISTERED'):create_plan(p,'A1',5)


def test_directed_two_opt_recalculates_reversed_internal_arcs():
    p=artificial_problem(6,2,1);d=p.od.distance_m
    assert (d!=d.T).any()
    # Test every permutation: the accepted improvement must be on the complete directed route.
    import itertools
    for route in itertools.permutations([1,2,3,4]):
        result,moves=_two_opt(route,d,2,1e-6)
        assert sorted(result)==sorted(route)
        assert _cost(result,d)<=_cost(route,d)+1e-6
        assert all(m['distance_delta_m']<0 for m in moves)


def test_unused_vehicle_one_trip_and_two_trips():
    p=artificial_problem(1,3,1);q=create_plan(p)
    assert len(q.trips)==1 and validate_plan(p,q).feasible
    p=artificial_problem(120,1,1);q=create_plan(p)
    assert [t.trip_no for t in q.trips]==[1,2]
    assert q.trips[1].ready_s==q.trips[0].return_s
    assert q.trips[1].load_start_s>=q.trips[0].return_s
    assert validate_plan(p,q).feasible


def test_insufficient_capacity_is_not_repaired():
    p=artificial_problem(121,1,1)
    with pytest.raises(ValueError,match='TOTAL_CAPACITY'):create_plan(p)


def test_common_rejects_A_third_trip_and_duplicate_visits():
    p=artificial_problem(6,2,1);q=create_plan(p)
    t=q.trips[0];q=replace(q,trips=(*q.trips,replace(t,trip_no=2),replace(t,trip_no=3)))
    report=validate_plan(p,q)
    assert not report.feasible and report.D_km is None and report.W_min is None
    assert {'VISIT_EXACTLY_ONCE','MAX_TWO_CONTIGUOUS_TRIPS'}<=codes(report)


def test_berth_overlap_loading_wait_and_distance_rejected():
    p=artificial_problem(20,3,1);q=create_plan(p)
    first,second,*rest=q.trips
    bad=replace(q,trips=(first,replace(second,load_start_s=first.load_start_s,load_end_s=first.load_end_s),*rest))
    assert 'BERTH_OVERLAP' in codes(validate_plan(p,bad))
    bad=replace(q,trips=(replace(first,waiting_s=first.waiting_s+1),*q.trips[1:]))
    assert 'WAITING_DEFINITION' in codes(validate_plan(p,bad))
    bad=replace(q,trips=(replace(first,distance_m=first.distance_m+1),*q.trips[1:]))
    assert 'DISTANCE_FROM_COMMON_OD' in codes(validate_plan(p,bad))


def test_customer_service_and_return_deadline_failures_are_visible():
    p=artificial_problem(6,2,1)
    p=rehash(p,replace(p.od,duration_s=p.od.duration_s*1000))
    q=create_plan(p,'A3');r=validate_plan(p,q)
    assert not r.feasible and 'RETURN_DEADLINE_2000' in codes(r) and r.D_km is None
    p=artificial_problem(6,2,1);q=create_plan(p);t=q.trips[0]
    visit=replace(t.visits[0],service_end_s=t.visits[0].service_end_s-1)
    bad=replace(q,trips=(replace(t,visits=(visit,*t.visits[1:])),*q.trips[1:]))
    assert 'CUSTOMER_SERVICE_TIME' in codes(validate_plan(p,bad))


def test_human_parallel_elapsed_not_person_sum_and_overhead_not_program_time():
    two=estimate_workflow([3,5],'low',2,measured_io_validation_s=0.25)
    one=estimate_workflow([3,5],'low',1,measured_io_validation_s=0.25)
    assert two['serial_s']==376 and two['parallel_makespan_s']==120
    assert two['workflow_elapsed_s']==496 and two['person_seconds']==592
    assert two['T_human_estimate_s']==496.25
    assert one['workflow_elapsed_s']==one['person_seconds']==592
    assert two['human_measured'] is False and two['Sagawa_actual'] is False
    unknown=estimate_workflow([100]*10,'low',10)
    assert unknown['T_human_estimate_s'] is None and unknown['workflow_elapsed_s']>0
    assert len(human_time_sensitivity([100]*10))==9
    with pytest.raises(ValueError):estimate_workflow([-1,2],'low',2)


def test_failure_and_unrun_range_denominators_and_missing_not_zero():
    rows=[{'scenario_id':'S1','condition':'A1','status':'INPUT_HOLD','reason':'no OD','D_km':None,'W_min':None,'T_program_s':None}]
    a=summary(rows)[0]
    assert a['feasible_rate'] is None and a['D_km_min'] is None and a['attempted_plans']==0
    rows.append({'scenario_id':'S1','condition':'A2','status':'INFEASIBLE_PLAN','reason':'late','D_km':None,'W_min':None,'T_program_s':None})
    a=summary(rows)[0]
    assert a['attempted_plans']==1 and a['feasible_rate']==0


def test_run_measured_input_to_validation_and_human_separation(tmp_path):
    p=artificial_problem(6,2,1);save_problem(p,tmp_path/'input');(tmp_path/'runs').mkdir()
    rows,human=run_case(tmp_path/'input','ART_N6',tmp_path/'runs',expected_kind='synthetic_validation')
    assert len(rows)==9 and len(human)==81 and all(r['status']=='FEASIBLE' for r in rows)
    runtime=json.loads((tmp_path/'runs'/'ART_N6-A1-angle0.runtime.json').read_text())
    assert 'T_s' not in runtime and runtime['T_program_s']>=0
    assert runtime['timing_events'][0]['name']=='input_load_start'
    assert runtime['timing_events'][-1]['name']=='independent_validation_end'
    assert runtime['timing_events'][-1]['elapsed_s']==runtime['T_program_s']
    assert all(r['T_human_estimate_s']>0 and not r['human_measured'] for r in human)
    assert all(r['independent_match'] for r in rows)


def test_artificial_bundle_cannot_be_used_as_frozen_research(tmp_path):
    p=artificial_problem(6,2,1);save_problem(p,tmp_path/'input');(tmp_path/'runs').mkdir()
    rows,human=run_case(tmp_path/'input','S1',tmp_path/'runs',expected_kind='frozen_research',expected_scenario='S1')
    assert not human and all(r['status']=='INPUT_HOLD' and r['D_km'] is None for r in rows)


def test_frozen_A_hashes_and_capacity_without_generation():
    rows=frozen_preflight()
    assert [(r['total_demand'],r['total_two_trip_capacity'],r['minimum_trips']) for r in rows]==[(1000,1200,17),(2000,2400,34),(4000,4800,67)]
    assert all(r['consumer_method_id']=='A' and r['capacity_necessary_condition'] and not r['feasibility_proved'] for r in rows)


def test_no_solver_or_BD_result_dependency_in_constructor_and_oracle():
    base=ROOT/'src/kmd_toc/baseline_a'
    for filename in ['construction.py','independent.py','human_time.py']:
        text=(base/filename).read_text();tree=ast.parse(text)
        modules=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
        assert not any(m and any(s in m for s in ['ortools','verypy','vehicle_day','column_generation','search_improvement']) for m in modules)
        assert 'output/toc_delivery/d_' not in text
    assert 'construction' not in (base/'independent.py').read_text()
