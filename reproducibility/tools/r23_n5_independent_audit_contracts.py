"""Supplemental audit-only counterexamples and independence checks, no pytest needed."""
from __future__ import annotations
import dataclasses
import importlib.util
import json
from pathlib import Path
import sys
import types
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reproducibility/outputs/traffic_simulation/r23_n5_runtime_optimization_code_audit/20260913_v2_independent'
sys.path.insert(0,str(ROOT/'05_src'))
from traffic_simulation.r23_qaoa_aer import metrics, qaoa, optimized_metrics_v4 as candidate
from traffic_simulation.r23_qaoa_aer.schema import R23Input

def main():
    assert not (OUT/'independent_seal.json').exists()
    ids=('A','B'); bits1=(1,0,0,1); bits2=(0,1,1,0)
    # Lower-cost route has lower probability. Costs chosen independently of candidate.
    matrix={'D':{'D':0.,'A':1.,'B':2.},'A':{'D':2.,'A':0.,'B':1.},'B':{'D':1.,'A':2.,'B':0.}}
    inp=R23Input('audit_fixture',2,ids,'D',0.,{}, {},'audit','audit',4.,3.,frozenset({bits1}),frozenset(),frozenset(),matrix,{})
    data=np.zeros(16,dtype=np.complex128);data[9]=.5;data[6]=np.sqrt(.75)
    state=types.SimpleNamespace(data=data)
    low=qaoa._v4_reporting_metrics(state,inp,1e-12)
    assert low['best_feasible_state']['record']['route']==['A','B']
    assert low['best_feasible_state']['normalized_route_objective']==3.
    changed=qaoa._v4_reporting_metrics(state,dataclasses.replace(inp,exact_optimal_bitstrings=frozenset({bits2})),1e-12)
    assert changed['best_feasible_state']==low['best_feasible_state']
    assert low['P_opt']==.25 and abs(changed['P_opt']-.75)<1e-12
    tie_matrix={a:{b:float(a!=b) for b in ('D','A','B')} for a in ('D','A','B')}
    tied=dataclasses.replace(inp,normalized_matrix=tie_matrix)
    original=metrics.probability_metrics({format(i,'04b'):float(abs(a)**2) for i,a in enumerate(data)},tied)
    actual=qaoa._v4_reporting_metrics(state,tied,1e-12)
    assert actual['best_feasible_state']['record']['route']==original['best_feasible_state']['record']['route']==['B','A']
    # Math-fixture expected quantities above stay fixed: demonstrate assertion can reject a corrupt output.
    detected=False
    corrupted=dict(low,P_opt=0.)
    try:assert corrupted['P_opt']==.25
    except AssertionError:detected=True
    assert detected
    # All-finite amplitudes that do not represent a unit state already reject in original.
    cases=[]
    for dtype in (np.float32,np.complex64,np.float64,np.complex128):
        v=np.arange(1,17,dtype=np.float64);v/=np.linalg.norm(v);v=v.astype(dtype)
        result=candidate.indexed_probability_metrics(v,ids,(bits1,),2)
        reference=float(np.vdot(v.astype(np.complex128),v.astype(np.complex128)).real)
        cases.append({'dtype':str(v.dtype),'candidate_total':result['probability_total'],'float64_reference_for_same_input':reference,'difference':abs(result['probability_total']-reference)})
    report={'best_route_minimizes_cost_not_probability':'PASS','exact_reference_changes_only_optimal_mass':'PASS',
        'equal_cost_tie_order_matches_original':'PASS','deliberately_corrupted_P_opt_assertion_rejected':detected,'precision_cases':cases,
        'pytest_attempt':{'command':'frozen Python -m pytest -q -p no:cacheprovider test_r23_optimized_metrics_v4_contract.py test_r23_qaoa_aer.py',
            'exit_code':1,'reason':'No module named pytest in frozen authority environment','environment_modified':False,
            'fallback':'Direct assertion-based audit scripts use exact frozen scientific dependencies; pytest suite not claimed as run.'}}
    (OUT/'supplemental_contract_probes.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))

if __name__=='__main__':main()
