"""B once -> independent C and D processes -> post-hoc comparison only."""
from dataclasses import asdict
from pathlib import Path
import time,json,resource
from kmd_toc.common_initial_v1.plans import create_initial,dump,sha,exact_metrics
from kmd_toc.common_initial_v1.engines import classical as old_C_distance
from kmd_toc.objective_alignment_v1.classical import run as exact_C
from kmd_toc.objective_alignment_v1.objective import measure,record
from kmd_toc.duty_break_v1.models import load_plan
from kmd_toc.measurement_audit_v1.measurement import cross_evaluate,physical_payload,digest_payload
from .runner import run_four

def run_C(p,initial,output,*,config,seed):
    out=Path(output);out.mkdir(parents=True,exist_ok=False);t=time.perf_counter();cpu=time.process_time();error=None
    try:
        result=exact_C(p,initial,out/'solver',config=config,seed=seed%(2**31-1))
        plan=load_plan(out/'solver/plan.json')
        if result['status']!='COMPLETE_COMPONENT_VALIDATION':error=result.get('CP_HOLD_reason') or result['status']
    except Exception as e:
        error=f'{type(e).__name__}:{e}';result=None;plan=initial.checked_plan(p)
    audit=cross_evaluate(p,plan)
    if audit['status']!='PASS':raise ValueError('CLASSICAL_FINAL_COMMON_MEASUREMENT_FAIL')
    dump(out/'plan.json',asdict(plan))
    r=dict(condition_id='C_Idual',status='COMPLETE' if error is None else 'HOLD_INITIAL_OR_CP_INCUMBENT_RETAINED',
        error=error,trial_id=initial.manifest['trial_id'],initial_plan_sha256=initial.manifest['plan_sha256'],
        initial_physical_hash=initial.manifest['physical_plan_hash'],initial_DW=initial.manifest['metrics'],
        selected=record(measure(p,plan),measure(p,initial.checked_plan(p))),metrics=exact_metrics(p,plan),
        native=result,wall_s=time.perf_counter()-t,CPU_s=time.process_time()-cpu,
        RSS_highwater_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
        generation_objective='distance Routing with 0.1m arc rounding',
        completed_plan_objective='exact pi0 I_dual; CP no route/total rounding; same frozen tie/zero ordering',
        native_schedule_identity='HOLD_NOT_REPRESENTED_IN_ROUTING',main_experiment='HOLD')
    dump(out/'RESULT.json',r);return r

def compare_results(p,initial,conditions):
    base=initial.checked_plan(p);ref=measure(p,base);rows=[];verified={}
    for name,(result,path) in conditions.items():
        if result['initial_plan_sha256']!=initial.manifest['plan_sha256'] or result['trial_id']!=initial.manifest['trial_id']:
            raise ValueError('COMPARISON_INITIAL_OR_TRIAL_MISMATCH')
        plan=load_plan(path);audit=cross_evaluate(p,plan)
        if audit['status']!='PASS' or exact_metrics(p,plan)!=result['metrics']:raise ValueError('COMPARISON_FINAL_MEASUREMENT_FAIL')
        m=measure(p,plan);verified[name]=m
        rows.append(dict(condition_id=name,status=result['status'],trial_id=initial.manifest['trial_id'],
            initial_sha256=initial.manifest['plan_sha256'],physical_hash=digest_payload(physical_payload(plan)),
            delta_D=float(m.D-ref.D),delta_W=float(m.W-ref.W),**record(m,ref),metrics=exact_metrics(p,plan),
            wall_s=result.get('wall_s'),model_feasible=True,statistical_outer_trial=False))
    q=verified['D_quantum'];c=verified['D_classical'];qs=record(q,ref)['I_dual_percent'];cs=record(c,ref)['I_dual_percent']
    return dict(results=rows,quantum_contribution=dict(delta_D_Q=float(q.D-c.D),delta_W_Q=float(q.W-c.W),
        I_quantum_percent=qs,I_classical_percent=cs,I_difference_percentage_points=qs-cs if qs is not None and cs is not None else None,
        scope='paired implementation diagnostic; not statistical evidence or quantum advantage'),
        formal_J='HOLD',outer_trials_obtained=0)

def run_comparison(p,input_directory,output,*,config,settings,outer_seed,trial_id,scale,initial=None,include_distance=True):
    out=Path(output);out.mkdir(parents=True,exist_ok=False);begin=time.perf_counter()
    if settings['diagnostic'] and (len(p.stops)>12 or p.experiment.kind!='synthetic_validation'):
        raise ValueError('DIAGNOSTIC_ENTRY_ACCEPTS_SMALL_SYNTHETIC_INPUT_ONLY')
    if not settings['diagnostic']:raise ValueError('MAIN_EXPERIMENT_PERMISSION_HOLD_USE_PREFLIGHT_FOR_S1_S2_S3')
    tick=time.perf_counter()
    initial=initial or create_initial(p,out/'initial',experiment_id='CD_COMPARISON_V2_DIAGNOSTIC',scale=scale,
        trial_id=trial_id,seed=outer_seed,config=config)
    preparation_s=time.perf_counter()-tick
    if initial.manifest['status']!='COMPLETE':
        r=dict(status='COMMON_INITIAL_UNAVAILABLE',conditions={k:'COMMON_INITIAL_UNAVAILABLE' for k in ('C_Idual','D_classical','D_quantum')},
            main_experiment='HOLD');dump(out/'RESULT.json',r);return r
    if initial.manifest['trial_id']!=trial_id:raise ValueError('COMMON_INITIAL_TRIAL_ID_NOT_REGISTERED')
    # D workers receive only immutable problem/pi0/own settings; not this dict
    # of C results, plan, history, or pool. They run as fresh processes.
    ci=run_C(p,initial,out/'C_Idual',config=config,seed=outer_seed)
    dc=run_four(p,initial,input_directory,out/'D_classical',condition='D_classical',settings=settings,outer_seed=outer_seed)
    dq=run_four(p,initial,input_directory,out/'D_quantum',condition='D_quantum',settings=settings,outer_seed=outer_seed)
    baseline=dict(status='COMPLETE',trial_id=trial_id,initial_plan_sha256=initial.manifest['plan_sha256'],metrics=initial.manifest['metrics'],
        wall_s=initial.manifest['generation_wall_s'])
    records={'B':(baseline,initial.directory/'plan.json'),'C_Idual':(ci,out/'C_Idual/plan.json'),
        'D_classical':(dc,out/'D_classical/selection/plan.json'),'D_quantum':(dq,out/'D_quantum/selection/plan.json')}
    if include_distance:
        legacy=old_C_distance(p,initial,out/'C_distance',config=config,seed=outer_seed%(2**31-1))
        records['C_distance']=({**legacy,'trial_id':trial_id},out/'C_distance/plan.json')
    compared=compare_results(p,initial,records)
    result=dict(status='COMPLETE_INTEGRATION_DIAGNOSTIC' if ci['status']=='COMPLETE' and
        dc['status']==dq['status']=='COMPLETE_FOUR_BRANCHES' else 'PARTIAL_INTEGRATION',
        trial_id=trial_id,scale=scale,initial_manifest_sha256=sha(initial.directory/'INITIAL.json'),
        initial_plan_sha256=initial.manifest['plan_sha256'],initial_generation_role=initial.manifest['generator_role'],
        common_preparation_s=preparation_s,wall_s=time.perf_counter()-begin,**compared,
        initial_condition_match=True,final_metric_and_selection_match=True,
        candidate_generation_objective_match='PARTIAL_C_ROUTING_AND_D_QUANTUM_DISTANCE_ORACLES_VS_FINAL_IDUAL',
        equal_work_or_time_budget='HOLD_UNAPPROVED; actual counts/resources logged',main_experiment='HOLD')
    dump(out/'RESULT.json',result);return result
