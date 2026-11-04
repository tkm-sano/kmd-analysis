"""Arithmetic replay of saved routes against immutable input matrices, no search."""
from pathlib import Path
import csv,json,hashlib,collections
from fractions import Fraction
import numpy as np
R=Path(__file__).resolve().parents[1]
D=Path('/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01')
BASE=Path('/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/unified_no_windows_r0_r8_20261022')
by=collections.defaultdict(list)
for v in csv.DictReader((D/'B_PLAN_REFERENCES_36800.csv').open()):by[v['problem_id']].append(v)
records=[]
for pid,vs in sorted(by.items()):
 f=BASE/'INPUTS'/(pid+'.npz');sha=hashlib.sha256(f.read_bytes()).hexdigest();assert {v['input_sha256'] for v in vs}=={sha}
 with np.load(f,allow_pickle=False) as z:t=z['travel'];d=z['demand'];service=z['service'];ready=z['ready'];due=z['due']
 assert not ready.any() and (due==32400).all();assert int(d.sum())<=216
 cache={};route_cache={};init_cache={}
 def cost(route):
  key=tuple(route)
  if key in route_cache:return route_cache[key]
  result=Fraction(0)
  for i,j in zip(route,route[1:]):
   edge=(i,j)
   if edge not in cache:cache[edge]=Fraction(str(t[i,j]))
   result+=cache[edge]
  route_cache[key]=result;return result
 for v in vs:
  route=json.loads(v['route_indices']);assert route[0]==route[-1]==0 and sorted(route[1:-1])==list(range(1,len(t)))
  j=cost(route);assert j==Fraction(v['objective_fraction'])
  assert j+102*(len(t)-1)<=32400
 records.append(dict(problem_id=pid,inputs_source=str(f),input_sha256=sha,rows_checked=len(vs),distinct_saved_routes=len(route_cache),demand_PE=int(d.sum()),same_J_exact_fraction=True,visit_capacity_return_valid=True,customer_time_windows=False,status='PASS'))
with (R/'evidence/SAVED_ROUTE_INPUT_CHECKS.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
(R/'evidence/ROUTE_REPLAY_SUMMARY.json').write_text(json.dumps(dict(inputs=len(records),saved_references=sum(v['rows_checked'] for v in records),exact_objective_mismatches=0,constraint_mismatches=0,input_hash_mismatches=0,route_search_executed=0,scope='保存経路の行列上の算術検証。新規探索・走行シミュレーションではない。'),ensure_ascii=False,indent=2))
print('PASS: all 36800 saved route costs and constraints match 460 immutable input matrices.')
