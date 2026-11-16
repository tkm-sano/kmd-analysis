"""Adapter checks on hand-auditable tours; no solver or public-data download."""
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('cook_transfer_cli',ROOT/'scripts/run_cook_transfer_study.py')
STUDY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(STUDY)


def tour(tmp_path, numbers, comment='Cost = 999_123'):
    p = tmp_path/'test.tour'
    p.write_text('NAME : test\nCOMMENT : '+comment+'\nTOUR_SECTION\n'+
                 '\n'.join(map(str,numbers))+'\n-1\nEOF\n')
    return p


def test_rotation_preserves_directed_order_and_separates_penalty(tmp_path):
    p = tour(tmp_path,[1,2,3])
    order,meta = STUDY.parse_tour(p,{'1':'B','2':'Depot','3':'A'},['Depot','A','B'])
    assert order == ['Depot','A','B']
    assert meta['penalty'] == 999
    assert meta['integer_travel_cost'] == 123


@pytest.mark.parametrize('numbers',[[1,1,3],[1,2],[1,2,3,3]])
def test_invalid_tour_membership_is_rejected(tmp_path,numbers):
    with pytest.raises(ValueError,match='INVALID_TOUR_PERMUTATION'):
        STUDY.parse_tour(tour(tmp_path,numbers),{'1':'D','2':'A','3':'B'},['D','A','B'])


def test_length_format_and_unmapped_id_are_checked(tmp_path):
    p = tour(tmp_path,[1,2,3],comment='Length = 78')
    order,meta = STUDY.parse_tour(p,{'1':'D','2':'A','3':'B'},['D','A','B'])
    assert order == ['D','A','B'] and meta['integer_travel_cost']==78
    with pytest.raises(KeyError):
        STUDY.parse_tour(p,{'1':'D','2':'A'},['D','A','B'])


def test_automatic_zones_do_not_read_original_zone_labels():
    route = {'stops':{'D':{'lng':0.,'lat':0.,'type':'Station','zone_id':None},
        **{str(i):{'lng':i/1000,'lat':i%2/1000,'type':'Dropoff','zone_id':'OBSERVED-'+str(i)} for i in range(8)}}}
    changed = json.loads(json.dumps(route))
    for stop in changed['stops'].values():
        if stop['type']=='Dropoff':
            stop['zone_id']='COMPLETELY_DIFFERENT'
    a = STUDY.auto_zones(route,2)
    b = STUDY.auto_zones(changed,2)
    assert a==b
    assert len({s['zone_id'] for s in a['stops'].values() if s['type']=='Dropoff'})==4
    assert route['stops']['0']['zone_id']=='OBSERVED-0'


def test_extraction_rejects_absent_route(tmp_path):
    p = tmp_path/'input.json'
    p.write_text('{"route1": {"actual": {"A": 0}}}')
    assert STUDY.extract(p,['route1'])=={'route1':{'actual':{'A':0}}}
    with pytest.raises(ValueError,match='MISSING_EXTRACTED_ROUTE'):
        STUDY.extract(p,['missing'])


def test_station_missing_zone_is_json_safe_without_changing_dropoff_label():
    route = {'stops':{'D':{'type':'Station','zone_id':float('nan')},
                      'A':{'type':'Dropoff','zone_id':'A-01.1A'}}}
    fixed = STUDY.canonical_route(route)
    assert fixed['stops']['D']['zone_id'] is None
    assert fixed['stops']['A']['zone_id']=='A-01.1A'
    json.dumps(fixed,allow_nan=False)


def test_reference_scorer_receives_closed_directed_tours_and_isolated_costs():
    original = {'D':{'A':1.}}
    class Official:
        def score(self,actual,candidate,costs):
            assert actual==['D','A','B','D']
            assert candidate==['D','B','A','D']
            costs['D']['A']=999
            return .123
    assert STUDY.official_reference_score(Official(),['D','A','B'],['D','B','A'],original)==.123
    assert original['D']['A']==1.


def test_cli_preserves_virtualenv_interpreter_symlink(tmp_path,monkeypatch):
    link = tmp_path/'venv-python'
    link.symlink_to(sys.executable)
    observed = []
    monkeypatch.setattr(STUDY,'run',lambda *args:observed.append(args[-1]))
    monkeypatch.setattr(sys,'argv',['study','run','--data',str(tmp_path),'--plan',str(tmp_path),
        '--output',str(tmp_path/'new'),'--code',str(tmp_path),'--author-python',str(link)])
    STUDY.main()
    assert observed==[link.absolute()]
    assert observed[0].is_symlink()


def test_end_to_end_score_export_uses_plain_json_booleans(tmp_path):
    data=tmp_path/'data';data.mkdir()
    out=tmp_path/'out';out.mkdir()
    splits={'same_station_future':['r1'],'unknown_station':['r2']}
    stops={'D':{'type':'Station','lat':0.,'lng':0.,'zone_id':None},
           'A':{'type':'Dropoff','lat':0.,'lng':.01,'zone_id':'A-01.1A'},
           'B':{'type':'Dropoff','lat':0.,'lng':.02,'zone_id':'A-02.1A'}}
    routes={r:{'station_code':r,'date_YYYY_MM_DD':'2018-09-01','stops':stops} for r in ['r1','r2']}
    matrix={'D':{'D':0.,'A':1.,'B':3.},'A':{'D':4.,'A':0.,'B':2.},'B':{'D':5.,'A':6.,'B':0.}}
    times={r:matrix for r in routes}
    proposals={'Cook_public_zones':{r:['D','B','A'] for r in routes},
               'NN_time':{r:['D','A','B'] for r in routes}}
    (data/'eval_actual.json').write_text(json.dumps({r:{'actual':{'D':0,'A':1,'B':2}} for r in routes}))
    STUDY.score_saved_proposals(data,out,{'variants':['Cook_public_zones']},splits,routes,times,proposals,{},[])
    parity=json.loads((out/'OFFICIAL_SCORER_PARITY.json').read_text())
    assert parity['all_passed'] is True
    assert len(parity['checks'])==6
    assert all(type(c['passed']) is bool for c in parity['checks'])
    assert json.loads((out/'SUMMARY.json').read_text())['all_order_checks_passed'] is True
