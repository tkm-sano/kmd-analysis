"""Post hoc metric diagnostic; reversed truth is NOT a planning candidate."""
import copy
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from kmd_toc.baseline_a.sequence_validation import (
    actual_order,metrics,official_normalization,route_ids,time_matrix)

plan=ROOT/'output/toc_delivery/a_cook_transfer_20261115_plan04'
reg=json.loads((plan/'REGISTRATION.json').read_text())
routes=json.loads((plan/'routes.json').read_text())
times=json.loads((plan/'selected_times.json').read_text())
truth=json.loads(Path('/home/takuma/.cache/kmd-analysis/external/amazon_sequence_validation_20261114_v1/eval_actual.json').read_text())
path=ROOT/'docs/research/baseline_a_sequence_validation_20261114_v1/sources/OFFICIAL_SCORE.py'
spec=importlib.util.spec_from_file_location('official',path)
official=importlib.util.module_from_spec(spec);spec.loader.exec_module(official)
rows=[]
for rid in reg['split_ids']['same_station_future']+reg['split_ids']['unknown_station']:
    ids=route_ids(routes[rid]);actual=actual_order(truth[rid],ids)
    reversed_truth=[actual[0],*reversed(actual[1:])]
    matrix=time_matrix(ids,times[rid])
    result=metrics(ids,reversed_truth,actual,matrix,routes[rid],official_normalization(matrix))
    reference=float(official.score([*actual,actual[0]],[*reversed_truth,actual[0]],copy.deepcopy(times[rid])))
    assert reference==result['amazon_score']==0.
    assert result['normalized_Kendall_inversions']==1.
    rows.append({'route_id':rid,'official_score':reference,
                 'normalized_Kendall_inversions':result['normalized_Kendall_inversions'],
                 'directed_edge_agreement':result['directed_edge_agreement']})
output=Path(__file__).parent/'BENCHMARK_LIMITATION_DIAGNOSTIC.json'
with output.open('x') as f:
    json.dump({'post_hoc':True,'planning_candidate':False,
        'reason':'same-station aggregate score and Kendall inversion pointed in different directions',
        'diagnostic':'reverse every actual dropoff while keeping station first; uses truth solely to examine a metric',
        'explanation':'each adjacent actual-rank difference remains 1, hence sequence deviation and official product score are 0 even with Kendall inversion 1',
        'rows':rows,'zero_score_is_not_order_equivalence':True},f,ensure_ascii=False,indent=2)
    f.write('\n')
print('reverse-order diagnostic verified on',len(rows),'routes')
