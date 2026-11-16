"""Deterministic overlapping domains; ledger is scoped to the LP dual snapshot.

Independent study extension, not Huang's full pricing completeness guarantee.
Pair coverage is a complete TRIP cover only for positive unit demands/Q=2.
Day partner/time completeness remains separate. No demand RNG is used.
"""
from itertools import combinations
import hashlib
import json
from dataclasses import replace
from kmd_toc.column_generation.models import Instance, Route
from kmd_toc.column_generation.reduction import contract, exact_domain_routes
from kmd_toc.column_generation.aoa import PricingAOA


def legacy_regions(problem,dual,iteration):
    ids=problem.base.customers
    top=tuple(sorted(ids,key=lambda i:(-dual['customer'][i-1],i))[:3])
    anchor=ids[iteration%len(ids)]
    near=tuple(sorted(ids,key=lambda i:(problem.base.distance[anchor,i],i))[:3])
    return [top] if set(top)==set(near) else [top,near]


def expanded_regions(problem,dual,iteration,max_domains=64):
    if len(problem.base.customers)>12:
        raise ValueError('ARTIFICIAL_REGION_DOMAIN_GUARD')
    domains=legacy_regions(problem,dual,iteration)
    ids=tuple(problem.base.customers)
    uncovered=set(combinations(ids,2))
    for d in domains: uncovered.difference_update(combinations(sorted(d),2))
    choices=list(combinations(ids,min(3,len(ids))))
    while uncovered and len(domains)<max_domains:
        best=min(choices,key=lambda d:(-len(set(combinations(d,2))&uncovered),d))
        if not set(combinations(best,2))&uncovered: break
        domains.append(best); uncovered.difference_update(combinations(best,2))
    return domains


def proxy_domain(problem,dual,profile,groups,slots):
    weight=0. if dual['phase']=='I' else (1. if profile.primary=='D' else -dual['other'])
    proxy=Instance(problem.base.name+'_proxy',weight*problem.base.distance,problem.base.demand,
                   max(v.capacity for v in problem.vehicles))
    return contract(proxy,dual['customer'],groups,'pricing_improvement_domain',slots=slots)


def exact_routes(problem,dual,profile,domains,slots=3):
    output=set()
    for subset in domains:
        # Enumerate feasibility in original distance units. Proxy scaling changes
        # AOA energies, never route feasibility; comparing proxy costs to raw
        # distances would incorrectly fail for W or Phase I (weight zero).
        domain=contract(problem.base,dual['customer'],[(i,) for i in subset],
                        'exact_scope',slots=slots)
        output.update(r.customers for r in exact_domain_routes(problem.base,domain))
    return output


def measure_routes(problem,dual,profile,domains,config,iteration=0,max_qubits=16):
    output=set(); logs=[]
    snapshot=hashlib.sha256(json.dumps(dual,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    for k,subset in enumerate(domains):
        domain=proxy_domain(problem,dual,profile,[(i,) for i in subset],config.slots)
        if len(domain.pricing.demand)*(config.slots-1)>max_qubits:
            raise ValueError('AOA_QUBIT_SAFETY_LIMIT')
        cfg=replace(config,solver_seed=config.solver_seed+100*iteration+k)
        result=PricingAOA(domain.pricing,domain.dual,cfg).run()
        routes={domain.expand(Route(tuple(r))).customers for r in result['routes']}
        output.update(routes)
        logs.append({'snapshot_hash':snapshot,'region':list(subset),'region_index':k,
                     'ledger_key':snapshot+':'+','.join(map(str,subset))+':singleton-v1',
                     'solver_seed':cfg.solver_seed,'result':result,'expanded_routes':sorted(routes)})
    return output,logs
