import time,json,platform,resource,inspect,importlib.metadata,itertools
from pathlib import Path
import numpy as np
from pyvrp import Model,ProblemData,Client,Depot,VehicleType,Route,Solution,solve
from pyvrp.stop import MaxRuntime
B=Path(__file__).parent
# Independent exhaustive contract check: asymmetric objective=road seconds,
# duration=road+service; capacity and hard return horizon separate.
t=np.array([[0,10,70,80],[50,0,15,60],[70,55,0,20],[25,90,65,0]],dtype=np.int64)
def make(h=32400,q=216,k=1):
 return ProblemData(clients=[Client(i,i,delivery=[1],service_duration=102) for i in range(1,4)],depots=[Depot(0,0)],vehicle_types=[VehicleType(num_available=k,capacity=[q],tw_early=0,tw_late=h,shift_duration=h,start_late=0,unit_distance_cost=1,unit_duration_cost=0,max_overtime=0)],distance_matrices=[t],duration_matrices=[t])
checks=[]
for p in itertools.permutations([1,2,3]):
 d=make();r=Route(d,list(p),0);seq=[0,*p,0];road=sum(int(t[i,j]) for i,j in zip(seq,seq[1:]));s=Solution(d,[r])
 assert r.distance()==road and r.duration()==road+306 and s.is_feasible()
 checks.append(dict(order=p,road_s=road,duration_s=r.duration()))
assert not Solution(make(h=300),[Route(make(h=300),[1,2,3],0)]).is_feasible()
assert not Solution(make(q=2),[Route(make(q=2),[1,2,3],0)]).is_feasible()
d=make()
try:
 Solution(d,[Route(d,[1],0),Route(d,[2,3],0)])
except RuntimeError:
 pass
else:
 raise AssertionError('vehicle count must be rejected')
assert not Solution(d,[Route(d,[1,2],0)]).is_feasible()
(B/'contract.json').write_text(json.dumps({'version':importlib.metadata.version('pyvrp'),'permutations':checks,'hard_return_reject':True,'capacity_reject':True,'vehicle_limit_reject':True,'missing_required_client_reject':True,'objective_mapping':'distance matrix stores road seconds; duration matrix stores road seconds; unit_distance_cost=1; unit_duration_cost=0; actual meters recomputed externally'},indent=2))
import sys
if '--contract-only' in sys.argv: sys.exit(0)
# Synthetic engineering probes only: generated OD has no Ota interpretation.
rows=[]
for k,n in [(1,100),(5,500),(10,1000),(20,2000),(30,3000)]:
 start=time.perf_counter();rng=np.random.default_rng(20261105);xy=rng.uniform(0,10000,(n+1,2));dist=np.rint(np.linalg.norm(xy[:,None]-xy[None,:],axis=2)).astype(np.int64);tt=np.ceil(dist/8).astype(np.int64);tt+=np.arange(n+1)[:,None]%7;np.fill_diagonal(tt,0)
 d=ProblemData(clients=[Client(float(x),float(y),delivery=[1],service_duration=102) for x,y in xy[1:]],depots=[Depot(*xy[0])],vehicle_types=[VehicleType(num_available=k,capacity=[216],tw_early=0,tw_late=32400,start_late=0,shift_duration=32400,unit_distance_cost=1,unit_duration_cost=0)],distance_matrices=[tt],duration_matrices=[tt]);build=time.perf_counter()-start
 # Known feasible seed partition: only a feasibility witness, not a solver warm start.
 routes=[Route(d,list(range(a+1,min(a+100,n)+1)),0) for a in range(0,n,100)];witness=Solution(d,routes);witness_ok=witness.is_feasible()
 ss=time.perf_counter();res=solve(d,stop=MaxRuntime(5),seed=0,display=False);wall=time.perf_counter()-ss;best=res.best
 # Independent per-route audit.
 valid=True;visited=[];roads=0;meters=0;maxdur=0
 for r in best.routes():
  seq=[0,*r.visits(),0];visited.extend(r.visits());road=sum(int(tt[i,j]) for i,j in zip(seq,seq[1:]));duration=road+102*len(r.visits());roads+=road;meters+=sum(int(dist[i,j]) for i,j in zip(seq,seq[1:]));maxdur=max(maxdur,duration);valid &= len(r.visits())<=216 and duration<=32400
 valid &= len(best.routes())<=k and sorted(visited)==list(range(1,n+1))
 row=dict(k=k,n=n,synthetic=True,seed=0,solver_budget_s=5,build_s=build,solver_wall_s=wall,end_to_end_s=time.perf_counter()-start,solver_feasible=best.is_feasible(),independent_feasible=bool(valid),feasible_witness=bool(witness_ok),road_s=roads,meters=meters,max_route_s=maxdur,routes=len(best.routes()),peak_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
 rows.append(row);print(json.dumps(row),flush=True);(B/'scale_probe.json').write_text(json.dumps(rows,indent=2))
(B/'environment.json').write_text(json.dumps(dict(python=platform.python_version(),platform=platform.platform(),processor=platform.processor(),packages={x:importlib.metadata.version(x) for x in ['pyvrp','numpy','vrplib']}),indent=2))
