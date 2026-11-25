"""Versioned common completion boundary; Q assignments cannot be re-optimized."""
from .cp import complete


def complete_supplied_routes(p,routes,method,config,ledger,seed,*,pinned_assignments=None):
    if method in ('Q','D') and pinned_assignments is None:
        raise ValueError('QUANTUM_ASSIGNMENT_MUST_BE_EXPLICITLY_PINNED')
    return complete(p,routes,method,config,ledger,seed,pinned_assignments=pinned_assignments)
