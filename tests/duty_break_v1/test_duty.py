from dataclasses import replace
import copy
import json

import numpy as np
import pytest

from kmd_toc.baseline_a.fixtures import artificial_problem
from kmd_toc.common.od import OD
from kmd_toc.duty_break_v1.models import activate,RestOptions,save_plan,load_plan
from kmd_toc.duty_break_v1.policy import VERSION,load_policy
from kmd_toc.duty_break_v1.scheduler import schedule,replay
from kmd_toc.duty_break_v1.validation import validate,require_valid


def with_times(base,edges):
    a=np.zeros_like(base.od.duration_s)
    for (i,j),seconds in edges.items():a[i,j]=seconds
    od=OD(base.od.ids,base.od.distance_m,a,base.od.reachable,base.od.metadata)
    return replace(base,od=od,experiment=replace(base.experiment,data_hashes={'od':od.fingerprint})).validate()


def one_stop(outbound,back=0,*,assumed=True):
    base=with_times(artificial_problem(1,1,1),{(0,1):outbound,(1,0):back})
    return activate(base,version=VERSION,rest_options=RestOptions(allow_assumed_locations=assumed))


@pytest.fixture
def witness():
    # Actual route durations / break propagation make the second-trip loading
    # order reverse compared to the unbroken FCFS schedule. Synthetic only.
    base=with_times(artificial_problem(4,2,1),{(0,1):12960,(0,3):6300,(3,0):4920})
    p=activate(base,version=VERSION,rest_options=RestOptions(allow_assumed_locations=True))
    routes={('v0',1):('c0001',),('v0',2):('c0002',),('v1',1):('c0003',),('v1',2):('c0004',)}
    return p,routes,schedule(p,routes,'B')


def codes(p,plan):return {x['code'] for x in validate(p,plan)['violations']}


def test_vehicle_deadline_and_berth_hours_separated_ready_unchanged():
    base=artificial_problem(10,10,2);before=base.fingerprint
    p=activate(base,version=VERSION)
    assert all(v.return_deadline_s==68400 for v in p.vehicles)
    assert all(v.return_deadline_s==72000 for v in base.vehicles)
    assert all((b.opening_s,b.closing_s)==(28800,72000) for b in p.berths)
    assert [v.first_ready_s for v in p.vehicles]==[v.first_ready_s for v in base.vehicles]
    assert min(v.first_ready_s for v in p.vehicles)>=28800
    assert base.fingerprint==before and p.fingerprint!=before
    c=load_policy()
    assert c['pre_shift_tasks_s']==c['post_return_tasks_s']==c['preparation_s']==0
    assert c['duty_span_s']==39600 and c['nonbreak_window_s']==36000


def test_new_version_explicit_and_legacy_default_stays_unbroken():
    from kmd_toc.fcfs_v1.scheduler import schedule as old_schedule
    from kmd_toc.fcfs_v1.validation import require_fcfs
    base=artificial_problem(1,1,1);route={('v0',1):('c0001',)}
    old=old_schedule(base,route,'B');assert require_fcfs(base,old)['feasible']
    assert old.schema_version=='1.0' and not hasattr(old,'breaks')
    with pytest.raises(ValueError,match='EXPLICIT_DUTY_VERSION'):activate(base,version='old')
    p=activate(base,version=VERSION)
    with pytest.raises(ValueError,match='NO_LEGACY_FALLBACK'):old_schedule(p,route,'B')
    assert not validate(p,old)['model_feasible']


def test_early_final_return_depot_break_and_unused_vehicle_excluded():
    base=artificial_problem(2,2,1)
    p=activate(base,version=VERSION,rest_options=RestOptions(allow_assumed_locations=True))
    plan=schedule(p,{('v0',1):('c0001','c0002')},'C');r=require_valid(p,plan)
    assert len(plan.breaks)==1
    b=plan.breaks[0]
    assert (b.vehicle_id,b.trip_no,b.start_s,b.end_s,b.placement)==('v0',None,43200,46800,'after_final_return_by_noon')
    unused=next(x for x in r['vehicles'] if x['vehicle_id']=='v1')
    assert not unused['used'] and not unused['break_constraint_applicable'] and unused['break_s'] is None
    assert r['stopping_site_feasibility']=='HOLD_UNVERIFIED_LOCATIONS'


@pytest.mark.parametrize('return_extra,valid',[(0,True),(1,False)])
def test_depot_fallback_only_return_by_noon(return_extra,valid):
    p=one_stop(7200,3480+return_extra)
    if valid:
        plan=schedule(p,{('v0',1):('c0001',)},'B')
        assert plan.trips[0].return_s==43200 and plan.breaks[0].start_s==43200
    else:
        candidate=schedule(p,{('v0',1):('c0001',)},'B',validate=False)
        assert 'EXACTLY_ONE_BREAK_PER_ACTIVE_DRIVER' in codes(p,candidate)
        with pytest.raises(ValueError,match='EXACTLY_ONE_BREAK'):require_valid(p,candidate)


@pytest.mark.parametrize('outbound,start,placement',[(10800,43200,'before_delivery_service'),
                                                    (14400,46800,'before_delivery_service'),
                                                    (10740,43260,'after_delivery_service')])
def test_break_start_boundaries_and_service_not_relabelled_as_rest(outbound,start,placement):
    p=one_stop(outbound);plan=schedule(p,{('v0',1):('c0001',)},'B');b=plan.breaks[0]
    assert (b.start_s,b.end_s,b.placement)==(start,start+3600,placement)
    v=plan.trips[0].visits[0]
    assert v.service_end_s-v.service_start_s==120
    if placement=='before_delivery_service':assert v.service_start_s-v.arrival_s==3600
    assert b.end_s<=50400 and require_valid(p,plan)['model_feasible']


def test_no_eligible_stop_window_rejected_not_shifted_to_depot_after_noon():
    p=one_stop(14401)
    with pytest.raises(ValueError,match='EXACTLY_ONE_BREAK'):schedule(p,{('v0',1):('c0001',)},'B')


@pytest.mark.parametrize('extra,valid',[(0,True),(1,False)])
def test_final_return_at_1900_boundary(extra,valid):
    p=one_stop(10800,21480+extra)
    candidate=schedule(p,{('v0',1):('c0001',)},'B',validate=False)
    assert candidate.trips[0].return_s==68400+extra
    assert validate(p,candidate)['model_feasible']==valid
    if not valid:assert 'RETURN_AFTER_1900' in codes(p,candidate)
    assert p.berths[0].closing_s==72000


def test_first_trip_break_changes_return_second_ready_and_other_vehicle_queue(witness):
    from kmd_toc.fcfs_v1.scheduler import schedule as old_schedule
    p,routes,plan=witness
    old=old_schedule(p.base,routes,'B');old_by={(t.vehicle_id,t.trip_no):t for t in old.trips}
    new_by={(t.vehicle_id,t.trip_no):t for t in plan.trips}
    assert new_by['v0',1].return_s==old_by['v0',1].return_s+3600
    assert new_by['v0',2].ready_s==new_by['v0',1].return_s
    assert old_by['v0',2].load_start_s<old_by['v1',2].load_start_s
    assert new_by['v1',2].load_start_s<new_by['v0',2].load_start_s
    assert old_by['v1',2].waiting_s==1740 and new_by['v1',2].waiting_s==0
    check=require_valid(p,plan)
    assert check['W_total_loading_min']==0
    assert check['D_km']==pytest.approx(sum(t.distance_m for t in old.trips)/1000)


def test_independent_validator_does_not_use_production_scheduler(witness,monkeypatch):
    import kmd_toc.duty_break_v1.scheduler as s
    p,_,plan=witness
    def forbidden(*a,**kw):raise AssertionError('independent validator called scheduler')
    monkeypatch.setattr(s,'schedule',forbidden);monkeypatch.setattr(s,'project_trip',forbidden)
    assert require_valid(p,plan)['feasible']


@pytest.mark.parametrize('fault',['missing','duplicate','duration','window','during_loading','wrong_location','intertrip'])
def test_invalid_breaks_rejected(witness,fault):
    p,_,plan=witness;b=plan.breaks[0]
    if fault=='missing':changed=()
    elif fault=='duplicate':changed=(*plan.breaks,b)
    else:
        if fault=='duration':b=replace(b,end_s=b.end_s-1)
        elif fault=='window':b=replace(b,start_s=46801,end_s=50401)
        elif fault=='during_loading':
            t=next(t for t in plan.trips if t.vehicle_id==b.vehicle_id and t.trip_no==2)
            b=replace(b,start_s=t.load_start_s,end_s=t.load_start_s+3600)
        elif fault=='wrong_location':b=replace(b,location_id=p.depot.depot_id)
        elif fault=='intertrip':b=replace(b,trip_no=None,location_id=p.depot.depot_id,placement='between_trips')
        changed=(b,*plan.breaks[1:])
    assert not validate(p,replace(plan,breaks=changed))['model_feasible']


@pytest.mark.parametrize('field,value,code',[('load_start_s',28799,'START_BEFORE_0800'),
                                            ('waiting_s',3600,'W_DEFINITION'),
                                            ('load_end_s',40000,'LOAD_30_MIN'),
                                            ('departure_s',50000,'IMMEDIATE_DEPARTURE')])
def test_wrong_shift_loading_departure_W_rejected(witness,field,value,code):
    p,_,plan=witness;t=replace(plan.trips[0],**{field:value})
    assert code in codes(p,replace(plan,trips=(t,*plan.trips[1:])))


def test_unknown_locations_not_promoted_to_verified_and_strict_mode_rejects():
    p=one_stop(10800,assumed=False)
    with pytest.raises(ValueError,match='EXACTLY_ONE_BREAK'):schedule(p,{('v0',1):('c0001',)},'B')
    proof=RestOptions(confirmed_locations=(('c0001','synthetic test confirmation; not real parking evidence'),))
    q=activate(p.base,version=VERSION,rest_options=proof)
    candidate=schedule(q,{('v0',1):('c0001',)},'B')
    assert candidate.breaks[0].location_status=='caller_confirmed'
    assert 'NOT_A_SITE_AUDIT' in require_valid(q,candidate)['stopping_site_feasibility']
    assert p.fingerprint!=q.fingerprint


def test_unsupported_detour_point_requires_approved_OD_change():
    with pytest.raises(ValueError,match='DETOUR_REQUIRES'):
        activate(artificial_problem(1,1,1),version=VERSION,rest_options=RestOptions(confirmed_locations=(('new_rest_area','proof'),)))


def test_versioned_save_load_roundtrip_and_legacy_loader_refusal(witness,tmp_path):
    from kmd_toc.common.models import load_plan as legacy_load
    p,_,plan=witness;path=tmp_path/'new.json';save_plan(plan,path)
    loaded=load_plan(path);assert require_valid(p,loaded)['model_feasible']
    assert loaded==plan
    with pytest.raises(ValueError):legacy_load(path)
    with pytest.raises(FileExistsError):save_plan(plan,path)


def test_berth_overlap_is_rejected_and_identified_for_affected_driver(witness):
    p,_,plan=witness
    t=plan.trips[0];other=next(t for t in plan.trips if t.vehicle_id=='v1' and t.trip_no==1)
    changed=replace(other,load_start_s=t.load_start_s,load_end_s=t.load_end_s,departure_s=t.departure_s)
    bad=replace(plan,trips=tuple(changed if x is other else x for x in plan.trips))
    report=validate(p,bad)
    assert 'BERTH_OVERLAP' in {x['code'] for x in report['violations']}
    assert all(r['berth_or_FCFS_violation'] for r in report['vehicles'])


def test_multi_berth_reconstruction_and_unused_drivers():
    p=activate(artificial_problem(4,4,2),version=VERSION,rest_options=RestOptions(allow_assumed_locations=True))
    plan=schedule(p,{('v0',1):('c0001',),('v1',1):('c0002',),('v2',1):('c0003','c0004')},'B')
    report=require_valid(p,plan)
    assert len({t.berth_id for t in plan.trips})==2
    assert sum(r['used'] for r in report['vehicles'])==3
    assert len(plan.breaks)==3


def test_new_policy_tamper_rejected_without_editing_actual_config(tmp_path,monkeypatch):
    import kmd_toc.duty_break_v1.policy as policy
    path=tmp_path/'changed.json';data=json.loads(policy.CONFIG.read_text())
    data['berth_closing_s']=68400;path.write_text(json.dumps(data))
    monkeypatch.setattr(policy,'CONFIG',path)
    with pytest.raises(ValueError,match='HASH_CHANGED'):policy.load_policy()


@pytest.mark.parametrize('fault',['trip_boolean','break_trip_boolean','distance_boolean'])
def test_boolean_scalars_cannot_pass_integer_or_distance_constraints(witness,fault):
    p,_,plan=witness
    if fault=='break_trip_boolean':
        bad=replace(plan,breaks=(replace(plan.breaks[0],trip_no=True),*plan.breaks[1:]))
    else:
        t=replace(plan.trips[0],**({'trip_no':True} if fault=='trip_boolean' else {'distance_m':True}))
        bad=replace(plan,trips=(t,*plan.trips[1:]))
    assert not validate(p,bad)['model_feasible']


def test_confirmed_location_roundtrip_and_policy_mode_hash_separation(tmp_path):
    base=one_stop(10800).base
    p=activate(base,version=VERSION,rest_options=RestOptions(confirmed_locations=(('c0001','synthetic fixture attestation'),)))
    plan=schedule(p,{('v0',1):('c0001',)},'C');path=tmp_path/'confirmed.json';save_plan(plan,path)
    assert require_valid(p,load_plan(path))['model_feasible']
    q=activate(base,version=VERSION,rest_options=RestOptions(allow_assumed_locations=True))
    assert not validate(q,plan)['model_feasible']


@pytest.mark.parametrize('method',['B','C','D','Q'])
def test_all_method_aliases_use_same_constraints_and_operational_plan(witness,method):
    p,routes,reference=witness;other=schedule(p,routes,method)
    assert other.trips==reference.trips and other.breaks==reference.breaks
    assert require_valid(p,other)['D_km']==require_valid(p,reference)['D_km']
    assert require_valid(p,other)['W_total_loading_min']==0


def test_A_external_is_excluded(witness):
    p,routes,_=witness
    with pytest.raises(ValueError,match='A_IS_EXTERNAL'):schedule(p,routes,'A')


def test_existing_sources_conditions_results_seeds_unchanged():
    import hashlib
    from kmd_toc.common.config import ROOT
    before=json.loads((ROOT/'docs/research/duty_break_20261121_v1/PRESERVATION_BEFORE.json').read_text())['files']
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected for name,expected in before.items())
