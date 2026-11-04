from decimal import getcontext
getcontext().prec = 80
"""Deterministic fixed-roster routing; HiGHS exact candidate and certified relaxation."""
from pathlib import Path
import time,itertools,math
from decimal import Decimal
import numpy as np
import highspy

def load(path):
 z=np.load(path,allow_pickle=False);return {k:z[k] for k in z.files}
def replay(a,route):
 r=np.asarray(route,dtype=int);t=a['travel'];work=np.cumsum(t[r[:-1],r[1:]]+a['service'][r[:-1]])
 start=work+np.maximum.accumulate(np.maximum(0,a['ready'][r[1:]]-work))
 return bool(np.all(start<=a['due'][r[1:]])),float(t[r[:-1],r[1:]].sum()),start

def exact_cost(a,r):return sum((Decimal(str(a['travel'][i,j])) for i,j in zip(r,r[1:])),Decimal(0))

def heuristic(a,sweeps=3):
 n=len(a['nodes']);t=a['travel'];ready=a['ready'];due=a['due']; routes=[];evaluated=0
 # Three deterministic constructors: earliest-due nearest, ready-class nearest,
 # and insertion by deadline. No relaxation or customer dropping.
 for mode in range(2):
  left=set(range(1,n));r=[0];clock=0.
  while left:
   if mode==0:
    key=min(due[j] for j in left);eligible=[j for j in left if due[j]==key]
   else:
    key=min(ready[j] for j in left);eligible=[j for j in left if ready[j]==key]
   j=min(eligible,key=lambda j:(t[r[-1],j],str(a['nodes'][j])))
   clock=max(clock+t[r[-1],j],ready[j])+102;r.append(j);left.remove(j)
  r.append(0)
  if replay(a,r)[0]:routes.append(r)
 r=[0,0]
 for j in sorted(range(1,n),key=lambda j:(due[j],ready[j],str(a['nodes'][j]))):
  choices=[]
  for k in range(1,len(r)):
   cand=r[:k]+[j]+r[k:];ok,cost,_=replay(a,cand);evaluated+=1
   if ok:choices.append((cost,tuple(cand),cand))
  if not choices:break
  r=min(choices)[2]
 if len(r)==n+1 and replay(a,r)[0]:routes.append(r)
 if not routes:return None,dict(evaluated=evaluated)
 r=min(routes,key=lambda r:(exact_cost(a,r),tuple(r)));cost=replay(a,r)[1]
 # First improving relocate and directed reversal, fixed exhaustive sweep order.
 for sweep in range(sweeps):
  changed=False
  for i in range(1,n):
   # Recompute route after each accepted move, no symmetric-distance assumption.
   for j in range(1,n):
    if i==j:continue
    node=r[i];base=r[:i]+r[i+1:];cand=base[:j]+[node]+base[j:]
    c=float(t[np.array(cand[:-1]),np.array(cand[1:])].sum())
    if c>cost+1e-9:continue
    if abs(c-cost)<=1e-9 and tuple(cand)>=tuple(r):continue
    evaluated+=1
    if replay(a,cand)[0]:
     ec,nc=exact_cost(a,r),exact_cost(a,cand)
     if nc<ec or (nc==ec and tuple(cand)<tuple(r)):
      r=cand;cost=c;changed=True
   # In asymmetric data reversal must reprice every reversed arc.
   for j in range(i+1,n):
    cand=r[:i]+list(reversed(r[i:j+1]))+r[j+1:];c=float(t[np.array(cand[:-1]),np.array(cand[1:])].sum())
    if c>cost+1e-9:continue
    if abs(c-cost)<=1e-9 and tuple(cand)>=tuple(r):continue
    evaluated+=1
    if replay(a,cand)[0]:
     ec,nc=exact_cost(a,r),exact_cost(a,cand)
     if nc<ec or (nc==ec and tuple(cand)<tuple(r)):
      r=cand;cost=c;changed=True
  if not changed:break
 assert sorted(r[1:-1])==list(range(1,n)) and replay(a,r)[0]
 return r,dict(evaluated=evaluated,sweeps=sweep+1)

def enumerate_exact(a):
 best=None;bestcost=None;feasible=0
 for p in itertools.permutations(range(1,len(a['nodes']))):
  r=[0,*p,0]
  clock=Decimal(0);ok=True
  for i,j in zip(r,r[1:]):
   clock=max(clock+Decimal(int(a['service'][i]))+Decimal(str(a['travel'][i,j])),Decimal(int(a['ready'][j])))
   if clock>Decimal(int(a['due'][j])):ok=False;break
  if ok:
   feasible+=1;c=exact_cost(a,r)
   if best is None or (c,tuple(r))<(bestcost,tuple(best)):best=r;bestcost=c
 return best,dict(feasible_permutations=feasible,total_permutations=math.factorial(len(a['nodes'])-1))

def addrow(h,coef,lo,up):
 assert h.addRow(lo,up,len(coef),np.array(list(coef),np.int32),np.array(list(coef.values()),float))==highspy.HighsStatus.kOk

def build(a,milp=False):
 n=len(a['nodes']);assert a['demand'].sum()<=216 and np.all(a['demand']<=216)
 h=highspy.Highs();h.setOptionValue('output_flag',False);h.setOptionValue('threads',1);h.setOptionValue('random_seed',0)
 arcs=[(i,j) for i in range(n) for j in range(n) if i!=j and Decimal(int(a['ready'][i]))+Decimal(int(a['service'][i]))+Decimal(str(a['travel'][i,j]))<=Decimal(int(a['due'][j]))];x={p:k for k,p in enumerate(arcs)};m=len(arcs)
 costs=np.array([a['travel'][i,j] for i,j in arcs]);h.addCols(m,costs,np.zeros(m),np.ones(m),0,np.zeros(m+1,dtype=np.int32),np.array([],np.int32),np.array([],float))
 if milp:h.changeColsIntegrality(m,np.arange(m,dtype=np.int32),np.ones(m,dtype=np.uint8))
 for i in range(n):addrow(h,{x[i,j]:1. for j in range(n) if (i,j) in x},1,1)
 for j in range(n):addrow(h,{x[i,j]:1. for i in range(n) if (i,j) in x},1,1)
 if milp:
  b={}
  for i in range(1,n):b[i]=h.getNumCol();h.addVar(float(a['ready'][i]),float(a['due'][i]))
  for (i,j),k in x.items():
   t=float(a['travel'][i,j])
   if i==0:
    M=max(0,t-float(a['ready'][j]));addrow(h,{b[j]:1.,k:-M},t-M,highspy.kHighsInf)
   elif j==0:
    M=max(0,float(a['due'][i])+102+t-32400);addrow(h,{b[i]:1.,k:M},-highspy.kHighsInf,32400-102-t+M)
   else:
    M=max(0,float(a['due'][i])+102+t-float(a['ready'][j]));addrow(h,{b[j]:1.,b[i]:-1.,k:-M},102+t-M,highspy.kHighsInf)
 return h,arcs

def assignment_bound(a):
 h,arcs=build(a,False);h.run();assert h.getModelStatus()==highspy.HighsModelStatus.kOptimal
 n=len(a['nodes']);dual=h.getSolution().row_dual;v=[Decimal(str(x)) for x in dual[n:2*n]]
 # Exact repair of row potentials makes every off-diagonal dual constraint valid.
 # Column upper bounds are redundant in assignment LP; no use of their duals.
 u=[min(Decimal(str(a['travel'][i,j]))-v[j] for ii,j in arcs if ii==i) for i in range(n)]
 lb=sum(u+v,Decimal(0));return str(lb),dict(u=[str(x) for x in u],v=[str(x) for x in v],variables=h.getNumCol(),constraints=h.getNumRow())

def milp_candidate(a,seconds=5,nodes=None):
 ts=time.perf_counter();h,arcs=build(a,True);buildtime=time.perf_counter()-ts
 h.setOptionValue('time_limit',seconds);h.setOptionValue('mip_rel_gap',0.0);h.setOptionValue('mip_abs_gap',0.0)
 if nodes is not None:h.setOptionValue('mip_max_nodes',nodes)
 ts=time.perf_counter();h.run();wall=time.perf_counter()-ts;info=h.getInfo();sol=h.getSolution();r=None
 if sol.value_valid:
  succ={i:j for k,(i,j) in enumerate(arcs) if sol.col_value[k]>.5};candidate=[0]
  for _ in range(len(a['nodes'])):
   if candidate[-1] not in succ:break
   candidate.append(succ[candidate[-1]])
   if candidate[-1]==0:break
  if len(candidate)==len(a['nodes'])+1 and sorted(candidate[1:-1])==list(range(1,len(a['nodes']))) and replay(a,candidate)[0]:r=candidate
 return r,dict(build_seconds=buildtime,wall_seconds=wall,variables=h.getNumCol(),constraints=h.getNumRow(),model_status=h.modelStatusToString(h.getModelStatus()),incumbent=info.objective_function_value if r else None,best_bound=info.mip_dual_bound if np.isfinite(info.mip_dual_bound) else None,gap=info.mip_gap if np.isfinite(info.mip_gap) else None,node_count=info.mip_node_count)
