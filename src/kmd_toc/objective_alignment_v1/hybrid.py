"""Matched D controls: one local case, completion, archive, selector and LP."""
from dataclasses import asdict,replace
from pathlib import Path
import time,resource
from kmd_toc.common_initial_v1.plans import dump,exact_metrics,sha
from kmd_toc.common_initial_v1.engines import relaxed_master,slot_routes
from kmd_toc.d_local_design.completion import pinned_routes,preserves
from kmd_toc.duty_break_v1.scheduler import schedule
from kmd_toc.duty_break_v1.validation import require_valid
from kmd_toc.measurement_audit_v1.measurement import physical_payload,digest_payload
from .archive import Archive
from .objective import measure,record,local_update
from .generators import prepare,case_digest

class SearchSession:
    """One pi0 archive can outlive many local calls; greedy state is separate."""
    def __init__(self,p,initial,condition,archive_output=None):
        self.p=p;self.condition=condition;self.state=initial
        self.pi0_physical_hash=digest_payload(physical_payload(initial))
        self.archive=Archive(p,initial,archive_output)
    def observe(self,plan,origin):
        kept=self.archive.add(plan,origin=origin)
        if self.archive.rows[-1]['status']=='INFEASIBLE_OR_MEASUREMENT_FAIL':return False,False,None
        new=measure(self.p,plan);accept=local_update(measure(self.p,self.state),new)
        if accept:self.state=plan
        return kept,accept,new

def complete_candidate(p,original,case,item,condition):
    if digest_payload(physical_payload(original))!=case.physical_initial_hash:
        raise ValueError('STALE_OR_DIFFERENT_LOCAL_INCUMBENT')
    decision=item['decision'];decision.validate(case.local.customer_ids)
    # method_id is only the old validator's physical metadata domain. A
    # classical control remains C/classical, never a false quantum execution.
    method='D' if condition=='D_quantum' else 'C'
    proposal=schedule(p,pinned_routes(original,case.local,decision),method,
        {'condition_id':condition,'generator_source':item['source'],'case_hash':case.case_hash,
         'quantum_candidate_origin':condition=='D_quantum','completion':'same pinned routes + duty/FCFS scheduler'})
    if not preserves(proposal,case.local,decision,original):raise ValueError('CANDIDATE_ASSIGNMENT_OR_ORDER_CHANGED')
    require_valid(p,proposal);return proposal

def run(p,initial,output,*,provider,case=None,n=2,seed=0,completion_limit,raw_order=None,session=None):
    if type(completion_limit) is not int or completion_limit<0:raise ValueError('EXPLICIT_COMPLETION_ATTEMPT_LIMIT')
    condition=provider.condition_id
    if condition not in ('D_classical','D_quantum'):raise ValueError('DECLARED_CONTROL_CONDITION_REQUIRED')
    out=Path(output);out.mkdir(parents=True,exist_ok=False);begin=time.perf_counter();cpu=time.process_time()
    if initial.manifest['status']!='COMPLETE':
        r={'condition_id':condition,'status':'COMMON_INITIAL_UNAVAILABLE','main_experiment':'HOLD'}
        dump(out/'RESULT.json',r);return r
    base=initial.checked_plan(p);method='D' if condition=='D_quantum' else 'C'
    state=replace(base,method_id=method,execution_kind='quantum_circuit_simulator' if method=='D' else 'classical')
    state=replace(state,method_settings={**state.method_settings,'condition_id':condition})
    if session is not None:
        if session.condition!=condition or session.p.fingerprint!=p.fingerprint:raise ValueError('SESSION_SCOPE_MISMATCH')
        if session.archive.reference!=measure(p,base):raise ValueError('SESSION_REFERENCE_NOT_COMMON_PI0')
        if session.pi0_physical_hash!=digest_payload(physical_payload(base)):
            raise ValueError('SESSION_PI0_PHYSICAL_HASH_MISMATCH')
        state=session.state
    case=case or prepare(p,state,n,seed)
    if (case.case_hash!=case_digest(case) or case.problem_hash!=p.fingerprint or case.od_hash!=p.od.fingerprint or
            case.physical_initial_hash!=digest_payload(physical_payload(state))):raise ValueError('MATCHED_CASE_NOT_SAME_INPUT')
    dump(out/'START.json',{'condition_id':condition,'initial_plan_sha256':initial.manifest['plan_sha256'],
        'physical_hash':case.physical_initial_hash,'case_hash':case.case_hash,'C_final_input':False,
        'quantum_source_condition':condition=='D_quantum','replay_only':provider.__class__.__name__=='MeasuredReplay'})
    dump(out/'LOCAL_CASE.json',{'local':case.local.payload(),'lookup':case.lookup,'case_hash':case.case_hash})
    dump(out/'start_plan.json',asdict(state))
    session=session or SearchSession(p,state,condition,out/'candidates')
    archive=session.archive;pool={r for r in slot_routes(p,state) if r}
    lp_begin=time.perf_counter();master=relaxed_master(p,pool);lp_s=time.perf_counter()-lp_begin
    generation_error=None;generation_start=time.perf_counter();generation_cpu=time.process_time()
    try:
        items,gen=provider.generate(p,state,case,out/'generation')
        if gen.get('condition_id')!=condition:raise ValueError('GENERATOR_RECEIPT_CONDITION_MISMATCH')
        if condition=='D_quantum':
            if not (gen.get('quantum_executed') is True or gen.get('replay_only') is True):
                raise ValueError('NO_QUANTUM_MEASUREMENT_OR_PINNED_REPLAY_PROVENANCE')
            if any(r.get('source')!='measured_quantum' for r in items):raise ValueError('NONQUANTUM_CANDIDATES_IN_QUANTUM_CONDITION')
        elif gen.get('quantum_executed') is not False or any(not r.get('source','').startswith('classical_') for r in items):
            raise ValueError('CLASSICAL_CONTROL_PROVENANCE_MISMATCH')
    except Exception as error:
        generation_error=f'{type(error).__name__}:{error}';items=[]
        gen={'condition_id':condition,'status':'FAILED_GENERATION','reason':generation_error,
            'generation_wall_s':time.perf_counter()-generation_start,'generation_CPU_s':time.process_time()-generation_cpu,
            'quantum_shots':None if condition=='D_quantum' else 0,'objective_evaluations':None,
            'optimization_iterations':None,'quantum_execution_status':'UNKNOWN_IF_PARTIAL_FAILURE',
            'no_replacement_or_changed_quantum_settings':True}
    # Common deterministic proxy ranking; never generator-specific truncation.
    items=sorted(items,key=lambda r:(r['proxy'],r['candidate_id']))
    if raw_order is not None:
        if sorted(raw_order)!=list(range(len(items))):raise ValueError('FULL_EXPLICIT_ORDER_PERMUTATION_REQUIRED')
        items=[items[i] for i in raw_order]
    evaluated=[];completion_s=0.;evaluation_s=0.;accepted=0;feasible=0;completed=0;measured=0
    original_for_case=state;new_columns=[]
    from kmd_toc.pipeline.completion import route_distance
    for rank,item in enumerate(items):
        info={k:v for k,v in item.items() if k!='decision'};info['decision']=asdict(item['decision']);info['rank_received']=rank+1
        if completed>=completion_limit:
            evaluated.append({**info,'status':'NOT_COMPLETED_BUDGET','W_status':'UNKNOWN_NOT_EVALUATED'});continue
        completed+=1;tick=time.perf_counter()
        try:proposal=complete_candidate(p,original_for_case,case,item,condition)
        except ValueError as error:
            completion_s+=time.perf_counter()-tick
            evaluated.append({**info,'status':'INFEASIBLE','reason':str(error)});continue
        completion_s+=time.perf_counter()-tick;feasible+=1;tick=time.perf_counter()
        # Save every baseline-nonworsening feasible candidate BEFORE greedy
        # state acceptance; later candidates are not lost when state improves.
        kept,accept,new=session.observe(proposal,item['source'])
        if new is None:
            evaluation_s+=time.perf_counter()-tick
            evaluated.append({**info,'status':'MEASUREMENT_REJECTED'});continue
        measured+=1
        if accept:state=session.state;accepted+=1
        for route in [tuple(p.od.ids.index(v.stop_id) for v in t.visits) for t in proposal.trips
                      if (t.vehicle_id,t.trip_no) in case.local.trip_ids]:
            rc=route_distance(p,route)/1000-sum(master['customer_duals_km'][i-1] for i in route)-master['fleet_dual_km']
            if rc < -1e-7 and route not in pool:pool.add(route);new_columns.append({'route':route,'rc_km':rc})
        evaluation_s+=time.perf_counter()-tick
        evaluated.append({**info,'status':'COMPLETED','archive_retained':kept,'greedy_state_update':accept,
                          **record(new,archive.reference)})
    tick=time.perf_counter();last_master=relaxed_master(p,pool);lp_s+=time.perf_counter()-tick
    final,why=archive.best();initial.checked_plan(p);archive.save(out/'ARCHIVE.json')
    dump(out/'plan.json',asdict(final));dump(out/'search_state_plan.json',asdict(state))
    dump(out/'CANDIDATES.json',evaluated)
    r={'condition_id':condition,'status':'FAILED_GENERATION_INITIAL_RETAINED' if generation_error else 'COMPLETE_COMPONENT_VALIDATION',
       'generation_error':generation_error,'initial_plan_sha256':initial.manifest['plan_sha256'],
       'case_hash':case.case_hash,'generator':gen,'candidate_completion_limit':completion_limit,
       'generated_unique':len(items),'completion_attempts':completed,'physically_feasible_candidates':feasible,
       'final_evaluated_candidates':measured,'not_completed':len(items)-completed,'greedy_state_updates':accepted,
       'retained_unique_with_initial':len(archive.candidates),'selected':why,'metrics':exact_metrics(p,final),
       'search_state_metrics':exact_metrics(p,state),'completion_s':completion_s,'evaluation_s':evaluation_s,'LP_s':lp_s,
       'new_negative_relaxation_columns':new_columns,'initial_LP':master,'final_LP':last_master,
       'CP_s':0.,'CPU_s':time.process_time()-cpu,'wall_s':time.perf_counter()-begin,
       'RSS_highwater_MiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
       'RSS_scope':'OS-reported process lifetime highwater, including startup/prior calls; not per-condition incremental peak',
       'shared_pipeline':'same local case, proxy, physical completion, evaluation, archive, final selection',
       'budget_A':'same explicit completion-attempt limit; raw generation work accounted separately',
       'budget_B':'HOLD_TIME_BUDGET_NOT_ADOPTED','full_physical_CG':'HOLD_NO_INTEGER_PHYSICAL_MASTER',
       'local_sequence_scope':'one frozen local incumbent per invocation; future discovery/path dependence remains',
       'formal_n_K_R':'HOLD','formal_J':'HOLD','main_experiment':'HOLD'}
    dump(out/'RESULT.json',r);return r
