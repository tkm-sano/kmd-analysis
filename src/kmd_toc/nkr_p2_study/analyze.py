"""Derived tables and scientific figures; never starts a quantum job."""
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import csv
import gzip
import hashlib
import json
import os
from pathlib import Path
from statistics import mean

from .study import OUT,DOC,read,dump,check_pins
from .model import coverage,classification,relation

ANALYSIS_SOURCE_BYTES=Path(__file__).read_bytes()
ANALYSIS_SOURCE_SHA256=hashlib.sha256(ANALYSIS_SOURCE_BYTES).hexdigest()


def csvout(name, rows, fields=None):
    fields=fields or list(dict.fromkeys(k for r in rows for k in r))
    with (OUT/name).open('w') as stream:
        w=csv.DictWriter(stream,fieldnames=fields);w.writeheader()
        for r in rows:w.writerow({k:json.dumps(v) if isinstance(v,(dict,list,tuple)) else v for k,v in r.items()})


def progress_rows(path, exists=None):
    if exists is False or (exists is None and not path.exists()):return []
    result=[]
    for line in path.read_text().splitlines():
        try:result.append(json.loads(line))
        except json.JSONDecodeError:continue
    return result


def nondominated(rows, keys):
    return [r for r in rows if not any(all(other[k]<=r[k] for k in keys) and any(other[k]<r[k] for k in keys) for other in rows)]


def closed_call_payload(call_dir):
    """Independent read-only I/O; map preserves the original call ordering."""
    files={entry.name for entry in os.scandir(call_dir)}
    if 'CALL.json' not in files:return call_dir,None
    return call_dir,{'files':files,'metadata':read(call_dir/'CALL.json'),
        'progress':progress_rows(call_dir/'evaluations.jsonl',exists='evaluations.jsonl' in files),
        **{key:read(call_dir/name) if name in files else None for key,name in
           [('quantum','RESULT.json'),('failure','FAILURE.json'),('assessment','ASSESSMENT.json')]}}


def closed_payloads(call_dirs):
    """Read bounded batches in order; used only for finished groups."""
    with ThreadPoolExecutor(max_workers=8) as readers:
        for offset in range(0,len(call_dirs),64):
            yield from readers.map(closed_call_payload,call_dirs[offset:offset+64])


def analyze(figures=True):
    check_pins();groups=[];branches=[];calls=[];iterations=[];candidates=[];all_sets={};raw_groups={}
    for path in sorted((OUT/'groups').glob('*/GROUP.json')):
        group=read(path);tag=group['tag'];raw_groups[tag]=group
        if 'scale' not in group:continue
        gsets=[];branch_d=[];branch_w=[];cpu=[];rss=[];quantum_seconds=[];g_calls=[];g_candidates=[]
        generated=oracle_pass=capacity_screened=checked_total=feasible_total=0
        resolved_d=[];resolved_w=[]
        initial_centers=None;adopted_count_changes=0
        base=group['initial'];N={'S1':1000,'S2':2000,'S3':4000}[group['scale']]
        for folder in sorted(path.parent.glob('branch_*')):
            result_path=folder/'RESULT.json';partial=folder/'PARTIAL.json'
            r=read(result_path) if result_path.exists() else read(partial) if partial.exists() else {'rows':[],'iterations':[]}
            generated+=sum(bool(row.get('generated')) for row in r.get('rows',[]))
            oracle_pass+=sum('oracle_check' in row for row in r.get('rows',[]))
            if r.get('after'):
                delta_d=r['after']['D_km']-base['D_km'];delta_w=r['after']['W_mean_min_per_operation']-base['W_mean_min_per_operation']
                branch_d.append(delta_d);branch_w.append(delta_w)
                resolved_d.append(round(delta_d*10000)/10000)
                resolved_w.append(round((r['after']['W_total_min']-base['W_total_min'])*60)/(60*r['after']['operation_count']))
            else:delta_d=delta_w=None
            bsets=[];b_calls=[]
            call_root=folder/'calls'
            call_dirs=sorted(Path(entry.path) for entry in os.scandir(call_root) if entry.is_dir()) if call_root.is_dir() else []
            # No quantum work: overlap independent NFS reads, then aggregate in
            # exactly the same sorted order. Bound memory to one branch.
            for call_dir,payload in closed_payloads(call_dirs):
                if payload is None:continue
                files=payload['files'];metadata=payload['metadata'];progress=payload['progress']
                completed=[e for e in progress if e['event']=='sampling_completed']
                started=[e for e in progress if e['event']=='sampling_started']
                for e in completed:
                    assert e['actual_shots']==sum(e['counts'].values())==e['requested_shots']
                    assert e['depth_p']==2 and e['TV_bound']<=1e-6
                    assert e['requested_shots']==(1000 if e['phase']=='optimization' else 10000)
                assert metadata['depth_p']==2 and metadata['optimization_shots']==1000 and metadata['final_extraction_shots']==10000
                quantum=payload['quantum'];failure=payload['failure']
                failed_bound=None
                if not quantum and 'updates.jsonl.gz' in files:
                    try:
                        with gzip.open(call_dir/'updates.jsonl.gz','rt') as stream:
                            for line in stream:
                                update=json.loads(line);v=update.get('truncation_trace_bound')
                                if v is not None:failed_bound=v if failed_bound is None else max(failed_bound,v)
                    except (EOFError,OSError,json.JSONDecodeError):pass
                assessment=payload['assessment']
                ids=set(metadata['local']['customer_ids'])
                if initial_centers is None:
                    width=group['n']//2;initial_centers=set()
                    for route in metadata['local']['outside_routes']:
                        original=route['original_customers'];offset=(len(original)-width)//2
                        if len(original)>=width:initial_centers.update(original[offset:offset+width])
                previous=set().union(*bsets) if bsets else set()
                if completed:bsets.append(ids);gsets.append(ids)
                call={'tag':tag,'scale':group['scale'],'n':group['n'],'K':group['K'],'R':group['R'],
                    'outer_seed':group['outer_seed'],'branch':int(folder.name.split('_')[-1]),'call_id':call_dir.name,
                    'status':'COMPLETE' if quantum else 'FAILED_OR_PARTIAL','customer_ids':sorted(ids),
                    'new_customer_slots':len(ids-previous),'repeated_customer_slots':len(ids & previous),
                    'all_customers_repeated':bool(previous) and ids<=previous,
                    'optimizer_seed':metadata['seed'],'optimizer_evaluations':sum(e['phase']=='optimization' for e in completed),
                    'optimizer_success':quantum.get('optimizer_success') if quantum else None,
                    'optimizer_message':quantum.get('optimizer_message') if quantum else None,
                    'optimization_shots_actual':sum(e['actual_shots'] for e in completed if e['phase']=='optimization'),
                    'final_shots_actual':sum(e['actual_shots'] for e in completed if e['phase']=='final_extraction'),
                    'inflight_shots':None if len(started)!=len(completed) else 0,
                    'failure_reason':failure.get('error') if failure else None,'failed_call_max_observed_bound':failed_bound,
                    'max_TV_bound_complete_states':max((e['TV_bound'] for e in completed),default=None),
                    'wall_s':quantum['wall_s'] if quantum else None,'CPU_s':quantum['CPU_s'] if quantum else None,
                    'RSS_MiB':quantum['RSS_highwater_MiB'] if quantum else None,
                    'adopted':assessment['adopted'] if assessment else None,
                    'adoption_classification':classification(assessment['before'],assessment['after']) if assessment else None,
                    'plan_yield':assessment['assessment']['plan_yield'] if assessment else None,
                    'feasible_checked':assessment['assessment']['feasible_checked'] if assessment else None,
                    'checked':assessment['assessment']['checked'] if assessment else None,
                    'all_shots_physical_rate':None,'path':str(call_dir.relative_to(OUT))}
                qt=quantum.get('timing',{}) if quantum else {}
                at=assessment['assessment']['timing'] if assessment else {}
                count_change=None
                if assessment and assessment['adopted']:
                    current_metrics=assessment['before'];decision=None
                    for candidate in assessment['assessment']['ledger']:
                        if candidate.get('status')=='ACCEPT' and relation(current_metrics,candidate['metrics'])=='ACCEPT':
                            current_metrics=candidate['metrics'];decision=candidate['decision']
                    assert current_metrics==assessment['after'] and decision is not None
                    targets=[tuple(t) for t in metadata['local']['trip_ids']]
                    route_map={tuple(r['trip_id']):r['original_customers'] for r in metadata['local']['outside_routes']}
                    old_counts=[len(set(route_map[t]) & ids) for t in targets]
                    new_counts=[len(decision['trip_1']),len(decision['trip_2'])]
                    count_change=old_counts!=new_counts
                    adopted_count_changes+=int(count_change)
                call.update({
                    'quantum_problem_s':qt.get('problem_s'),'SDK_circuit_s':qt.get('circuit_s'),
                    'optimizer_inclusive_s':qt.get('optimizer_inclusive_s'),'final_evolution_s':qt.get('final_evolution_s'),
                    'final_sampling_s':qt.get('final_sampling_s'),'decode_sort_s':qt.get('decode_sort_s'),
                    'decode_scoring_all_evaluations_s':qt.get('scoring_s'),
                    'completion_s':at.get('completion_s'),'physical_validation_s':at.get('validation_s'),
                    'DW_reevaluation_s':at.get('reevaluation_s'),'acceptance_s':at.get('acceptance_s'),'candidate_save_s':at.get('save_s'),
                    'timing_overlap':'optimizer inclusive contains optimization evolution/sampling/decode-scoring; do not sum inclusive with internal totals'})
                call['adopted_trip_cardinality_changed']=count_change
                calls.append(call);g_calls.append(call);b_calls.append(call)
                if quantum:quantum_seconds.append(quantum['wall_s'])
                if assessment:
                    capacity_screened+=assessment['assessment']['capacity_screened']
                    checked_total+=assessment['assessment']['checked']
                    feasible_total+=assessment['assessment']['feasible_checked']
                    for c in assessment['assessment']['ledger']:
                        if 'metrics' not in c:continue
                        candidate={'tag':tag,'scale':group['scale'],'n':group['n'],'K':group['K'],'R':group['R'],
                            'branch':call['branch'],'call_id':call_dir.name,'D':c['metrics']['D_km'],'W':c['metrics']['W_mean_min_per_operation'],
                            'W_total':c['metrics']['W_total_min'],'delta_D':c['metrics']['D_km']-base['D_km'],
                            'delta_W':c['metrics']['W_mean_min_per_operation']-base['W_mean_min_per_operation'],
                            'status':c['status'],'plan':c['plan'],'elapsed_branch_wall_s':assessment['elapsed_wall_s']}
                        candidates.append(candidate);g_candidates.append(candidate)
            after=r.get('after') or {}
            b=int(folder.name.split('_')[-1]);brow={'tag':tag,'scale':group['scale'],'n':group['n'],'K':group['K'],'R':group['R'],
                'outer_seed':group['outer_seed'],'branch':b,'status':r.get('status','INCOMPLETE'),'reason':r.get('reason'),
                'delta_D':delta_d,'delta_W':delta_w,'D':after.get('D_km'),
                'W':after.get('W_mean_min_per_operation'),'W_total':after.get('W_total_min'),
                'delta_W_total':after['W_total_min']-base['W_total_min'] if after else None,
                'operation_count':after.get('operation_count'),'loading_W_min':after.get('loading_W_min'),
                'unloading_W_min':after.get('unloading_W_min'),'other_W_min':after.get('other_W_min'),
                'wait_incidence_pct':after.get('wait_incidence_pct'),**coverage(bsets,N),
                'quantum_calls_complete':sum(c['status']=='COMPLETE' for c in b_calls),'quantum_calls_with_sampled_states':len(bsets),
                'optimizer_evaluations':sum(c['optimizer_evaluations'] for c in b_calls),
                'optimization_shots_actual':sum(c['optimization_shots_actual'] for c in b_calls),
                'final_shots_actual':sum(c['final_shots_actual'] for c in b_calls),
                'CPU_s':r.get('CPU_s'),'wall_s':r.get('wall_s'),'RSS_highwater_MiB':r.get('RSS_highwater_MiB')}
            brow['stage_times']=r.get('timings')
            if brow['CPU_s'] is not None:cpu.append(brow['CPU_s'])
            if brow['RSS_highwater_MiB'] is not None:rss.append(brow['RSS_highwater_MiB'])
            branches.append(brow)
            for iteration in r.get('iterations',[]):
                ir=[c for c in b_calls if c['call_id'].startswith(f"r{iteration['r']:03d}_")]
                iterations.append({'tag':tag,'scale':group['scale'],'n':group['n'],'K':group['K'],'R':group['R'],
                    'outer_seed':group['outer_seed'],'branch':b,'delta_D_cumulative':iteration['D']-base['D_km'],
                    'delta_W_cumulative':iteration['W']-base['W_mean_min_per_operation'],
                    'customer_sets':[c['customer_ids'] for c in ir],
                    'max_completed_state_TV_bound':max((c['max_TV_bound_complete_states'] for c in ir if c['max_TV_bound_complete_states'] is not None),default=None),
                    'end_reason':'COMPLETED_ITERATION',**iteration})
        result={'tag':tag,'scale':group['scale'],'n':group['n'],'K':group['K'],'R':group['R'],'P':group['P'],
            'outer_seed':group['outer_seed'],'status':group['status'],'reason':group['reason'],
            'E_plan_four_branches':4*group['n']*group['K']*group['R'],**coverage(gsets,N),
            'initial_center_pool_size':len(initial_centers) if initial_centers is not None else None,
            'U_outside_initial_centers':len(set().union(*gsets)-initial_centers) if gsets and initial_centers is not None else None,
            'adopted_trip_cardinality_changes':adopted_count_changes,
            'delta_D_branch_mean':mean(branch_d) if len(branch_d)==group['P'] else None,
            'delta_W_branch_mean':mean(branch_w) if len(branch_w)==group['P'] else None,
            'comparison_D_resolved_branch_mean':mean(resolved_d) if len(resolved_d)==group['P'] else None,
            'comparison_W_resolved_branch_mean':mean(resolved_w) if len(resolved_w)==group['P'] else None,
            'delta_D_min':min(branch_d,default=None),'delta_D_max':max(branch_d,default=None),
            'delta_W_min':min(branch_w,default=None),'delta_W_max':max(branch_w,default=None),
            'parent_wall_s':group['parent_wall_s'],'CPU_workers_sum_s':sum(cpu) if len(cpu)==group['P'] else None,
            'parent_CPU_s':None,'max_worker_RSS_MiB':max(rss+[b['sampled_peak_RSS_MiB'] for b in group['branch_results']],default=None),
            'worker_RSS_scope':'worker ru_maxrss when available; sampled lower bounds for stopped workers',
            'whole_group_peak_RSS_MiB':None,
            'quantum_wall_workers_sum_s':sum(quantum_seconds),'quantum_calls_completed':sum(c['status']=='COMPLETE' for c in g_calls),
            'generated_local_candidates':generated,'oracle_passed_local_candidates':oracle_pass,
            'sampled_capacity_screened_outputs':capacity_screened,'top3_checked_candidates':checked_total,'top3_feasible_candidates':feasible_total,
            'optimizer_evaluations':sum(c['optimizer_evaluations'] for c in g_calls),
            'optimizer_reported_success_calls':sum(c['optimizer_success'] is True for c in g_calls),
            'optimizer_reported_unsuccessful_calls':sum(c['optimizer_success'] is False for c in g_calls),
            'optimization_shots_actual':sum(c['optimization_shots_actual'] for c in g_calls),
            'final_shots_actual':sum(c['final_shots_actual'] for c in g_calls),
            'adopted_calls':sum(bool(c['adopted']) for c in g_calls),
            'resolved_improved_calls':sum(c['adoption_classification'] in ('BOTH_STRICT','D_ONLY','W_ONLY') for c in g_calls),
            'adoption_rate':sum(bool(c['adopted']) for c in g_calls)/len(g_calls) if g_calls else None,
            'plan_yield':mean(c['plan_yield'] for c in g_calls if c['plan_yield'] is not None) if any(c['plan_yield'] is not None for c in g_calls) else None,
            'initial_plan_generation_s':None,'full_main_planning_time_s':None}
        groups.append(result);all_sets[tag]=gsets
    csvout('GROUPS.csv',groups);csvout('BRANCHES.csv',branches);csvout('CALLS.csv',calls);csvout('ITERATIONS.csv',iterations);csvout('CANDIDATES.csv',candidates)
    group_iterations=[]
    for tag in {row['tag'] for row in iterations}:
        group=next(g for g in groups if g['tag']==tag);N={'S1':1000,'S2':2000,'S3':4000}[group['scale']]
        for r in sorted({row['r'] for row in iterations if row['tag']==tag}):
            points=[row for row in iterations if row['tag']==tag and row['r']==r]
            cs=[c for c in calls if c['tag']==tag and int(c['call_id'][1:4])<=r and c['optimizer_evaluations']>0]
            group_iterations.append({'tag':tag,'scale':group['scale'],'n':group['n'],'K':group['K'],'R_planned':group['R'],'r':r,
                'branches_at_completed_iteration':len(points),'all_branches_at_iteration':len(points)==group['P'],
                **coverage([set(c['customer_ids']) for c in cs],N),
                'D_branch_mean':mean(p['D'] for p in points),'W_branch_mean':mean(p['W'] for p in points),
                'adopted_in_iteration':sum(p['adopted'] for p in points),
                'max_branch_cumulative_wall_s':max(p['cumulative_wall_s'] for p in points),'parent_prefix_wall_s':None})
    csvout('GROUP_ITERATIONS.csv',group_iterations)
    grid=[]
    for scale,V in [('S1',10),('S2',20),('S3',40)]:
        for n in (10,12):
            for K in (V//2,V,2*V):
                for R in (5,13,25):
                    match=next((g for g in groups if g['scale']==scale and g['n']==n and g['K']==K and g['R']==R and g['P']==4 and g['outer_seed']==9201),None)
                    tag=f'screen_{scale}_n{n}_K{K}_R{R}_seed9201';gate=OUT/'gates'/(tag+'.json')
                    started=(OUT/'groups'/tag/'branch_0/JOB.json').exists() and not (OUT/'groups'/tag/'GROUP.json').exists()
                    grid.append({'scale':scale,'n':n,'K':K,'R':R,'E_plan_per_branch':n*K*R,'E_plan_four_branches':4*n*K*R,
                        'status':match['status'] if match else 'IN_PROGRESS' if started else 'NOT_RUN',
                        'not_run_reason':'STARTED_NO_FINAL_GROUP_YET' if started else read(gate).get('reason') if gate.exists() and not match else 'STAGED_NOT_SELECTED_OR_RESOURCE_GATED' if not match else None,
                        **{k:match.get(k) if match else None for k in ['E','U','coverage','repeat_rate','delta_D_branch_mean','delta_W_branch_mean',
                            'delta_D_min','delta_D_max','delta_W_min','delta_W_max','parent_wall_s','quantum_calls_completed','optimizer_evaluations','max_worker_RSS_MiB']}})
    assert len(grid)==54;csvout('ALL54.csv',grid)
    plans=[]
    for tag in raw_groups:
        plans+=nondominated([r for r in candidates if r['tag']==tag],['D','W'])
    csvout('NONDOMINATED_PLANS.csv',plans)
    complete=[r for r in groups if r['status']=='COMPLETE' and r['P']==4 and r['outer_seed']==9201]
    pareto=[]
    for scale in ('S1','S2','S3'):
        pareto+=nondominated([r for r in complete if r['scale']==scale],['comparison_D_resolved_branch_mean','comparison_W_resolved_branch_mean','parent_wall_s'])
    csvout('PARETO_CONDITIONS.csv',pareto)
    decision='CONDITIONAL' if any(g['comparison_D_resolved_branch_mean']<0 or g['comparison_W_resolved_branch_mean']<0 for g in complete) else 'HOLD'
    dump(OUT/'DECISION.json',{'status':decision,'adopted_n':None,'adopted_K_coefficient':None,'adopted_R':None,
        'reason':'formal selection requires completed K/R comparison, measured interaction and unused-optimizer-seed confirmation; fixed demand only; no common T optimality claim',
        'promising_measured_candidates':[{'scale':r['scale'],'n':r['n'],'K':r['K'],'R':r['R']} for r in pareto if r['comparison_D_resolved_branch_mean']<0 or r['comparison_W_resolved_branch_mean']<0],
        'comparison_precision':'branch D deltas at 0.1m, total wait deltas at 1s converted to mean per-operation; raw values retained'})
    summary={'groups_including_probes':len(groups),'complete_54_conditions':sum(r['status']=='COMPLETE' for r in grid),
        'in_progress_54_conditions':sum(r['status']=='IN_PROGRESS' for r in grid),
        'incomplete_54_conditions':sum(r['status']=='INCOMPLETE' for r in grid),'not_run_54_conditions':sum(r['status']=='NOT_RUN' for r in grid),
        'actual_quantum_calls_complete':sum(r['status']=='COMPLETE' for r in calls),
        'actual_objective_evaluations':sum(r['optimizer_evaluations'] for r in calls),
        'actual_optimization_shots':sum(r['optimization_shots_actual'] for r in calls),'actual_final_shots':sum(r['final_shots_actual'] for r in calls),
        'max_completed_state_TV_bound':max((r['max_TV_bound_complete_states'] for r in calls if r['max_TV_bound_complete_states'] is not None),default=None),
        'decision':decision,'main_experiment':False,'current_p':2,'current_shots':[1000,10000]}
    dump(OUT/'SUMMARY.json',summary)
    if figures:plots(groups,iterations)
    revisions=OUT/'source_revisions';revisions.mkdir(exist_ok=True)
    snapshot=revisions/f'analyze_{ANALYSIS_SOURCE_SHA256}.py'
    if not snapshot.exists():snapshot.write_bytes(ANALYSIS_SOURCE_BYTES)
    dump(OUT/'ANALYSIS_PROVENANCE.json',{'analysis_source_sha256':ANALYSIS_SOURCE_SHA256,'figures_generated':figures,
        'group_hashes':{str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((OUT/'groups').glob('*/GROUP.json'))},
        'source_snapshot':str(snapshot.relative_to(OUT))})
    return summary


def plots(groups,iterations):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    dest=OUT/'figures';dest.mkdir(exist_ok=True)
    measured=[g for g in groups if g['P']==4 and g['status']=='COMPLETE' and g['outer_seed']==9201]
    def finish(fig,name):
        fig.tight_layout();fig.savefig(dest/(name+'.png'),dpi=160);fig.savefig(dest/(name+'.pdf'));plt.close(fig)
    def empty(ax):ax.text(.5,.5,'No complete comparisons measured',ha='center',va='center',transform=ax.transAxes)
    for key,name,label in [('delta_D_branch_mean','01_nkr_D','Delta D (km; branch mean)'),('delta_W_branch_mean','02_nkr_W','Delta W (min/operation; branch mean)')]:
        fig,axes=plt.subplots(1,3,figsize=(14,4))
        for ax,scale in zip(axes,['S1','S2','S3']):
            subset=[g for g in measured if g['scale']==scale];ax.set_title(scale)
            if subset:
                ax.bar(range(len(subset)),[g[key] for g in subset]);ax.set_xticks(range(len(subset)),[f"{g['n']}/{g['K']}/{g['R']}" for g in subset],rotation=65)
            else:empty(ax)
            ax.axhline(0,color='black',lw=.5);ax.set_ylabel(label);ax.set_xlabel('n / K / R')
        finish(fig,name)
    for x,name in [('K','03_K_time'),('R','04_R_time')]:
        fig,axes=plt.subplots(1,3,figsize=(13,4))
        for ax,scale in zip(axes,['S1','S2','S3']):
            V={'S1':10,'S2':20,'S3':40}[scale]
            subset=[g for g in measured if g['scale']==scale and (g['R']==5 if x=='K' else g['K']==V//2)]
            ax.set_title(f'{scale} (R=5)' if x=='K' else f'{scale} (K={V//2}=V/2)')
            for n,marker in [(10,'o'),(12,'s')]:
                points=[g for g in subset if g['n']==n]
                if points:ax.scatter([g[x] for g in points],[g['parent_wall_s'] for g in points],marker=marker,label=f'n={n}')
            if not subset:empty(ax)
            else:ax.legend()
            ax.set_xlabel(x);ax.set_ylabel('Measured parent wall (s)')
        finish(fig,name)
    fig,axes=plt.subplots(2,3,figsize=(14,7))
    for col,scale in enumerate(['S1','S2','S3']):
        points=[r for r in iterations if r['scale']==scale and not r['tag'].startswith('probe')]
        for row,key in enumerate(['delta_D_cumulative','delta_W_cumulative']):
            ax=axes[row,col]
            if not points:empty(ax)
            for tag in sorted({r['tag'] for r in points}):
                subset=[r for r in points if r['tag']==tag];byr=defaultdict(list)
                for r in subset:byr[r['r']].append(r[key])
                group=next(g for g in groups if g['tag']==tag);status=group['status']
                byr={r:values for r,values in byr.items() if len(values)==group['P']}
                ax.plot(sorted(byr),[mean(byr[r]) for r in sorted(byr)],label=tag.replace('screen_','')+(' [partial]' if status!='COMPLETE' else ''),
                    marker='.',linestyle='-' if status=='COMPLETE' else '--')
            ax.set_title(scale);ax.set_xlabel('Completed iteration');ax.set_ylabel('Delta D (km)' if row==0 else 'Delta W (min/op)')
        if points:axes[0,col].legend(fontsize=5)
    finish(fig,'05_R_cumulative_DW')
    fig,axes=plt.subplots(2,3,figsize=(13,7))
    for col,scale in enumerate(['S1','S2','S3']):
        subset=[g for g in measured if g['scale']==scale]
        for ax,key,label in zip(axes[:,col],['delta_D_branch_mean','delta_W_branch_mean'],['Delta D (km)','Delta W (min/op)']):
            for n,marker in [(10,'o'),(12,'s')]:
                points=[g for g in subset if g['n']==n]
                if points:ax.scatter([g['coverage'] for g in points],[g[key] for g in points],marker=marker,label=f'n={n}')
            if not subset:empty(ax)
            else:ax.legend(fontsize=7)
            ax.set_title(scale);ax.set_xlabel('Measured union coverage');ax.set_ylabel(label)
    finish(fig,'06_coverage_DW')
    fig,axes=plt.subplots(1,3,figsize=(13,4))
    for ax,scale in zip(axes,['S1','S2','S3']):
        subset=[g for g in measured if g['scale']==scale]
        for n,marker in [(10,'o'),(12,'s')]:
            points=[g for g in subset if g['n']==n]
            if points:ax.scatter([g['repeat_rate'] for g in points],[g['adoption_rate'] for g in points],marker=marker,label=f'n={n}')
        if not subset:empty(ax)
        else:ax.legend(fontsize=7)
        ax.set_title(scale);ax.set_xlabel('Repeat rate');ax.set_ylabel('Adopted calls / calls')
    finish(fig,'07_repeats_adoption')
    fig=plt.figure(figsize=(16,5))
    for i,scale in enumerate(['S1','S2','S3'],1):
        ax=fig.add_subplot(1,3,i,projection='3d');points=[g for g in measured if g['scale']==scale]
        if points:
            for n,marker in [(10,'o'),(12,'s')]:
                ns=[g for g in points if g['n']==n]
                if ns:ax.scatter([g['delta_D_branch_mean'] for g in ns],[g['delta_W_branch_mean'] for g in ns],[g['parent_wall_s'] for g in ns],marker=marker,alpha=.6,label=f'n={n}')
            for g in points:ax.text(g['delta_D_branch_mean'],g['delta_W_branch_mean'],g['parent_wall_s'],f" {g['n']}/{g['K']}/{g['R']}",fontsize=6)
            front=nondominated(points,['comparison_D_resolved_branch_mean','comparison_W_resolved_branch_mean','parent_wall_s'])
            ax.scatter([g['delta_D_branch_mean'] for g in front],[g['delta_W_branch_mean'] for g in front],[g['parent_wall_s'] for g in front],
                marker='*',s=100,c='none',edgecolors='black',label='Non-dominated')
            ax.legend(fontsize=6)
        else:ax.text2D(.1,.5,'No complete comparisons',transform=ax.transAxes)
        ax.set_title(scale+' (branch means)');ax.set_xlabel('Delta D (km)');ax.set_ylabel('Delta W (min/op)');ax.set_zlabel('Parent wall (s)')
    finish(fig,'08_DW_time_pareto')
    fig,axes=plt.subplots(1,2,figsize=(11,4));probes=[g for g in groups if g['P']==1]
    for ax,key,label in zip(axes,['parent_wall_s','max_worker_RSS_MiB'],['Probe parent wall (s)','Probe worker peak RSS (MiB)']):
        for n in [10,12]:
            subset=[g for g in probes if g['n']==n and g.get(key) is not None]
            if subset:ax.scatter([g['scale'] for g in subset],[g[key] for g in subset],label=f'n={n}')
        if not probes:empty(ax)
        else:ax.legend()
        ax.set_ylabel(label)
    finish(fig,'09_n_resources')


if __name__=='__main__':print(json.dumps(analyze(),indent=2))
