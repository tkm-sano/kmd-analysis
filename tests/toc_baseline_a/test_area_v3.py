from collections import Counter
from copy import deepcopy
import json
import numpy as np
import pytest

from kmd_toc.baseline_a.area import local_xy, spatial_labels, ordered_nodes
from kmd_toc.baseline_a.area_study import candidates, choose, settings, split_metadata, fit_loss
from kmd_toc.baseline_a.sequence_validation import nearest_projection
from kmd_toc.baseline_a.area_program import create_plan, measured, load_model
from kmd_toc.baseline_a.fixtures import artificial_problem
from kmd_toc.baseline_a.program_validation import audit_plan
from kmd_toc.common.validation import validate_plan
from kmd_toc.baseline_a.construction import create_plan as legacy_plan


def test_spatial_partition_preserves_every_node_and_capacity():
    xy = np.array([[0.,0.],*[[(i%5)*10.,(i//5)*10.] for i in range(20)]])
    ids = ['depot',*[f's{i:03}' for i in range(20)]]
    forward = spatial_labels(range(1,21),xy,ids,6)
    backward = spatial_labels(list(reversed(range(1,21))),xy,ids,6)
    assert forward == backward
    assert set(forward) == set(range(1,21))
    assert max(Counter(forward.values()).values()) <= 6


def test_identical_coordinates_split_deterministically():
    xy = np.zeros((21,2))
    ids = ['depot',*[f's{i:03}' for i in range(20)]]
    labels = spatial_labels(range(1,21),xy,ids,6)
    assert set(labels) == set(range(1,21))
    assert max(Counter(labels.values()).values())<=6


def test_NN_exactly_matches_prior_component():
    ids = ['depot','AA','BB','CC','DD']
    costs = np.array([[0,1,1,7,8],[8,0,4,2,5],[6,3,0,1,3],[7,1,2,0,1],[2,3,5,6,0]],dtype=float)
    order,_ = ordered_nodes(range(1,5),costs,np.zeros((5,2)),ids,{'kind':'NN'})
    assert [ids[0],*[ids[j] for j in order]]==nearest_projection(ids,costs)


def test_finite_preference_permits_area_exit_and_reentry():
    ids = ['depot','AA','BB','CC']
    costs = np.array([[0,1,2,10],[9,0,1,9],[9,1,0,1],[1,9,1,0]],dtype=float)
    labels = {1:'A',2:'B',3:'A'}
    parameters = {'kind':'area','leaf_capacity':2,'stay_factor':3.}
    order,trace = ordered_nodes([1,2,3],costs,np.zeros((4,2)),ids,parameters,labels)
    assert order==[1,2,3]
    assert [step['area'] for step in trace['decisions']]==['A','B','A']
    assert not trace['decisions'][1]['same_area_preference']
    strict,_ = ordered_nodes([1,2,3],costs,np.zeros((4,2)),ids,{**parameters,'stay_factor':None},labels)
    assert strict==[1,3,2]


def test_auto_areas_do_not_use_supplied_operator_labels():
    ids = ['depot','AA','BB','CC']
    costs = np.array([[0,1,2,10],[9,0,1,9],[9,1,0,1],[1,9,1,0]],dtype=float)
    xy = np.array([[0,0],[1,0],[2,0],[10,0]],dtype=float)
    p = {'kind':'area','leaf_capacity':2,'stay_factor':3.}
    a,trace = ordered_nodes([1,2,3],costs,xy,ids,p)
    b,_ = ordered_nodes([3,2,1],costs,xy,ids,p)
    assert a==b and trace['automatic_areas']


def metadata(station,day):
    return {'station_code':station,'date_YYYY_MM_DD':day,'stops':{
        'ST':{'type':'Station','lat':35.,'lng':139.},
        'AA':{'type':'Dropoff','lat':35.01,'lng':139.01},
        'BB':{'type':'Dropoff','lat':35.02,'lng':139.02}}}


def test_split_excludes_prior_groups_and_pilot_stations_from_holdout():
    cfg = settings()
    rows = {}
    for station in range(16):
        for day in range(5):
            for route in range(2):
                rows[f'{station}-{day}-{route}']=metadata(str(station),str(day))
    prior = [f'{station}-0-0' for station in range(7)]
    pilot = [metadata('7','0')]
    split = split_metadata(rows,prior,cfg,pilot)
    cs,vs = set(split['calibration_stations']),set(split['validation_stations'])
    assert len(cs)==6 and len(vs)==6 and not cs & vs
    assert '7' not in vs
    assert not set(split['calibration']) & set(split['validation'])
    assert all(not (rows[r]['station_code'] in set(map(str,range(8))) and rows[r]['date_YYYY_MM_DD']=='0')
               for r in split['calibration']+split['validation'])
    assert split_metadata(dict(reversed(list(rows.items()))),prior,cfg,pilot)==split


def test_calibration_selection_can_retain_NN():
    cfg = settings();params = candidates(cfg)
    rows = [{'method':p['id'],'route_id':str(r),'station_code':'S','date':str(r),
             'status':'SCORED','fit_loss':0.1 if p['kind']=='NN' else 0.2}
            for p in params for r in range(2)]
    winner,area,scores = choose(rows,params)
    assert winner['kind']=='NN' and area['kind']=='area'
    assert len(scores)==10


def test_calibration_failure_is_not_selected_and_ties_prefer_simple():
    params = candidates(settings())
    rows = [{'method':p['id'],'route_id':'r','station_code':'S','date':'d','status':'SCORED','fit_loss':0.1} for p in params]
    assert choose(rows,params)[0]['kind']=='NN'
    rows[0]['status']='FAILED'
    winner,_,scores = choose(rows,params)
    assert winner['kind']=='area' and not scores['NN']['eligible']


def test_loss_and_local_coordinates_are_dimensionally_explicit():
    actual={'zone_reentries_per_dropoff':0.01}
    measured={'amazon_score':0.3,'zone_reentries_per_dropoff':0.04,'matrix_travel_time_ratio_to_actual':1.}
    assert fit_loss(measured,actual)==pytest.approx(.11)
    xy=local_xy([139.,139.],[35.,35.01],139.,35.)
    assert xy[0].tolist()==[0,0] and xy[1,1]==pytest.approx(1111.9508,abs=.01)


@pytest.mark.parametrize('factor',[0,.5,float('nan'),float('inf')])
def test_bad_preference_rejected(factor):
    with pytest.raises(ValueError,match='STAY_FACTOR'):
        ordered_nodes([1,2],np.ones((3,3)),np.zeros((3,2)),['depot','a','b'],
                      {'kind':'area','leaf_capacity':2,'stay_factor':factor})


def test_unreachable_is_rejected_without_repair():
    costs=np.ones((3,3));costs[1,2]=float('nan')
    with pytest.raises(ValueError,match='UNREACHABLE'):
        ordered_nodes([1,2],costs,np.zeros((3,2)),['depot','a','b'],{'kind':'NN'})


@pytest.mark.parametrize('kind',['NN','area'])
@pytest.mark.parametrize('n,v,b',[(6,2,1),(120,1,1),(240,3,1)])
def test_full_program_double_validation_and_assignment_preservation(kind,n,v,b):
    p=artificial_problem(n,v,b)
    model={'selected_parameters':{'kind':kind,'leaf_capacity':6,'stay_factor':1.5}}
    q=create_plan(p,model,'a'*64)
    old=legacy_plan(p,'A2',0)
    assert validate_plan(p,q).feasible
    assert audit_plan(p,q)['feasible']
    assert q.method_settings['final_assignment']==old.method_settings['final_assignment']
    if kind=='NN':
        assert q.trips==old.trips
    assert sum(len(t.visits) for t in q.trips)==n


def test_full_program_unused_vehicle_and_failure_no_repair():
    p=artificial_problem(1,3,1)
    m={'selected_parameters':{'kind':'area','leaf_capacity':6,'stay_factor':1.5}}
    q=create_plan(p,m,'a'*64)
    assert len(q.trips)==1 and audit_plan(p,q)['feasible']
    p=artificial_problem(121,1,1)
    with pytest.raises(ValueError,match='CAPACITY'):
        create_plan(p,m,'a'*64)


def test_measured_model_hash_failure_and_time_scope(tmp_path):
    p=tmp_path/'model.json';p.write_text('{}')
    with pytest.raises(ValueError,match='MODEL_HASH'):
        load_model(p,'0'*64)
    model={'selected_parameters':{'kind':'area','leaf_capacity':6,'stay_factor':1.5}}
    row,plan=measured(lambda:artificial_problem(),lambda:(model,'a'*64))
    assert row['status']=='VALIDATED' and row['physical_feasible']
    assert row['T_program_s']==row['timing_events'][-1]['elapsed_s']
    assert row['timing_events'][-1]['name']=='agreement_end'
    assert row['T_A_human_reference'] is None
    row,_=measured(lambda:artificial_problem(),lambda:(_ for _ in ()).throw(ValueError('MODEL_HASH')))
    assert row['status']=='INPUT_HOLD' and row['T_program_s'] is row['D_km'] is row['W_min'] is None


def test_measured_late_return_is_rejected():
    from dataclasses import replace
    p=artificial_problem()
    od=replace(p.od,duration_s=p.od.duration_s*1000)
    p=replace(p,od=od,experiment=replace(p.experiment,data_hashes={'od':od.fingerprint}))
    model={'selected_parameters':{'kind':'area','leaf_capacity':6,'stay_factor':1.5}}
    row,plan=measured(lambda:p,lambda:(model,'a'*64))
    assert row['status']=='REJECTED_PLAN' and plan is not None
    assert row['D_km'] is row['W_min'] is row['T_program_s'] is None


def test_execute_resolves_registered_root_and_exports_all_products(tmp_path,monkeypatch):
    from kmd_toc.baseline_a import area_program as module
    source=tmp_path/'model.json';source.write_text('{}')
    problem=artificial_problem()
    model={'selected_parameters':{'kind':'NN'}}
    monkeypatch.setattr(module,'load_model',lambda *_:model)
    monkeypatch.setattr(module,'input_settings',lambda:{'input_root':'frozen','scenarios':{'S1':{'files':{}}}})
    seen=[]
    def loader(directory,registration,case):
        seen.append((directory,case))
        return problem
    monkeypatch.setattr(module,'load_registered',loader)
    out=tmp_path/'out'
    row=module.execute('S1',source,'a'*64,out)
    assert seen==[(module.ROOT/'frozen'/'S1','S1')]
    assert row['status']=='VALIDATED'
    for name,sha in json.loads((out/'OUTPUT_HASHES.json').read_text()).items():
        assert module.digest(out/name)==sha
