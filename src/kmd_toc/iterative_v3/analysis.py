"""Saved-plan verification and descriptive output; pilots never become main J."""
from pathlib import Path
import csv,math,time
from .io import *
from .physical import metrics
from kmd_toc.descriptive_v1.statistics import summary,relative,dual
from kmd_toc.objective_alignment_v1.objective import measure

def csvfile(path,rows):
    with Path(path).open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def aggregate(directory):
    root=Path(directory);m=read(root/'MANIFEST.json');folders=root/'analysis';folders.mkdir(exist_ok=True)
    out=folders/f'{len(list(folders.iterdir()))+1:03d}';out.mkdir();rows=[];paired=[];chains=[];statuses=[]
    for case in m['cases']:
        trial=root/case['output_subdir'];path=trial/'RESULT.json'
        if not path.exists():
            partial=sorted(trial.glob('PARTIAL_*.json'))
            statuses.append(dict(scale=case['scale'],trial_id=case['trial_id'],status='INCOMPLETE_NOT_CLASSIFIED' if trial.exists() else 'NOT_STARTED',
                formal_J_contribution=0))
            if not partial:continue
            path=partial[-1]
        else:statuses.append(dict(scale=case['scale'],trial_id=case['trial_id'],status='COMPLETE',formal_J_contribution=m['formal_J_contribution']))
        result=read(path);p=load_problem(case['input'],m['configuration']['rest_options'])
        b=result['conditions']['B'];baseline=load_plan(b['plan']);ref=measure(p,baseline)
        if identity(baseline)!=result['initial_hash']:raise ValueError('INITIAL_HASH_AGGREGATION_MISMATCH')
        verified={}
        for method,row in result['conditions'].items():
            if not row['plan'] or row['status'] not in ('COMPLETE','COMPLETE_FOUR_BRANCHES'):continue
            plan=load_plan(row['plan']);actual=metrics(p,plan,ref)
            if actual!=row['metrics']:raise ValueError('SAVED_FINAL_METRICS_AGGREGATION_MISMATCH')
            verified[method]=actual
            rows.append(dict(scale=case['scale'],trial_id=case['trial_id'],seed=case['seed'],method=method,status=row['status'],
                D=actual['D_km'],W=actual['W_total_min'],first_W=actual['first_trip_W_min'],second_W=actual['second_trip_W_min'],
                active_trips=actual['active_trips'],I_dual_pi0=actual['I_dual_percent'],
                I_dual_C_posthoc=row.get('C_reference_posthoc',{}).get('I_dual_percent'),
                initial_hash=result['initial_hash'],final_hash=actual['physical_hash'],plan=row['plan'],
                formal_J_contribution=result['formal_J_contribution'],model_feasible=actual['model_feasible'],site_feasibility=actual['site_feasibility']))
        for a,b in [('B','C_Idual'),('B','D_quantum'),('C_Idual','D_quantum'),('D_classical','D_quantum')]:
            if a in verified and b in verified:
                x,y=verified[a],verified[b]
                paired.append(dict(scale=case['scale'],trial_id=case['trial_id'],baseline=a,candidate=b,
                    delta_D=y['D_km']-x['D_km'],delta_W=y['W_total_min']-x['W_total_min'],
                    relative_D_percent=relative(x['D_km'],y['D_km']),relative_W_percent=relative(x['W_total_min'],y['W_total_min']),
                    strict_dual=y['D_km']<x['D_km'] and y['W_total_min']<x['W_total_min'],
                    pairing_basis='same registered trial/problem/immutable pi0; not seed integer matching',formal_J_contribution=result['formal_J_contribution']))
        for method in ('D_classical','D_quantum'):
            for b in range(4):
                folder=trial/method/f'branch_{b}/work';previous=result['initial_hash']
                for path in sorted(folder.glob('iteration_*/COMMIT.json')):
                    c=read(path);prep=read(path.parent/'PREPARED.json')
                    if c['input_hash']!=previous or prep['input_hash']!=previous:raise ValueError('ADAPTIVE_CONTENT_CHAIN_BROKEN')
                    plan=load_plan(c['adopted_plan_path']);checked=metrics(p,plan,ref)
                    if identity(plan)!=c['adopted_hash'] or checked!=c['state_metrics']:raise ValueError('ADOPTED_PLAN_REPLAY_MISMATCH')
                    chains.append(dict(scale=case['scale'],method=method,branch=b,iteration=c['iteration'],input_hash=c['input_hash'],
                        adopted_hash=c['adopted_hash'],adopted=c['adopted'],adopted_origin=c['adopted_origin'],
                        best_incumbent_hash=c['best_incumbent_hash'],remaining=c['remaining_completions']))
                    previous=c['adopted_hash']
    if rows:csvfile(out/'RESULTS.csv',rows)
    csvfile(out/'TRIAL_STATUS.csv',statuses)
    if paired:csvfile(out/'PAIRED_DIFFERENCES.csv',paired)
    if chains:csvfile(out/'STATE_CHAINS.csv',chains)
    summaries=[];contrasts=[]
    formal_data='MAIN' in m['configuration']['role'] and m['configuration'].get('formal_J_confirmed',False)
    for scale in m['configuration']['scales']:
        for method in ('B','C_Idual','D_classical','D_quantum'):
            subset=[r for r in rows if r['scale']==scale and r['method']==method]
            for metric in ('D','W','I_dual_pi0'):
                values=[r[metric] for r in subset if r[metric] is not None];s=summary(values,independent=formal_data)
                # Existing summary J denotes observed count; rename to avoid
                # suggesting these registered pilots contribute to formal J.
                s['observed_records']=s.pop('J');s['formal_outer_J']=len(values) if formal_data else 0
                s['planned_trials']=sum(x['scale']==scale for x in m['cases']);s['successful_trials']=len(subset)
                s['success_fraction']=len(subset)/s['planned_trials'] if s['planned_trials'] else None
                summaries.append(dict(scale=scale,method=method,metric=metric,**s))
        for baseline,candidate in [('B','C_Idual'),('B','D_quantum'),('C_Idual','D_quantum'),('D_classical','D_quantum')]:
            data=[r for r in paired if r['scale']==scale and r['baseline']==baseline and r['candidate']==candidate]
            for metric in ('delta_D','delta_W'):
                s=summary([r[metric] for r in data],independent=formal_data);s['observed_pairs']=s.pop('J')
                contrasts.append(dict(scale=scale,baseline=baseline,candidate=candidate,metric=metric,**s,
                    strict_dual_count=sum(r['strict_dual'] for r in data),matched_trials=len(data),
                    strict_dual_fraction=sum(r['strict_dual'] for r in data)/len(data) if data else None))
    dump(out/'DESCRIPTIVE.json',summaries)
    dump(out/'PAIRED_DESCRIPTIVE.json',contrasts)
    index_of_means=[]
    for scale in m['configuration']['scales']:
        def mean_for(method,metric):
            values=[r[metric] for r in rows if r['scale']==scale and r['method']==method]
            return sum(values)/len(values) if values else None
        d0,w0=mean_for('B','D'),mean_for('B','W')
        for method in ('C_Idual','D_classical','D_quantum'):
            d,w=mean_for(method,'D'),mean_for(method,'W')
            index_of_means.append(dict(scale=scale,method=method,I_dual_of_mean_DW=dual(d0,w0,d,w) if None not in (d0,w0,d,w) else None,
                scope='index of means, NOT mean of trial indices; MCSE for nonlinear estimand unapproved'))
    dump(out/'IDUAL_OF_MEANS.json',index_of_means)
    # Plots only when sufficient observed repeated records exist. Do not fake
    # trial distributions from the 4 branches or scales.
    plots='NOT_CREATED_SINGLE_PILOT_PER_SCALE; SD/MCSE undefined; no fake boxes/bars'
    if any(x['observed_records']>=2 for x in summaries):
        try:
            import matplotlib;matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            for scale in m['configuration']['scales']:
                for metric in ('D','W'):
                    methods=['B','C_Idual','D_classical','D_quantum'];sets=[[r[metric] for r in rows if r['scale']==scale and r['method']==k] for k in methods]
                    fig,ax=plt.subplots();ax.boxplot(sets,labels=methods,whis=1.5);ax.set_title(f'{scale} {metric} '+('registered main' if formal_data else 'pilot only'));fig.savefig(out/f'{scale}_{metric}_box.png');plt.close(fig)
                    fig,ax=plt.subplots()
                    for i,values in enumerate(sets):
                        s=summary(values)
                        if s['mean'] is not None:ax.errorbar(i,s['mean'],yerr=s['SD'],fmt='o',label=methods[i])
                    ax.set_xticks(range(len(methods)),methods);ax.set_title(f'{scale} {metric} mean +/- sample SD');fig.savefig(out/f'{scale}_{metric}_SD.png');plt.close(fig)
            plots='pilot-only Tukey boxes; per-scale no pooling'
        except ImportError:plots='HOLD_MATPLOTLIB_NOT_AVAILABLE_NO_ENVIRONMENT_MUTATION'
    r=dict(output=str(out),verified_saved_plans=len(rows),verified_adaptive_transitions=len(chains),
        formal_outer_trials_added=len({r['trial_id'] for r in rows}) if formal_data else 0,statistics='descriptive only; per scale; SD ddof1; MCSE only justified independent repeated trials',plots=plots)
    dump(out/'RESULT.json',r);atomic(root/'LATEST_ANALYSIS.json',r);return r

def readiness(directory):
    destination=Path(directory);registration=read(destination/'MANIFEST.json');proposed=registration['configuration']
    root=Path(proposed.get('pilot_evidence',destination)) if 'MAIN' in proposed['role'] else destination
    m=read(root/'MANIFEST.json');c=m['configuration'];checks=[]
    for case in m['cases']:
        path=root/case['output_subdir']/'RESULT.json'
        if not path.exists():checks.append(dict(scale=case['scale'],completed=False));continue
        r=read(path);stage=dict(scale=case['scale'],completed=r['status']=='COMPLETE',actual_order_sizes=[],
            actual_quantum_calls=0,adopted_state_chain_verified=True,inter_vehicle_moves=False,intra_trip_moves=False,
            fixed_assignment_verified=True,finite_work_completed=True)
        for method in ('D_classical','D_quantum'):
            for b in range(4):
                folder=root/case['output_subdir']/method/f'branch_{b}/work';previous=r['initial_hash']
                for commit in sorted(folder.glob('iteration_*/COMMIT.json')):
                    v=read(commit)
                    if v['input_hash']!=previous:stage['adopted_state_chain_verified']=False
                    previous=v['adopted_hash']
                    for move in v['moves']:
                        for d in move['membership_diff']:
                            stage['inter_vehicle_moves']|=d['before'][0]!=d['after'][0]
                            stage['intra_trip_moves']|=d['before'][0]==d['after'][0] and d['before'][1]!=d['after'][1]
                if method=='D_quantum':
                    for call in folder.glob('iteration_*/local_*/solver/RESULT.json'):
                        q=read(call);stage['actual_quantum_calls']+=1
                        size=len(read(call.parent/'CALL.json')['problem']['ids']);stage['actual_order_sizes'].append(size)
                        if q['p']!=2 or q['optimization_shots']!=1000 or q['final_shots']!=10000:stage['fixed_assignment_verified']=False
                    for decoded in folder.glob('iteration_*/local_*/DECODED_*.json'):
                        v=read(decoded)
                        if v['assignment_before']!=v['assignment_after']:stage['fixed_assignment_verified']=False
        checks.append(stage)
    evidence=bool(checks) and all(x.get('completed') and x.get('actual_quantum_calls',0)>0 and
        x.get('fixed_assignment_verified') and x.get('adopted_state_chain_verified') and x.get('inter_vehicle_moves') and x.get('intra_trip_moves') and
        set(x.get('actual_order_sizes',[]))=={c['search']['local_order_size']} for x in checks)
    scale_ready=evidence and set(c['scales'])=={'S1','S2','S3'} and c['search']['local_order_size']==12
    matching=proposed['search']==c['search'] and proposed['rest_options']==c['rest_options'] and registration['code_hashes']==m['code_hashes']
    diagnostic=c.get('diagnostic_evidence');transition_proof=False
    if diagnostic:
        dr=Path(diagnostic);dm=read(dr/'MANIFEST.json') if (dr/'MANIFEST.json').exists() else None
        if dm and dm['code_hashes']==m['code_hashes']:
            for path in dr.glob('*/D_*/branch_*/work/iteration_0000/COMMIT.json'):
                first=read(path);second=path.parent.parent/'iteration_0001/PREPARED.json'
                if first['adopted'] and second.exists() and read(second)['input_hash']==first['adopted_hash'] and first['input_hash']!=first['adopted_hash']:
                    transition_proof=True
    r=dict(REGISTERED_RUN_COMPLETE=evidence,IMPLEMENTATION_AND_SCALE_PILOT_READY=scale_ready and transition_proof,
        EXPERIMENT_READY=scale_ready and transition_proof and matching and proposed.get('formal_J_confirmed',False),
        evidence_directory=str(root),matching_main_configuration=matching,nontrivial_adoption_transition_verified=transition_proof,
        main_experiment_authorized=proposed['main_experiment_authorized'],formal_J_confirmed=proposed.get('formal_J_confirmed',False),J_proposal=proposed['J_proposal'],
        reason='formal J remains unconfirmed; request approval of concrete main manifest before main execution' if evidence else 'missing execution evidence',
        scale_checks=checks,exact_pricing_required=False,route_column_combination_required=False,
        site_feasibility='MODEL_ONLY_UNVERIFIED_STOPPING_SITES',old54_restarted=False)
    atomic(destination/'READINESS.json',r);return r
