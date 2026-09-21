"""Temporal forbidden-pattern extension; original Direct QUBO is imported unchanged.

No time grid, optimal-route lookup, route-selector variables or capacity filtering.
Complete simple per-vehicle sequences are compiled, including all partial routes.
This is explicitly factorial preprocessing, restricted to the frozen small suite.
"""
from itertools import permutations, product
from types import SimpleNamespace
import numpy as np
from traffic_simulation.r24_direct_qubo import model as direct
from traffic_simulation.r24_vrptw.instance import validate_input, json_number


def replay_sequence(v, sequence):
    """Independent recurrence, deliberately does not invoke the authority validator."""
    clock = v['opening']; previous = v['depot_id']; records = []; late = False
    for customer in sequence:
        c = v['customers'][customer]
        arrival = clock + v['arcs'][previous, customer][0]
        start = max(arrival, c['earliest'])
        clock = start + c['duration']
        late |= start > c['latest']
        records.append(dict(customer=customer, arrival=json_number(arrival), start=json_number(start),
            waiting=json_number(start-arrival), end=json_number(clock)))
        previous = customer
    returned = clock + v['arcs'][previous, v['depot_id']][0] if sequence else v['opening']
    return dict(temporal=not late, depot=returned <= v['closing'], returned=json_number(returned), records=records)


def compile_patterns(data):
    v = validate_input(data); customers = list(v['customers']); n = len(customers)
    if not 2 <= n <= 4 or len(v['vehicles']) > 3:
        raise ValueError('Frozen small-case scope only')
    patterns = []; inventory = []
    for size in range(1,n+1):
        for sequence in permutations(customers,size):
            result = replay_sequence(v,sequence)
            symbols = tuple(customers.index(c)+1 for c in sequence) + (0,)*(n-size)
            inventory.append(dict(sequence=sequence,symbols=symbols,**result))
            for family in ('temporal','depot'):
                if not result[family]:
                    patterns.append(dict(sequence=sequence,symbols=symbols,family=family))
    return v, patterns, inventory


def build(data):
    v, patterns, inventory = compile_patterns(data)
    customers = tuple(v['customers']); m = len(v['vehicles']); n = len(customers)
    if set(v['vehicles'].values()) != {14}:
        raise ValueError('Original Q=14 capacity semantics required')
    instance = SimpleNamespace(customers=customers, depot=v['depot_id'],max_vehicles=m,capacity=14,
        demands={c:int(v['customers'][c]['demand']) for c in customers},
        arcs={k:SimpleNamespace(travel_time=float(t),distance=float(d or 0)) for k,(t,d) in v['arcs'].items()})
    assert all(v['customers'][c]['demand']==instance.demands[c] for c in customers)
    base = direct.build(instance); A = base['penalty_weights']['visit']; M = 2*A
    N = base['N'] + m*len(patterns)*max(0,n-2)
    if N > 2000:
        raise ValueError('QUBO_CONSTRUCTION_RESOURCE_STOP')
    h=np.zeros(N); h[:base['N']]=base['h']
    J=np.zeros((N,N)); J[:base['N'],:base['N']]=base['J']
    names=base['names'].copy(); chains=[]; terms=[]; cursor=base['N']
    def pair(i,j,value):
        J[min(i,j),max(i,j)] += value
    for k in range(m):
        for p,pattern in enumerate(patterns):
            indices=[int(base['x'][k,t,s]) for t,s in enumerate(pattern['symbols'])]
            left=indices[0]; local=[]
            for t in range(1,n-1):
                right=indices[t]; z=cursor; cursor+=1
                # Rosenberg AND: ab-2az-2bz+3z >= 0 for all binary states.
                pair(left,right,M); pair(left,z,-2*M); pair(right,z,-2*M); h[z]+=3*M
                local.append((left,right,z)); chains.append((left,right,z))
                names.append(f'and_{k}_{p}_{t}'); left=z
            pair(left,indices[-1],A)
            terms.append(dict(vehicle=k,pattern=p,family=pattern['family'],indices=indices,
                              chains=local,terminal=[left,indices[-1]]))
    assert cursor == N
    return dict(base=base,v=v,data=data,patterns=patterns,inventory=inventory,N=N,h=h,J=J,
                offset=base['offset'],A=A,M=M,n=n,m=m,names=names,chains=chains,terms=terms)


def factorized(model,bits):
    bits=np.asarray(bits,dtype=np.int64)
    objective,penalties,energy=direct.factorized(model['base'],bits[:,:model['base']['N']])
    penalties={**penalties,'temporal':np.zeros(len(bits),dtype=np.int64),
               'depot':np.zeros(len(bits),dtype=np.int64),'ancilla':np.zeros(len(bits),dtype=np.int64)}
    for a,b,z in model['chains']:
        penalties['ancilla'] += bits[:,a]*bits[:,b]-2*bits[:,a]*bits[:,z]-2*bits[:,b]*bits[:,z]+3*bits[:,z]
    for term in model['terms']:
        a,b=term['terminal']; penalties[term['family']]+=bits[:,a]*bits[:,b]
    energy += model['A']*(penalties['temporal']+penalties['depot']) + model['M']*penalties['ancilla']
    return objective,penalties,energy


def expanded(model,bits):
    bits=np.asarray(bits,dtype=np.int64)
    # Stable accumulation of the SAME float64 coefficients, not coefficient tuning.
    energy=np.longdouble(model['offset'])+bits.astype(np.longdouble)@model['h'].astype(np.longdouble)
    for i,j in zip(*np.nonzero(model['J'])):
        energy += np.longdouble(model['J'][i,j])*bits[:,i]*bits[:,j]
    return energy


def complete_ancillas(model,bits):
    for a,b,z in model['chains']:
        bits[z]=bits[a]*bits[b]
    return bits


def encode_routes(model,routes):
    base=model['base']; v=model['v']; by_vehicle={r['vehicle_id']:r['stops'][1:-1] for r in routes}
    bits=np.zeros(model['N'],dtype=np.int64)
    for k,vid in enumerate(v['vehicles']):
        sequence=by_vehicle.get(vid,[]); load=sum(base['instance'].demands[c] for c in sequence)
        for t in range(model['n']):
            s=base['instance'].customers.index(sequence[t])+1 if t<len(sequence) else 0
            bits[base['x'][k,t,s]]=1
        slack=max(0,14-load)
        for b in range(4): bits[base['b'][k,b]]=(slack>>b)&1
    return complete_ancillas(model,bits)


def decode_candidate(model,bits):
    """No repair; independently report encoding residuals and replay authority."""
    from traffic_simulation.r24_vrptw.validator import validate_routes
    bits=np.asarray(bits)
    if bits.shape != (model['N'],) or not np.isin(bits,[0,1]).all():
        raise ValueError('Invalid bit vector')
    bits=bits.astype(np.int64)
    _,p,e=factorized(model,bits[None,:]); residuals={k:int(v[0]) for k,v in p.items()}
    if any(residuals[k] for k in ('slot','prefix')):
        return dict(encoding_residuals=residuals,energy=float(e[0]),replay_status='NOT_EVALUABLE',routes=None)
    routes=[]; base=model['base']; depot=model['v']['depot_id']
    for k,vid in enumerate(model['v']['vehicles']):
        symbols=bits[base['x'][k]].argmax(axis=1)
        sequence=[base['instance'].customers[s-1] for s in symbols if s]
        if sequence:routes.append(dict(vehicle_id=vid,stops=[depot,*sequence,depot]))
    replay=validate_routes(model['data'],routes)
    return dict(encoding_residuals=residuals,energy=float(e[0]),routes=routes,replay=replay,replay_status=replay['status'])


def gadget_truth_tables():
    tested=0
    for n in (2,3,4):
        for original in product((0,1),repeat=n):
            values=[]
            for aux in product((0,1),repeat=n-2):
                left=original[0]; e=0
                for b,z in zip(original[1:-1],aux):
                    e+=2*(left*b-2*left*z-2*b*z+3*z);left=z
                e+=left*original[-1];values.append(e);tested+=1
            assert min(values)==int(all(original))
    return tested
