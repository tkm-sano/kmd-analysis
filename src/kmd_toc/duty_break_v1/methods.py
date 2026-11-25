"""Existing B/C route algorithms, common new completion; no Q replacement."""
from .cp import complete
from .validation import require_valid


def generate(p,method,config,ledger,seeds):
    p.validate_duty()
    if method not in ('B','C'):
        raise ValueError('A_EXTERNAL_Q_REQUIRES_MEASURED_PINNED_DECISION_NO_CLASSICAL_SUBSTITUTION')
    if p.experiment.kind!='synthetic_validation' or len(p.stops)>12:
        raise ValueError('GENERATION_SMALL_SYNTHETIC_ONLY_USE_SAVED_SCALE_REPLAY')
    from kmd_toc.pipeline.classical import directed_cw
    from kmd_toc.termination_v1.solvers import routing_pool
    routes,settings=directed_cw(p);incumbent=None
    if method=='C':
        from kmd_toc.pipeline.completion import greedy_assignment
        from .scheduler import schedule
        try:
            assigned={(p.vehicles[i['v']].vehicle_id,i['trip_no']):tuple(p.od.ids[j] for j in i['route'])
                      for i in greedy_assignment(p,routes)}
            incumbent=schedule(p,assigned,'C',{'candidate_source':'shared_CW_duty_incumbent'})
        except (ValueError,IndexError) as error:ledger.emit('C_duty_seed_unavailable',reason=str(error))
        routes,extra=routing_pool(p,routes,config,ledger,seeds['solver_seed']);settings.update(extra)
    plan=complete(p,routes,method,config,ledger,seeds['solver_seed'],settings,incumbent=incumbent)
    require_valid(p,plan)
    return plan
