"""Registered pilot/main-capable orchestration; main remains authorization gated."""
from pathlib import Path
import subprocess,os,sys,time,resource,fcntl
from .io import *
from .physical import metrics
from kmd_toc.cd_comparison_v2.resources import sample
from kmd_toc.cd_comparison_v2.runner import physical_cores
from kmd_toc.common_initial_v1.plans import create_initial
from kmd_toc.objective_alignment_v1.objective import measure,selection_key

def validate_config(c):
    if (c['p'],c['optimization_shots'],c['final_shots'])!=(2,1000,10000):raise ValueError('P_SHOTS_FREEZE')
    if c['physical_cores']!=4 or c['native_threads']!=1:raise ValueError('FOUR_BRANCH_NATIVE1_CONTRACT')
    s=c['search']
    for k in ('outer_iterations','moves_per_family','neighbor_attempts_per_family','tabu_tenure','local_calls_per_iteration','local_order_size','returned_order_candidates','physical_completion_budget'):
        if type(s[k]) is not int or s[k]<1:raise ValueError('FINITE_POSITIVE_WORK_REQUIRED:'+k)
    if s['mode']!='adaptive_adopted_plan' or s['local_order_size']<2:raise ValueError('ADOPTED_STATE_ARCHITECTURE_REQUIRED')
    if c['limits']['wall_time_limit'] is not None or c['limits']['predictive_time_exclusion']:raise ValueError('OLD_TIME_CAPS_MUST_NOT_RETURN')
    if c.get('diagnostic_initial_routes') and 'DIAGNOSTIC' not in c['role']:raise ValueError('FIXTURE_INITIAL_FORBIDDEN_IN_SCALE_PILOT_OR_MAIN')

def register(config,path,*,diagnostic_inputs=None):
    from kmd_toc.d_local_design.pipeline import INPUTS
    c=read(config);validate_config(c);out=Path(path).resolve();out.mkdir(parents=True,exist_ok=False)
    cases=[];files={};pins=sources();cfg=read(ROOT/'configs/toc_delivery/termination_rules_20261116_v1.json')
    for scale in c['scales']:
        inp=Path(diagnostic_inputs[scale]) if diagnostic_inputs else INPUTS/scale
        p=load_problem(inp,c['rest_options']);N,V,B=len(p.stops),len(p.vehicles),len(p.berths)
        if not diagnostic_inputs and (N,V,B)!={'S1':(1000,10,2),'S2':(2000,20,4),'S3':(4000,40,8)}[scale]:raise ValueError('SCALE_FREEZE_MISMATCH')
        for f in inp.rglob('*'):
            if f.is_file():files[str(f.resolve())]=sha(f)
        repeats=c['J_proposal'] if 'MAIN' in c['role'] else c['pilot_trials_per_scale']
        for j in range(repeats):
            seed=c['registered_seeds'][scale] if repeats==1 else int(__import__('numpy').random.SeedSequence([c['registered_seeds'][scale],j,17]).generate_state(1)[0])
            cases.append(dict(scale=scale,input=str(inp.resolve()),seed=seed,outer_index=j,
                output_subdir=scale if repeats==1 else f'{scale}/trial_{j:03d}',
                trial_id=f'{c["role"]}_{scale}_{seed}_{j}',problem_hash=p.fingerprint,od_hash=p.od.fingerprint,N=N,V=V,berths=B))
    m=dict(version='iterative-v3',configuration=c,configuration_source=str(Path(config).resolve()),configuration_sha256=sha(config),
        cases=cases,input_hashes=files,code_hashes=pins,classical_configuration=cfg,
        formal_J_contribution=0 if 'PILOT' in c['role'] or 'DIAGNOSTIC' in c['role'] else 1,
        p=2,shots=dict(training=1000,final=10000),execution_order='scale S1 then S2 then S3; methods sequential; four branches within each D',
        no_C_final_in_D_inputs=True)
    dump(out/'MANIFEST.json',m);(out/'MANIFEST.json').chmod(0o444)
    dump(out/'REGISTRATION.json',dict(manifest_sha256=sha(out/'MANIFEST.json'),all_seeds_and_work_fixed_before_run=True))
    return m

def verify_manifest(out):
    out=Path(out);m=read(out/'MANIFEST.json')
    if sha(out/'MANIFEST.json')!=read(out/'REGISTRATION.json')['manifest_sha256']:raise ValueError('MANIFEST_CHANGED')
    verify_pins(m['code_hashes'])
    for p,h in m['input_hashes'].items():
        if sha(p)!=h:raise ValueError('REGISTERED_INPUT_CHANGED:'+p)
    return m

def supervise(jobs,directory,config):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    executions=directory/'executions';executions.mkdir(exist_ok=True);attempt=executions/f'{len(list(executions.iterdir()))+1:03d}';attempt.mkdir()
    children=[];handles=[];begin=time.perf_counter();cpu=time.process_time()
    child_before=resource.getrusage(resource.RUSAGE_CHILDREN);peak=0;reason=None
    env={**os.environ,'PYTHONPATH':str(ROOT/'src'),'PYTHONDONTWRITEBYTECODE':'1',
        **{k:'1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}}
    try:
        for j,job in enumerate(jobs):
            h=(attempt/f'process_{j}.log').open('x');handles.append(h)
            executable=config['classical_python'] if job['action']=='_classical' else config['branch_python']
            c=subprocess.Popen([executable,'-B',str(ROOT/'scripts/run_iterative_v3.py'),job['action'],'--job',str(job['path'])],cwd=ROOT,
                env=env,stdout=h,stderr=subprocess.STDOUT,start_new_session=True)
            children.append(c);dump(attempt/f'PID_{j}.json',dict(PID=c.pid,identity=sample(c.pid)))
        with (attempt/'RESOURCES.jsonl').open('x') as trace:
            while any(c.poll() is None for c in children):
                ps=[x for c in children if c.poll() is None and (x:=sample(c.pid)) is not None]
                rss=sum(x['RSS_bytes'] for x in ps)+sample(os.getpid())['RSS_bytes'];peak=max(peak,rss)
                trace.write(__import__('json').dumps(dict(elapsed_s=time.perf_counter()-begin,tree_RSS_bytes=rss,processes=ps))+'\n');trace.flush()
                if any(x['RSS_bytes']>config['limits']['per_worker_rss_mib']*2**20 for x in ps):reason='MEASURED_WORKER_RSS_LIMIT'
                if rss>config['limits']['tree_rss_mib']*2**20:reason='MEASURED_TREE_RSS_LIMIT'
                import shutil
                if shutil.disk_usage(directory).free<config['limits']['minimum_free_disk_gib']*2**30:reason='MEASURED_DISK_LIMIT'
                if reason:
                    for c in children:
                        if c.poll() is None:c.terminate()
                    break
                time.sleep(.25)
        codes=[c.wait() for c in children]
    except BaseException:
        for c in children:
            if c.poll() is None:c.terminate()
        for c in children:c.wait()
        raise
    finally:
        for h in handles:h.close()
        after=resource.getrusage(resource.RUSAGE_CHILDREN)
        dump(attempt/'RESOURCES.json',dict(wall_s=time.perf_counter()-begin,parent_CPU_s=time.process_time()-cpu,
            all_child_CPU_s=(after.ru_utime+after.ru_stime)-(child_before.ru_utime+child_before.ru_stime),
            sampled_tree_RSS_MiB=peak/2**20,reason=reason,scope='fresh process startup, input load, search, validation and save included; no wall deadline'))
    return codes,reason

def classical_helper(job):
    verify_pins(job['code_hashes']);p=load_problem(job['input'],job['rest_options']);out=Path(job['output']);out.mkdir(parents=True,exist_ok=True)
    if job['stage']=='initial':
        if (out/'B_CURRENT.json').exists():return read(out/'B_CURRENT.json')['status']=='COMPLETE'
        attempts=out/'initial_attempts';attempts.mkdir(exist_ok=True);attempt=attempts/f'{len(list(attempts.iterdir()))+1:03d}';attempt.mkdir()
        generator=None
        if job.get('diagnostic_initial_routes'):
            from kmd_toc.duty_break_v1.scheduler import schedule
            generator=lambda p,seed:schedule(p,decode_routes(job['diagnostic_initial_routes']),'B')
        capsule=create_initial(p,attempt/'initial',experiment_id='ITERATIVE_V3',scale=job['scale'],trial_id=job['trial_id'],
            seed=job['seed']%(2**31-1),config=job['classical_configuration'],generator=generator)
        atomic(out/'B_CURRENT.json',dict(status=capsule.manifest['status'],directory=str(capsule.directory)))
        return capsule.manifest['status']=='COMPLETE'
    initial=read_initial(job['initial_directory'])
    from kmd_toc.cd_comparison_v2.comparison import run_C
    if (out/'C_CURRENT.json').exists():return read(out/'C_CURRENT.json')['status']=='COMPLETE'
    attempts=out/'solver_attempts';attempts.mkdir(exist_ok=True);attempt=attempts/f'{len(list(attempts.iterdir()))+1:03d}'
    r=run_C(p,initial,attempt,config=job['classical_configuration'],seed=job['seed'])
    atomic(out/'C_CURRENT.json',dict(status=r['status'],directory=str(attempt)))
    return r['status']=='COMPLETE'

def run_trial(manifest,case,directory):
    c=manifest['configuration'];out=Path(directory);out.mkdir(parents=True,exist_ok=True);p=load_problem(case['input'],c['rest_options'])
    common=dict(**case,rest_options=c['rest_options'],classical_configuration=manifest['classical_configuration'],code_hashes=manifest['code_hashes'],
        diagnostic_initial_routes=c.get('diagnostic_initial_routes'))
    initial_group=out/'B';initial_group.mkdir(exist_ok=True)
    if not (initial_group/'B_CURRENT.json').exists():
        # An incomplete setup has its own attempt directory; completed initial
        # plans are never regenerated and never replaced on resume.
        job=initial_group/'JOB.json'
        if not job.exists():dump(job,{**common,'stage':'initial','output':str(initial_group.resolve())})
        codes,reason=supervise([dict(action='_classical',path=job)],initial_group,c)
        if any(codes) or reason:return dict(status='FAILED_COMMON_INITIAL',scale=case['scale'],reason=reason,exit_codes=codes)
    initial_path=Path(read(initial_group/'B_CURRENT.json')['directory'])
    initial=read_initial(initial_path)
    if initial.manifest['status']!='COMPLETE':return dict(status='FAILED_COMMON_INITIAL',scale=case['scale'])
    base=initial.checked_plan(p);ref=measure(p,base)
    cg=out/'C_Idual';cg.mkdir(exist_ok=True)
    if not (cg/'C_CURRENT.json').exists():
        job=cg/'JOB.json'
        if not job.exists():dump(job,{**common,'stage':'C','initial_directory':str(initial_path.resolve()),'output':str(cg.resolve())})
        supervise([dict(action='_classical',path=job)],cg,c)
    conditions={};conditions['B']=dict(metrics=metrics(p,base,ref),plan=str(initial_path/'plan.json'),status='COMPLETE')
    current=read(cg/'C_CURRENT.json') if (cg/'C_CURRENT.json').exists() else {}
    cdir=Path(current['directory']) if current else cg/'unavailable'
    cpath=cdir/'plan.json';cr=cdir/'RESULT.json'
    if cr.exists() and cpath.exists():conditions['C_Idual']=dict(status=read(cr)['status'],metrics=metrics(p,load_plan(cpath),ref),plan=str(cpath))
    else:conditions['C_Idual']=dict(status='FAILED_NO_RESULT',metrics=None,plan=None)
    cpus=physical_cores()
    for condition in ('D_classical','D_quantum'):
        print(case['scale'],condition,'START',flush=True);folder=out/condition;folder.mkdir(exist_ok=True);jobs=[]
        for b in range(4):
            branch=folder/f'branch_{b}';branch.mkdir(exist_ok=True);path=branch/'JOB.json'
            seed=int(__import__('numpy').random.SeedSequence([case['seed'],b,3]).generate_state(1)[0])
            job=dict(condition=condition,settings=c['search'],seed=seed,branch=b,cpu=cpus[b],input=case['input'],
                rest_options=c['rest_options'],initial_directory=str(initial_path.resolve()),output=str((branch/'work').resolve()),
                code_hashes=manifest['code_hashes'])
            if path.exists():
                if digest_payload(read(path))!=digest_payload(job):raise ValueError('RESUME_JOB_CHANGED')
            else:dump(path,job)
            if not (branch/'work/RESULT.json').exists():jobs.append(dict(action='_branch',path=path))
        if jobs:supervise(jobs,folder,c)
        plans=[dict(branch=None,plan=base)]
        branches=[]
        for b in range(4):
            path=folder/f'branch_{b}/work/RESULT.json';planpath=folder/f'branch_{b}/work/plan.json'
            if not path.exists() or not planpath.exists():branches.append(dict(branch=b,status='MISSING'));continue
            r=read(path);plan=load_plan(planpath)
            if r['trial_id']!=case['trial_id'] or r['pi0_hash']!=identity(base):raise ValueError('BRANCH_INITIAL_OR_TRIAL_MISMATCH')
            if r['metrics']!=metrics(p,plan,ref):raise ValueError('BRANCH_FINAL_METRICS_MISMATCH')
            branches.append(r)
            # A completed branch with a local-generator failure still has a
            # validated best full plan, possibly from classical reallocation.
            # Preserve it as a fallback, while keeping the run PARTIAL.
            if r['status'] in ('COMPLETE','COMPLETE_WITH_LOCAL_FAILURES'):
                plans.append(dict(branch=b,plan=plan))
        def key(x):return selection_key(measure(p,x['plan']),ref,initial=x['branch'] is None,branch_id=x['branch'] or 0,stable_id=identity(x['plan']))
        selected=min(plans,key=key);plan=selected['plan']
        complete_four=sum(r['status']=='COMPLETE' for r in branches)==4
        # Partial snapshots are immutable and versioned. A later recovered
        # branch may select a different plan; it must not overwrite the old
        # partial plan or conflict with an already-final canonical path.
        partial_index=len(list(folder.glob('PARTIAL_*.json')))+1
        plan_path=folder/('plan.json' if complete_four else f'partial_plan_{partial_index:03d}.json')
        save_plan(plan_path,plan)
        row=dict(status='COMPLETE_FOUR_BRANCHES' if complete_four else 'PARTIAL_FAILED_OR_MISSING_BRANCHES',
            metrics=metrics(p,plan,ref),plan=str(plan_path),selected_branch=selected['branch'],branches=branches)
        if row['status']=='COMPLETE_FOUR_BRANCHES':
            if not (folder/'RESULT.json').exists():dump(folder/'RESULT.json',row)
        else:dump(folder/f'PARTIAL_{len(list(folder.glob("PARTIAL_*.json")))+1:03d}.json',row)
        atomic(folder/'STATUS.json',dict(status=row['status']))
        conditions[condition]=row;print(case['scale'],condition,row['status'],row['metrics']['D_km'],row['metrics']['W_total_min'],flush=True)
    # C-reference indices are created only after both independent D searches.
    cm=measure(p,load_plan(conditions['C_Idual']['plan'])) if conditions['C_Idual']['plan'] else None
    for name,row in conditions.items():
        if row['plan'] and cm is not None:
            from kmd_toc.objective_alignment_v1.objective import record
            row['C_reference_posthoc']=record(measure(p,load_plan(row['plan'])),cm)
    complete=conditions['C_Idual']['status']=='COMPLETE' and all(conditions[k]['status']=='COMPLETE_FOUR_BRANCHES' for k in ('D_classical','D_quantum'))
    result=dict(status='COMPLETE' if complete else 'PARTIAL',scale=case['scale'],trial_id=case['trial_id'],seed=case['seed'],
        initial_sha256=initial.manifest['plan_sha256'],initial_hash=identity(base),conditions=conditions,
        formal_J_contribution=manifest['formal_J_contribution'])
    if complete:
        if not (out/'RESULT.json').exists():dump(out/'RESULT.json',result)
    else:dump(out/f'PARTIAL_{len(list(out.glob("PARTIAL_*.json")))+1:03d}.json',result)
    return result

def execute(directory):
    out=Path(directory).resolve();manifest=verify_manifest(out);c=manifest['configuration']
    if 'MAIN' in c['role'] and not (c.get('main_experiment_authorized') and c.get('formal_J_confirmed')):
        raise ValueError('MAIN_START_PERMISSION_AND_FORMAL_J_NOT_CONFIRMED')
    with (out/'EXECUTION.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        result=[]
        for case in manifest['cases']:
            directory=out/case['output_subdir'];directory.mkdir(parents=True,exist_ok=True)
            if (directory/'RESULT.json').exists():row=read(directory/'RESULT.json')
            else:row=run_trial(manifest,case,directory)
            result.append(row)
            if row['status']!='COMPLETE':break
        atomic(out/'RUN_STATUS.json',dict(results=result,complete_scales=sum(x['status']=='COMPLETE' for x in result),
            expected_scales=len(manifest['cases']),main_experiment_executed='MAIN' in c['role']))
        return result
