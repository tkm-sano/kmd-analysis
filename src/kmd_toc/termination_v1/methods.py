"""Whole-method finite-work execution; no elapsed-time decisions."""
from dataclasses import replace
import itertools
import math
import numpy as np
from kmd_toc.pipeline.classical import directed_cw
from kmd_toc.pipeline.completion import assemble
from .solvers import complete,routing_pool
from .work import key,verified


def generate(p,method,config,ledger,seeds):
    if method=='A':
        from kmd_toc.baseline_a.rule_v1 import generate as frozen_generate
        plan,diagnostic=frozen_generate(p,max_evaluations=config['A']['candidate_evaluations'])
        ledger.capture('A_diagnostic',diagnostic)
        ledger.emit('A_complete',reason=plan.method_settings['stop_reason'],
                    candidate_evaluations=plan.method_settings.get('candidate_evaluations'),
                    accepted_moves=plan.method_settings['accepted_moves'])
        return plan
    routes,info=directed_cw(p)
    ledger.count('CW_directed_savings',len(p.stops)*(len(p.stops)-1))
    ledger.emit('CW_complete',routes=len(routes),metadata=info)
    ledger.capture('directed_CW',{'routes':routes,'metadata':info})
    if method=='B':return complete(p,routes,'B',config,ledger,seeds['solver_seed'],info)
    if method=='C':
        incumbent=None
        from kmd_toc.pipeline.completion import greedy_assignment
        try:
            candidate=assemble(p,greedy_assignment(p,routes),'C',{'candidate_source':'shared_CW_incumbent'})
            if verified(p,candidate,ledger):incumbent=candidate
        except (ValueError,IndexError) as e:ledger.emit('C_seed_unavailable',error=str(e))
        routes,extra=routing_pool(p,routes,config,ledger,seeds['solver_seed']);info.update(extra)
        return complete(p,routes,'C',config,ledger,seeds['solver_seed'],info,incumbent=incumbent)
    if method not in ('D','D_CLASSICAL_REPLACEMENT'):raise ValueError('UNKNOWN_METHOD')
    return hybrid(p,routes,info,method,config,ledger,seeds)


def hybrid(p,routes,info,method,config,ledger,seeds):
    from kmd_toc.common.adapters import to_vehicle_day
    from kmd_toc.column_generation.models import Route
    from kmd_toc.vehicle_day.generation import make_day
    from .master import solve_master
    native_method='D' if method=='D' else 'B'
    seed_plan=complete(p,routes,native_method,config,ledger,seeds['solver_seed'],info)
    ledger.capture('seed_plan',seed_plan)
    day=to_vehicle_day(p,delta_s=1);id_index={j:i for i,j in enumerate(p.od.ids)};initial=[]
    for v in day.vehicles:
        trips=sorted((t for t in seed_plan.trips if t.vehicle_id==v.vehicle_id),key=lambda t:t.trip_no)
        if trips:initial.append(make_day(day,v.vehicle_id,
            tuple(Route(tuple(id_index[s.stop_id] for s in t.visits)) for t in trips),tuple(t.load_start_s for t in trips)))
    _,base=solve_master(p,day,routes,seed_plan,initial,config,ledger,'base_master')
    duals=base['LP']['dual_customer'] if base.get('LP',{}).get('success') else [0.]*len(p.stops)
    sampled=set();domain=set();quantum_summary=[]
    if method=='D':
        from kmd_toc.column_generation.reduction import contract
        from kmd_toc.column_generation.aoa import AOAConfig
        from .quantum import FinitePricingAOA
    for iteration in range(config['D']['pricing_rounds']):
        ledger.count('pricing_rounds')
        for ri,route in enumerate(routes):
            ledger.count('pricing_calls_attempted')
            call_id=f'round{iteration:02d}_route{ri:03d}'
            groups=tuple(tuple(int(i) for i in arr) for arr in np.array_split(np.array(route,dtype=int),
                        min(config['D']['macro_groups'],len(route))) if len(arr))
            exact={tuple(i for k in order for i in groups[k]) for order in itertools.permutations(range(len(groups)))}
            domain.update(exact)
            if method=='D_CLASSICAL_REPLACEMENT':
                # Each ordered macro permutation evaluated once per call, including duplicates across rounds.
                sampled.update(exact);ledger.count('classical_permutations_evaluated',math.factorial(len(groups)))
                ledger.capture(call_id,{'groups':groups,'routes':sorted(exact),'permutations':math.factorial(len(groups)),
                    'shots':0,'termination':'SEARCH_EXHAUSTED','scope':'same macro groups as D, exact permutation enumeration only'})
                ledger.emit('classical_pricing_complete',call_id=call_id,permutations=math.factorial(len(groups)))
                continue
            qseed=int(np.random.SeedSequence([seeds['quantum_seed'],iteration,ri]).generate_state(1)[0])
            ledger.emit('quantum_call_start',call_id=call_id,seed=qseed,groups=groups,
                        max_evaluations_per_restart=config['D']['max_evaluations'],total_starts=config['D']['restarts'])
            try:
                sub=contract(day.base,duals,groups,call_id,slots=len(groups)+1)
                cfg=AOAConfig(slots=len(groups)+1,solver_seed=qseed,
                    **{k:config['D'][k] for k in ('p','max_evaluations','restarts','train_shots','final_shots','tolerance','statevector_backend')})
                engine=FinitePricingAOA(sub.pricing,sub.dual,cfg,ledger,call_id)
                ledger.emit('quantum_problem',call_id=call_id,qubits=engine.q,one_hot_states=len(engine.assignments))
                result=engine.run();accepted=[]
                for small in result['routes']:
                    if len(small)==len(groups) and set(small)==set(range(1,len(groups)+1)):
                        full=sub.expand(Route(tuple(small))).customers;sampled.add(full);accepted.append(full)
                ledger.capture(call_id,{'seed':qseed,'groups':groups,'accepted_full_routes':accepted,'result':result})
                quantum_summary.append({'call_id':call_id,'seed':qseed,'qubits':engine.q,
                    'training_evaluations':sum(h['nfev'] for h in result['history']),
                    'training_shots':sum(h['nfev'] for h in result['history'])*cfg.train_shots,
                    'final_shots':result['measured_shots'],'accepted_full_routes':accepted})
                ledger.count('quantum_calls_completed');ledger.emit('quantum_call_end',call_id=call_id)
            except Exception as e:
                # One failed evaluation/call consumes its call; no unregistered retry.
                ledger.count('quantum_calls_failed')
                ledger.emit('quantum_call_failed',call_id=call_id,error=repr(e))
    pool=sorted(set(routes)|sampled)
    cols,solved=solve_master(p,day,pool,seed_plan,initial,config,ledger,'hybrid_master')
    best=seed_plan
    if solved.get('IP',{}).get('success'):
        vehicle_index={v.vehicle_id:i for i,v in enumerate(p.vehicles)}
        if config.get('operating_policy') == 'FCFS_v1':
            from kmd_toc.fcfs_v1.scheduler import schedule
            rows=solved['IP']['fcfs_assignments']
            proposed=schedule(p,{(r['vehicle_id'],r['trip_no']):tuple(r['route']) for r in rows},native_method,
                              {**solved['IP']['fcfs_settings'],'candidate_source':'finite_day_IP_FCFS'})
            items=None
        else:
            items=[{'v':vehicle_index[cols[i].vehicle_id],'trip_no':t.trip_id,'route':t.customers,'start_s':t.load_start_s}
                   for i in solved['IP']['selected'] for t in cols[i].trips]
        try:
            if items is not None:proposed=assemble(p,items,native_method,{'candidate_source':'finite_day_IP'})
            if verified(p,proposed,ledger) and key(proposed)<key(best):best=proposed
        except ValueError as e:ledger.emit('day_IP_rejected',error=str(e))
    metadata={**info,'algorithm':'finite_Huang_AOA_vehicle_day_master_shared_completion',
        'scope':'finite macro and fixed seed-calendar catalogue; assignment remains free among all vehicles',
        'classical_replacement':method=='D_CLASSICAL_REPLACEMENT','quantum_enabled':method=='D',
        'quantum_calls':quantum_summary,'macro_domain_size':len(domain),'candidate_routes':len(pool),
        'sampling_new_routes':len(sampled-set(routes)),'final_candidate_source_before_CP':best.method_settings.get('candidate_source',best.method_settings.get('completion_selected_source')),
        'quantum_improvement_claim':False}
    if config.get('operating_policy') == 'FCFS_v1':
        metadata.update(algorithm=metadata['algorithm']+'_FCFS_v1',
            scope='same_finite_macro_routes; distance_pricing_LP_surrogate; joint_FCFS_route_pool_CP_completion')
    result=complete(p,pool,native_method,config,ledger,seeds['solver_seed'],metadata,incumbent=best)
    final_routes={tuple(id_index[v.stop_id] for v in t.visits) for t in result.trips}
    return replace(result,execution_kind='quantum_circuit_simulator' if method=='D' else 'classical',
                   method_settings={**result.method_settings,'new_pricing_routes_in_final':len(final_routes&(sampled-set(routes)))})
