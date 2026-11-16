from copy import deepcopy
import importlib.util
import itertools
import json
from pathlib import Path

import numpy as np
import pytest

from kmd_toc.baseline_a.sequence_validation import (
    ROOT, actual_order, amazon_score, digest, geographic_matrix, iter_json_object,
    metrics, nearest_projection, official_normalization, route_ids, run,
    select_routes, sequence_deviation, settings, time_matrix, validate_order,
)


def route():
    return {'station_code': 'TEST', 'date_YYYY_MM_DD': '2020-01-01', 'stops': {
        'ST': {'type': 'Station', 'lat': 35., 'lng': 139., 'zone_id': None},
        'AA': {'type': 'Dropoff', 'lat': 35.01, 'lng': 139., 'zone_id': 'X'},
        'BB': {'type': 'Dropoff', 'lat': 35.02, 'lng': 139., 'zone_id': 'X'},
        'CC': {'type': 'Dropoff', 'lat': 35.03, 'lng': 139., 'zone_id': 'Y'},
    }}


@pytest.mark.parametrize('chunk', [1, 2, 7, 10000])
def test_streaming_parser_across_boundaries(tmp_path, chunk):
    obj = {'route\\"A': {'nested': {'x': [1, 'escaped \\ and " text', None]}},
           'b': {'cost': 1.25}, 'number': -12.3e-10, 'empty': {}}
    p = tmp_path/'data.json'
    p.write_text(json.dumps(obj, indent=2)+'\n')
    assert dict(iter_json_object(p, chunk)) == obj


@pytest.mark.parametrize('raw', ['{"r": {"x": 1}', '{"r": 2,}', '{} trailing', '{"a": 1.2x}'])
def test_streaming_parser_rejects_truncation_and_garbage(tmp_path, raw):
    p = tmp_path/'data.json'
    p.write_text(raw)
    with pytest.raises(ValueError):
        list(iter_json_object(p, 2))


def test_score_matches_official_reference_all_small_permutations():
    source = ROOT/'docs/research/baseline_a_sequence_validation_20261114_v1/sources/OFFICIAL_SCORE.py'
    spec = importlib.util.spec_from_file_location('amazon_official_reference', source)
    official = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(official)
    ids = ['ST','AA','BB','CC']
    for seed in range(4):
        matrix = np.random.default_rng(seed).integers(1, 30, size=(4,4)).astype(float)
        if seed % 2 == 0:
            np.fill_diagonal(matrix, 0)
        costs = {a: {b: float(matrix[i,j]) for j,b in enumerate(ids)} for i,a in enumerate(ids)}
        normalized = official_normalization(matrix)
        for order in itertools.permutations(ids[1:]):
            candidate = [ids[0], *order]
            # The official normalizer shallow-copies, mutating nested dicts.
            expected = official.score([*ids,ids[0]], [*candidate,ids[0]], deepcopy(costs))
            assert amazon_score(ids,candidate,ids,normalized) == pytest.approx(expected,abs=1e-10)
        assert costs['ST']['AA'] == matrix[0,1]


def test_score_zero_does_not_imply_identical_order():
    ids = ['ST','AA','BB','CC']
    reversed_order = ['ST','CC','BB','AA']
    matrix = np.array([[0,1,2,3],[4,0,6,7],[8,9,0,11],[12,13,14,0]],dtype=float)
    m = metrics(ids,reversed_order,ids,matrix,route(),official_normalization(matrix))
    assert m['amazon_score'] == 0 and sequence_deviation(ids,reversed_order) == 0
    assert m['normalized_Kendall_inversions'] == 1
    assert m['directed_edge_agreement'] == 0


def test_actual_self_units_and_directionality():
    ids = route_ids(route())
    matrix = np.array([[0,1,2,3],[4,0,6,7],[8,9,0,11],[12,13,14,0]],dtype=float)
    m = metrics(ids,ids,ids,matrix,route(),official_normalization(matrix))
    assert m['amazon_score'] == 0 and m['directed_edge_agreement'] == 1
    assert m['matrix_travel_time_s_closed_route'] == 1+6+11+12
    assert m['matrix_travel_time_ratio_to_actual'] == 1
    assert m['zone_reentries'] == 0
    order = ['ST','AA','CC','BB']
    assert metrics(ids,order,ids,matrix,route(),official_normalization(matrix))['zone_reentries'] == 1


def test_nearest_projection_reuses_direction_and_id_ties():
    ids = ['ST','AA','BB','CC']
    matrix = np.array([[0,1,1,8],[99,0,9,1],[9,1,0,1],[9,1,1,0]],dtype=float)
    before = matrix.copy()
    assert nearest_projection(ids,matrix) == ['ST','AA','CC','BB']
    assert np.array_equal(matrix,before)
    distances = geographic_matrix(ids,route())
    assert distances[0,1] == pytest.approx(1111.9508,abs=.01)
    assert distances[0,1] == distances[1,0]


@pytest.mark.parametrize('order', [['ST','AA','AA','CC'],['AA','ST','BB','CC'],['ST','AA','BB'],['ST','AA','BB','ZZ']])
def test_invalid_coverage_is_rejected(order):
    with pytest.raises(ValueError,match='EXACTLY_ONCE'):
        validate_order(['ST','AA','BB','CC'],order)


def test_invalid_actual_and_missing_matrix_rejected():
    ids = ['ST','AA','BB','CC']
    with pytest.raises(ValueError,match='POSITIONS'):
        actual_order({'actual':dict(zip(ids,[0,1,1,3]))},ids)
    with pytest.raises(ValueError,match='MATRIX_IDS'):
        time_matrix(ids, {'ST':{}})
    raw = {a:{b:0. for b in ids} for a in ids}
    raw['AA']['CC'] = float('nan')
    with pytest.raises(ValueError,match='INVALID'):
        time_matrix(ids,raw)


def test_positive_self_stop_time_is_preserved():
    ids = ['ST','AA','BB']
    raw = {a:{b:float(i*3+j+1) for j,b in enumerate(ids)} for i,a in enumerate(ids)}
    matrix = time_matrix(ids,raw)
    assert matrix[0,0] == 1 and matrix[1,1] == 5 and matrix[2,2] == 9


def test_selection_only_uses_metadata_and_is_stable():
    metadata = {}
    for station in range(12):
        for day in range(3):
            for r in range(4):
                row = route()
                row.update(station_code=f'S{station}', date_YYYY_MM_DD=f'2020-01-{day+1:02}')
                metadata[f'RouteID_{station}_{day}_{r}'] = row
    selected, excluded = select_routes(metadata,settings())
    assert len(selected)==40 and not excluded
    assert select_routes(dict(reversed(list(metadata.items()))),settings())[0] == selected


def fixture_bundle(root, reverse_actual=False):
    root.mkdir()
    files = {}
    for split in ['pilot','eval']:
        rid = f'RouteID_{split}'
        row = route()
        ids = route_ids(row)
        matrix = np.array([[0,1,2,3],[4,0,6,7],[8,9,0,11],[12,13,14,0]],dtype=float)
        raw = {a:{b:float(matrix[i,j]) for j,b in enumerate(ids)} for i,a in enumerate(ids)}
        order = [ids[0], *reversed(ids[1:])] if reverse_actual else ids
        objects = {'routes':{rid:row},'times':{rid:raw},'actual':{rid:{'actual':{s:i for i,s in enumerate(order)}}}}
        for kind, obj in objects.items():
            p = root/f'{split}_{kind}.json'
            p.write_text(json.dumps(obj))
            files[p.name] = {'sha256':digest(p)}
    (root/'MANIFEST.json').write_text(json.dumps({'status':'COMPLETE','files':files,'kind':'synthetic_unit_test'}))


def test_pipeline_freezes_proposals_without_actual_order_leakage(tmp_path):
    fixture_bundle(tmp_path/'data1')
    fixture_bundle(tmp_path/'data2',True)
    first = run(tmp_path/'data1',tmp_path/'run1')
    second = run(tmp_path/'data2',tmp_path/'run2')
    assert digest(tmp_path/'run1/PROPOSED_SEQUENCES.json') == digest(tmp_path/'run2/PROPOSED_SEQUENCES.json')
    frozen = json.loads((tmp_path/'run1/PROPOSALS_FROZEN.json').read_text())
    assert not frozen['actual_order_parsed']
    assert first['eval']['failed_rows']==second['eval']['failed_rows']==0
    assert first['eval']['original_A2_distance_validation']=='NOT_TESTED'
    assert first['eval']['D_km'] is first['eval']['W_min'] is None
    with pytest.raises(FileExistsError):
        run(tmp_path/'data1',tmp_path/'run1')


def test_hash_failure_persisted(tmp_path):
    fixture_bundle(tmp_path/'data')
    (tmp_path/'data/eval_times.json').write_text('{}')
    with pytest.raises(ValueError,match='DATA_HASH'):
        run(tmp_path/'data',tmp_path/'run')
    failure = json.loads((tmp_path/'run/FAILURE.json').read_text())
    assert failure['status']=='FAILED' and 'DATA_HASH' in failure['message']


def test_failed_metrics_are_retained(tmp_path,monkeypatch):
    import kmd_toc.baseline_a.sequence_validation as module
    fixture_bundle(tmp_path/'data')
    def fail(*args):
        raise ValueError('deliberate audit failure')
    monkeypatch.setattr(module,'metrics',fail)
    summary = run(tmp_path/'data',tmp_path/'run')
    assert summary['eval']['failed_rows']==13
    assert summary['eval']['attempts_by_method']['NN_time']['failed']==1
    assert json.loads((tmp_path/'run/RUN_STATUS.json').read_text())['status']=='FAILED_ROWS'


def test_cli_returns_failure_for_rejected_metric_rows(monkeypatch):
    import os
    import sys
    import kmd_toc.baseline_a.sequence_validation as module
    source = ROOT/'scripts/validate_a_sequences.py'
    spec = importlib.util.spec_from_file_location('sequence_cli_test',source)
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    monkeypatch.setattr(sys,'argv',['validate_a_sequences.py','--data','unused','--output','unused'])
    monkeypatch.setattr(os,'sched_setaffinity',lambda *args:None)
    for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
        monkeypatch.setenv(key,os.environ.get(key,'1'))
    monkeypatch.setattr(module,'run',lambda *args:{'pilot':{'failed_rows':0},'eval':{'failed_rows':1}})
    assert cli.main() == 1
