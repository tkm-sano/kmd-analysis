"""Strict current FCFS eligibility and unchanged D / total loading-W definitions."""
from .validation import require_fcfs


def evaluate(problem,plan,*,planning_time_s=None):
    from kmd_toc.cargo_wait_v2.evaluation import evaluate as evaluate_ledger
    check=require_fcfs(problem,plan)
    report=evaluate_ledger(problem,plan,planning_time_s=planning_time_s)
    # With the existing no-destination-wait condition, keep both diagnostics,
    # but the v1 research W is ALWAYS the sum of loading starts minus readiness.
    if report['loading_W_min']!=check['W_loading_min']:
        raise ValueError('FCFS_W_GATEWAYS_DISAGREE')
    return {**report,'operating_policy':'FCFS_v1','W_min':check['W_loading_min'],
            'source_plan_operating_policy':plan.method_settings.get('operating_policy','historical_unversioned'),
            'source_plan_treatment':plan.method_settings.get('conversion','original_generation'),
            'primary_W_definition':'total_loading_wait_min','fcfs':check,
            'main_experiment':'HOLD','I_dual_implementation':'UNCHANGED_NOT_IMPLEMENTED_BY_THIS_TASK'}
