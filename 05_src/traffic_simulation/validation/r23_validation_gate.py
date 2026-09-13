"""Evidence-derived validation gates. Empty, unexecuted or incomplete checks never pass."""
from __future__ import annotations
import math

STATUSES = frozenset({'VERIFIED', 'FAILED', 'PARTIAL', 'NOT_TESTED', 'BLOCKED'})

def aggregate_checks(checks):
    """Required checks only: FAILED > BLOCKED > incomplete; optional outcomes stay visible."""
    if not checks:
        return 'NOT_TESTED'
    if any(c.get('result') not in STATUSES or c.get('required') not in ('REQUIRED','OPTIONAL','NOT_APPLICABLE') for c in checks):
        return 'FAILED'
    required = [c['result'] for c in checks if c['required']=='REQUIRED']
    if not required:
        return 'PARTIAL'
    if 'FAILED' in required:
        return 'FAILED'
    if 'BLOCKED' in required:
        return 'BLOCKED'
    if all(s=='VERIFIED' for s in required):
        return 'VERIFIED'
    if all(s=='NOT_TESTED' for s in required):
        return 'NOT_TESTED'
    return 'PARTIAL'

def numerical_comparison(observed, expected, tolerance=1e-12):
    if tolerance != 1e-12:
        raise ValueError("R23 tolerance is fixed at 1e-12")
    return (isinstance(observed,(int,float)) and isinstance(expected,(int,float))
            and math.isfinite(observed) and math.isfinite(expected) and abs(observed-expected)<=tolerance)

def evaluate_gate(records, required_ids):
    required=set(required_ids)
    ids=[r.get("test_id") for r in records]
    if not required:
        status='NOT_TESTED'
    elif len(required)!=len(required_ids) or len(ids)!=len(set(ids)) or set(ids)-required:
        status='FAILED'
    elif required-set(ids):
        status='BLOCKED'
    else:
        checks=[]
        for r in records:
            if r.get('executed') is not True:state='NOT_TESTED'
            elif not r.get('checks') or not r.get('evidence'):state='BLOCKED'
            elif any(c.get('passed') is not True for c in r['checks']):state='FAILED'
            elif r.get('result')=='VERIFIED':state='VERIFIED'
            else:state='PARTIAL'
            checks.append({'required':'REQUIRED','result':state})
        status=aggregate_checks(checks)
    return {"result":status, "passed":status=='VERIFIED',
            "missing_ids":sorted(required-set(ids)), "required_count":len(required), "executed_count":sum(r.get("executed") is True for r in records)}
