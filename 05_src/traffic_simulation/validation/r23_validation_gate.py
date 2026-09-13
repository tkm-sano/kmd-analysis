"""Evidence-derived validation gates. Empty, unexecuted or incomplete checks never pass."""
from __future__ import annotations
import math

def numerical_comparison(observed, expected, tolerance=1e-12):
    if tolerance != 1e-12:
        raise ValueError("R23 tolerance is fixed at 1e-12")
    return (isinstance(observed,(int,float)) and isinstance(expected,(int,float))
            and math.isfinite(observed) and math.isfinite(expected) and abs(observed-expected)<=tolerance)

def evaluate_gate(records, required_ids):
    required=set(required_ids)
    ids=[r.get("test_id") for r in records]
    complete=bool(required) and len(ids)==len(set(ids)) and set(ids)==required
    verified=complete and all(r.get("executed") is True and r.get("result")=="VERIFIED"
                             and r.get("checks") and all(c.get("passed") is True for c in r["checks"])
                             and bool(r.get("evidence")) for r in records)
    return {"result":"VERIFIED" if verified else "PARTIAL", "passed":bool(verified),
            "missing_ids":sorted(required-set(ids)), "required_count":len(required), "executed_count":sum(r.get("executed") is True for r in records)}
