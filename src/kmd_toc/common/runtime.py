"""End-to-end measured boundary: before input load through final validation."""
from dataclasses import asdict
import platform
import sys
import time
from .validation import validate_plan
from .models import Plan


def environment():
    return {'python':sys.version, 'platform':platform.platform(), 'processor':platform.processor(),
            'timer':'time.perf_counter; elapsed wall seconds'}


def run_measured(load_input, create_plan, *, clock=time.perf_counter, validator=validate_plan):
    """create_plan(problem, mark) includes ALL method-specific work and tuning.

    The complete common input/OD load must occur in load_input, never beforehand.
    No optimizer is selected or executed by this module itself.
    """
    start = clock()
    events = [{'name':'input_load_start','elapsed_s':0.0}]
    def mark(name):
        events.append({'name':name,'elapsed_s':clock()-start})
    plan = report = None
    status, error = 'ERROR', None
    try:
        problem = load_input()
        problem.validate()
        mark('input_load_end')
        candidate = create_plan(problem, mark)
        if not isinstance(candidate,Plan):
            raise ValueError('METHOD_DID_NOT_RETURN_PLAN')
        plan = candidate
        mark('method_all_processing_end')
        mark('independent_validation_start')
        report = validator(problem, plan)
        mark('independent_validation_end')
        status = 'FEASIBLE' if report.feasible else 'INFEASIBLE_PLAN'
    except Exception as exc:
        error = {'type':type(exc).__name__, 'message':str(exc)}
        status = 'INPUT_HOLD' if not any(e['name']=='input_load_end' for e in events) else 'ERROR'
        mark('failed')
    elapsed = events[-1]['elapsed_s']
    return {'schema_version':'1.0','status':status,'plan':asdict(plan) if plan is not None else None,
            'validation':report.as_dict() if report is not None else None,
            'D_km':report.D_km if report else None,'W_min':report.W_min if report else None,
            'T_s':elapsed if status == 'FEASIBLE' else None,'elapsed_wall_s':elapsed,
            'timing_events':events,'environment':environment(),'error':error,
            'common_road_OD_preprocessing_in_T':False}
