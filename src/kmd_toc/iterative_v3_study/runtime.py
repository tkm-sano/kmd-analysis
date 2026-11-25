"""Formal campaign wrapper; uses the unchanged v3 trial/branch algorithms."""
from pathlib import Path
from contextlib import contextmanager
import os,sys,time,resource,signal,traceback,fcntl
from kmd_toc.iterative_v3.io import ROOT,read,dump,atomic,sha,verify_pins,load_problem,read_initial
from .plan import CLI,preflight

@contextmanager
def study_workers():
    import kmd_toc.iterative_v3.experiment as legacy
    original=legacy.subprocess.Popen
    def launch(command,*args,**kwargs):
        argv=list(command)
        if len(argv)>3 and Path(argv[2])==ROOT/'scripts/run_iterative_v3.py' and argv[3] in ('_branch','_classical'):
            argv[2]=str(CLI)
        return original(argv,*args,**kwargs)
    legacy.subprocess.Popen=launch
    try:yield
    finally:legacy.subprocess.Popen=original

def branch_worker(job):
    from kmd_toc.iterative_v3.search import run
    from .telemetry import instrument
    out=Path(job['output']);out.mkdir(parents=True,exist_ok=True);t=time.perf_counter();c=time.process_time();status='FAILED'
    attempt=len(list(out.glob('ATTEMPT_*.json')))+1
    def stop(sig,frame):raise KeyboardInterrupt('explicit process termination')
    signal.signal(signal.SIGTERM,stop)
    try:
        os.sched_setaffinity(0,{job['cpu']});verify_pins(job['code_hashes'])
        p=load_problem(job['input'],job['rest_options']);initial=read_initial(job['initial_directory'])
        with instrument(out):r=run(p,initial,out,job['condition'],job['settings'],job['seed'],job['branch'])
        status=r['status'];return 0 if status=='COMPLETE' else 2
    except BaseException as e:
        status='INTERRUPTED' if isinstance(e,KeyboardInterrupt) else 'FAILED'
        dump(out/f'{status}_{attempt:03d}.json',dict(error=repr(e),traceback=traceback.format_exc()))
        return 130 if status=='INTERRUPTED' else 2
    finally:
        dump(out/f'ATTEMPT_{attempt:03d}.json',dict(status=status,PID=os.getpid(),CPU_s=time.process_time()-c,wall_s=time.perf_counter()-t,
            affinity=sorted(os.sched_getaffinity(0)),native_threads=1,python=sys.version,executable=sys.executable,
            entry=str(CLI),entry_sha256=sha(CLI),
            RSS_highwater_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024))

def classical_worker(job):
    from kmd_toc.iterative_v3.experiment import classical_helper
    if 'C_cpu' in job:os.sched_setaffinity(0,{job['C_cpu']})
    out=Path(job['output']);out.mkdir(parents=True,exist_ok=True)
    dump(out/f'CLASSICAL_ENTRY_{len(list(out.glob("CLASSICAL_ENTRY_*.json")))+1:03d}.json',dict(PID=os.getpid(),entry=str(CLI),entry_sha256=sha(CLI),
        stage=job['stage'],seed=job['seed'],affinity=sorted(os.sched_getaffinity(0)),native_threads=1,python=sys.version,executable=sys.executable))
    return 0 if classical_helper(job) else 2

def prepare_case(manifest,case,out):
    out=Path(out);b=out/'B';b.mkdir(parents=True,exist_ok=True)
    pointer=dict(status='COMPLETE',directory=case['initial_directory'])
    if (b/'B_CURRENT.json').exists():
        if read(b/'B_CURRENT.json')!=pointer:raise ValueError('CASE_INITIAL_POINTER_CHANGED')
    else:dump(b/'B_CURRENT.json',pointer)
    binding=dict(trial_id=case['trial_id'],seed=case['seed'],initial_sha256=case['initial_plan_sha256'],streams=case['streams'],
        configuration_sha256=manifest['configuration_sha256'])
    if (out/'CASE_BINDING.json').exists():
        if read(out/'CASE_BINDING.json')!=binding:raise ValueError('CASE_BINDING_CHANGED')
    else:dump(out/'CASE_BINDING.json',binding)
    pointer=out/'C_Idual/C_CURRENT.json'
    if pointer.exists():
        directory=Path(read(pointer)['directory']).resolve()
        if not directory.is_relative_to((out/'C_Idual/solver_attempts').resolve()):raise ValueError('C_PILOT_OR_OTHER_TRIAL_REUSE_FORBIDDEN')
        result=read(directory/'RESULT.json');job=read(out/'C_Idual/JOB.json')
        if result['trial_id']!=case['trial_id'] or result['initial_plan_sha256']!=case['initial_plan_sha256'] or job['seed']!=case['seed'] or job['code_hashes']!=manifest['code_hashes']:
            raise ValueError('C_FORMAL_SEED_OR_INITIAL_BINDING_CHANGED')

def execute(manifest,output,*,explicit_execute=False):
    if not explicit_execute:raise ValueError('EXPLICIT_EXECUTE_REQUIRED; preparation never launches workers')
    out=Path(output).resolve();preflight(manifest,out)
    from .readiness import readiness
    if readiness(manifest,out)['preparation_state']!='EXPERIMENT_READY':raise ValueError('TECHNICAL_READINESS_BLOCKED')
    m=read(manifest);results=[]
    from kmd_toc.iterative_v3.experiment import run_trial
    with (out/'EXECUTION.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        atomic(out/'EXECUTION_STATE.json',dict(state='RUNNING',planned_cases=90,explicit_execute=True))
        for case in m['cases']:
            trial=out/case['output_subdir'];commit=trial/'CASE_COMMIT.json'
            if commit.exists():
                saved=read(commit)
                for f,h in saved['file_hashes'].items():
                    if sha(f)!=h:raise ValueError('COMPLETED_CASE_ARTIFACT_CHANGED')
                results.append(saved);continue
            prepare_case(m,case,trial);begin=time.perf_counter();cpu=time.process_time();before=resource.getrusage(resource.RUSAGE_CHILDREN)
            try:
                with study_workers():r=run_trial(m,case,trial)
            except KeyboardInterrupt:
                atomic(out/'EXECUTION_STATE.json',dict(state='INTERRUPTED',trial_id=case['trial_id'],planned_cases=90));raise
            except Exception as e:
                atomic(out/'EXECUTION_STATE.json',dict(state='BLOCKED',trial_id=case['trial_id'],reason=repr(e)));raise
            after=resource.getrusage(resource.RUSAGE_CHILDREN)
            resource_files=sorted(trial.glob('*/executions/*/RESOURCES.json'))
            alarms=[dict(file=str(p),reason=read(p)['reason']) for p in resource_files if read(p).get('reason')]
            record=dict(trial_id=case['trial_id'],scale=case['scale'],seed=case['seed'],status=r['status'],
                operational_results=r,wall_s=time.perf_counter()-begin,parent_CPU_s=time.process_time()-cpu,
                child_CPU_s=(after.ru_utime+after.ru_stime)-(before.ru_utime+before.ru_stime),
                RSS_parent_lifetime_HWM_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
                peak_sampled_method_tree_RSS_MiB=max((read(p)['sampled_tree_RSS_MiB'] for p in resource_files),default=None),
                scope='current attempt of comparison case, including parent input, final validation and save; sum distinct CASE_ATTEMPT files for resumed total; B is fixed input',resource_alarms=alarms)
            dump(trial/f'CASE_ATTEMPT_{len(list(trial.glob("CASE_ATTEMPT_*.json")))+1:03d}.json',record)
            if alarms:
                atomic(out/'EXECUTION_STATE.json',dict(state='INTERRUPTED_RESOURCE',trial_id=case['trial_id'],alarms=alarms));return results+[record]
            terminal=all((trial/f'{method}/branch_{b}/work/RESULT.json').exists() for method in ('D_classical','D_quantum') for b in range(4)) and (trial/'C_Idual/C_CURRENT.json').exists()
            if r['status']=='COMPLETE' or terminal:
                paths=[p for p in [trial/'RESULT.json',*trial.glob('PARTIAL_*.json')] if p.exists()]
                paths += [Path(x['plan']) for x in r.get('conditions',{}).values() if x.get('plan')]
                record['terminal_failure_retained']=r['status']!='COMPLETE';record['file_hashes']={str(p):sha(p) for p in paths};dump(commit,record)
            else:
                atomic(out/'EXECUTION_STATE.json',dict(state='INTERRUPTED',trial_id=case['trial_id'],reason='unfinished worker result; resume same streams'));return results+[record]
            results.append(record)
        atomic(out/'EXECUTION_STATE.json',dict(state='COMPLETED' if all(x['status']=='COMPLETE' for x in results) else 'COMPLETED_WITH_FAILURES',attempted_cases=len(results),planned_cases=90))
    return results
