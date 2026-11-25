"""Read-only exact inspection of stored candidates and adoption transitions."""
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
import csv
from kmd_toc.iterative_v3.io import read,dump,load_plan,identity,routes,decode_routes,memberships,assignment_hash,digest_payload,verify_pins
from kmd_toc.iterative_v3.reallocation import Tabu
from kmd_toc.objective_alignment_v1.objective import Metrics,selection_key
from kmd_toc.iterative_v3.order import OrderProblem,cost

def metric(v):return Metrics(F(v['D_exact']),F(v['W_exact']))
def index(x,r):return 100*min((r.D-x.D)/r.D,(r.W-x.W)/r.W) if r.D>0 and r.W>0 else None
def csvwrite(path,rows):
    if not rows:return
    with Path(path).open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def diagnose(source,destination):
    source,destination=Path(source),Path(destination);destination.mkdir(parents=True,exist_ok=False)
    manifest=read(source/'MANIFEST.json');verify_pins(manifest['code_hashes'])
    rows=[];violations=[];branches=[];reasons=Counter();baseline_rows=[]
    for case in manifest['cases']:
        trial=source/case['output_subdir'];result=read(trial/'RESULT.json') if (trial/'RESULT.json').exists() else None
        if result is None:continue
        initial=result['conditions']['B']['metrics'];ref=metric(initial);initial_hash=result['initial_hash']
        initial_key=selection_key(ref,ref,initial=True,stable_id=initial_hash)
        for method in ('D_classical','D_quantum'):
            final=result['conditions'][method]
            final_candidates=[(selection_key(ref,ref,initial=True,stable_id=initial_hash),initial_hash)]
            baseline_rows.append(dict(scale=case['scale'],method=method,D_pi0=float(ref.D),W_pi0=float(ref.W),
                D_final=final['metrics']['D_km'],W_final=final['metrics']['W_total_min'],
                I_dual_pi0_percent=final['metrics']['I_dual_percent'],
                I_dual_C_posthoc_percent=final.get('C_reference_posthoc',{}).get('I_dual_percent')))
            for branch in range(4):
                work=trial/method/f'branch_{branch}/work';state=ref;state_hash=initial_hash;best=ref;tabu={};archive={initial_hash:ref}
                for path in sorted(work.glob('iteration_*/COMMIT.json')):
                    commit=read(path);prepared=read(path.parent/'PREPARED.json');i=commit['iteration']
                    if prepared['input_hash']!=state_hash or commit['input_hash']!=state_hash:violations.append(str(path)+':STATE_CHAIN')
                    plan=load_plan(path.parent/'input.plan.json')
                    if identity(plan)!=state_hash:violations.append(str(path)+':INPUT_PLAN_HASH')
                    before=memberships(routes(plan));moves=prepared['moves']
                    for move in moves:
                        after=memberships(decode_routes(move['routes']))
                        diff=[dict(customer=s,before=list(before[s]),after=list(after[s])) for s in sorted(before) if before[s]!=after[s]]
                        if set(before)!=set(after) or diff!=move['membership_diff']:violations.append(str(path)+':MEMBERSHIP_DIFF')
                    candidate_receipts=[x for x in commit['candidate_receipts'] if 'candidate_id' in x]
                    feasible=[x for x in candidate_receipts if x['status']=='FEASIBLE'];failed=[x for x in candidate_receipts if x['status']!='FEASIBLE']
                    failure_counts=Counter(x.get('reason',x['status']) for x in failed);reasons.update(failure_counts)
                    orders=[];calls=0;raw=None;solver_stops=[];local_move={};local_better=0
                    for local in sorted(path.parent.glob('local_*')):
                        h=read(local/'CASE.json');calls+=1
                        rs=decode_routes(h['problem']['routes'])
                        if assignment_hash(rs)!=h['assignment_before']:violations.append(str(local)+':CASE_ASSIGNMENT')
                        q=local/'solver/RESULT.json';c=local/'CLASSICAL_RESULT.json'
                        if q.exists():
                            v=read(q);items=v['candidates'];raw=(raw or 0)+v['raw_sample_count'];solver_stops.append(v['optimizer_message'])
                        elif c.exists():
                            v=read(c);items=v['orders'];solver_stops.append(v['receipt']['stop_reason'])
                        else:items=[];solver_stops.append('NO_COMPLETED_LOCAL_RESULT')
                        for j,item in enumerate(items):
                            local_better+=item['local_distance_m']<cost(OrderProblem(**h['problem']),tuple(range(len(h['problem']['ids']))))-1e-7
                            ids=h['problem']['ids'];slot=(h['problem']['vehicle'],h['problem']['trip'])
                            ordered=dict(rs);ordered[slot]=tuple(h['problem']['prefix'])+tuple(ids[t] for t in item['order'])+tuple(h['problem']['suffix'])
                            decoded=local/f'DECODED_{j:03d}.json'
                            if assignment_hash(ordered)!=assignment_hash(rs):violations.append(str(local)+':ORDER_CHANGED_ASSIGNMENT')
                            if decoded.exists():
                                d=read(decoded)
                                if d['assignment_before']!=d['assignment_after']:violations.append(str(decoded)+':ASSIGNMENT')
                            else:violations.append(str(local)+':MISSING_DECODED')
                            intent=path.parent/f'order_{local.name.split("_")[-1]}_{j:03d}.json'
                            if not intent.exists():violations.append(str(local)+':RETURNED_NOT_COMPLETED')
                            orders.append(tuple(item['order'])!=tuple(range(len(ids))))
                        matches=[m for m in moves if digest_payload(m['routes'])==digest_payload(h['problem']['routes'])]
                        local_move[local.name.split('_')[-1]]=matches[0] if matches else None
                    key=lambda x,sid:selection_key(x,ref,initial=sid==initial_hash,stable_id=sid)
                    admissible=[(key(state,state_hash),state_hash)];blocked=0;aspirations=0;better_initial=0
                    memory=Tabu(manifest['configuration']['search']['tabu_tenure'],tabu)
                    prior_best_sid=min(archive,key=lambda sid:key(archive[sid],sid));prior_best=archive[prior_best_sid]
                    for receipt in feasible:
                        x=metric(receipt['metrics']);sid=receipt['metrics']['physical_hash'];archive[sid]=x
                        if identity(load_plan(receipt['plan_path']))!=sid:violations.append(receipt['plan_path']+':PHYSICAL_HASH')
                        if key(x,sid)<initial_key:better_initial+=1
                        value=index(x,ref)
                        if value is not None and value!=F(receipt['metrics']['I_dual_exact']):violations.append(str(path)+':I_DUAL')
                        parts=receipt['candidate_id'].split('_')
                        move=moves[int(parts[1])] if parts[0]=='reallocation' else local_move.get(parts[1])
                        is_blocked=move is not None and memory.prohibited(move,i)
                        aspiration=key(x,sid)<key(prior_best,prior_best_sid)
                        blocked+=int(is_blocked);aspirations+=int(is_blocked and aspiration)
                        if not is_blocked or aspiration:admissible.append((key(x,sid),sid))
                    if min(admissible)[1]!=commit['adopted_hash']:violations.append(str(path)+':ADOPTION_REPLAY')
                    vals=[metric(x['metrics']) for x in feasible]
                    row=dict(scale=case['scale'],method=method,branch=branch,iteration=i,input_hash=state_hash,
                        attempted_reallocations=None,attempt_count_status='NOT_RECORDED',attempt_upper_bound=3*manifest['configuration']['search']['neighbor_attempts_per_family'],
                        changed_assignment_candidates=len(moves),unique_assignments=len({assignment_hash(decode_routes(x['routes'])) for x in moves}),
                        unique_route_candidates=len({digest_payload(x['routes']) for x in moves}),local_calls=calls,returned_candidates=len(orders),changed_orders=sum(orders),
                        locally_shorter_than_reallocated_order=local_better,
                        raw_quantum_shots=raw,completion_attempts=len(candidate_receipts),completion_successes=len(feasible),infeasible_reasons=str(dict(failure_counts)),
                        distance_improved=sum(x.D<ref.D for x in vals),wait_improved=sum(x.W<ref.W for x in vals),strict_dual=sum(x.D<ref.D and x.W<ref.W for x in vals),
                        distance_only_with_W_worse=sum(x.D<ref.D and x.W>ref.W for x in vals),
                        distance_equal=sum(x.D==ref.D for x in vals),distance_worse=sum(x.D>ref.D for x in vals),
                        wait_equal=sum(x.W==ref.W for x in vals),wait_worse=sum(x.W>ref.W for x in vals),
                        minimum_delta_D_km=float(min((x.D-ref.D for x in vals),default=F(0))) if vals else None,
                        minimum_delta_W_min=float(min((x.W-ref.W for x in vals),default=F(0))) if vals else None,
                        beats_pi0_selection=better_initial,best_generated_I_dual=max((index(x,ref) for x in vals),default=None),
                        best_archive_I_dual=max((index(x,ref) for x in archive.values()),default=None),
                        tabu_blocked=blocked,aspiration_admitted=aspirations,adopted=commit['adopted'],noninitial_transition=commit['adopted_hash']!=initial_hash,
                        remaining_completions=commit['remaining_completions'],completed_work=commit['counters']['completion_requests'],solver_stop_reasons=' | '.join(solver_stops),record=str(path))
                    rows.append(row);state=metric(commit['state_metrics']);state_hash=commit['adopted_hash'];best=metric(commit['best_metrics']);tabu=commit['tabu']
                result_path=work/'RESULT.json'
                if result_path.exists():
                    br=read(result_path);winner=min(archive,key=lambda sid:key(archive[sid],sid))
                    if winner!=br['best_incumbent_hash']:violations.append(str(result_path)+':ARCHIVE_FINAL_SELECTION')
                    disk={p.name.removesuffix('.plan.json') for p in (work/'archive').glob('*.plan.json')}
                    if disk!=set(archive):violations.append(str(result_path)+':UNACCOUNTED_ARCHIVE_PLAN')
                    if br['status']=='COMPLETE':final_candidates.append((selection_key(metric(br['metrics']),ref,initial=False,branch_id=branch,stable_id=br['metrics']['physical_hash']),br['metrics']['physical_hash']))
                    branches.append(dict(scale=case['scale'],method=method,branch=branch,status=br['status'],iterations=br['completed_iterations'],stop_reason=br['stop_reason'],
                        completions=br['counters']['completion_requests'],remaining=br['remaining_completions'],archive_size=br['archive_size'],final_hash=br['metrics']['physical_hash'],
                        final_initial=br['metrics']['physical_hash']==initial_hash))
            if min(final_candidates)[1]!=final['metrics']['physical_hash']:violations.append(str(trial/method/'RESULT.json')+':FOUR_BRANCH_SELECTION')
    csvwrite(destination/'ITERATION_DIAGNOSIS.csv',rows);csvwrite(destination/'BRANCH_DIAGNOSIS.csv',branches);csvwrite(destination/'BASELINES.csv',baseline_rows)
    result=dict(source=str(source),rows=len(rows),violations=violations,infeasible_reasons=dict(reasons),
        attempted_reallocations='NOT_RECORDED; maxima are not observed counts',
        categories=(['IMPLEMENTATION_OR_ARTIFACT_INCONSISTENCY'] if violations else ['finite work limit reached'])+
            (['no archived candidate beats pi0 under frozen selection'] if not any(x['beats_pi0_selection'] for x in rows) else ['archive improvement observed']),
        archive_improvements=sum(x['beats_pi0_selection'] for x in rows),distance_improvements=sum(x['distance_improved'] for x in rows),wait_improvements=sum(x['wait_improved'] for x in rows),
        strict_dual_candidates=sum(x['strict_dual'] for x in rows),completion_attempts=sum(x['completion_attempts'] for x in rows),completion_successes=sum(x['completion_successes'] for x in rows))
    dump(destination/'DIAGNOSIS.json',result);return result
