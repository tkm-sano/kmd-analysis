from dataclasses import replace
import itertools
import json
import hashlib
import inspect
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
import numpy as np
import pytest
from kmd_toc.baseline_a.fixtures import artificial_problem
from kmd_toc.baseline_a.independent import recompute
from kmd_toc.common.validation import validate_plan
from kmd_toc.common.models import Snap
from kmd_toc.pipeline.roads import FixedSnapOSRM,resumable_od
from kmd_toc.pipeline.classical import directed_cw
from kmd_toc.pipeline.completion import complete_routes
from kmd_toc.pipeline.hybrid import EventDayMaster,create_hybrid


def test_original_coordinates_hints_and_one_point_block():
    p=artificial_problem(1,1,1);snap=p.depot.snap;seen=[]
    def transport(url):
        seen.append(url)
        return {'code':'Ok','sources':[{'location':[snap.longitude,snap.latitude]}],
                'destinations':[{'location':[snap.longitude,snap.latitude]}],'distances':[[0]],'durations':[[0]]}
    client=FixedSnapOSRM({'x':(139.123456789,35.987654321)},transport=transport)
    a,b,r,_=client.table(('x',),('x',),{'x':snap})
    assert r.all() and a[0,0]==0
    assert '139.123456789,35.987654321;139.123456789,35.987654321' in seen[0]
    assert parse_qs(urlsplit(seen[0]).query)['sources']==['0']
    bad=replace(snap,longitude=snap.longitude+.01)
    with pytest.raises(ValueError,match='DRIFT'):client.table(('x',),('x',),{'x':bad})


def test_resumption_refuses_tampered_block_and_changed_context(tmp_path):
    p=artificial_problem(1,1,1);snaps={p.depot.depot_id:p.depot.snap,p.stops[0].stop_id:p.stops[0].snap}
    class Client:
        calls=0
        def table(self,src,dst,snaps):
            self.calls+=1;i=[p.od.ids.index(x) for x in src];j=[p.od.ids.index(x) for x in dst]
            d=p.od.distance_m[np.ix_(i,j)];t=p.od.duration_s[np.ix_(i,j)]
            return d,t,np.ones_like(d,dtype=bool),{'distances':d.tolist(),'durations':t.tolist()}
    client=Client()
    a=resumable_od(p.od.ids,snaps,p.od.metadata,tmp_path,block_size=1,client=client)
    assert client.calls==4
    b=resumable_od(p.od.ids,snaps,p.od.metadata,tmp_path,block_size=1,client=client)
    assert client.calls==4 and a.fingerprint==b.fingerprint
    with pytest.raises(ValueError,match='CONTEXT_CHANGED'):resumable_od(tuple(reversed(p.od.ids)),snaps,p.od.metadata,tmp_path,block_size=1,client=client)
    block=tmp_path/'blocks/0_1.json.gz';block.write_bytes(block.read_bytes()+b'x')
    with pytest.raises(ValueError,match='BLOCK_HASH'):resumable_od(p.od.ids,snaps,p.od.metadata,tmp_path,block_size=1,client=client)


@pytest.mark.parametrize('n,v,b',[(6,2,1),(20,3,1),(120,2,1)])
@pytest.mark.parametrize('primary',['D','W'])
def test_directed_cw_free_assignment_completion_and_independent_metrics(n,v,b,primary):
    p=artificial_problem(n,v,b);routes,info=directed_cw(p)
    assert sorted(i for r in routes for i in r)==list(range(1,n+1))
    assert all(len(r)<=60 for r in routes)
    plan=complete_routes(p,routes,'B',primary,seconds=5)
    c=validate_plan(p,plan);o=recompute(p,plan)
    assert c.feasible and o['feasible']
    assert c.D_km==pytest.approx(float(o['D_km'])) and c.W_min==pytest.approx(float(o['W_min']))
    for t in plan.trips:
        if t.trip_no==1:assert t.ready_s==next(v.first_ready_s for v in p.vehicles if v.vehicle_id==t.vehicle_id)
        else:assert t.ready_s==next(q.return_s for q in plan.trips if q.vehicle_id==t.vehicle_id and q.trip_no==1)
    assert info['symmetric_OD_substitution'] is False


@pytest.mark.parametrize('primary',['D','W'])
def test_exact_event_master_matches_original_grid_master_and_exhaustive_ip(primary):
    from kmd_toc.vehicle_day.fixtures import small_problem
    from kmd_toc.vehicle_day.generation import enumerate_days
    from kmd_toc.vehicle_day.master import solve_lp,solve_integer
    from kmd_toc.vehicle_day.model import ObjectiveProfile
    from kmd_toc.vehicle_day.validation import validate_plan as check
    p=small_problem(4,1);cols=[c for c in enumerate_days(p) if all(t.load_start_s in [0,120,840,960] for t in c.trips)];m=EventDayMaster(p,cols);ix=list(range(len(cols)))
    profile=ObjectiveProfile(primary);oldlp=solve_lp(p,cols,profile);oldip=solve_integer(p,cols,profile)
    lp=m.lp(ix,primary);ip=m.ip(ix,primary)
    assert lp['objective']==pytest.approx(oldlp['objective'])
    assert ip['objective']==pytest.approx(oldip['objective'])
    # Independent combinations of one day per physical vehicle, not MILP.
    candidates=[[None]+[c for c in cols if c.vehicle_id==v.vehicle_id] for v in p.vehicles]
    best=(float('inf'),float('inf'))
    for chosen in itertools.product(*candidates):
        q=[c for c in chosen if c is not None]
        if check(p,q)['valid']:
            first=sum(c.distance_km if primary=='D' else c.waiting_min for c in q)
            second=sum(c.waiting_min if primary=='D' else c.distance_km for c in q)
            best=min(best,(first,second))
    assert ip['objective']==pytest.approx(best[0])
    assert ip['secondary_objective']==pytest.approx(best[1])


def test_actual_aoa_candidates_have_finite_scope_and_no_global_claim():
    p=artificial_problem(6,2,1);plan=create_hybrid(p)
    assert validate_plan(p,plan).feasible and recompute(p,plan)['feasible']
    m=plan.method_settings
    assert m['quantum'] and m['qubits_max']<=16
    assert m['global_integer_gap'] is None and not m['quantum_advantage_claim']
    assert not m['completion_used_exact_domain_oracle_routes']
    obtained={tuple(route) for sample in m['quantum'] for route in sample['full_route_obtained']}
    assert m['quantum_new_full_routes']<=len(obtained)
    cfg=json.loads(Path('configs/toc_delivery/ad_pipeline_v1.json').read_text())
    assert len({s['iteration'] for s in m['quantum']})==cfg['D']['pricing_rounds']
    for sample in m['quantum']:
        observed=sample['result']['config']
        for key in ['p','max_evaluations','restarts','train_shots','final_shots']:assert observed[key]==cfg['D'][key]
        assert observed['solver_seed']==cfg['seed']+100*sample['iteration']+sample['route_index']


def test_registered_config_consistency_and_runtime_defaults():
    from kmd_toc.pipeline.classical import routing_pool
    path=Path('configs/toc_delivery/ad_pipeline_v1.json');cfg=json.loads(path.read_text())
    registration=json.loads(Path('output/toc_delivery/ad_pipeline_20261112/PREREGISTRATION.json').read_text())
    assert hashlib.sha256(path.read_bytes()).hexdigest()==registration['sha256']
    assert cfg['conditions_sha256']==hashlib.sha256(Path('configs/toc_delivery/common_conditions_v1_1.json').read_bytes()).hexdigest()
    assert cfg['A_config_sha256']==hashlib.sha256(Path('configs/toc_delivery/a_rule_baseline_v1.json').read_bytes()).hexdigest()
    assert inspect.signature(routing_pool).parameters['seconds'].default==cfg['C']['routing_seconds']
    assert inspect.signature(complete_routes).parameters['seconds'].default==cfg['C']['schedule_seconds']
    assert inspect.signature(complete_routes).parameters['seed'].default==cfg['seed']
    revised=Path('configs/toc_delivery/ad_pipeline_v2_route.json')
    if revised.exists():
        cfg2=json.loads(revised.read_text());reg2=json.loads(Path('output/toc_delivery/ad_pipeline_20261112_route_v2/PREREGISTRATION.json').read_text())
        assert hashlib.sha256(revised.read_bytes()).hexdigest()==reg2['sha256']
        for key in ['A_config_sha256','B','C','D','epsilon','seed','threads','conditions_sha256']:assert cfg2[key]==cfg[key]
        assert cfg2['osrm']['table_distance_used'] is False


def test_synthetic_cannot_masquerade_as_road_validation():
    p=artificial_problem(6,2,1)
    bad=replace(p,experiment=replace(p.experiment,kind='road_validation',scenario_id='ROAD_N6'))
    with pytest.raises(ValueError):bad.validate()


def test_hybrid_result_serialization_and_measured_boundary(tmp_path):
    from kmd_toc.common.models import save_problem
    from kmd_toc.pipeline.execution import execute
    p=artificial_problem(6,2,1);save_problem(p,tmp_path/'input')
    r=execute(tmp_path/'input','D',tmp_path/'result')
    saved=json.loads((tmp_path/'result/result.json').read_text())
    assert r['status']==saved['status']=='FEASIBLE'
    assert saved['T_program_s']>0 and saved['second_validation']['feasible']


def test_positive_reduced_cost_column_can_improve_integer_after_lp_closure():
    from kmd_toc.common.adapters import to_vehicle_day
    from kmd_toc.column_generation.models import Route
    from kmd_toc.vehicle_day.generation import make_day
    from kmd_toc.pipeline.hybrid import column_generation
    day=to_vehicle_day(artificial_problem(3,3,3),delta_s=1);cols=[];seed=[]
    for vi,v in enumerate(day.vehicles):
        for k in [1,2,3]:
            for subset in itertools.combinations([1,2,3],k):
                c=make_day(day,v.vehicle_id,(Route(subset),),(v.ready_s+(186 if k==3 else 120),))
                if k<=2:seed.append(len(cols))
                cols.append(c)
    result=column_generation(EventDayMaster(day,cols),seed,'W',None)
    assert result['finite_pool_lp_closed']
    assert result['LP']['objective']==pytest.approx(3.)
    assert result['IP_after_zero_face']['objective']==pytest.approx(4.)
    assert result['IP_all_declared_columns']['objective']==pytest.approx(3.1)
    assert result['IP']['objective']==pytest.approx(3.1)
