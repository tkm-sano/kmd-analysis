"""Direct vehicle/position QUBO. No route search or route catalog preprocessing."""
import numpy as np

STATE_LIMIT = 1 << 20
TOTAL_STATE_LIMIT = 1 << 23
OBJECTIVE_TOL = 1e-7
ENERGY_TOL = 1e-6
FAMILIES = ('visit', 'slot', 'prefix', 'capacity', 'reach')

def dimensions(n, m):
    if n < 1 or m < 1:
        raise ValueError('Positive n and m required')
    route = m * n * (n + 1)
    slack = 4 * m
    return {'route_variables': route, 'slack_variables': slack, 'quadratization_ancillas': 0,
            'total_binary_variables': route + slack, 'full_enumeration_size': 1 << (route + slack)}

def build(instance):
    n = len(instance.customers); m = instance.max_vehicles
    if n not in (2, 3, 4) or instance.capacity != 14:
        raise ValueError('This validation implementation requires n=2,3,4 and Q=14')
    if any(not isinstance(q, int) or q < 1 or q > 14 for q in instance.demands.values()):
        raise ValueError('Positive integer demands in [1,14] required')
    dims = dimensions(n, m); N = dims['total_binary_variables']; B = dims['route_variables']
    nodes = (instance.depot, *instance.customers)
    costs = np.zeros((n+1, n+1)); forbidden = np.zeros_like(costs, dtype=np.int64)
    for i, u in enumerate(nodes):
        for j, v in enumerate(nodes):
            if i == j: continue  # depot self is padding; customer repeats violate visit.
            arc = instance.arcs.get((u, v))
            if arc is None:
                forbidden[i, j] = 1
            else:
                if not np.isfinite(arc.travel_time) or arc.travel_time < 0:
                    raise ValueError('Travel costs must be finite/nonnegative')
                costs[i, j] = arc.travel_time
    U = (n + m) * float(costs.max())
    A = U + max(1., .01 * U)
    x = np.arange(B).reshape(m, n, n+1); b = np.arange(B, N).reshape(m, 4)
    h = np.zeros(N); J = np.zeros((N, N)); offset = 0.
    q = np.array([instance.demands[c] for c in instance.customers], dtype=np.int64)
    def pair(a, c, value):
        if a == c: h[a] += value
        else: J[min(a,c), max(a,c)] += value
    def square(indices, values, target, weight=A):
        nonlocal offset
        offset += weight * target**2
        for i, a in enumerate(indices):
            h[a] += weight * (values[i]**2 - 2*target*values[i])
            for j in range(i+1, len(indices)):
                pair(a, indices[j], 2*weight*values[i]*values[j])
    for i in range(1, n+1):
        indices = x[:,:,i].ravel().tolist()
        square(indices, [1]*len(indices), 1)
    for k in range(m):
        for t in range(n):
            square(x[k,t,:].tolist(), [1]*(n+1), 1)
        square(x[k,:,1:].ravel().tolist() + b[k].tolist(), np.tile(q,n).tolist() + [1,2,4,8], 14)
        for t in range(n-1):
            for j in range(1,n+1): pair(x[k,t,0], x[k,t+1,j], A)
        for i in range(n+1):
            h[x[k,0,i]] += costs[0,i] + A*forbidden[0,i]
            h[x[k,n-1,i]] += costs[i,0] + A*forbidden[i,0]
            for t in range(n-1):
                for j in range(n+1):
                    pair(x[k,t,i], x[k,t+1,j], costs[i,j] + A*forbidden[i,j])
    names = [f'x_{k}_{t}_{nodes[i]}' for k in range(m) for t in range(n) for i in range(n+1)]
    names += [f'b_{k}_{l}' for k in range(m) for l in range(4)]
    return dict(instance=instance, n=n, m=m, N=N, B=B, x=x, b=b, q=q,
                costs=costs, forbidden=forbidden, U_bound_s=U, penalty_weights={f:A for f in FAMILIES},
                h=h, J=J, offset=offset, names=names, **dims)

def factorized(model, bits):
    """Original objective/constraints, separate from the coefficient expansion."""
    bits = np.asarray(bits, dtype=np.int64)
    x = bits[:,:model['B']].reshape(-1,model['m'],model['n'],model['n']+1)
    b = bits[:,model['B']:].reshape(-1,model['m'],4)
    visit = ((x[:,:,:,1:].sum(axis=(1,2))-1)**2).sum(axis=1)
    slot = ((x.sum(axis=3)-1)**2).sum(axis=(1,2))
    prefix = (x[:,:,:-1,0] * x[:,:,1:,1:].sum(axis=3)).sum(axis=(1,2))
    load = np.einsum('bkti,i->bk',x[:,:,:,1:],model['q'])
    slack = b @ np.array([1,2,4,8], dtype=np.int64)
    capacity = ((load+slack-14)**2).sum(axis=1)
    def arcs(matrix):
        return ((x[:,:,0,:] * matrix[0,:]).sum(axis=(1,2))
                + (x[:,:,-1,:] * matrix[:,0]).sum(axis=(1,2))
                + np.einsum('bkti,ij,bktj->b',x[:,:,:-1,:],matrix,x[:,:,1:,:],optimize=True))
    objective = arcs(model['costs'])
    penalties = dict(visit=visit, slot=slot, prefix=prefix, capacity=capacity, reach=arcs(model['forbidden']))
    energy = objective.copy()
    for family, residual in penalties.items():
        assert np.all(residual >= 0)
        energy += model['penalty_weights'][family] * residual
    return objective, penalties, energy

def expanded(model, bits):
    return model['offset'] + bits @ model['h'] + np.einsum('bi,ij,bj->b',bits,model['J'],bits,optimize=True)

def decode(model, bits):
    bits = np.asarray(bits)
    if bits.shape != (model['N'],) or not np.all((bits==0)|(bits==1)):
        raise ValueError('Wrong length or nonbinary input')
    _, penalties, _ = factorized(model,bits[None,:])
    if any(p[0] != 0 for p in penalties.values()):
        raise ValueError('Infeasible bitstring; no repair')
    instance = model['instance']; routes=[]; vehicle_ids=[]
    x = bits[:model['B']].reshape(model['m'],model['n'],model['n']+1)
    for k in range(model['m']):
        symbols = x[k].argmax(axis=1)
        customers = [instance.customers[i-1] for i in symbols if i != 0]
        if customers:
            routes.append((instance.depot,*customers,instance.depot)); vehicle_ids.append(k)
    return routes, vehicle_ids

def encode_witness(model, routes):
    """Encode a supplied route in its existing order; performs no optimization."""
    if len(routes)>model['m']: raise ValueError('Fleet limit')
    instance = model['instance']; bits=np.zeros(model['N'],dtype=np.int64)
    for k in range(model['m']):
        route=routes[k] if k<len(routes) else (instance.depot,instance.depot)
        if route[0]!=instance.depot or route[-1]!=instance.depot: raise ValueError('Depot endpoints')
        inner=route[1:-1]
        if len(inner)>model['n']: raise ValueError('Too many customers')
        load=sum(instance.demands[c] for c in inner)
        if load>14: raise ValueError('Capacity')
        for t in range(model['n']):
            i=instance.customers.index(inner[t])+1 if t<len(inner) else 0
            bits[model['x'][k,t,i]]=1
        for l in range(4): bits[model['b'][k,l]]=((14-load)>>l)&1
    decode(model,bits)
    return bits

def exhaustive(model, validate, reference_highs, reference_subset):
    """Search every binary state only after a strict resource guard."""
    total=model['full_enumeration_size']
    if total>STATE_LIMIT:
        return {'status':'RESOURCE_LIMIT_NOT_EXECUTED','states_enumerated':0,
                'reason':f'{total} states exceed per-condition limit {STATE_LIMIT}'}
    best=float('inf'); winners=[]; invalid_min=float('inf'); feasible_count=0; max_error=0.
    invalid_by_family={f:float('inf') for f in FAMILIES}
    best_expanded=float('inf')
    for start in range(0,total,16384):
        states=np.arange(start,min(start+16384,total),dtype=np.uint64)
        bits=((states[:,None]>>np.arange(model['N'],dtype=np.uint64))&1).astype(np.int64)
        objective,penalties,energy=factorized(model,bits)
        expanded_energy=expanded(model,bits)
        max_error=max(max_error,float(np.max(np.abs(energy-expanded_energy))))
        assert max_error<ENERGY_TOL, max_error
        best_expanded=min(best_expanded,float(expanded_energy.min()))
        valid=np.ones(len(bits),dtype=bool)
        for f,p in penalties.items():
            valid &= p==0
            if (p>0).any(): invalid_by_family[f]=min(invalid_by_family[f],float(energy[p>0].min()))
        feasible_count+=int(valid.sum())
        if (~valid).any(): invalid_min=min(invalid_min,float(energy[~valid].min()))
        local=float(energy.min())
        if local<best-OBJECTIVE_TOL:
            best=local; winners=[]
        if abs(local-best)<=OBJECTIVE_TOL:
            for idx in np.flatnonzero(np.abs(energy-best)<=OBJECTIVE_TOL):
                winners.append((int(states[idx]),bits[idx].tolist()))
    assert winners and abs(best-best_expanded)<ENERGY_TOL
    assert invalid_min>=min(model['penalty_weights'].values())-ENERGY_TOL
    max_highs_difference=0.; max_subset_difference=0.
    for _,bits in winners:
        routes,vehicles=decode(model,bits)
        result=validate(model['instance'],routes,best)
        assert result.status=='VALID_SOLUTION', result.errors
        max_highs_difference=max(max_highs_difference,abs(result.objective-reference_highs))
        max_subset_difference=max(max_subset_difference,abs(result.objective-reference_subset))
        assert max_highs_difference<=OBJECTIVE_TOL and max_subset_difference<=OBJECTIVE_TOL
    state,bits=min(winners); routes,vehicles=decode(model,bits)
    result=validate(model['instance'],routes,reference_highs)
    return {'status':'PASS','states_enumerated':total,'feasible_states':feasible_count,
            'invalid_states':total-feasible_count,'ground_state_count':len(winners),
            'all_ground_states_independently_validated':True,'minimum_energy_s':best,
            'minimum_expanded_energy_s':best_expanded,'minimum_invalid_energy_s':invalid_min,
            'invalid_ground_gap_s':invalid_min-best,'max_expansion_error_s':max_error,
            'minimum_energy_by_violated_family_s':{f:None if np.isinf(v) else v for f,v in invalid_by_family.items()},
            'direct_objective_s':result.objective,'highs_objective_s':reference_highs,
            'subset_objective_s':reference_subset,'max_highs_difference_s':max_highs_difference,
            'max_subset_difference_s':max_subset_difference,'validator_status':result.status,
            'representative_state':state,'bits':bits,'routes':routes,'vehicle_ids':vehicles,
            'route_loads':result.route_loads,'used_vehicles':result.used_vehicles,
            'total_distance_m':result.total_distance}
