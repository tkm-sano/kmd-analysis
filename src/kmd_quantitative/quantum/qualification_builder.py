"""Direct customer-position QUBO with exact forbidden-permutation compilation.
No solver, optimizer or sampling. Factorial compilation is intentionally disclosed.
"""
from decimal import Decimal as D, getcontext
from itertools import permutations
getcontext().prec=80

def schedule(a,order):
    clock=D(0);tw=True;starts=[]
    for i,j in zip([0]+list(order),list(order)+[0]):
        clock=max(clock+D(str(a['travel'][i,j])),D(int(a['ready'][j])))
        starts.append(str(clock))
        if j:tw &= clock<=D(int(a['due'][j]))
        clock+=D(int(a['service'][j]))
    horizon=clock<=D(32400) and D(starts[-1])<=D(int(a['due'][0]))
    return bool(tw),bool(horizon),starts

def build(a):
    n=len(a['nodes'])-1; assert n in (3,4)
    assert str(a['nodes'][0])=='DEP_006' and int(a['service'][0])==0
    assert all(int(x)==102 for x in a['service'][1:])
    assert int(a['ready'][0])==0 and int(a['due'][0])==32400
    assert all(int(x)>=0 for x in a['demand']) and int(a['demand'][0])==0
    U=D(n+1)*max(D(str(x)) for x in a['travel'].flat);A=U+D(1)
    names=[f'x_customer{i}_position{p}' for i in range(1,n+1) for p in range(n)]
    x=lambda i,p:(i-1)*n+p
    records=[];bad=[]
    for perm in permutations(range(1,n+1)):
        tw,ret,starts=schedule(a,perm)
        records.append(dict(order=list(perm),TIME_WINDOW=tw,RETURN_HORIZON=ret,starts=starts))
        if not(tw and ret):bad.append(perm)
    prefixes=sorted({perm[:k] for perm in bad for k in range(2,n) },key=lambda z:(len(z),z))
    anc={prefix:n*n+j for j,prefix in enumerate(prefixes)}
    names += ['z_prefix_'+'_'.join(map(str,z)) for z in prefixes]
    linear=[D(0)]*len(names);pairs={};offset=D(0)
    def pair(i,j,v):
        if i==j:linear[i]+=v
        else:
            ij=tuple(sorted((i,j)));pairs[ij]=pairs.get(ij,D(0))+v
    def square(ids):
        nonlocal offset
        offset+=A
        for i in ids:linear[i]-=A
        for k,i in enumerate(ids):
            for j in ids[k+1:]:pair(i,j,2*A)
    for i in range(1,n+1):square([x(i,p) for p in range(n)])
    for p in range(n):square([x(i,p) for i in range(1,n+1)])
    # Nonnegative physical objective for every assignment, not just permutations.
    for i in range(1,n+1):
        linear[x(i,0)]+=D(str(a['travel'][0,i]));linear[x(i,n-1)]+=D(str(a['travel'][i,0]))
        for j in range(1,n+1):
            for p in range(n-1):pair(x(i,p),x(j,p+1),D(str(a['travel'][i,j])))
    ands=[]
    for prefix,z in anc.items():
        u=x(prefix[0],0) if len(prefix)==2 else anc[prefix[:-1]]
        vv=x(prefix[-1],len(prefix)-1)
        # R(u,v,z)=uv-2uz-2vz+3z: zero iff z=uv; otherwise >=1.
        pair(u,vv,A);pair(u,z,-2*A);pair(vv,z,-2*A);linear[z]+=3*A
        ands.append(dict(u=u,v=vv,z=z,prefix=list(prefix)))
    forbidden_pairs=[]
    for perm in bad:
        u=anc[perm[:-1]];vv=x(perm[-1],n-1);pair(u,vv,A);forbidden_pairs.append([u,vv])
    capacity_ok=sum(map(int,a['demand']))<=216
    if not capacity_ok:offset+=A
    return dict(encoding='DIRECT_POSITION_FORBIDDEN_PERMUTATION_PREFIX_AND_V1',n=n,customer_ids=list(map(str,a['nodes'][1:])),names=names,position_variable_count=n*n,ancilla_count=len(anc),logical_variables=len(names),linear=list(map(str,linear)),quadratic=[[i,j,str(v)] for (i,j),v in sorted(pairs.items()) if v],offset=str(offset),penalty_s=str(A),objective_upper_bound_s=str(U),capacity_ok=capacity_ok,total_demand=sum(map(int,a['demand'])),capacity=216,ands=ands,forbidden_pairs=forbidden_pairs,permutations=records,forbidden_order_count=len(bad),time_quantization='NONE_DECIMAL_OF_FROZEN_INPUT',capacity_slack_bits=0,time_slack_bits=0)

def witness(model,perm):
    n=model['n'];b=[0]*model['logical_variables']
    for p,i in enumerate(perm):b[(i-1)*n+p]=1
    for gate in model['ands']:b[gate['z']]=b[gate['u']]*b[gate['v']]
    return b

def energy(model,b):
    return D(model['offset'])+sum((D(v)*b[i] for i,v in enumerate(model['linear'])),D(0))+sum((D(v)*b[i]*b[j] for i,j,v in model['quadratic']),D(0))
