from copy import deepcopy
from dataclasses import asdict, replace
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
import numpy as np
import pytest
from kmd_toc.common import (load_conditions, validate_plan, save_problem, load_problem,
                             save_plan, load_plan, run_measured)
from kmd_toc.common.config import CONFIG_PATH, ROOT, CONFIG_SHA256, ready_s, conditions_table
from kmd_toc.common.od import OD, LocalOSRM, generate_local_od, load_od
from kmd_toc.common.adapters import to_vehicle_day, from_vehicle_day, indexed_solver_input, from_frozen
from conftest import fixture_problem, fixture_plan, rehash_problem


def codes(report):
    return {v['code'] for v in report.violations}


def change_trip(plan,index=0,**changes):
    trips=list(plan.trips)
    trips[index]=replace(trips[index],**changes)
    return replace(plan,trips=tuple(trips))


def independent_objectives(p,plan):
    """Second implementation: arc incidence counts and vehicle ready equations."""
    arcs={}
    for trip in plan.trips:
        nodes=['depot']+[v.stop_id for v in trip.visits]+['depot']
        for i,j in zip(nodes,nodes[1:]):
            arcs[i,j]=arcs.get((i,j),0)+1
    distance=sum((Decimal(str(p.od.distance_m[p.od.ids.index(i),p.od.ids.index(j)]))*count
                  for (i,j),count in arcs.items()),Decimal(0))/1000
    wait=Decimal(0)
    for vehicle in p.vehicles:
        trips=sorted((t for t in plan.trips if t.vehicle_id==vehicle.vehicle_id),key=lambda t:t.trip_no)
        for k,trip in enumerate(trips):
            ready=vehicle.first_ready_s if k==0 else trips[k-1].return_s
            wait+=Decimal(trip.load_start_s-ready)/60
    return distance,wait


def test_adopted_config_and_doc_sync():
    c=load_conditions()
    assert c['operations']==dict(demand_per_stop=1,capacity_per_trip=60,max_trips_per_vehicle=2,
        service_s=120,loading_s=1800,preparation_s=0,opening_s=28800,closing_s=72000,first_ready_span_s=3600)
    assert c['conditions_version']=='AD-common-20261111-v1.1'
    old=json.loads((ROOT/'configs/toc_delivery/common_conditions_v1.json').read_text())
    assert old['operations']['preparation_s']==900
    assert {k:v for k,v in c['operations'].items() if k!='preparation_s'}=={
        k:v for k,v in old['operations'].items() if k!='preparation_s'}
    for section in ('scope','units','scenarios','timing_policy','road_policy','comparison'):
        assert c[section]==old[section]
    assert c['comparison']['epsilon_W_min'] is None and c['comparison']['epsilon_D_km'] is None
    doc=(ROOT/'docs/research/toc_delivery_common/COMMON_CONDITIONS_V1.md').read_text()
    assert doc.split('<!-- BEGIN GENERATED CONDITIONS -->\n')[1].split('\n<!-- END GENERATED CONDITIONS -->')[0]==conditions_table()
    assert hashlib.sha256(CONFIG_PATH.read_bytes()).hexdigest()==CONFIG_SHA256


def test_config_drift_rejected(tmp_path):
    c=load_conditions();c['operations']['capacity_per_trip']=61
    path=tmp_path/'changed.json';path.write_text(json.dumps(c))
    with pytest.raises(ValueError,match='CONDITIONS_HASH'):
        load_conditions(path)


def test_old_conditions_are_not_silently_relabelled(problem):
    with pytest.raises(ValueError,match='CONDITIONS_HASH'):
        load_conditions(ROOT/'configs/toc_delivery/common_conditions_v1.json')
    old=replace(problem,experiment=replace(problem.experiment,conditions_version='AD-common-20261111-v1.0'))
    with pytest.raises(ValueError,match='VERSION'):old.validate()
    old=replace(problem,berths=(replace(problem.berths[0],preparation_s=900),*problem.berths[1:]))
    with pytest.raises(ValueError,match='BERTH_CONDITIONS'):old.validate()


@pytest.mark.parametrize('count',[10,20,40])
def test_ready_equation(count):
    for v in range(count):
        expected=28800+(Decimal(3600)*(Decimal(v)+Decimal('0.5'))/count).__floor__()
        assert ready_s(v,count)==expected


@pytest.mark.parametrize('mutation,code',[
    (lambda p: replace(p,stops=(p.stops[0],p.stops[0],*p.stops[2:])), 'DUPLICATE'),
    (lambda p: replace(p,stops=(replace(p.stops[0],stop_id=''),*p.stops[1:])), 'MISSING'),
    (lambda p: replace(p,stops=p.stops[:-1]), 'OD_IDS'),
    (lambda p: replace(p,vehicles=()),'EMPTY'),
    (lambda p: replace(p,berths=()),'EMPTY'),
    (lambda p: replace(p,stops=(replace(p.stops[0],demand=2),*p.stops[1:])),'DEMAND'),
    (lambda p: replace(p,stops=(replace(p.stops[0],demand=True),*p.stops[1:])),'DEMAND'),
    (lambda p: replace(p,vehicles=(replace(p.vehicles[0],capacity=59),*p.vehicles[1:])),'VEHICLE'),
    (lambda p: replace(p,vehicles=(replace(p.vehicles[0],first_ready_s=28800),*p.vehicles[1:])),'VEHICLE'),
    (lambda p: replace(p,depot=replace(p.depot,entrance_verified=False)),'ENTRANCE'),
    (lambda p: replace(p,stops=(replace(p.stops[0],longitude=math.nan),*p.stops[1:])),'COORDINATE'),
    (lambda p: replace(p,stops=(replace(p.stops[0],snap=replace(p.stops[0].snap,reviewed=False)),*p.stops[1:])),'SNAP'),
    (lambda p: replace(p,stops=(replace(p.stops[0],snap=replace(p.stops[0].snap,distance_m=101)),*p.stops[1:])),'SNAP'),
    (lambda p: replace(p,stops=(replace(p.stops[0],source={}),*p.stops[1:])),'PROVENANCE'),
    (lambda p: replace(p,experiment=replace(p.experiment,conditions_sha256='0'*64)),'VERSION'),
])
def test_input_mutations(problem,mutation,code):
    with pytest.raises(ValueError,match=code):mutation(problem).validate()


def test_roundtrip_common_io_and_output(tmp_path,problem,plan):
    save_problem(problem,tmp_path/'input')
    loaded=load_problem(tmp_path/'input')
    assert isinstance(loaded.od.distance_m,np.memmap)
    assert not loaded.od.distance_m.flags.writeable
    assert loaded.fingerprint==problem.fingerprint
    save_plan(plan,tmp_path/'plan.json')
    actual=load_plan(tmp_path/'plan.json')
    assert actual==plan
    assert validate_plan(loaded,actual).feasible
    with pytest.raises(FileExistsError):save_problem(problem,tmp_path/'input')
    with pytest.raises(FileExistsError):save_plan(plan,tmp_path/'plan.json')


def test_bundle_hash_tamper_rejected(tmp_path,problem):
    save_problem(problem,tmp_path/'input')
    path=tmp_path/'input/od/distance_m.npy'
    a=np.load(path,allow_pickle=False);a[0,1]+=1;np.save(path,a)
    with pytest.raises(ValueError,match='OD_FILE_HASH'):load_problem(tmp_path/'input')


def test_json_duplicate_and_nonfinite_rejected(tmp_path,plan):
    p=tmp_path/'plan.json'
    for data in ['{"schema_version":"1.0","schema_version":"2"}', '{"distance_m":NaN}']:
        p.write_text(data)
        with pytest.raises(ValueError):load_plan(p)


def test_snap_displacement_cannot_be_hidden(problem):
    s=problem.stops[0]
    bad=replace(s,snap=replace(s.snap,longitude=s.snap.longitude+.01))
    with pytest.raises(ValueError,match='REPORTED_DISTANCE'):
        replace(problem,stops=(bad,*problem.stops[1:])).validate()


def test_od_shape_units_diagonal_missing_asymmetry(problem):
    assert problem.od.audit()['asymmetric_directed_cells']>0
    for od,match in [(replace(problem.od,distance_m=np.zeros((2,2))),'SHAPE'),
            (replace(problem.od,metadata={**problem.od.metadata,'units':{'distance':'km','duration':'s'}}),'UNITS')]:
        with pytest.raises(ValueError,match=match):od.audit()
    d=problem.od.distance_m.copy();d[0,0]=1
    with pytest.raises(ValueError,match='DIAGONAL'):replace(problem.od,distance_m=d).audit()
    d[0,0]=0;d[0,1]=np.nan
    with pytest.raises(ValueError,match='MISSING'):replace(problem.od,distance_m=d).audit()


def test_od_unreachable_is_detected_and_never_estimated(problem):
    d=problem.od.distance_m.copy();t=problem.od.duration_s.copy();r=problem.od.reachable.copy()
    d[0,1]=t[0,1]=np.nan;r[0,1]=False
    od=replace(problem.od,distance_m=d,duration_s=t,reachable=r)
    assert od.audit(require_all_reachable=False)['unreachable_pairs']==1
    with pytest.raises(ValueError,match='UNREACHABLE'):od.audit()
    with pytest.raises(ValueError,match='UNREACHABLE'):od.leg('depot','c1')


@pytest.mark.parametrize('n',[4,5,6,20])
def test_small_and_medium_witness_and_independent_metrics(n):
    p=fixture_problem(n)
    if n==5:plan=fixture_plan(p)
    else:plan=fixture_plan(p,[('v0',tuple(s.stop_id for s in p.stops),90,'b0')])
    before=deepcopy(asdict(plan))
    report=validate_plan(p,plan)
    assert report.feasible,report.violations
    d,w=independent_objectives(p,plan)
    assert report.D_km==pytest.approx(float(d)) and report.W_min==pytest.approx(float(w))
    assert asdict(plan)==before


def test_hand_calculation_0_1_2_trips(problem,plan):
    r=validate_plan(problem,plan)
    assert r.feasible
    assert r.D_km==1.4 and r.W_min==3.5
    assert r.W1_min==1.5 and r.W2_min==2
    assert r.ready_to_loading_end_min==93.5
    assert [t.return_s for t in plan.trips]==[31716,34124,32721]
    assert len([t for t in plan.trips if t.vehicle_id=='v0'])==2
    assert len([t for t in plan.trips if t.vehicle_id=='v1'])==1
    assert not any(t.vehicle_id=='v2' for t in plan.trips)


@pytest.mark.parametrize('field,value,code',[
    ('origin_id','elsewhere','DEPOT_ROUND_TRIP'),('destination_id','elsewhere','DEPOT_ROUND_TRIP'),
    ('ready_s',28800,'READY_DEFINITION'),('load_end_s',31000,'LOADING_DURATION'),
    ('departure_s',30000,'DEPARTURE_AT_LOADING_END'),('return_s',72001,'RETURN_DEADLINE_2000'),
    ('distance_m',0.46,'DISTANCE_FROM_COMMON_OD'),('distance_m',math.nan,'DISTANCE_FROM_COMMON_OD'),
    ('waiting_s',1860,'WAITING_DEFINITION'),('berth_id','b999','UNKNOWN_BERTH'),
    ('departure_s',31260.0,'INTEGER_SECOND_TIMES'),('trip_no',3,'MAX_TWO_CONTIGUOUS_TRIPS'),
])
def test_output_mutations(problem,plan,field,value,code):
    changed=change_trip(plan,**{field:value})
    r=validate_plan(problem,changed)
    assert not r.feasible and code in codes(r)
    assert r.D_km is None and r.W_min is None
    assert getattr(changed.trips[0],field)==value or math.isnan(value)


def test_missing_repeated_unknown_visits_and_trip3(problem,plan):
    for trips,expected in [(plan.trips[:-1],'VISIT_EXACTLY_ONCE'),
                           ((*plan.trips,plan.trips[0]),'MAX_TWO_CONTIGUOUS_TRIPS')]:
        r=validate_plan(problem,replace(plan,trips=tuple(trips)))
        assert expected in codes(r)
    r=validate_plan(problem,change_trip(plan,visits=(replace(plan.trips[0].visits[0],stop_id='unknown'),)))
    assert 'UNKNOWN_STOP' in codes(r)


def test_capacity_60_and_61():
    for n,feasible in [(60,True),(61,False)]:
        p=fixture_problem(n)
        plan=fixture_plan(p,[('v0',tuple(s.stop_id for s in p.stops),0,'b0')])
        r=validate_plan(p,plan)
        assert r.feasible==feasible
        if not feasible:assert 'CAPACITY' in codes(r)


def test_second_trip_cannot_load_before_return(problem,plan):
    first=plan.trips[0]
    for start in [first.return_s-120,first.return_s-1]:
        r=validate_plan(problem,change_trip(plan,1,load_start_s=start,departure_s=start+1800,load_end_s=start+1800))
        assert 'READY_OR_SECOND_TRIP_PREPARATION' in codes(r)


@pytest.mark.parametrize('method,execution_kind',[
    ('B','classical'),('C','classical'),('D','quantum_circuit_simulator')])
def test_immediate_second_loading_and_waiting_shared_by_methods(problem,method,execution_kind):
    plan=fixture_plan(problem,[('v0',('c1','c2'),0,'b0'),('v0',('c3','c4','c5'),0,'b0')])
    plan=replace(plan,method_id=method,execution_kind=execution_kind)
    first,second=plan.trips
    assert second.ready_s==second.load_start_s==first.return_s
    assert second.load_end_s==second.departure_s==first.return_s+1800
    report=validate_plan(problem,plan)
    assert report.feasible and report.W_min==0
    assert report.ready_to_loading_end_min==60
    # Starting one second before the independently recomputed return is invalid.
    early=replace(shift_trip(second,-1),waiting_s=0)
    assert 'READY_OR_SECOND_TRIP_PREPARATION' in codes(validate_plan(problem,replace(plan,trips=(first,early))))
    # A scheduled 15-minute delay remains real waiting, not preparation.
    delayed=shift_trip(second,900)
    report=validate_plan(problem,replace(plan,trips=(first,delayed)))
    assert report.feasible and report.W_min==15
    assert float(independent_objectives(problem,replace(plan,trips=(first,delayed)))[1])==15
    forged=replace(delayed,ready_s=first.return_s+900,waiting_s=0)
    rejected=validate_plan(problem,replace(plan,trips=(first,forged)))
    assert 'READY_DEFINITION' in codes(rejected) and 'WAITING_DEFINITION' in codes(rejected)


def test_zero_preparation_still_requires_free_berth(problem):
    plan=fixture_plan(problem,[('v0',('c1','c2'),0,'b0'),('v0',('c3','c4'),0,'b0'),
                               ('v1',('c5',),0,'b0')])
    first,second,_=plan.trips
    assert second.load_start_s==first.return_s
    assert 'BERTH_OVERLAP' in codes(validate_plan(problem,plan))


def test_customer_service_and_travel(problem,plan):
    t=plan.trips[0];v=t.visits[0]
    for visit,code in [(replace(v,service_end_s=v.service_end_s-1),'CUSTOMER_SERVICE_TIME'),
                       (replace(v,arrival_s=v.arrival_s-1),'TRAVEL_TIME')]:
        r=validate_plan(problem,change_trip(plan,visits=(visit,*t.visits[1:])))
        assert code in codes(r)


def shift_trip(trip,delta):
    return replace(trip,load_start_s=trip.load_start_s+delta,load_end_s=trip.load_end_s+delta,
        departure_s=trip.departure_s+delta,return_s=trip.return_s+delta,waiting_s=trip.waiting_s+delta,
        visits=tuple(replace(v,arrival_s=v.arrival_s+delta,service_start_s=v.service_start_s+delta,
                             service_end_s=v.service_end_s+delta) for v in trip.visits))


def test_deadline_exact_and_one_second_late():
    p=fixture_problem(4)
    plan=fixture_plan(p,[('v0',tuple(s.stop_id for s in p.stops),0,'b0')])
    t=plan.trips[0]
    for deadline in [72000,72001]:
        altered=replace(plan,trips=(shift_trip(t,deadline-t.return_s),))
        r=validate_plan(p,altered)
        assert r.feasible==(deadline==72000)


def test_berth_overlap_count_half_open_and_availability(problem,plan):
    # Initial v0 and v1 loading overlap, valid on separate berths, invalid on b0.
    assert validate_plan(problem,plan).feasible
    assert 'BERTH_OVERLAP' in codes(validate_plan(problem,change_trip(plan,2,berth_id='b0')))
    p=fixture_problem(5,berths=1)
    adapted=replace(plan,problem_hash=p.fingerprint,od_hash=p.od.fingerprint,
                    trips=tuple(replace(t,berth_id='b0') for t in plan.trips))
    r=validate_plan(p,adapted)
    assert 'BERTH_COUNT_EXCEEDED' in codes(r)
    # End==start is accepted, while moving one second earlier creates overlap.
    t=plan.trips[2];delta=plan.trips[0].load_end_s-t.load_start_s
    adjacent=replace(shift_trip(t,delta),berth_id='b0')
    later_second=shift_trip(plan.trips[1],adjacent.load_end_s-plan.trips[1].load_start_s)
    test=replace(plan,trips=(plan.trips[0],later_second,adjacent))
    assert validate_plan(problem,test).feasible
    assert 'BERTH_OVERLAP' in codes(validate_plan(problem,replace(test,trips=(*test.trips[:2],shift_trip(adjacent,-1)))))
    r=validate_plan(problem,change_trip(plan,load_start_s=28799,load_end_s=30599))
    assert 'BERTH_AVAILABILITY' in codes(r)


def test_hash_and_aoa_execution_labels(problem,plan):
    assert 'COMMON_INPUT_OR_OD_HASH' in codes(validate_plan(problem,replace(plan,od_hash='fake')))
    assert 'AOA_EXECUTION_KIND' in codes(validate_plan(problem,replace(plan,method_id='D')))
    assert validate_plan(problem,replace(plan,method_id='D',execution_kind='quantum_circuit_simulator')).feasible


def test_output_bad_scalar_type_rejected(problem,plan):
    assert 'PLAN_FIELD_TYPES' in codes(validate_plan(problem,change_trip(plan,vehicle_id=['v0'])))
    assert 'INTEGER_SECOND_TIMES' in codes(validate_plan(problem,change_trip(plan,waiting_s=True)))


def test_t_boundary_includes_load_method_all_stages_and_validation(problem,plan):
    class Clock:
        t=0
        def __call__(self):return self.t
    clock=Clock()
    stages=['initial_solution','transformation','optimization','tuning','sampling',
            'decoding','integer_selection','postprocessing']
    def load():
        clock.t+=2
        return problem
    def solve(p,mark):
        for stage in stages:clock.t+=1;mark(stage)
        return plan
    def check(p,pl):
        clock.t+=7
        return validate_plan(p,pl)
    r=run_measured(load,solve,clock=clock,validator=check)
    assert r['T_s']==17 and r['elapsed_wall_s']==17
    assert r['timing_events'][0]['name']=='input_load_start'
    assert r['timing_events'][-1]['name']=='independent_validation_end'
    assert set(stages)<={e['name'] for e in r['timing_events']}
    bad=run_measured(load,lambda p,m:replace(plan,trips=()),clock=clock)
    assert bad['status']=='INFEASIBLE_PLAN' and bad['T_s'] is None
    failed=run_measured(lambda: (_ for _ in ()).throw(ValueError('input missing')),solve,clock=clock)
    assert failed['status']=='INPUT_HOLD' and failed['D_km'] is None


def test_t_real_clock_reads_serialized_input(tmp_path,problem,plan):
    import time
    save_problem(problem,tmp_path/'input')
    before=time.perf_counter()
    result=run_measured(lambda:load_problem(tmp_path/'input'),lambda p,m:plan)
    outer=time.perf_counter()-before
    assert result['status']=='FEASIBLE' and 0<result['T_s']<=outer


def test_input_bridges_only_no_solver(problem):
    view=indexed_solver_input(problem)
    assert view['distance_m'] is problem.od.distance_m
    day=to_vehicle_day(problem)
    assert np.array_equal(day.base.distance,problem.od.distance_m/1000)
    assert day.delta_s==1 and all(v.capacity==60 for v in day.vehicles)
    assert day.travel_s[0][1]==66
    assert all(v.preparation_s==0 and v.loading_s==1800 for v in day.vehicles)
    assert day.service_s==(0,*(120 for _ in problem.stops))


def test_d_output_bridge_preserves_bad_distance_for_rejection(problem,plan):
    from kmd_toc.vehicle_day.model import DayColumn, TripSchedule
    day=to_vehicle_day(problem)
    columns=[];berths={}
    for v in problem.vehicles:
        trips=[]
        for t in plan.trips:
            if t.vehicle_id!=v.vehicle_id:continue
            ids=tuple(problem.od.ids.index(x.stop_id) for x in t.visits)
            trips.append(TripSchedule(t.trip_no,ids,len(ids),t.ready_s,t.load_start_s,t.load_end_s,
                t.departure_s,t.return_s,t.return_s-t.departure_s-120*len(ids),120*len(ids),
                load_conditions()['operations']['preparation_s'],t.distance_m/1000))
            berths[v.vehicle_id,t.trip_no]=t.berth_id
        columns.append(DayColumn(day.fingerprint,v.vehicle_id,28800,72000,tuple(trips)))
    exported=from_vehicle_day(problem,day,columns,berths,method_settings={'validation_only':True})
    assert validate_plan(problem,exported).feasible
    bad=replace(columns[0].trips[0],distance_km=123)
    columns[0]=replace(columns[0],trips=(bad,*columns[0].trips[1:]))
    altered=from_vehicle_day(problem,day,columns,berths,method_settings={})
    assert altered.trips[0].distance_m==123000
    assert 'DISTANCE_FROM_COMMON_OD' in codes(validate_plan(problem,altered))
    with pytest.raises(ValueError,match='EXPLICIT_BERTH'):
        from_vehicle_day(problem,day,columns,{},method_settings={})


def test_frozen_research_counts_cannot_be_weakened(problem):
    p=replace(problem,experiment=replace(problem.experiment,kind='frozen_research',scenario_id='S1'))
    with pytest.raises(ValueError,match='SCENARIO_COUNTS'):p.validate()


@pytest.mark.parametrize('url',['https://router.project-osrm.org','http://example.com',
                                'http://localhost:5000','http://127.0.0.1/redirect',
                                'http://user@127.0.0.1:5000'])
def test_public_osrm_is_rejected(url):
    with pytest.raises(ValueError,match='LOOPBACK'):LocalOSRM(url)


def road_metadata():
    return dict(kind='osm_osrm',units={'distance':'m','duration':'s'},source_url='https://example.test/osm',
        acquired_at='2026-11-11T00:00:00Z',osm_timestamp='2026-07-16T20:21:30Z',road_version='test-OSM',
        graph_id='synthetic-graph-v1',osrm_version='test-only',profile='test-only',profile_sha256='1'*64,
        raw_sha256='2'*64,graph_artifacts={'test.osrm':'3'*64},build_commands=['TEST STUB ONLY'],
        generated_at='2026-11-11T00:00:00Z',route_policy='fastest_same_route',
        fallback_speed_allowed=False,directed=True)


def stub_transport(problem, *, fallback=False, bad_null=False):
    def transport(url):
        parsed=urlsplit(url);q=parse_qs(parsed.query)
        assert q['annotations']==['distance,duration'] and 'fallback_speed' not in q
        points=[tuple(map(float,point.split(','))) for point in parsed.path.split('/')[-1].split(';')]
        sources=[int(i) for i in q['sources'][0].split(';')]
        destinations=[int(i) for i in q['destinations'][0].split(';')]
        indexes=[round((lon-139.7)/.0001) for lon,lat in points]
        def matrix(a):return [[float(a[indexes[i],indexes[j]]) for j in destinations] for i in sources]
        out=dict(code='Ok',sources=[{'location':points[i]} for i in sources],
            destinations=[{'location':points[j]} for j in destinations],
            distances=matrix(problem.od.distance_m),durations=matrix(problem.od.duration_s))
        if fallback:out['fallback_speed_cells']=[[0,0]]
        if bad_null:out['distances'][0][0]=None
        return out
    return transport


def test_osrm_block_pipeline_stub_and_hash(tmp_path,problem):
    snaps={s.stop_id:replace(s.snap,evidence='sha256:'+'4'*64) for s in problem.stops}
    snaps['depot']=replace(problem.depot.snap,evidence='sha256:'+'5'*64)
    client=LocalOSRM(transport=stub_transport(problem))
    od=generate_local_od(problem.od.ids,snaps,road_metadata(),tmp_path/'od',client=client,block_size=2)
    assert np.array_equal(od.distance_m,problem.od.distance_m)
    assert np.array_equal(od.duration_s,problem.od.duration_s)
    assert len(list((tmp_path/'od/responses').glob('*.gz')))==9
    assert json.loads((tmp_path/'od/manifest.json').read_text())['status']=='COMPLETE'


@pytest.mark.parametrize('fallback,bad_null',[(True,False),(False,True)])
def test_osrm_invalid_response_preserves_incomplete(tmp_path,problem,fallback,bad_null):
    snaps={
        **{s.stop_id:replace(s.snap,evidence='sha256:'+'4'*64) for s in problem.stops},
        'depot':replace(problem.depot.snap,evidence='sha256:'+'5'*64)}
    with pytest.raises(ValueError):
        generate_local_od(problem.od.ids,snaps,road_metadata(),tmp_path/'od',
                          client=LocalOSRM(transport=stub_transport(problem,fallback=fallback,bad_null=bad_null)))
    assert json.loads((tmp_path/'od/manifest.json').read_text())['status']=='INCOMPLETE'
    with pytest.raises(ValueError,match='INCOMPLETE'):load_od(tmp_path/'od')


def test_frozen_bundle_all_eight_hashes_and_consumers():
    from kmd_toc.frozen_demand import load_frozen_demand
    from kmd_toc.frozen_demand_pin import MANIFEST_SHA256
    inventory=json.loads((ROOT/'review_outputs/toc_demand_freeze_20261110/FILE_HASHES.json').read_text())
    bundle=ROOT/'03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1'
    assert len(list(bundle.iterdir()))==8
    for path in bundle.iterdir():
        assert hashlib.sha256(path.read_bytes()).hexdigest()==inventory[str(path.relative_to(ROOT))]['sha256']
    for scenario,n,v,b in [('S1',1000,10,2),('S2',2000,20,4),('S3',4000,40,8)]:
        values=[load_frozen_demand(scenario,method_id=m) for m in 'ABCD']
        assert len({a.csv_sha256 for a in values})==1
        assert (values[0].N,values[0].vehicles,values[0].berths)==(n,v,b)
        assert values[0].manifest_sha256==MANIFEST_SHA256


def test_frozen_bridge_rejects_missing_road_input(problem):
    with pytest.raises(ValueError,match='SNAP_ID_SET'):
        from_frozen('S1',depot=problem.depot,snaps={},od=problem.od,environment={'test':True})


def test_frozen_corruption_rejected_without_generating_demand(tmp_path):
    import shutil
    from kmd_toc.frozen_demand import load_frozen_demand, FrozenDemandError
    source=ROOT/'03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1'
    target=tmp_path/'frozen-copy'
    shutil.copytree(source,target)
    path=target/'S1.csv'
    path.write_bytes(path.read_bytes()+b'\n')
    with pytest.raises(FrozenDemandError):
        load_frozen_demand('S1',method_id='B',bundle_dir=target)
