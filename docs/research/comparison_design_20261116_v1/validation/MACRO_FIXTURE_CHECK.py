import sys,os,time
sys.path.insert(0,'/home/takuma/kmd-analysis/src')
from kmd_toc.baseline_a.fixtures import artificial_problem
from kmd_toc.dwt.budget import Budget
from kmd_toc.dwt.methods import generate
from kmd_toc.common.validation import validate_plan
from kmd_toc.comparison_v1.design import profile_config
p=artificial_problem(12,4,1)
b=Budget(15, .08)
r=generate(p,'D_CLASSICAL_REPLACEMENT',None,b,{'solver_seed':11,'quantum_seed':None},profile_config('lean'))
assert validate_plan(p,r).feasible
assert r.method_id=='B'
logs=[v for k,v in b.evidence.items() if k.startswith('D_CLASSICAL_')]
assert logs and all(x['shots']==0 and x['permutations']<=6 for x in logs)
print('replacement fixture validated',len(logs),time.perf_counter()-b.start)
