"""New local-Q completion version; leave hash-pinned historical pilots intact."""
from kmd_toc.d_local_design.completion import pinned_routes, preserves
from .scheduler import schedule
from .validation import require_fcfs


def complete(p, original, local, decision):
    require_fcfs(p,original)
    result=schedule(p,pinned_routes(original,local,decision),'D',
                    {'purpose':'local_Q_FCFS_v1','quantum_origin':'caller-supplied measured decision',
                     'source_plan_id':original.plan_id})
    if not preserves(result,local,decision,original):
        raise ValueError('FCFS_COMPLETION_CHANGED_QUANTUM_ASSIGNMENT_OR_ORDER')
    return result


def evaluate(p,original,local,decision):
    """Reuse the existing D/W Pareto rule; do not decide a new search objective."""
    from kmd_toc.d_local_design.completion import evaluate as historical_gateway
    require_fcfs(p,original)
    selected,ledger=historical_gateway(p,original,local,decision,completer=complete)
    require_fcfs(p,selected)
    return selected,{**ledger,'operating_policy':'FCFS_v1'}
