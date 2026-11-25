"""Transactional adaptive Tabu search with immutable per-iteration commits."""
from pathlib import Path
from dataclasses import asdict,replace
import random,time,resource,fcntl
from .io import *
from .reallocation import generate,Tabu,valid_structure
from .order import build,expand,classical,cost
from .physical import Archive,evaluate,metrics,measure
from .quantum import run as quantum,DiagnosticPause

def run(p,initial,output,condition,settings,seed,branch_id,*,pause_after_iterations=None):
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    with (out/'LOCK').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        return _run(p,initial,out,condition,settings,seed,branch_id,pause_after_iterations)

def _run(p,initial,out,condition,settings,seed,branch_id,pause_after_iterations):
    if condition not in ('D_classical','D_quantum'):raise ValueError('DECLARED_D_CONDITION_REQUIRED')
    begin=time.perf_counter();cpu=time.process_time()
    base=initial.checked_plan(p);method='D' if condition=='D_quantum' else 'C'
    base=replace(base,method_id=method,execution_kind='quantum_circuit_simulator' if method=='D' else 'classical')
    header=dict(version='iterative-v3',condition=condition,seed=seed,branch=branch_id,
        trial_id=initial.manifest['trial_id'],problem_hash=p.fingerprint,od_hash=p.od.fingerprint,
        pi0_hash=identity(base),pi0_file_sha256=initial.manifest['plan_sha256'],settings=settings)
    if (out/'START.json').exists():
        if digest_payload(read(out/'START.json'))!=digest_payload(header):raise ValueError('RESUME_BRANCH_CONTRACT_MISMATCH')
    else:dump(out/'START.json',header)
    if (out/'RESULT.json').exists():
        r=read(out/'RESULT.json');plan=load_plan(out/'plan.json')
        if r['metrics']!=metrics(p,plan,measure(p,base)):raise ValueError('RESUMED_FINAL_RESULT_MISMATCH')
        return r
    state=base;store=Archive(p,base,out/'archive');rng=random.Random(seed);tabu=Tabu(settings['tabu_tenure'])
    remaining=settings['physical_completion_budget'];commits=[];counters=dict(completion_requests=0,returned_order_candidates=0,
        raw_local_samples=0,local_calls=0,quantum_shots=0,order_solver_failures=0,reallocation_candidates=0,quantum_inflight_unknown=False)
    # Reconstruct state from immutable commits, not an untrusted mutable last
    # checkpoint. A commit written before interruption is never executed twice.
    for iteration in range(settings['outer_iterations']):
        folder=out/f'iteration_{iteration:04d}';folder.mkdir(exist_ok=True);commit=folder/'COMMIT.json'
        if commit.exists():
            c=read(commit)
            if c['input_hash']!=identity(state):raise ValueError('BROKEN_ADOPTED_STATE_CHAIN')
            adopted=load_plan(c['adopted_plan_path']);metrics(p,adopted,store.ref)
            if identity(adopted)!=c['adopted_hash']:raise ValueError('ADOPTED_COMMIT_HASH_MISMATCH')
            state=adopted;tabu=Tabu(settings['tabu_tenure'],c['tabu']);rng.setstate(tuples(c['rng_state']))
            counters=c['counters'];remaining=c['remaining_completions'];commits.append(c)
            atomic(out/'CHECKPOINT.json',c);continue
        if remaining<=0:break
        preparation=folder/'PREPARED.json';input_hash=identity(state)
        if preparation.exists():
            prep=read(preparation)
            if prep['input_hash']!=input_hash:raise ValueError('RELOCATION_INPUT_NOT_ADOPTED_STATE')
            moves=prep['moves'];rng.setstate(tuples(prep['rng_after']))
        else:
            # Actual classical vehicle/trip membership changes are generated
            # FROM the last adopted complete physical plan, never from pi0.
            moves=generate(p,state,rng,per_family=settings['moves_per_family'],attempts_per_family=settings['neighbor_attempts_per_family'],max_candidates=remaining)
            prep=dict(input_hash=input_hash,input_plan_id=state.plan_id,moves=moves,rng_after=rng.getstate(),
                iteration=iteration,branch=branch_id,trial_id=header['trial_id'],mode='adaptive_adopted_plan')
            dump(preparation,prep)
        save_plan(folder/'input.plan.json',state)
        counts=dict(counters);counts['reallocation_candidates']+=len(moves)
        pool=[dict(plan=state,origin='current',move=None)];receipts=[];fresh=0
        previous_best=store.entries[commits[-1]['best_incumbent_hash']]['plan'] if commits else base
        def candidate(rs,cid,origin,move):
            nonlocal remaining,fresh
            path=folder/(cid+'.json')
            if path.exists():
                value=read(path)
                if value['routes_hash']!=digest_payload(encode_routes(rs)):raise ValueError('CACHED_CANDIDATE_ROUTES_CHANGED')
            else:
                try:
                    plan=evaluate(p,rs,condition);sid=store.add(plan,origin);planpath=out/'archive'/(sid+'.plan.json')
                    value=dict(status='FEASIBLE',routes_hash=digest_payload(encode_routes(rs)),plan_path=str(planpath),metrics=metrics(p,plan,store.ref),origin=origin)
                except ValueError as e:
                    value=dict(status='INFEASIBLE',routes_hash=digest_payload(encode_routes(rs)),reason=str(e),origin=origin)
                dump(path,value);fresh+=1
            remaining-=1;counts['completion_requests']+=1
            if value['status']=='FEASIBLE':
                plan=load_plan(value['plan_path']);store.add(plan,origin);pool.append(dict(plan=plan,origin=origin,move=move))
            receipts.append(dict(candidate_id=cid,**value));return value
        # Reserve space before generation. Classical-only candidates are kept
        # even if quantum ordering fails, and never attributed to quantum.
        limit_moves=min(len(moves),remaining)
        for j,move in enumerate(moves[:limit_moves]):
            candidate(decode_routes(move['routes']),f'reallocation_{j:03d}','classical_reallocation_only',move)
        local_targets=[]
        for offset in range(len(moves)):
            move=moves[(iteration+branch_id+offset)%len(moves)]
            assigned=decode_routes(move['routes'])
            case=build(p,assigned,settings['local_order_size'],seed+iteration*10007+offset*101,move['affected_slots'])
            if case is not None:local_targets.append((move,assigned,case))
            if len(local_targets)>=settings['local_calls_per_iteration']:break
        if moves and not local_targets:receipts.append(dict(status='NO_ELIGIBLE_FIXED_ORDER_BLOCK'))
        for j,(move,assigned,case) in enumerate(local_targets):
            return_limit=min(settings['returned_order_candidates'],remaining)
            if return_limit<=0:break
            local=folder/f'local_{j:03d}';local.mkdir(exist_ok=True)
            call_header=dict(problem=asdict(case),case_hash=case.fingerprint,assignment_before=assignment_hash(assigned),return_limit=return_limit)
            if (local/'CASE.json').exists():
                if digest_payload(read(local/'CASE.json'))!=digest_payload(call_header):raise ValueError('RESUME_LOCAL_PROBLEM_MISMATCH')
            else:dump(local/'CASE.json',call_header)
            counts['local_calls']+=1
            try:
                if condition=='D_quantum':
                    orders,receipt=quantum(case,settings['quantum'],local/'solver',return_limit)
                else:
                    if (local/'CLASSICAL_RESULT.json').exists():
                        saved=read(local/'CLASSICAL_RESULT.json');orders=saved['orders'];receipt=saved['receipt']
                    else:
                        orders,receipt=classical(case,settings['classical'],return_limit);dump(local/'CLASSICAL_RESULT.json',dict(orders=orders,receipt=receipt))
                counts['returned_order_candidates']+=len(orders)
                counts['raw_local_samples']+=receipt.get('raw_sample_count',receipt.get('raw_candidate_evaluations',0))
                counts['quantum_shots']+=receipt.get('total_shots_actual',0)
                for k,item in enumerate(orders):
                    ordered=expand(case,tuple(item['order']))
                    if assignment_hash(ordered)!=case.assignment_hash:raise ValueError('QUANTUM_CHANGED_SLOT_ASSIGNMENT')
                    value=candidate(ordered,f'order_{j:03d}_{k:03d}',item['source'],move)
                    if value['status']=='FEASIBLE':
                        import math
                        index={s:i for i,s in enumerate(p.od.ids)};depot=p.depot.depot_id
                        route_distance=lambda rs:math.fsum(float(p.od.distance_m[index[a],index[b]]) for r in rs.values() for a,b in zip((depot,*r),(*r,depot)))
                        expected=route_distance(assigned)-cost(case,tuple(range(case.n)))+item['local_distance_m']
                        if abs(1000*value['metrics']['D_km']-expected)>1e-7:raise ValueError('EXPANDED_ORDER_BOUNDARY_DISTANCE_MISMATCH')
                    value_receipt=dict(order=item['order'],source=item['source'],assignment_before=case.assignment_hash,
                        assignment_after=assignment_hash(ordered),entry=case.entry,exit=case.exit,
                        case_hash=case.fingerprint,global_candidate_status=value['status'])
                    target=local/f'DECODED_{k:03d}.json'
                    if not target.exists():dump(target,value_receipt)
                receipts.append(dict(status='LOCAL_COMPLETED',move_id=move['move_id'],case_hash=case.fingerprint,receipt=receipt))
            except DiagnosticPause:raise
            except Exception as e:
                counts['order_solver_failures']+=1
                if condition=='D_quantum':counts['quantum_inflight_unknown']=True
                receipts.append(dict(status='LOCAL_SOLVER_FAILED',reason=repr(e),move_id=move['move_id'],classical_reallocation_preserved=True,
                    quantum_shots_if_inflight='UNKNOWN_NOT_ZERO'))
        admissible=[]
        for item in pool:
            blocked=item['move'] is not None and tabu.prohibited(item['move'],iteration)
            aspiration=store.key(item['plan'])<store.key(previous_best)
            if not blocked or aspiration or item['origin']=='current':admissible.append(item)
        chosen=min(admissible,key=lambda x:store.key(x['plan']))
        adopted_plan=chosen['plan']
        changed=identity(adopted_plan)!=input_hash
        if changed and chosen['move']:tabu.record(chosen['move'],iteration)
        # This assignment is the production transition, not just an option
        # name or a seen-set update. The next generate() consumes this plan.
        state=adopted_plan
        best=store.best();path=out/'archive'/(identity(state)+'.plan.json');save_plan(path,state)
        c=dict(iteration=iteration,mode='adaptive_adopted_plan',input_hash=input_hash,adopted_hash=identity(state),
            adopted_plan_path=str(path),adopted_origin=chosen['origin'],adopted_move_id=chosen['move']['move_id'] if chosen['move'] else None,adopted=changed,
            best_incumbent_hash=identity(best['plan']),best_metrics=best['metrics'],state_metrics=metrics(p,state,store.ref),
            adoption_rule='best pi0 I_dual/ties among current and non-tabu or aspirational complete plans; no worsening vs current',
            tabu=tabu.entries,rng_state=rng.getstate(),remaining_completions=remaining,counters=counts,
            moves=prep['moves'],candidate_receipts=receipts,fresh_completion_evaluations=fresh)
        dump(commit,c);atomic(out/'CHECKPOINT.json',c);commits.append(c);counters=counts
        if pause_after_iterations and len(commits)>=pause_after_iterations:
            return dict(status='INTERRUPTED_DIAGNOSTIC',committed_iterations=len(commits),adopted_hash=identity(state))
    best=store.best();plan=best['plan'];save_plan(out/'plan.json',plan);save_plan(out/'search_state.plan.json',state)
    result=dict(status='COMPLETE_WITH_LOCAL_FAILURES' if counters['order_solver_failures'] else 'COMPLETE',
        condition=condition,branch=branch_id,seed=seed,trial_id=header['trial_id'],pi0_hash=header['pi0_hash'],
        metrics=metrics(p,plan,store.ref),search_state_hash=identity(state),best_incumbent_hash=identity(plan),
        completed_iterations=len(commits),adopted_iterations=sum(c['adopted'] for c in commits),
        adopted_origins=[c['adopted_origin'] for c in commits],counters=counters,remaining_completions=remaining,
        quantum_shots_total=None if counters['quantum_inflight_unknown'] else counters['quantum_shots'],
        quantum_completed_call_shots_lower_bound=counters['quantum_shots'],
        archive_size=len(store.entries),stop_reason='FINITE_ITERATION_OR_COMPLETION_WORK_LIMIT',
        best_incumbent_origins=store.origins.get(identity(plan),[]),
        current_attempt_CPU_s=time.process_time()-cpu,current_attempt_wall_s=time.perf_counter()-begin,
        RSS_highwater_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,formal_outer_J=0)
    dump(out/'RESULT.json',result);return result
