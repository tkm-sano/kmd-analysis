"""Research-only D variant: fresh duals, singleton domains, true complete-day RC.
Uses the existing common input, initial CW, completion, day contracts and validators.
The domain/calendar are finite; no exhaustive routes or B/C plans are injected.
"""
from adapters import *
from dataclasses import replace
from kmd_toc.pipeline.hybrid import EventDayMaster,day_candidates
from kmd_toc.pipeline.completion import assemble
from kmd_toc.pipeline.classical import directed_cw
from kmd_toc.common.adapters import to_vehicle_day
from kmd_toc.vehicle_day.generation import make_day
from kmd_toc.column_generation.reduction import contract
from kmd_toc.dwt.methods import complete,verify_candidate
from scipy.optimize import linprog

class AuditedMaster(EventDayMaster):
    def lp(self,indices,primary='D',limit=None):
        a,b,rhs,cost=self.arrays(indices,primary,limit)
        r=linprog(cost,A_eq=a,b_eq=np.ones(self.n),A_ub=b,b_ub=rhs,bounds=(0,None),method='highs',options={'threads':1,'time_limit':5.})
        if not r.success:raise ValueError('TRIAL_RMP_FAILED:'+r.message)
        y=np.r_[r.eqlin.marginals,r.ineqlin.marginals[:len(self.rhs)]]
        eps=float(r.ineqlin.marginals[-1]) if limit is not None else 0.
        rc=self.d-np.asarray(self.a.T@y).ravel()-eps*self.w
        assert np.allclose(rc[indices],r.lower.marginals,atol=1e-7)
        assert abs(r.fun-(r.eqlin.marginals.sum()+r.ineqlin.marginals@rhs))<1e-7
        return {'success':True,'objective':float(r.fun),'dual_customer':r.eqlin.marginals.tolist(),
                'dual_resources':r.ineqlin.marginals[:len(self.rhs)].tolist(),'epsilon_dual':eps,
                'resource_rhs':self.rhs.tolist(),'event_intervals':self.intervals,'rc':rc.tolist()}


def generate_updated(p,method,epsilon,budget,seeds,config):
    assert method=='D'
    from kmd_toc.column_generation.aoa import PricingAOA
    routes,info=directed_cw(p)
    budget.capture('directed_CW',{'routes':routes,'metadata':info})
    seed=complete(p,routes,'D',epsilon,budget,seeds['solver_seed'],info,cap=budget.seconds*config['allocation']['D_seed_fraction'])
    day=to_vehicle_day(p,delta_s=1);ids={s:i for i,s in enumerate(p.od.ids)}
    initial=[]
    for v in day.vehicles:
        trips=sorted((t for t in seed.trips if t.vehicle_id==v.vehicle_id),key=lambda t:t.trip_no)
        if trips:initial.append(make_day(day,v.vehicle_id,tuple(Route(tuple(ids[s.stop_id] for s in t.visits)) for t in trips),tuple(t.load_start_s for t in trips)))
    pool={c.column_id:c for c in initial};quantum=[];trace=[];route_pool=set(routes);added_count=0;updates=0;all_sets={frozenset(r) for r in routes}
    generated=set();best=seed
    for iteration in range(config['trial_cg']['max_rounds']):
        budget.left()
        master=AuditedMaster(day,list(pool.values()),native_threads=1);lp=master.lp(list(range(len(pool))),'D',epsilon)
        top=sorted(day.base.customers,key=lambda i:(-lp['dual_customer'][i-1],i))[:3]
        anchor=day.base.customers[iteration%len(day.base.customers)]
        near=sorted(day.base.customers,key=lambda i:(day.base.distance[anchor,i],i))[:3]
        sets=[]
        for subset in [top,near]:
            if set(subset) not in [set(s) for s in sets]:sets.append(subset)
        required=set();proxy=[]
        for di,subset in enumerate(sets):
            budget.left()
            domain=contract(day.base,lp['dual_customer'],[(i,) for i in subset],f'cg_{iteration}_{di}',slots=3)
            qseed=int(np.random.SeedSequence([seeds['quantum_seed'],iteration,di]).generate_state(1)[0])
            cfg=AOAConfig(slots=3,**{k:config['D'][k] for k in ['p','max_evaluations','restarts','train_shots','final_shots']},solver_seed=qseed)
            engine=PricingAOA(domain.pricing,domain.dual,cfg);result=engine.run()
            expanded={domain.expand(Route(tuple(r))).customers for r in result['routes']}
            required.update(expanded);generated.update(expanded)
            proxy.extend({'route':r,'proxy_rc':float(sum(day.base.distance[a,b] for a,b in zip((0,*r),( *r,0)))-sum(lp['dual_customer'][i-1] for i in r))} for r in sorted(expanded))
            log={'iteration':iteration,'domain':subset,'quantum_seed':qseed,'full_routes':sorted(expanded),
                 'training_total_shots':sum(h['nfev'] for h in result['history'])*cfg.train_shots,'final_total_shots':result['measured_shots'],
                 'result':result,'fragment_groups':[(i,) for i in subset]}
            quantum.append(log);budget.capture(f'D_AOA_{iteration}_{di}',log)
        possible=day_candidates(day,route_pool|required,seed,p)
        possible=[c for c in possible if any(t.customers in required for t in c.trips)]
        assert len(possible)<=10000,'FINITE_CATALOGUE_RESOURCE_GUARD'
        catalogue={**pool,**{c.column_id:c for c in possible}}
        columns=list(catalogue.values());index={c.column_id:i for i,c in enumerate(columns)}
        m=AuditedMaster(day,columns,native_threads=1);before=m.lp([index[k] for k in pool],'D',epsilon)
        assert np.isclose(before['objective'],lp['objective'],atol=1e-7)
        negative=sorted((i for i,c in enumerate(columns) if c.column_id not in pool and before['rc'][i]<-1e-7),key=lambda i:(before['rc'][i],columns[i].column_id))
        accepted=negative[:config['trial_cg']['batch_size']]
        added=[columns[i] for i in accepted];pool.update((c.column_id,c) for c in added)
        added_count+=len(added)
        for c in added:route_pool.update(t.customers for t in c.trips)
        # Mandatory fresh solve after addition, before the next Pricing round.
        after=m.lp([index[k] for k in pool],'D',epsilon);updates+=bool(added)
        trace.append({'iteration':iteration,'LP_before':lp,'LP_candidates_same_RMP':before,'LP_after_addition':after,
                      'proxy_route_rc':proxy,'new_negative_count':len(negative),'added':[(columns[i].column_id,before['rc'][i]) for i in accepted],
                      'candidate_true_rc':[{'column_id':c.column_id,'vehicle':c.vehicle_id,'trips':[t.customers for t in c.trips],'RC':before['rc'][i]} for i,c in enumerate(columns)],
                      'customer_dual_changed':not np.allclose(lp['dual_customer'],after['dual_customer'],atol=1e-10),
                      'full_dual_changed':lp['dual_resources']!=after['dual_resources'] or lp['dual_customer']!=after['dual_customer']})
        budget.capture(f'D_CG_round_{iteration}',trace[-1])
        if not added:break
    final_master=AuditedMaster(day,list(pool.values()),native_threads=1)
    final_lp=final_master.lp(list(range(len(pool))),'D',epsilon)
    ip=final_master.ip(list(range(len(pool))),'D',epsilon,seconds=min(5.,budget.left()))
    if ip['success']:
        columns=final_master.columns;vi={v.vehicle_id:i for i,v in enumerate(p.vehicles)}
        items=[{'v':vi[columns[i].vehicle_id],'trip_no':t.trip_id,'route':t.customers,'start_s':t.load_start_s} for i in ip['selected'] for t in columns[i].trips]
        candidate=assemble(p,items,'D',{'candidate_source':'updated_dual_trial_IP'})
        if verify_candidate(p,candidate,epsilon,budget):
            if (sum(t.distance_m for t in candidate.trips),sum(t.waiting_s for t in candidate.trips))<(sum(t.distance_m for t in best.trips),sum(t.waiting_s for t in best.trips)):best=candidate
    meta={**info,'algorithm':'TRIAL_updated_dual_singleton_CG','quantum':quantum,'quantum_calls':len(quantum),
          'CG_trace':trace,'RMP_addition_updates':updates,'added_valid_columns':added_count,'final_LP':final_lp,'IP':ip,
          'accepted_distinct_routes':len(generated),'changed_customer_set_routes':sum(frozenset(r) not in all_sets for r in generated),
          'proxy_is_not_full_day_RC':True,'scope':'finite singleton domains and seed calendars; no global Pricing certificate'}
    final=complete(p,sorted(route_pool),'D',epsilon,budget,seeds['solver_seed'],meta,incumbent=best)
    return replace(final,method_settings={**final.method_settings,**meta},execution_kind='quantum_circuit_simulator')
