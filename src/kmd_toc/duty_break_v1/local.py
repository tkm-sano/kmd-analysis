"""Quantum decision -> pinned routes -> common duty completion, no replacement."""
from fractions import Fraction
from kmd_toc.d_local_design.completion import pinned_routes,preserves
from .scheduler import schedule
from .validation import require_valid


def metrics(p,plan):
    index={s:i for i,s in enumerate(p.od.ids)};distance=Fraction(0)
    for t in plan.trips:
        nodes=(p.depot.depot_id,*(v.stop_id for v in t.visits),p.depot.depot_id)
        distance+=sum((Fraction(str(float(p.od.distance_m[index[a],index[b]])))
                       for a,b in zip(nodes,nodes[1:])),Fraction(0))
    return distance/1000,Fraction(sum(t.load_start_s-t.ready_s for t in plan.trips),60)


def complete(p,original,local,decision,*,quantum_provenance):
    require_valid(p,original)
    if (local.plan_reference.get('problem_hash')!=p.fingerprint or
            local.plan_reference.get('od_hash')!=p.od.fingerprint or
            local.plan_reference.get('plan_id')!=original.plan_id):
        raise ValueError('QUANTUM_LOCAL_STALE_INPUT')
    if not isinstance(quantum_provenance,dict) or not quantum_provenance:
        raise ValueError('EXPLICIT_QUANTUM_PROVENANCE_REQUIRED')
    result=schedule(p,pinned_routes(original,local,decision),'D',
                    {'purpose':'pinned_quantum_decision_duty_completion','quantum_provenance':quantum_provenance,
                     'source_plan_id':original.plan_id})
    if not preserves(result,local,decision,original):
        raise ValueError('DUTY_COMPLETION_CHANGED_QUANTUM_ASSIGNMENT_OR_ORDER')
    require_valid(p,result)
    return result


def evaluate(p,original,local,decision,*,quantum_provenance):
    require_valid(p,original)
    try:
        proposal=complete(p,original,local,decision,quantum_provenance=quantum_provenance)
    except ValueError as error:
        # Ordinary infeasible quantum proposals never discard a valid incumbent
        # and never get repaired/reassigned by a classical route optimizer.
        require_valid(p,original)
        return original,{'status':'REJECT_DUTY_COMPLETION','reason':str(error),
                         'delta_D_km':None,'delta_W_total_min':None,
                         'invalid_candidate_never_adopted':True,
                         'quantum_decision_used_as_classical_seed':False,
                         'final_four_branch_selection':'separate_I_dual_rule_not_called_here'}
    old,new=metrics(p,original),metrics(p,proposal)
    accept=new[0]<=old[0] and new[1]<=old[1] and new!=old
    return (proposal if accept else original),{'status':'ACCEPT' if accept else 'KEEP_INCUMBENT',
        'delta_D_km':float(new[0]-old[0]),'delta_W_total_min':float(new[1]-old[1]),
        'quantum_assignment_and_order_preserved':True,
        'local_acceptance':'both nonworsening, at least one strict; no tolerance',
        'final_four_branch_selection':'separate_I_dual_rule_not_called_here'}
