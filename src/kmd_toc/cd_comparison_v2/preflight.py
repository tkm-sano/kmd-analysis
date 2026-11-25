"""Read-only existing S1/S2/S3 input and saved-plan applicability smoke."""
from pathlib import Path
import json,time
from kmd_toc.common_initial_v1.plans import dump,sha
from kmd_toc.nkr_unlimited.common import problem,checked,load_plan,INPUTS
from kmd_toc.objective_alignment_v1.objective import exact_units,ObjectiveHold
from kmd_toc.common_initial_v1.engines import slot_routes
from .local import prepare
ROOT=Path(__file__).resolve().parents[3]

def run(output):
    out=Path(output);out.mkdir(parents=True,exist_ok=False);rows=[]
    for s,N,V,B in [('S1',1000,10,2),('S2',2000,20,4),('S3',4000,40,8)]:
        begin=time.perf_counter();p=problem(s);assert (len(p.stops),len(p.vehicles),len(p.berths))==(N,V,B)
        path=ROOT/'output/nkr_unlimited_20261121_v1/baselines'/s/'plan.json'
        plan=load_plan(path);m,validation=checked(p,plan);case=prepare(p,plan,12,22112201)
        units=None;hold=None
        try:
            u=exact_units(p,[r for r in slot_routes(p,plan) if r],plan)
            units=dict(scale_per_m=u.scale_per_m,integer_activity_bound=u.objective_bound)
        except ObjectiveHold as e:hold=str(e)
        row=dict(scale=s,input_directory=str(INPUTS/s),problem_hash=p.fingerprint,od_hash=p.od.fingerprint,
            baseline_plan_sha256=sha(path),role='old saved B fixed-route duty replay ONLY, not new B-generated trial',
            N=N,V=V,berths=B,model_feasible=validation['model_feasible'],D=float(m.D),W=float(m.W),
            stopping_site=validation['stopping_site_feasibility'],local_n12_initialization=case is not None,
            exact_CP_initial_pool_units=units,exact_CP_hold=hold,wall_s=time.perf_counter()-begin,
            optimization_or_quantum_executed=False,new_outer_trials=0,full_new_method_application='HOLD')
        rows.append(row);dump(out/f'{s}.json',row)
    result=dict(status='PASS_INPUT_AND_SAVED_PLAN_PREFLIGHT',scales=rows,main_experiment='HOLD',
        scope='no B generation, Routing, CP solve, LP solve, QAOA, branch execution or outer trial')
    dump(out/'RESULT.json',result);return result
