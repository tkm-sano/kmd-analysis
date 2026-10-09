"""Independent decoder: no QUBO builder imports; no repair; little-endian index bits."""
from decimal import Decimal as D,getcontext
getcontext().prec=80

def classical_constraint_readback(a,route):
    n=len(a['nodes'])-1
    depot=len(route)>=2 and route[0]==route[-1]==0
    visit=depot and sorted(route[1:-1])==list(range(1,n+1))
    status=dict(VISIT=visit,ROUTE=visit,DEPOT=depot,CAPACITY=False,TIME_WINDOW=False,SERVICE=False,RETURN_HORIZON=False)
    if not visit:return status,None
    status['CAPACITY']=sum(int(a['demand'][j]) for j in route[1:-1])<=216
    time=D(0);travel=D(0);distance=D(0);waiting=D(0);tw=True;starts=[]
    for i,j in zip(route,route[1:]):
        cost=D(str(a['travel'][i,j]));dd=D(str(a['distance'][i,j]))
        if not cost.is_finite() or cost<0 or not dd.is_finite() or dd<0:status['ROUTE']=False;return status,None
        arrival=time+cost
        wait=max(D(int(a['ready'][j]))-arrival,D(0));start=arrival+wait
        if j!=0 and start>D(int(a['due'][j])):tw=False
        starts.append(str(start));time=start+D(int(a['service'][j]));travel+=cost;distance+=dd;waiting+=wait
    status.update(TIME_WINDOW=tw,SERVICE=all(int(a['service'][i])==102 for i in route[1:-1]) and int(a['service'][0])==0,RETURN_HORIZON=time<=32400 and D(starts[-1])<=int(a['due'][0]))
    return status,dict(objective_s=str(travel),distance_m=str(distance),waiting_s=str(waiting),duration_s=str(time),starts=starts)

def decode(a,bits,ands):
    n=len(a['nodes'])-1;N=n*n+len(ands)
    if len(bits)!=N or any(x not in (0,1) for x in bits):return dict(valid=False,reason='NONBINARY_OR_WIDTH',route=None)
    core=bits[:n*n]
    if any(sum(core[(i-1)*n+p] for p in range(n))!=1 for i in range(1,n+1)) or any(sum(core[(i-1)*n+p] for i in range(1,n+1))!=1 for p in range(n)):
        return dict(valid=False,reason='ASSIGNMENT',route=None)
    order=[next(i for i in range(1,n+1) if core[(i-1)*n+p]) for p in range(n)]
    route=[0]+order+[0];status,physical=classical_constraint_readback(a,route)
    ancilla_ok=all(bits[g['z']]==bits[g['u']]*bits[g['v']] for g in ands)
    return dict(valid=all(status.values()) and ancilla_ok,reason='OK' if all(status.values()) and ancilla_ok else 'PHYSICAL_OR_ANCILLA',route=route,constraints=status,physical=physical,ancilla_ok=ancilla_ok)
