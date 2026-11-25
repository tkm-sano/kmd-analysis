"""Finite-work branch; all methods share completion, master and final archive."""
from dataclasses import asdict,replace
from pathlib import Path
import json,resource,time
from kmd_toc.common_initial_v1.plans import dump,exact_metrics
from kmd_toc.measurement_audit_v1.measurement import physical_payload,digest_payload
from kmd_toc.objective_alignment_v1.objective import measure,record,local_update
from kmd_toc.nkr_p2_study.model import seed_for
from kmd_toc.main_experiment_d.quantum import backend_modules
from .local import prepare,complete,Quantum,Classical
from .master import PhysicalMaster

def generate_provider(condition,settings,seed):
    if condition=='D_quantum':return Quantum(settings['quantum_protocol'],diagnostic=settings['diagnostic'])
    if condition=='D_classical':return Classical(settings['classical_generator'],evaluations=settings['classical_evaluations'],seed=seed)
    raise ValueError('ONLY_EXPLICIT_QUANTUM_OR_CLASSICAL_CONTROL')

def validate_settings(s):
    for key in ('n','K','R_local'):
        if type(s[key]) is not int or s[key]<1:raise ValueError('EXPLICIT_POSITIVE_SEARCH_PARAMETERS')
    if s['anchor'] not in ('common_initial','search_state'):raise ValueError('DECLARED_LOCAL_ANCHOR')
    if s['completion_policy'] not in ('all_generated','legacy_distance_top'):raise ValueError('COMPLETION_POLICY')
    if s['completion_policy']=='legacy_distance_top' and (type(s.get('completion_cap')) is not int or s['completion_cap']<1):
        raise ValueError('DIAGNOSTIC_CAP_REQUIRED')
    if not s['diagnostic'] and s['n'] not in (10,12):raise ValueError('RESEARCH_N_CANDIDATE_NOT_REGISTERED')
    if s['diagnostic'] and s['n']!=2:raise ValueError('N2_DIAGNOSTIC_ONLY')

def run_branch(p,initial,output,*,condition,settings,outer_seed,branch_id,provider_factory=generate_provider):
    validate_settings(settings)
    if branch_id not in range(4):raise ValueError('FOUR_FIXED_BRANCH_IDS')
    out=Path(output);out.mkdir(parents=True,exist_ok=False);t0=time.perf_counter();c0=time.process_time()
    base=initial.checked_plan(p);method='D' if condition=='D_quantum' else 'C'
    anchor0=replace(base,method_id=method,execution_kind='quantum_circuit_simulator' if method=='D' else 'classical')
    state=anchor0;master=PhysicalMaster(p,anchor0,out/'master');seen=set();calls=[];candidates=[];error=None
    dump(out/'START.json',dict(condition_id=condition,branch_id=branch_id,outer_seed=outer_seed,
        trial_id=initial.manifest['trial_id'],initial_plan_sha256=initial.manifest['plan_sha256'],
        initial_physical_hash=digest_payload(physical_payload(base)),initial_DW=exact_metrics(p,base),
        problem_hash=p.fingerprint,od_hash=p.od.fingerprint,
        C_final_plan_or_metrics_or_pool_input=False,settings=settings))
    totals=dict(generation_s=0.,completion_s=0.,evaluation_s=0.,objective_evaluations=0,quantum_shots=0,
        optimizer_function_evaluations=0,generated_candidates=0,completion_attempts=0,feasible_candidates=0,
        evaluated_candidates=0,not_completed=0,quantum_calls=0,greedy_updates=0)
    try:
        for r in range(1,settings['R_local']+1):
            for k in range(1,settings['K']+1):
                seed=seed_for(outer_seed,branch_id,r,k);anchor=anchor0 if settings['anchor']=='common_initial' else state
                case=prepare(p,anchor,settings['n'],seed,seen)
                if case is None:
                    calls.append(dict(r=r,k=k,seed=seed,status='NO_ELIGIBLE_LOCAL_PROBLEM',quantum_executed=False));continue
                seen.update(case.local.customer_ids);folder=out/f'local_{r:03d}_{k:03d}';folder.mkdir()
                dump(folder/'CASE.json',dict(case_hash=case.case_hash,physical_anchor_hash=case.physical_initial_hash,
                    local=case.local.payload(),lookup=case.lookup,
                    oracle_empty_descriptors_are_not_active_physical_trips=True))
                lp_before=dict(master.last);tick=time.perf_counter()
                provider=provider_factory(condition,settings,seed)
                items,receipt=provider.generate(p,anchor,case,folder/'generation')
                totals['generation_s']+=time.perf_counter()-tick
                if receipt.get('condition_id')!=condition:raise ValueError('GENERATOR_CONDITION_RECEIPT_MISMATCH')
                if condition=='D_quantum':
                    if receipt.get('quantum_executed') is not True or receipt.get('replay_only'):
                        raise ValueError('FOUR_BRANCH_QUANTUM_REQUIRES_ACTUAL_EXECUTION_NOT_REPLAY')
                    if any(x.get('source')!='measured_quantum' for x in items):raise ValueError('QUANTUM_SOURCE_RELABELED')
                    totals['quantum_calls']+=1
                elif receipt.get('quantum_executed') is not False or any(not x.get('source','').startswith('classical_') for x in items):
                    raise ValueError('CLASSICAL_CONTROL_HAS_QUANTUM_OR_UNDECLARED_SOURCE')
                if receipt.get('case_hash')!=case.case_hash:raise ValueError('GENERATOR_LOCAL_CASE_MISMATCH')
                for field in ('objective_evaluations','quantum_shots','optimizer_function_evaluations'):
                    totals[field]+=receipt.get(field,0) or 0
                totals['generated_candidates']+=len(items)
                # Default removes distance-only early pruning, not merely a
                # larger top-K. Explicit legacy cap is a diagnostic comparator.
                items=sorted(items,key=(lambda x:(x['proxy'],x['candidate_id'])) if settings['completion_policy']=='legacy_distance_top'
                             else (lambda x:x['candidate_id']))
                q,_=backend_modules();constant=float(measure(p,anchor).D*1000)-q.lookup_cost(q.initial_order(case.local),case.lookup)
                attempted=0
                for item in items:
                    row=dict(r=r,k=k,case_hash=case.case_hash,**{a:b for a,b in item.items() if a!='decision'},decision=asdict(item['decision']))
                    if settings['completion_policy']=='legacy_distance_top' and attempted>=settings['completion_cap']:
                        totals['not_completed']+=1;candidates.append(dict(**row,status='NOT_COMPLETED_BUDGET',W=None));continue
                    attempted+=1;totals['completion_attempts']+=1;tick=time.perf_counter()
                    try:plan=complete(p,anchor,case,item,condition)
                    except ValueError as e:
                        totals['completion_s']+=time.perf_counter()-tick
                        candidates.append(dict(**row,status='INFEASIBLE',reason=str(e)));continue
                    totals['completion_s']+=time.perf_counter()-tick;totals['feasible_candidates']+=1;tick=time.perf_counter()
                    m=measure(p,plan)
                    if abs(float(m.D*1000)-(item['proxy']*case.lookup['bound_m']+constant))>1e-7:
                        raise ValueError('LOCAL_DISTANCE_ORACLE_NOT_EQUAL_COMPLETE_PHYSICAL_D')
                    # Archive is updated before, and independently of, state.
                    kept,verified=master.add(plan,origin=f"{item['source']}:{r}:{k}:{item['candidate_id']}",branch_id=branch_id)
                    if verified is None:
                        candidates.append(dict(**row,status='INDEPENDENT_MEASUREMENT_REJECT'));continue
                    totals['evaluated_candidates']+=1
                    accept=local_update(measure(p,state),m)
                    if accept:state=plan;totals['greedy_updates']+=1
                    totals['evaluation_s']+=time.perf_counter()-tick
                    candidates.append(dict(**row,status='COMPLETED',archive_retained=kept,greedy_state_update=accept,
                        **record(m,master.reference)))
                calls.append(dict(r=r,k=k,seed=seed,status='COMPLETE',case_hash=case.case_hash,generator=receipt,
                    RMP_duals_before_generation=lp_before,
                    dual_use='actual full-plan reduced cost AFTER physical completion; NOT in distance Hamiltonian',
                    complete_plan_column_count=len(master.archive.candidates)))
    except Exception as e:error=f'{type(e).__name__}:{e}'
    plan,integer=master.finish();initial.checked_plan(p)
    dump(out/'plan.json',asdict(plan));dump(out/'search_state_plan.json',asdict(state));dump(out/'CANDIDATES.json',candidates)
    result=dict(condition_id=condition,branch_id=branch_id,outer_seed=outer_seed,trial_id=initial.manifest['trial_id'],
        status='FAILED_INITIAL_OR_ARCHIVE_RETAINED' if error else 'COMPLETE',error=error,
        initial_plan_sha256=initial.manifest['plan_sha256'],initial_physical_hash=initial.manifest['physical_plan_hash'],
        selected=integer['selected'],metrics=exact_metrics(p,plan),calls=calls,**totals,
        LP_s=master.lp_s,integer_master_s=master.integer_s,CP_s=0.,
        CPU_s=time.process_time()-c0,wall_s=time.perf_counter()-t0,
        RSS_highwater_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
        RSS_scope='fresh branch process lifetime including imports; sampled parent tree separately',
        quantum_candidate_source_traceable=True,pricing_objective_alignment='PARTIAL_DISTANCE_ORACLE_VS_FULL_PLAN_MINIMAX',
        local_schedule_anchor=settings['anchor'],
        same_realized_local_cases_across_controls='guaranteed by common_initial anchor and matching seeds; search_state may diverge',
        formal_n_K_R='HOLD',formal_J='HOLD',main_experiment='HOLD')
    result['generation_accounting_scope']='completed generation receipts; failed generation may have extra unmeasured work'
    if error and condition=='D_quantum':
        # Partial circuit work without a returned receipt is unknown, not zero.
        for field in ('quantum_shots','objective_evaluations','optimizer_function_evaluations'):
            result['known_completed_'+field]=result[field];result[field]=None
        result['partial_quantum_execution']='UNKNOWN_NOT_IMPUTED'
    dump(out/'RESULT.json',result);return result
