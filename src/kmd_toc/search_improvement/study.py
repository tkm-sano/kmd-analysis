"""Controlled pricing snapshots, CG and classical integer-pool enrichment.

All diagnostic full-domain values are separated from candidate generation.
AOA never uses an oracle fallback. Full catalogue is artificial-only required
preprocessing in this implementation, counted separately in cold timing.
"""
from itertools import combinations
from time import perf_counter
import numpy as np
from kmd_toc.vehicle_day.generation import seed_plan
from kmd_toc.vehicle_day.model import ObjectiveProfile
from .regions import legacy_regions, expanded_regions, exact_routes, measure_routes

TOL=1e-7


def pool_from_saved(master,saved):
    ids={c.column_id for c in seed_plan(master.problem)}
    ids.update(x['column_id'] for t in saved['trace'] for x in t['added'])
    return sorted(master.index[x] for x in ids)


def coverage(master,pool,dual,profile,domains,sampled,batch_size=20):
    """Column counts and shot counts use separate units; undefined rates are null."""
    rc=master.rc(dual,profile); negative=set(np.flatnonzero(rc < -TOL).tolist())
    known=master.known(pool)
    theoretical=master.complete(exact_routes(master.problem,dual,profile,domains),known)
    actual=master.complete(sampled,known)
    if not actual<=theoretical: raise RuntimeError('MEASUREMENT_OUTSIDE_DECLARED_SCOPE')
    scoped=negative&theoretical; got=negative&actual
    fresh=got-set(pool)
    ranked=sorted(fresh,key=lambda i:(rc[i],master.ids[i]))
    best_global=float(np.min(rc)) if len(rc) else None
    best_actual=float(min(rc[i] for i in actual)) if actual else None
    return {'global_negative_count':len(negative),'scope_negative_count':len(scoped),
            'obtained_negative_count':len(got),'outside_scope_negative_count':len(negative-scoped),
            'measurement_missed_negative_count':len(scoped-got),
            'completion_lost_valid_columns':0,'invalid_completed_columns':0,
            'duplicate_existing_negative_count':len(got&set(pool)),
            'batch_excluded_negative_count':max(0,len(fresh)-batch_size),
            'candidate_coverage':len(scoped)/len(negative) if negative else None,
            'acquisition_rate':len(got)/len(scoped) if scoped else None,
            'global_min_rc':best_global,'obtained_min_rc':best_actual,
            'minimum_rc_gap':best_actual-best_global if best_actual is not None else None,
            'global_best_obtained':bool(any(abs(rc[i]-best_global)<TOL for i in actual)),
            'scope_size':len(theoretical),'actual_completed_size':len(actual),
            'added_indices':ranked[:batch_size],
            'negative_examples_outside_scope':[master.ids[i] for i in sorted(negative-scoped)[:5]]}


def run_search(master,profile,config,mode='aoa',max_rounds=40,batch_size=20,max_calls=800):
    if mode not in ('aoa','same_scope_classical','full_classical'):
        raise ValueError('INVALID_SEARCH_MODE')
    started=perf_counter(); diagnostic_s=0.; calls=0; quantum_s=0.; lp_s=0.; trace=[]
    pool=[master.index[c.column_id] for c in seed_plan(master.problem)]
    if profile.other_limit is not None and sum(profile.other(master.columns[i]) for i in pool)>profile.other_limit+TOL:
        pool=[]
    phase='I'; stop='CG_ROUND_SAFETY_LIMIT'
    for iteration in range(max_rounds):
        lp=master.lp(pool,profile,phase); lp_s+=lp.get('seconds',0.)
        if not lp['success']: stop=lp['reason']; break
        if phase=='I' and lp['artificial_sum']<=TOL:
            phase='II'; lp=master.lp(pool,profile,phase); lp_s+=lp['seconds']
        dual=lp['dual']; domains=expanded_regions(master.problem,dual,iteration)
        logs=[]
        if mode=='aoa':
            if calls+len(domains)>max_calls: stop='AOA_CALL_SAFETY_LIMIT'; break
            begin=perf_counter()
            sampled,logs=measure_routes(master.problem,dual,profile,domains,config,iteration)
            quantum_s+=perf_counter()-begin; calls+=len(domains)
        else:
            sampled=exact_routes(master.problem,dual,profile,domains,config.slots)
        ds=perf_counter()
        record=coverage(master,pool,dual,profile,domains,sampled,batch_size)
        diagnostic_s+=perf_counter()-ds
        # Calculate actual selected candidates independently of diagnostic oracle.
        rc=master.rc(dual,profile)
        candidates=set(range(len(master.columns))) if mode=='full_classical' else master.complete(sampled,master.known(pool))
        new=sorted((i for i in candidates-set(pool) if rc[i]<-TOL),key=lambda i:(rc[i],master.ids[i]))[:batch_size]
        trace.append({'iteration':iteration,'lp':lp,'domains':domains,'coverage':record,
                      'quantum':logs,'added_indices':new,'added_ids':[master.ids[i] for i in new]})
        if not new:
            stop='FULL_GLOBAL_PRICING_CERTIFIED' if mode=='full_classical' else 'DEFINED_DOMAINS_EXHAUSTED_NO_NEW_NEGATIVE'
            break
        pool.extend(new)
    lp=master.lp(pool,profile,phase)
    ip=master.ip(pool,profile) if phase=='II' else {'success':False,'reason':'PHASE_I_NOT_CLOSED'}
    if lp['success']:
        ds=perf_counter(); minimum=float(np.min(master.rc(lp['dual'],profile))); diagnostic_s+=perf_counter()-ds
    else: minimum=None
    return {'mode':mode,'profile':vars(profile),'pool':pool,'trace':trace,'stop':stop,
            'lp':lp,'ip':ip,'final_global_min_rc_diagnostic':minimum,
            'aoa_calls':calls,'aoa_seconds':quantum_s,'lp_seconds':lp_s,
            'warm_method_seconds':perf_counter()-started-diagnostic_s,'diagnostic_seconds':diagnostic_s,
            'total_seconds':perf_counter()-started,'oracle_fallback_used':False}


def zero_face(master,pool,profile):
    started=perf_counter(); lp=master.lp(pool,profile)
    if not lp['success']: return {'success':False,'reason':'NO_FEASIBLE_RMP','seconds':perf_counter()-started}
    rc=master.rc(lp['dual'],profile)
    zero=set(np.flatnonzero(np.abs(rc)<=TOL).tolist())
    enriched=sorted(set(pool)|zero)
    ip=master.ip(enriched,profile)
    return {'success':ip['success'],'pool':enriched,'added':len(set(enriched)-set(pool)),
            'ip':ip,'seconds':perf_counter()-started,'attribution':'CLASSICAL_ZERO_FACE_ENUMERATION',
            'negative_columns_not_inserted':int(np.sum(rc < -TOL))}


def incumbent_repair(master,pool,profile,max_free=2):
    """Exact finite-catalogue one/two-vehicle replacement; classical attribution.

    Fix other incumbent columns by restricting their vehicles to that one column;
    whole equality/berth/epsilon constraints then account for residual resources.
    With F=2,max_free=2 this is the entire full IP, explicitly not scalable proof.
    """
    started=perf_counter(); initial=master.ip(pool,profile)
    if not initial['success']: return {'success':False,'ip':initial,'seconds':perf_counter()-started}
    best=initial; trials=[]; eligible_added=set(); ids=[v.vehicle_id for v in master.problem.vehicles]
    selected={master.columns[i].vehicle_id:i for i in initial['selected_indices']}
    for count in range(1,min(max_free,len(ids))+1):
        for free in combinations(ids,count):
            fixed=[i for v,i in selected.items() if v not in free]
            customers={i for j in fixed for i in master.columns[j].customers}
            eligible=fixed+[j for j,c in enumerate(master.columns) if c.vehicle_id in free and not set(c.customers)&customers]
            solved=master.ip(eligible,profile)
            trials.append({'free_vehicles':free,'eligible_count':len(eligible),'result':solved})
            if solved['success'] and solved['objective']<best['objective']-TOL:
                best=solved
            eligible_added.update(set(solved.get('selected_indices',()))-set(pool))
    return {'success':best['success'],'ip':best,'added_selected':len(eligible_added),'trials':trials,
            'seconds':perf_counter()-started,'attribution':'CLASSICAL_INCUMBENT_VEHICLE_REPAIR',
            'full_problem_when_two_vehicles':len(ids)<=max_free}


def nondominated(points):
    points=set(tuple(p) for p in points)
    return sorted(p for p in points if not any(q[0]<=p[0]+TOL and q[1]<=p[1]+TOL and
                  (q[0]<p[0]-TOL or q[1]<p[1]-TOL) for q in points))
