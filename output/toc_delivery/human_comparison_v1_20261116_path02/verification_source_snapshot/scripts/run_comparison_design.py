#!/usr/bin/env python3
"""Bounded comparison_v1 pilots -> frozen settings -> independent variance -> design table.

No formal runs are launched. Resume never overwrites or reruns an existing trial.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key]='1'


def plan_for(rules,profile,phase,repetitions,seed_root,lock=None):
    import numpy as np
    from kmd_toc.comparison_v1.contract import CONTRACT_ID,TIME_KIND,digest
    from kmd_toc.comparison_v1.design import METHODS,RULES_PATH
    rng=np.random.default_rng(seed_root)
    cases=[{'case_id':s,'scenario_id':'ota-toc-frozen-demand-v1:'+s,'scale':s,
            'input_dir':str(ROOT/'output/toc_delivery/ad_pipeline_20261112_route_v2/roads/inputs'/s),
            'budget_wall_s':profile['tau_s'],
            'case_parameters':{'BCD_epsilon_W_min':None,'BCD_native_cap_s':profile['native_cap_s']}}
           for s in rules['pilot']['scales']]
    runs=[];groups=[]
    for repeat in range(1,repetitions+1):
        batch=[]
        for case in cases:
            for method in METHODS:
                batch.append({'run_id':f'{phase}_{profile["id"]}_{case["case_id"]}_{method}_r{repeat}',
                    'case_id':case['case_id'],'method':method,'attempt_id':1,'repeat_id':repeat,
                    'pair_id':f'{case["case_id"]}_r{repeat}', 'retry_of':None,
                    'solver_seed':int(rng.integers(1,2**31-1)) if method!='A' else None,
                    'quantum_seed':int(rng.integers(1,2**31-1)) if method=='D' else None,
                    'reference_group_id':phase+'_'+case['case_id']+'_A'})
        rng.shuffle(batch);runs.extend(batch)
    for case in cases:
        members=[r['run_id'] for r in runs if r['case_id']==case['case_id'] and r['method']=='A']
        groups.append({'group_id':phase+'_'+case['case_id']+'_A','purpose':phase,
                       'required_count':len(members),'run_ids':members})
    return {'experiment_id':rules['experiment_id'],'contract_id':CONTRACT_ID,'T_kind':TIME_KIND,
        'phase':phase,'cases':cases,'runs':runs,'reference_groups':groups,
        'design_extension':{'rules_path':RULES_PATH,'rules_sha256':digest(ROOT/RULES_PATH),
            'profile':profile['id'],'settings_lock':lock,
            'dependency_prefix':rules['pilot']['dependency_prefix'],
            'tree_memory_limit_MiB':rules['pilot']['tree_memory_limit_MiB']}}


def stage(root,name,plan,*,resume=False,deadline=None):
    from kmd_toc.comparison_v1.contract import dump,read,register
    from kmd_toc.comparison_v1.execution import run_registered
    from kmd_toc.comparison_v1.evaluation import aggregate
    path=root/name
    if path.exists():
        if not resume:raise ValueError('EXPERIMENT_ALREADY_EXISTS')
        if not (path/'tables/ALL_ATTEMPTS.json').exists():
            raise ValueError('INCOMPLETE_STAGE_REQUIRES_AUDIT_NOT_AUTOMATIC_RERUN:'+name)
        return read(path/'REGISTERED.json'),read(path/'tables/ALL_ATTEMPTS.json')['rows']
    plan['design_extension']['pipeline_deadline_perf_counter']=deadline
    plan_path=root/(name+'_PLAN.json')
    revision=1
    while plan_path.exists() and resume:
        revision+=1
        plan_path=root/(name+f'_PLAN_r{revision}.json')
    dump(plan_path,plan)
    registered=register(plan_path,path)
    registered_manifest=read(registered)
    try:
        run_registered(registered)
    finally:
        # A correctly uses one core during T. Restore the shared allocation only
        # after the entire stage, before registration of the next stage.
        os.sched_setaffinity(0,set(registered_manifest['cpu_profile']['cpu_ids']))
    aggregate(registered,path/'tables')
    return read(registered),read(path/'tables/ALL_ATTEMPTS.json')['rows']


def execute(root,resume=False):
    from kmd_toc.comparison_v1.contract import read,dump,digest,fingerprint,check_freeze
    from kmd_toc.comparison_v1.design import RULES_PATH,setting_identity,require_same_settings
    from kmd_toc.comparison_v1.design_report import report
    rules=read(ROOT/RULES_PATH)
    started=time.perf_counter()
    root.mkdir(parents=True,exist_ok=resume)
    precommit=root/'PRECOMMIT.json'
    boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    previous_elapsed=0.
    if precommit.exists():
        clock=read(precommit)
        if 'pipeline_started_perf_counter' not in clock:
            amendment=root/'PIPELINE_CLOCK_AMENDMENT_R2.json'
            if amendment.exists():clock=read(amendment)
            else:
                # Original precommit omitted a monotonic clock. NFS mtimes can
                # have server clock skew. Bound start conservatively from the
                # persisted first job and include 300s pretrial preparation.
                jobs=[read(p) for p in root.glob('*/runs/*/job.json')]
                if not jobs:raise ValueError('RESUME_CLOCK_REQUIRES_AUDIT')
                origin=min(j['deadline_perf_counter']-j['case']['budget_wall_s'] for j in jobs)-300
                clock={'pipeline_started_perf_counter':origin,'boot_id':boot_id,
                    'scope':'conservative reconstructed start, 300s before first saved trial; no NFS wall timestamp used'}
                dump(amendment,clock)
        if clock['boot_id']!=boot_id:raise ValueError('RESUME_AFTER_REBOOT_REQUIRES_CLOCK_AUDIT')
        previous_elapsed=max(0.,started-clock['pipeline_started_perf_counter'])
    deadline=started+max(0.,rules['pilot']['maximum_pipeline_wall_s']-previous_elapsed)-300
    if not (root/'PREREGISTERED_RULES.json').exists():
        dump(root/'PREREGISTERED_RULES.json',rules)
        dump(root/'PRECOMMIT.json',{'rules_sha256':digest(ROOT/RULES_PATH),'before_first_trial':True,
            'pipeline_started_perf_counter':started,'boot_id':boot_id,
            'maximum_attempts':90,'maximum_sum_attempt_caps_s':19800,
            'maximum_pipeline_wall_s':rules['pilot']['maximum_pipeline_wall_s'],
            'pilot_is_not_implementation_smoke':True,'README_modified':False})
    elif fingerprint(read(root/'PREREGISTERED_RULES.json'))!=fingerprint(rules):
        raise ValueError('RULES_CHANGED_USE_NEW_EXPERIMENT_ID')
    check_freeze()
    selection=[]
    for index,profile in enumerate(rules['profiles']):
        m,rows=stage(root,'selection_'+profile['id'],plan_for(rules,profile,'selection_pilot',
            rules['pilot']['selection_repetitions'],rules['pilot']['seed_root']+index),resume=resume,deadline=deadline)
        calls={s:sum((r.get('native_resources') or {}).get('completed_quantum_call_observations') or 0
                    for r in rows if r['case_id']==s and r['method']=='D') for s in rules['pilot']['scales']}
        qualified=all(r['adoptable'] for r in rows) and all(calls.values())
        selection.append({'profile':profile,'qualified':bool(qualified),'quantum_calls':calls,
                          'manifest':m,'rows':rows})
        if time.perf_counter()-started>rules['pilot']['maximum_pipeline_wall_s']:
            raise TimeoutError('PIPELINE_WALL_LIMIT')
    chosen=next((s for s in selection if s['qualified']),selection[-1])
    lock=setting_identity(chosen['manifest'])
    if not (root/'SETTINGS_LOCK.json').exists():
        dump(root/'SETTINGS_LOCK.json',{'profile':chosen['profile'],'setting_identity':lock,
            'qualified':chosen['qualified'],'selection_rule':rules['selection'],
            'candidate_summary':[{k:s[k] for k in ('profile','qualified','quantum_calls')} for s in selection],
            'source_hashes':chosen['manifest']['source_hashes'],'input_cases':chosen['manifest']['cases'],
            'warning':'qualification is not statistical validation or optimality'})
    variance_m,variance_rows=stage(root,'variance',plan_for(rules,chosen['profile'],'variance_pilot',
        rules['pilot']['variance_repetitions'],rules['pilot']['seed_root']+100,lock),resume=resume,deadline=deadline)
    require_same_settings([chosen['manifest'],variance_m])
    confirm_m,confirm_rows=stage(root,'confirmation',plan_for(rules,chosen['profile'],'confirmation',
        rules['pilot']['confirmation_repetitions'],rules['pilot']['confirmation_seed_root'],lock),resume=resume,deadline=deadline)
    require_same_settings([variance_m,confirm_m])
    result=report(root,rules,selection,chosen,variance_m,variance_rows,confirm_m,confirm_rows)
    dump(root/'PIPELINE_COMPLETION.json',{'elapsed_this_invocation_s':time.perf_counter()-started,
        'elapsed_including_prior_invocations_s':previous_elapsed+time.perf_counter()-started,
        'status':result,'main_started':False,'frozen_A_valid':bool(check_freeze())})
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='output/toc_delivery/comparison_design_20261116_v1')
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--finalize-main',action='store_true',help='Register fixed main manifest after explicit precision/cost choices; never executes it')
    parser.add_argument('--h-D',type=float)
    parser.add_argument('--rate-halfwidth',type=float)
    parser.add_argument('--main-budget-s',type=float)
    parser.add_argument('--allocation',choices=['equal','cost_variance'],default='equal')
    parser.add_argument('--sensitivity',choices=['point','normal_variance_upper'],default='normal_variance_upper')
    parser.add_argument('--main-registration')
    args=parser.parse_args()
    if args.finalize_main:
        if any(v is None for v in (args.h_D,args.rate_halfwidth,args.main_budget_s,args.main_registration)):
            parser.error('explicit --h-D --rate-halfwidth --main-budget-s --main-registration required')
        finalize(Path(args.output).resolve(),args)
    else:
        execute(Path(args.output).resolve(),args.resume)


def finalize(root,args):
    from kmd_toc.comparison_v1.contract import read,dump,digest,fingerprint,register
    from kmd_toc.comparison_v1.design import RULES_PATH,setting_identity
    rules=read(ROOT/RULES_PATH);status=read(root/'design/STATUS.json')
    if status['engineering_blockers'] or not status['pilot_pipeline_complete']:
        raise ValueError('PILOT_ENGINEERING_GATE_NOT_PASSED')
    variance_manifest=read(root/'variance/REGISTERED.json')
    for name,expected in variance_manifest['source_hashes'].items():
        if digest(ROOT/name)!=expected:raise ValueError('CODE_OR_CONFIG_CHANGED_NEW_VARIANCE_PILOT_REQUIRED:'+name)
    candidate=next((c for c in read(root/'design/CANDIDATES.json') if c['scale']=='S2' and c['metric']=='D'
        and c['h']==args.h_D and c['rate_h']==args.rate_halfwidth and c['allocation']==args.allocation
        and c['sensitivity']==args.sensitivity and c['main_budget_candidate_s']==args.main_budget_s),None)
    if not candidate or not candidate['within_caps'] or candidate['zero_sample_variance']:
        raise ValueError('NO_CERTIFIABLE_REGISTERED_CANDIDATE_FOR_CHOICES')
    plan=plan_for(rules,status['selected_profile'],'formal',max(candidate['R_a'].values()),
        2026111701,setting_identity(variance_manifest))
    plan['runs']=[r for r in plan['runs'] if r['case_id']=='S2' and r['repeat_id']<=candidate['R_a'][r['method']]]
    plan['reference_groups']=[g for g in plan['reference_groups'] if g['group_id']=='formal_S2_A']
    members=[r['run_id'] for r in plan['runs'] if r['method']=='A']
    plan['reference_groups'][0].update(run_ids=members,required_count=len(members))
    plan['experiment_id']=rules['experiment_id']+'_main_S2'
    plan['main_scope']='fixed S2 only; S1/S3 are registered shared input identities, not main observations'
    plan['design_extension']['main_lock']={'h_D':args.h_D,'rate_h':args.rate_halfwidth,
        'budget_s':args.main_budget_s,'fixed_attempt_count':len(plan['runs']),
        'run_list_hash':fingerprint(plan['runs']),'stopping':'fixed_count'}
    target=Path(args.main_registration).resolve()
    plan_path=target.with_name(target.name+'_PLAN.json');dump(plan_path,plan)
    print(register(plan_path,target))


if __name__=='__main__':main()
