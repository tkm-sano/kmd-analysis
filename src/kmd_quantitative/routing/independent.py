from decimal import getcontext
getcontext().prec = 80
"""Independent Decimal schedule and dual certificate checking; no solver imports."""
from decimal import Decimal as D
def dec(x):return D(str(x))
def validate(a,r):
 n=len(a['nodes'])
 assert r[0]==r[-1]==0 and sorted(r[1:-1])==list(range(1,n)), 'coverage'
 load=sum(int(x) for x in a['demand']);assert load<=216
 time=D(0);road=D(0);distance=D(0);waiting=D(0);service=D(0);stops=[];legs=[]
 for order,(i,j) in enumerate(zip(r,r[1:]),1):
  tt=dec(a['travel'][i,j]);dd=dec(a['distance'][i,j]);assert tt.is_finite() and dd.is_finite() and tt>=0 and dd>=0
  arrival=time+tt;start=max(arrival,D(int(a['ready'][j])));wait=start-arrival
  assert start<=int(a['due'][j]),('TW/depot',str(a['nodes'][j]),start)
  st=D(int(a['service'][j]));end=start+st
  load-=int(a['demand'][j]);assert load>=0
  stops.append(dict(stop_order=order,customer_id=str(a['nodes'][j]),demand=int(a['demand'][j]),remaining_delivery_load=load,tw_ready_seconds=int(a['ready'][j]),tw_due_seconds=int(a['due'][j]),arrival_seconds=str(arrival),waiting_seconds=str(wait),service_start_seconds=str(start),service_duration_seconds=str(st),departure_seconds=str(end)))
  legs.append(dict(origin_id=str(a['nodes'][i]),destination_id=str(a['nodes'][j]),SUMO_travel_seconds=str(tt),SUMO_distance_m=str(dd),partition_index=int(a['partition'][i,j])))
  time=end;road+=tt;distance+=dd;waiting+=wait;service+=st
 assert load==0 and time<=32400 and time==road+waiting+service
 return dict(stops=stops,legs=legs,totals=dict(road_travel_seconds=str(road),road_distance_m=str(distance),waiting_seconds=str(waiting),service_seconds=str(service),route_duration_seconds=str(time),depot_return_seconds=str(time)))

def verify_dual(a,proof,lower_bound):
 n=len(a['nodes']);u=list(map(D,proof['u']));v=list(map(D,proof['v']));assert len(u)==len(v)==n
 admitted=0;excluded=0
 for i in range(n):
  for j in range(n):
   if i==j:continue
   c=dec(a['travel'][i,j])
   # Necessary earliest possible arrival on this arc; no triangle inequality.
   earliest=D(int(a['ready'][i]))+D(int(a['service'][i]))+c
   if earliest>D(int(a['due'][j])):excluded+=1;continue
   assert u[i]+v[j]<=c,('invalid dual',i,j)
   admitted+=1
 assert sum(u+v,D(0))==D(lower_bound)
 return dict(admitted_arcs=admitted,necessarily_excluded_arcs=excluded)

def exact_dfs(a):
 # Exhaustive prefix enumeration with only exact temporal infeasibility pruning.
 n=len(a['nodes']);best=None;cost=None;leaves=0;prefixes=0
 def visit(last,left,clock,road,path):
  nonlocal best,cost,leaves,prefixes
  prefixes+=1
  if not left:
   end=clock+dec(a['travel'][last,0])
   if end>32400:return
   leaves+=1;value=road+dec(a['travel'][last,0]);r=[0]+path+[0]
   if best is None or (value,r)<(cost,best):best=r;cost=value
   return
  for j in sorted(left):
   start=max(clock+dec(a['travel'][last,j]),D(int(a['ready'][j])))
   if start>D(int(a['due'][j])):continue
   visit(j,left-{j},start+D(int(a['service'][j])),road+dec(a['travel'][last,j]),path+[j])
 visit(0,set(range(1,n)),D(0),D(0),[])
 return best,str(cost),dict(feasible_leaves=leaves,prefixes=prefixes)
