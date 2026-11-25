"""Trial-first descriptive analysis with separate primary and control cohorts."""
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
import csv
from kmd_toc.iterative_v3.io import read,dump,atomic,sha,load_problem,read_initial,load_plan,identity
from kmd_toc.iterative_v3.physical import metrics
from kmd_toc.objective_alignment_v1.objective import measure
from kmd_toc.descriptive_v1.statistics import summary
from .plan import preflight,METHODS

def delta(x,y):
    """Candidate x vs reference y, exact stored physical metric units."""
    d,w,rd,rw=(F(x['D_exact']),F(x['W_exact']),F(y['D_exact']),F(y['W_exact']))
    rD=100*(rd-d)/rd if rd>0 else None;rW=100*(rw-w)/rw if rw>0 else None
    return dict(delta_D_km=float(d-rd),delta_W_min=float(w-rw),relative_D_percent=float(rD) if rD is not None else None,
        relative_W_percent=float(rW) if rW is not None else None,I_dual_percent=float(min(rD,rW)) if rD is not None and rW is not None else None,
        strict_dual=d<rd and w<rw,nonworse=d<=rd and w<=rw,
        tolerance_D_km=0,tolerance_W_min=0,unit='percent; differences km/min')

def stat(values):
    z=summary(values,independent=True);z['J_eff']=z.pop('J');z.pop('formal_J',None)
    return dict(planned_J=30,**z)

def summarize(records):
    output=[];pairs=[];cohorts=[];status=[]
    for scale in ('S1','S2','S3'):
        data=[r for r in records if r['scale']==scale]
        primary=[r for r in data if all(r['methods'][k]['eligible'] for k in ('C_Idual','D_quantum'))]
        control=[r for r in data if all(r['methods'][k]['eligible'] for k in ('D_classical','D_quantum'))]
        cohorts.append(dict(scale=scale,primary_trial_ids=[r['trial_id'] for r in primary],control_trial_ids=[r['trial_id'] for r in control],
            primary_J_eff=len(primary),control_J_eff=len(control),planned_J=30,conditional_on_common_normal_completion=True))
        for method in METHODS:
            valid=[r for r in data if r['methods'][method]['eligible']]
            scopes=[('method_valid',valid),('primary_matched',primary)] if method in ('C_Idual','D_quantum') else [('method_valid',valid)]
            if method in ('D_classical','D_quantum'):scopes.append(('control_matched',control))
            for scope,cohort in scopes:
                values=[r['methods'][method] for r in cohort]
                for metric in ('D_km','W_total_min','I_dual_pi0_percent','I_dual_C_posthoc_percent'):
                    v=[r[metric] for r in values if r[metric] is not None]
                    output.append(dict(scale=scale,method=method,scope=scope,metric=metric,**stat(v),
                        undefined_count=sum(r[metric] is None for r in values),trial_ids=[r['trial_id'] for r in cohort]))
            counts=Counter(r['methods'][method]['status'] for r in data)
            status.append(dict(scale=scale,method=method,planned=30,status_counts=dict(counts),valid=len(valid),
                normal_initial_retained=counts['NORMAL_INITIAL_RETAINED'],fallbacks=counts['ERROR_FALLBACK'],
                normal_changed=counts['NORMAL_CHANGED'],not_started=counts['NOT_STARTED']))
        for name,cohort,baseline,candidate in [('primary_B_C',primary,'B','C_Idual'),('primary_B_Q',primary,'B','D_quantum'),
                ('primary_C_Q',primary,'C_Idual','D_quantum'),('control_classical_quantum',control,'D_classical','D_quantum')]:
            values=[]
            for r in cohort:
                d=delta(r['methods'][candidate]['metrics'],r['baseline_metrics'] if baseline=='B' else r['methods'][baseline]['metrics'])
                candidate_i=delta(r['methods'][candidate]['metrics'],r['baseline_metrics'])['I_dual_percent']
                baseline_i=delta(r['baseline_metrics'] if baseline=='B' else r['methods'][baseline]['metrics'],r['baseline_metrics'])['I_dual_percent']
                d['delta_I_dual_pi0_percentage_points']=candidate_i-baseline_i if candidate_i is not None and baseline_i is not None else None
                values.append(dict(scale=scale,trial_id=r['trial_id'],comparison=name,baseline=baseline,candidate=candidate,**d))
            for metric in ('delta_D_km','delta_W_min','relative_D_percent','relative_W_percent','I_dual_percent','delta_I_dual_pi0_percentage_points'):
                v=[r[metric] for r in values if r[metric] is not None]
                pairs.append(dict(scale=scale,comparison=name,baseline=baseline,candidate=candidate,metric=metric,**stat(v),
                    strict_dual_count=sum(r['strict_dual'] for r in values),strict_dual_fraction=sum(r['strict_dual'] for r in values)/len(values) if values else None,
                    paired_trial_ids=[r['trial_id'] for r in values],values=values if metric=='delta_D_km' else None))
    return dict(method_statistics=output,paired_statistics=pairs,cohorts=cohorts,status=status,
        fixed_B_is_reference_not_independent_sample=True,I_dual_aggregation='compute each trial first, then summarize; no substitution by index of mean D/W',
        precision='achieved MCSE, no a-priori target and no sequential J adjustment',hypothesis_testing=False)

def collect(m,out):
    records=[];fixed={};references=[]
    for scale in m['configuration']['scales']:
        case=next(x for x in m['cases'] if x['scale']==scale);p=load_problem(case['input'],m['configuration']['rest_options'])
        baseline=read_initial(m['fixed_initials'][scale]['directory']).checked_plan(p);ref=measure(p,baseline);base=metrics(p,baseline,ref)
        fixed[scale]=base;references.append(dict(scale=scale,metrics=base,unique_plan_count=1,independent_observations=0,
            reference_uses_planned=30,SD=None,MCSE=None,role='fixed reference, never a pseudo trial distribution'))
        for case in [x for x in m['cases'] if x['scale']==scale]:
            trial=out/case['output_subdir'];path=trial/'RESULT.json';partial=sorted(trial.glob('PARTIAL_*.json'))
            if not path.exists():path=partial[-1] if partial else None
            root=read(path) if path else None;methods={}
            root_ok=root is not None and root.get('trial_id')==case['trial_id'] and root.get('seed')==case['seed'] and root.get('initial_hash')==identity(baseline)
            for method in METHODS:
                row=root.get('conditions',{}).get(method) if root else None
                status='NOT_STARTED' if not trial.exists() else 'INCOMPLETE_OR_UNCOMMITTED';eligible=False;actual=None;reason=None
                if row and row.get('plan'):
                    try:
                        plan=load_plan(row['plan']);actual=metrics(p,plan,ref)
                        if not root_ok or actual!=row['metrics']:raise ValueError('TRIAL_OR_SAVED_METRICS_MISMATCH')
                        normal=row['status']==('COMPLETE' if method=='C_Idual' else 'COMPLETE_FOUR_BRANCHES')
                        if method=='C_Idual' and normal:
                            pointer=read(trial/'C_Idual/C_CURRENT.json');directory=Path(pointer['directory']).resolve()
                            cr=read(directory/'RESULT.json');job=read(trial/'C_Idual/JOB.json')
                            if not directory.is_relative_to((trial/'C_Idual/solver_attempts').resolve()) or cr['trial_id']!=case['trial_id'] or cr['initial_plan_sha256']!=case['initial_plan_sha256'] or job['seed']!=case['seed'] or job['code_hashes']!=m['code_hashes']:
                                raise ValueError('C_FORMAL_EXECUTION_PROVENANCE_MISMATCH')
                        if method.startswith('D_') and normal:
                            if len(row.get('branches',[]))!=4 or any(x['status']!='COMPLETE' or x['trial_id']!=case['trial_id'] or x['pi0_hash']!=identity(baseline) for x in row['branches']):
                                raise ValueError('FOUR_NORMAL_BRANCHES_NOT_PROVEN')
                            for b in range(4):
                                work=trial/method/f'branch_{b}/work';br=read(work/'RESULT.json')
                                job=read(work.parent/'JOB.json');expected=case['streams'][method+'_branch_seeds'][b]
                                if br['status']!='COMPLETE' or br['branch']!=b or br['seed']!=expected or job['seed']!=expected or job['code_hashes']!=m['code_hashes'] or br['metrics']!=row['branches'][b]['metrics']:raise ValueError('BRANCH_ARTIFACT_MISMATCH')
                        eligible=normal;status=('NORMAL_INITIAL_RETAINED' if identity(plan)==identity(baseline) else 'NORMAL_CHANGED') if normal else 'ERROR_FALLBACK'
                    except (ValueError,OSError,KeyError) as e:status='INVALID';reason=str(e);eligible=False
                elif row:status='FAILED_OR_MISSING';reason=row.get('status')
                methods[method]=dict(status=status,eligible=eligible,reason=reason,metrics=actual,
                    D_km=actual['D_km'] if actual else None,W_total_min=actual['W_total_min'] if actual else None,
                    I_dual_pi0_percent=actual['I_dual_percent'] if actual else None,I_dual_C_posthoc_percent=None,
                    saved_plan=row.get('plan') if row else None)
            if methods['C_Idual']['eligible']:
                for method in METHODS:
                    if methods[method]['metrics'] is not None:
                        methods[method]['I_dual_C_posthoc_percent']=delta(methods[method]['metrics'],methods['C_Idual']['metrics'])['I_dual_percent']
            records.append(dict(scale=scale,trial_id=case['trial_id'],seed=case['seed'],baseline_metrics=base,methods=methods,
                result_record=str(path) if path else None,execution_state='NOT_STARTED' if not trial.exists() else 'RECORDED'))
    return records,references

def csvwrite(path,rows):
    if not rows:return
    with Path(path).open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def aggregate(manifest,output):
    preflight(manifest,output);m=read(manifest);out=Path(output).resolve();folders=out/'analysis';folders.mkdir(exist_ok=True)
    target=folders/f'{len(list(folders.iterdir()))+1:03d}';target.mkdir()
    records,refs=collect(m,out);report=summarize(records)
    dump(target/'TRIAL_RECORDS.json',records);dump(target/'FIXED_B_REFERENCES.json',refs);dump(target/'DESCRIPTIVE.json',report)
    rows=[]
    for r in records:
        for method,v in r['methods'].items():
            rows.append(dict(scale=r['scale'],trial_id=r['trial_id'],seed=r['seed'],method=method,status=v['status'],eligible=v['eligible'],
                D_km=v['D_km'],W_total_min=v['W_total_min'],I_dual_pi0_percent=v['I_dual_pi0_percent'],I_dual_C_posthoc_percent=v['I_dual_C_posthoc_percent'],reason=v['reason'],plan=v['saved_plan']))
    csvwrite(target/'TRIAL_STATUS_AND_RESULTS.csv',rows)
    pairs=[v for p in report['paired_statistics'] if p['values'] for v in p['values']];csvwrite(target/'PAIRED_TRIAL_DIFFERENCES.csv',pairs)
    plots=[]
    if any(x['J_eff']>=2 for x in report['method_statistics']):
        import matplotlib;matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        for scale in m['configuration']['scales']:
            for metric in ('D_km','W_total_min','I_dual_pi0_percent'):
                fig,axes=plt.subplots(1,2);bucket=[];labels=[]
                for j,method in enumerate(METHODS):
                    values=[r['methods'][method][metric] for r in records if r['scale']==scale and r['methods'][method]['eligible'] and r['methods'][method][metric] is not None]
                    if not values:continue
                    z=stat(values);labels.append(method);bucket.append(values)
                    axes[1].errorbar([j],[z['mean']],yerr=[z['SD']] if z['SD'] is not None else None,fmt='o')
                if bucket:axes[0].boxplot(bucket,tick_labels=labels,whis=1.5,showfliers=True)
                if metric in ('D_km','W_total_min'):
                    value=next(r['metrics'][metric] for r in refs if r['scale']==scale)
                    for ax in axes:ax.axhline(value,label='fixed B reference')
                axes[1].set_xticks(range(3),METHODS);axes[1].set_title('Mean +/- 1 sample SD; not MCSE');fig.suptitle(f'{scale} {metric}')
                fig.savefig(target/f'{scale}_{metric}.png');plt.close(fig);plots.append(f'{scale}_{metric}.png')
            for metric in ('delta_D_km','delta_W_min','I_dual_percent','delta_I_dual_pi0_percentage_points'):
                data=[x for x in report['paired_statistics'] if x['scale']==scale and x['metric']==metric and x['J_eff']>0]
                if not data:continue
                fig,ax=plt.subplots()
                for j,z in enumerate(data):ax.errorbar([j],[z['mean']],yerr=[z['SD']] if z['SD'] is not None else None,fmt='o')
                ax.set_xticks(range(len(data)),[x['comparison'] for x in data],rotation=20)
                ax.set_title(f'{scale} paired {metric}: mean +/- sample SD');fig.tight_layout()
                name=f'{scale}_paired_{metric}.png';fig.savefig(target/name);plt.close(fig);plots.append(name)
    result=dict(output=str(target),planned_cases=90,normal_method_observations=sum(v['eligible'] for r in records for v in r['methods'].values()),
        unique_fixed_B_references=3,independent_B_observations=0,plots=plots,
        execution_state=read(out/'EXECUTION_STATE.json')['state'] if (out/'EXECUTION_STATE.json').exists() else 'NOT_STARTED',
        hashes={str(p):sha(p) for p in [Path(manifest),target/'TRIAL_RECORDS.json',Path(__file__)]},precision_target=None,J_fixed=30)
    dump(target/'ANALYSIS_MANIFEST.json',result);atomic(out/'LATEST_ANALYSIS.json',result);return result
