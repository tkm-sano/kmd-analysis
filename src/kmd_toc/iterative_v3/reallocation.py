"""Finite classical neighborhood on actual physical vehicle/trip memberships."""
from collections import Counter
from .io import routes,memberships,encode_routes,decode_routes

def valid_structure(p,rs):
    vehicles={v.vehicle_id:v for v in p.vehicles};demand={s.stop_id:s.demand for s in p.stops}
    if Counter(s for r in rs.values() for s in r)!=Counter(demand):raise ValueError('COVERAGE_DUPLICATE_OR_MISSING')
    for (v,k),r in rs.items():
        if v not in vehicles or k not in (1,2) or not r:raise ValueError('INVALID_ACTIVE_SLOT')
        if k==2 and (v,1) not in rs:raise ValueError('SECOND_WITHOUT_FIRST')
        if sum(demand[s] for s in r)>vehicles[v].capacity:raise ValueError('CAPACITY')
    return True

def change(p,original,source,target,customer,other=None):
    rs={k:list(v) for k,v in original.items()};rs.setdefault(target,[])
    if source==target:raise ValueError('DISTINCT_RELOCATION_SLOTS')
    if other is None:
        rs[source].remove(customer);rs[target].append(customer)
    else:
        a=rs[source].index(customer);b=rs[target].index(other);rs[source][a],rs[target][b]=other,customer
    rs={k:tuple(r) for k,r in rs.items() if r};valid_structure(p,rs)
    before=memberships(original);after=memberships(rs)
    diff=[dict(customer=s,before=list(before[s]),after=list(after[s])) for s in sorted(before) if before[s]!=after[s]]
    return rs,diff

def generate(p,plan,rng,*,per_family,attempts_per_family,max_candidates=None):
    rs=routes(plan);valid_structure(p,rs);active=sorted(rs);slots=sorted((v.vehicle_id,k) for v in p.vehicles for k in (1,2))
    result=[];seen=set()
    for family in ('inter_relocate','inter_swap','intra_transfer'):
        if max_candidates is not None and len(result)>=max_candidates:break
        made=0
        for attempt in range(attempts_per_family):
            if made>=per_family or (max_candidates is not None and len(result)>=max_candidates):break
            source=rng.choice(active)
            targets=[k for k in slots if (k[0]!=source[0] if family.startswith('inter') else k[0]==source[0] and k[1]!=source[1])]
            if family=='inter_swap':targets=[k for k in targets if k in rs]
            if not targets:continue
            target=rng.choice(targets);customer=rng.choice(rs[source]);other=rng.choice(rs[target]) if family=='inter_swap' else None
            signature=(source,target,customer,other)
            if signature in seen:continue
            seen.add(signature)
            try:new,diff=change(p,rs,source,target,customer,other)
            except ValueError:continue
            # No distance-gain screen: all three families can increase D.
            result.append(dict(move_id=f'{family}_{made}',family=family,routes=encode_routes(new),membership_diff=diff,
                inverse_tabu_attributes=[[x['customer'],*x['before']] for x in diff],
                tabu_destination_attributes=[[x['customer'],*x['after']] for x in diff],
                affected_slots=[list(k) for k in sorted({source,target})],distance_screen=False))
            made+=1
    return result

class Tabu:
    def __init__(self,tenure,entries=None):self.tenure=tenure;self.entries=entries or {}
    def prohibited(self,move,iteration):
        return any(self.entries.get('|'.join(map(str,k)),-1)>iteration for k in move['tabu_destination_attributes'])
    def record(self,move,iteration):
        for k in move['inverse_tabu_attributes']:self.entries['|'.join(map(str,k))]=iteration+self.tenure+1
        self.entries={k:v for k,v in self.entries.items() if v>iteration}
