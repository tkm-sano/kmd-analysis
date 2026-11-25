"""D3 v2 orchestration. Physics, branch search, C and descriptive analysis are reused."""
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
import copy
import csv
import fcntl
import hashlib
import json
import os
import shutil
import subprocess
import time

from kmd_toc.iterative_v3 import experiment
from kmd_toc.iterative_v3.io import (
    ROOT, atomic, digest_payload, dump, identity, load_plan, load_problem,
    read, read_initial, sha, sources, verify_pins,
)
from kmd_toc.iterative_v3.physical import metrics
from kmd_toc.iterative_v3_study import analysis, plan, runtime
from kmd_toc.cd_comparison_v2.runner import physical_cores
from kmd_toc.objective_alignment_v1.objective import measure, selection_key

from .environment_v2 import fingerprint, observe_process
from .overlay import variant_worker
from . import rng_v2 as rng

CANONICAL = Path('/home/takuma/kmd-analysis')
ENTRY = ROOT/'scripts/run_iterative_d3_v2.py'
METHODS = tuple(plan.METHODS)
SCALES = ('S1','S2','S3')
END_FILE = 'COMPLETE_RECORD.json'
ENV_ROLES = ('classical','branch')


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def fsync_dir(path):
    fd = os.open(path,os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def durable(path, value):
    atomic(path,value)
    fsync_dir(path.parent)


@contextmanager
def locked(path):
    with path.open('a') as stream:
        fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield


def registry(diagnostics, excluded):
    ctx = [rng.context('pilot',s,0) for s in SCALES]
    ctx += [rng.context('formal',s,j) for s in SCALES for j in range(30)]
    ctx += [rng.context('diagnostic',s,j) for s,j in diagnostics]
    return rng.build(ctx,excluded)


def exclusions(old):
    result = set(old['configuration']['excluded_pilot_seeds'])
    initial = (old, read(old['configuration']['D0_formal_manifest']))
    for manifest in initial:
        for c in manifest['cases']:
            result.add(c['seed'])
            result.add(c['streams']['C_Idual_seed'])
    # Legacy measurement integers are derived by additions of <= 190,265 to
    # a uint32 value. The 128-bit v2 spaces are verified above this range;
    # C's int31 stream remains within the exact C/old trial exclusions.
    return sorted(result)


def environment(config):
    observed = {}
    for role in ENV_ROLES:
        exe = config[role+'_python']
        raw = subprocess.check_output([exe,'-B',str(ENTRY),'_environment','--role',role],cwd=ROOT)
        observed[role] = json.loads(raw)
        pools = observed[role]['native_limits']
        if not pools or any(x['threads']!=1 for x in pools):
            raise ValueError(f'NATIVE_THREAD_LIMIT_UNVERIFIED:{role}')
    return observed


def pins():
    result = sources()
    for p in (ENTRY, ROOT/'scripts/run_iterative_d3.py', ROOT/'scripts/audit_iterative_d3_precision_v2.py'):
        result[str(p.relative_to(ROOT))] = sha(p)
    return result


def register(out, stage, legacy, *, benchmark=None):
    out = out.resolve()
    legacy = legacy.resolve()
    old = read(legacy)
    if old['version']!='iterative-d3-v1' or sha(legacy)!=read(legacy.parent/'FREEZE_RECORD.json')['manifest_sha256']:
        raise ValueError('LEGACY_REGISTRATION_IDENTITY')
    cfg = copy.deepcopy(old['configuration'])
    code = pins()
    if ROOT != CANONICAL:
        verify_pins({str(CANONICAL/p):h for p,h in code.items()})
    if stage == 'diagnostic':
        items = read(benchmark)
        allowed = {'outer_iterations','physical_completion_budget','local_order_size'}
        patch = items['search']
        if not set(patch)<=allowed:
            raise ValueError('DIAGNOSTIC_OVERRIDE_SCOPE')
        cfg['search'].update(patch)
        cfg['search']['quantum']['optimizer_max_evaluations'] = items['optimizer_max_evaluations']
        inputs = items['inputs']
        diagnostics = [(x['scale'],x['outer_index']) for x in inputs]
    else:
        if benchmark is not None:
            raise ValueError('FROZEN_CONDITIONS_CANNOT_BE_OVERRIDDEN')
        # Keep condition values verbatim. Execution revision is on the manifest.
        diagnostics = []
        inputs = []
        for c in old['cases']:
            if stage=='pilot' and c['outer_index']!=0:
                continue
            src = old['fixed_initials'][c['scale']]
            inputs.append(dict(scale=c['scale'], outer_index=c['outer_index'],
                               input=c['input'], initial=src['directory']))
        verify_pins(old['input_hashes'] | old['asset_hashes'])
    exclusion = exclusions(old)
    ledger, slots = registry(diagnostics, exclusion)
    assert all(int(line.rsplit(',',1)[-1]) > (1<<33) for line in ledger.splitlines()[1:]
               if ',C_Idual,' not in line)
    env = environment(cfg)
    cpus = physical_cores()
    if cpus != cfg['cpu_ids']:
        raise ValueError('REVISED_CPU_BINDING')
    out.mkdir(parents=True,exist_ok=False)
    cfg_path = out/'EFFECTIVE_CONFIGURATION.json'
    dump(cfg_path,cfg)
    dump(out/'ENVIRONMENT.json',env)
    (out/'SEEDS.csv').write_text(ledger)
    case_list, fixed, data = [], {}, {}
    problems = {}
    for x in inputs:
        s=x['scale']
        inp=Path(x['input']).resolve()
        if s not in problems:
            problems[s]=load_problem(inp,cfg['rest_options'])
        p=problems[s]
        if stage=='diagnostic' and (p.experiment.kind!='synthetic_validation' or len(p.stops)>12):
            raise ValueError('DIAGNOSTIC_REQUIRES_SYNTHETIC_INPUT')
        if s not in fixed:
            src=Path(x['initial']).resolve()
            initial=read_initial(src)
            base=initial.checked_plan(p)
            if stage!='diagnostic' and initial.manifest['plan_sha256']!=old['fixed_initials'][s]['plan_sha256']:
                raise ValueError('PI0_REUSE_MISMATCH')
            fixed[s]=dict(directory=str(src),plan_sha256=sha(src/'plan.json'),physical_hash=identity(base))
            data.update({str(f):sha(f) for f in (src/'INITIAL.json',src/'plan.json')})
            data.update({str(f):sha(f) for f in sorted(inp.rglob('*')) if f.is_file()})
        trial=f"{rng.EXECUTION}_{stage}_{s}_T{x['outer_index']:03d}"
        alias=plan.alias_initial(x['initial'],out/'initial_aliases'/trial,trial)
        if alias.manifest['plan_sha256']!=fixed[s]['plan_sha256']:
            raise ValueError('TRIAL_FIXED_INPUT_CHANGED')
        data[str(alias.directory/'INITIAL.json')]=sha(alias.directory/'INITIAL.json')
        ctx=(stage,s,x['outer_index'])
        case_list.append(dict(trial_id=trial,scale=s,outer_index=x['outer_index'],input=str(inp),
             context=rng.context(*ctx),output_subdir=f"trials/{s}/T{x['outer_index']:03d}",
             initial_directory=str(alias.directory),initial_plan_sha256=fixed[s]['plan_sha256'],
             initial_physical_hash=fixed[s]['physical_hash'],problem_hash=p.fingerprint,od_hash=p.od.fingerprint,
             seed=slots[(*ctx,'trial',-1)],C_seed=slots[(*ctx,'C_Idual',-1)],
             branch_seeds=[slots[(*ctx,'D_shared',b)] for b in range(4)]))
    m=dict(version=rng.EXECUTION,rng_version=rng.VERSION,stage=stage,root=str(ROOT),output=str(out),
           source_manifest=str(legacy),source_manifest_sha256=sha(legacy),configuration=cfg,
           configuration_sha256=sha(cfg_path),code_hashes=code,asset_hashes=data,
           seed_sha256=sha(out/'SEEDS.csv'),environment_sha256=sha(out/'ENVIRONMENT.json'),excluded=exclusion,
           classical_configuration=old['classical_configuration'],cases=case_list,fixed_initials=fixed,
           formal_J=30,diagnostics=diagnostics,counts=dict(comparison_cases=len(case_list),
               D_branch_jobs=8*len(case_list),C_runs=len(case_list),solver_jobs=9*len(case_list)))
    dump(out/'MANIFEST.json',m)
    dump(out/'REGISTRATION.json',dict(manifest_sha256=sha(out/'MANIFEST.json'),workers_submitted=0))
    for filename in ('MANIFEST.json','REGISTRATION.json','SEEDS.csv','EFFECTIVE_CONFIGURATION.json','ENVIRONMENT.json'):
        (out/filename).chmod(0o444)
    return dict(state='REGISTERED_HOLD' if stage=='formal' else 'REGISTERED',counts=m['counts'],workers_submitted=0)


def approved(out,m):
    path=out/'FREEZE_RECORD.json'
    if not path.exists():
        return False
    f=read(path)
    if f['manifest_sha256']!=sha(out/'MANIFEST.json') or f['seed_sha256']!=m['seed_sha256']:
        raise ValueError('FREEZE_BINDING')
    evidence=Path(f['evidence'])
    if sha(evidence)!=f['evidence_sha256']:
        raise ValueError('AUDIT_EVIDENCE_CHANGED')
    validate_evidence(out,m,read(evidence))
    return True


def validate_evidence(out,m,evidence):
    required=('A6','C2','C3','E8','F3','G1','G2','G3','H3')
    if (evidence.get('start_blockers')!=[] or
        any(evidence.get('criteria',{}).get(k)!='PASS' for k in required) or
        evidence['manifest_sha256']!=sha(out/'MANIFEST.json') or
        evidence['code_hashes']!=m['code_hashes'] or
        evidence['environment_sha256']!=m['environment_sha256']):
        raise ValueError('OPEN_AUDIT_REQUIREMENTS')
    verify_pins(evidence['evidence_hashes'])
    pilot=Path(evidence['pilot_registration'])
    pm=read(pilot/'MANIFEST.json')
    if (pm['stage']!='pilot' or pm['counts']['comparison_cases']!=3 or pm['seed_sha256']!=m['seed_sha256'] or
       pm['code_hashes']!=m['code_hashes'] or pm['environment_sha256']!=m['environment_sha256'] or
       any(not (pilot/c['output_subdir']/'CASE_COMMIT.json').is_file() for c in pm['cases'])):
        raise ValueError('PILOT_COMPLETION_EVIDENCE')


def preflight(out, *, probe=True):
    out=out.resolve()
    m=read(out/'MANIFEST.json')
    if (m['version'],m['rng_version'],m['root'],m['output']) != (rng.EXECUTION,rng.VERSION,str(ROOT),str(out)):
        raise ValueError('OUTPUT_EXECUTION_BINDING')
    verify_pins({str(out/'MANIFEST.json'):read(out/'REGISTRATION.json')['manifest_sha256'],
                 str(out/'SEEDS.csv'):m['seed_sha256'],str(out/'EFFECTIVE_CONFIGURATION.json'):m['configuration_sha256'],
                 str(out/'ENVIRONMENT.json'):m['environment_sha256'],m['source_manifest']:m['source_manifest_sha256']})
    if read(out/'EFFECTIVE_CONFIGURATION.json')!=m['configuration']:
        raise ValueError('CONFIG_BINDING')
    verify_pins(m['code_hashes'])
    if ROOT != CANONICAL:
        verify_pins({str(CANONICAL/p):h for p,h in m['code_hashes'].items()})
    verify_pins(m['asset_hashes'])
    ledger,slots=registry(m['diagnostics'],m['excluded'])
    if digest_bytes(ledger.encode())!=m['seed_sha256']:
        raise ValueError('RNG_REGISTRY_MISMATCH')
    stage=m['stage']
    expected = (dict.fromkeys(SCALES,30) if stage=='formal' else dict.fromkeys(SCALES,1))
    if stage != 'diagnostic' and Counter(c['scale'] for c in m['cases'])!=expected:
        raise ValueError('CASE_COUNTS')
    for c in m['cases']:
        ctx=(stage,c['scale'],c['outer_index'])
        if (c['seed']!=slots[(*ctx,'trial',-1)] or c['C_seed']!=slots[(*ctx,'C_Idual',-1)] or
           c['branch_seeds']!=[slots[(*ctx,'D_shared',b)] for b in range(4)] or c['context']!=rng.context(*ctx) or
           sha(Path(c['initial_directory'])/'plan.json')!=c['initial_plan_sha256']):
            raise ValueError('CASE_RNG_OR_PI0_BINDING')
    limits=m['configuration']['limits']
    if stage!='diagnostic' and (physical_cores()!=m['configuration']['cpu_ids'] or
           shutil.disk_usage(out).free < limits['minimum_free_disk_gib']*2**30):
        raise ValueError('LIVE_RESOURCE_PRECONDITION')
    if probe and environment(m['configuration'])!=read(out/'ENVIRONMENT.json'):
        raise ValueError('LIVE_ENVIRONMENT_CHANGED')
    state = 'EXPERIMENT_READY' if stage=='formal' and approved(out,m) else 'HOLD_PENDING_REAUDIT' if stage=='formal' else 'PREFLIGHT_PASS'
    return dict(state=state,stage=stage,counts=m['counts'],workers_submitted=0)


def freeze(out,evidence):
    out=out.resolve()
    m=read(out/'MANIFEST.json')
    if m['stage']!='formal':
        raise ValueError('FREEZE_ONLY_FORMAL')
    preflight(out)
    evidence=evidence.resolve()
    validate_evidence(out,m,read(evidence))
    marker=out/'FREEZE_RECORD.json'
    dump(marker,dict(manifest_sha256=sha(out/'MANIFEST.json'),seed_sha256=m['seed_sha256'],
                     evidence=str(evidence),evidence_sha256=sha(evidence),state='EXPERIMENT_READY'))
    marker.chmod(0o444)
    return dict(state='EXPERIMENT_READY',workers_submitted=0)


def jobs(m,c,folder,method):
    cfg=m['configuration']
    d=folder/method
    role='classical' if method=='C_Idual' else 'branch'
    env=read(Path(m['output'])/'ENVIRONMENT.json')[role]
    for b in range(1 if method=='C_Idual' else 4):
        job_path=d/'JOB.json' if method=='C_Idual' else d/f'branch_{b}/JOB.json'
        work=d if method=='C_Idual' else job_path.parent/'work'
        job=dict(version=m['version'],trial_id=c['trial_id'],condition=method,
            branch=b,cpu=cfg['cpu_ids'][b],C_cpu=cfg['cpu_ids'][0],
            input=c['input'],rest_options=cfg['rest_options'],initial_directory=c['initial_directory'],
            initial_plan_sha256=c['initial_plan_sha256'],pi0_hash=c['initial_physical_hash'],
            problem_hash=c['problem_hash'],od_hash=c['od_hash'],output=str(work),
            code_hashes=m['code_hashes'], seed=c['C_seed'] if method=='C_Idual' else c['branch_seeds'][b],
            environment=env, scope=m['stage'])
        if method=='C_Idual':
            job.update(stage='C',scale=c['scale'],classical_configuration=m['classical_configuration'])
        else:
            job['settings']=cfg['search'] | {'rng_v2':c['context'] | {'branch':b}}
        yield job_path,job


def job_work(job):
    return Path(job['output'])


def completion_path(job):
    directory=job_work(job)
    return directory/END_FILE if job['condition']=='C_Idual' else directory.parent/END_FILE


def pair_paths(job):
    out=job_work(job)
    if job['condition']=='C_Idual':
        pointer=read(out/'C_CURRENT.json')
        native=Path(pointer['directory']).resolve()
        if not native.is_relative_to((out/'solver_attempts').resolve()) or pointer['status']!='COMPLETE':
            raise ValueError('C_POINTER_OR_STATUS')
        return native/'plan.json',native/'RESULT.json',[out/'C_CURRENT.json']
    return out/'plan.json',out/'RESULT.json',[out/'START.json']


def start_matches(job,r):
    fields={'version':job['version'],'trial_id':job['trial_id'],'condition':job['condition'],
            'pi0_hash':job['pi0_hash'],'pi0_file_sha256':job['initial_plan_sha256'],
            'branch':job['branch'],'seed':job['seed'],'settings':job['settings'],
            'problem_hash':job['problem_hash'],'od_hash':job['od_hash']}
    return all(r.get(k)==v for k,v in fields.items())


def check_pair(job,p,base):
    plan_file,result_file,more=pair_paths(job)
    r=read(result_file)
    if r['status']!='COMPLETE' or r.get('trial_id')!=job['trial_id']:
        raise ValueError('NONNORMAL_RESULT_OR_TRIAL')
    if job['condition']=='C_Idual':
        if r.get('condition_id')!='C_Idual' or r.get('initial_plan_sha256')!=job['initial_plan_sha256']:
            raise ValueError('C_BINDING')
    elif (not start_matches(job,read(more[0])) or
          any(r.get(k)!=job[k] for k in ('condition','branch','seed','pi0_hash'))):
        raise ValueError('BRANCH_BINDING')
    candidate=load_plan(plan_file)
    actual=metrics(p,candidate,measure(p,base))
    if job['condition']=='C_Idual':
        if any(r['selected'].get(k)!=actual[k] for k in ('D_exact','W_exact','I_dual_exact')):
            raise ValueError('C_MEASUREMENT_MISMATCH')
    elif r['metrics']!=actual or r['best_incumbent_hash']!=actual['physical_hash']:
        raise ValueError('BRANCH_MEASUREMENT_MISMATCH')
    return dict(plan=str(plan_file),metrics=actual,artifacts={str(f):sha(f) for f in [plan_file,result_file,*more]})


def inspect_output(job,p,base):
    mark=completion_path(job)
    work=job_work(job)
    if not mark.is_file():
        pending = any((work/x).exists() for x in ('plan.json','RESULT.json','C_CURRENT.json'))
        return None,'UNPUBLISHED_ARTIFACTS' if pending else 'NO_COMPLETION_RECORD'
    try:
        published=read(mark)
        if published['job_hash']!=digest_payload(job):
            raise ValueError('COMPLETION_JOB_BINDING')
        current=check_pair(job,p,base)
        if published['result']!=current:
            raise ValueError('COMPLETION_ARTIFACT_HASH')
        return current,None
    except (OSError,ValueError,KeyError,TypeError) as err:
        return None,f'INVALID_COMPLETION:{err}'


def publish(job,current):
    mark=completion_path(job)
    for f in current['artifacts']:
        fsync_dir(Path(f).parent)
    durable(mark,dict(job_hash=digest_payload(job),result=current))


def recover(job,reason):
    directory=job_work(job)
    c = job['condition']=='C_Idual'
    parent=directory if c else directory.parent
    # Unpublish first, before moving any artifact. Keep old checkpoint paths
    # when their START contract still matches this logical branch.
    stale=False
    if not c and directory.is_dir():
        try:
            stale=not start_matches(job,read(directory/'START.json'))
        except (OSError,ValueError,KeyError,TypeError):
            stale=True
    candidates=[completion_path(job)]
    if c:
        candidates += [directory/'C_CURRENT.json']
    elif stale:
        candidates.append(directory)
    else:
        candidates += [directory/x for x in ('RESULT.json','plan.json','search_state.plan.json')]
    candidates=[p for p in candidates if p.exists()]
    if not candidates:
        return
    root=parent/'recoveries'
    root.mkdir(exist_ok=True)
    recovery=root/f'{len(list(root.iterdir()))+1:04d}'
    recovery.mkdir()
    durable(recovery/'REASON.json',dict(reason=reason,version=job['version'],paths=list(map(str,candidates)),
                  checkpoint_retained=not stale and not c))
    for p in candidates:
        p.rename(recovery/p.name)
        fsync_dir(p.parent)
    fsync_dir(recovery)


def checked_job(job):
    if job['version']!=rng.EXECUTION:
        raise ValueError('JOB_EXECUTION_VERSION')
    verify_pins(job['code_hashes'])
    p=load_problem(job['input'],job['rest_options'])
    capsule=read_initial(job['initial_directory'])
    base=capsule.checked_plan(p)
    if (identity(base),capsule.manifest['plan_sha256'],capsule.manifest['trial_id'],p.fingerprint,p.od.fingerprint)!=(
           job['pi0_hash'],job['initial_plan_sha256'],job['trial_id'],job['problem_hash'],job['od_hash']):
        raise ValueError('JOB_INPUT_BINDING')
    return p,base


@contextmanager
def worker_entry():
    old=runtime.CLI
    runtime.CLI=ENTRY
    try:
        yield
    finally:
        runtime.CLI=old


def worker(jobfile,action):
    job=read(jobfile)
    classical=job['condition']=='C_Idual'
    if classical!=(action=='_classical') or job['scope'] not in rng.SCOPES:
        raise ValueError('WORKER_METHOD_BINDING')
    # A private job cannot bypass the formal start gate.
    power=next((p for p in jobfile.resolve().parents if (p/'MANIFEST.json').is_file()),None)
    if power is None:
        raise ValueError('UNBOUND_WORKER_JOB')
    m=read(power/'MANIFEST.json')
    if (m['version']!=rng.EXECUTION or m['stage']!=job['scope'] or
        sha(power/'MANIFEST.json')!=read(power/'REGISTRATION.json')['manifest_sha256']):
        raise ValueError('WORKER_MANIFEST_BINDING')
    if m['stage']=='formal' and not approved(power,m):
        raise ValueError('HOLD_FORMAL_WORKER')
    c=next(x for x in m['cases'] if x['trial_id']==job['trial_id'])
    if not any(path==jobfile.resolve() and declared==job
               for path,declared in jobs(m,c,power/c['output_subdir'],job['condition'])):
        raise ValueError('REGISTERED_WORKER_JOB_CHANGED')
    work=job_work(job)
    work.mkdir(parents=True,exist_ok=True)
    os.sched_setaffinity(0,{job['cpu']})
    p,base=checked_job(job)
    root=completion_path(job).parent
    with locked(root/'PUBLISH.lock'):
        actual,issue=inspect_output(job,p,base)
        if actual is not None:
            # Direct CLI reads and validates the existing publish marker.
            return 0
        role='classical' if classical else 'branch'
        env=fingerprint(role)
        if env!=job['environment']:
            raise ValueError('WORKER_ENVIRONMENT_CHANGED')
        if issue=='UNPUBLISHED_ARTIFACTS':
            try:
                actual=check_pair(job,p,base)
            except (OSError,ValueError,KeyError,TypeError) as e:
                issue=f'UNPUBLISHED_ARTIFACTS:{e}'
            else:
                publish(job,actual)
                return 0
        recover(job,issue)
        root_attempts=root/'worker_attempts'
        root_attempts.mkdir(exist_ok=True)
        attempt=root_attempts/f'{len(list(root_attempts.iterdir()))+1:04d}'
        attempt.mkdir()
        durable(attempt/'BEGIN.json',dict(version=job['version'],seed=job['seed'],pid=os.getpid(),
                affinity=sorted(os.sched_getaffinity(0)),native_limits=env['native_limits'],
                environment_binding=digest_payload(env),observed=observe_process(os.getpid()),
                actual_imports=env['source'],recovery_reason=issue))
        start=time.perf_counter()
        code=2
        try:
            with worker_entry():
                if classical:
                    code=runtime.classical_worker(job)
                else:
                    with variant_worker():
                        code=runtime.branch_worker(job)
            if code==0:
                publish(job,check_pair(job,p,base))
            return code
        except Exception as error:
            code=2
            durable(attempt/'ERROR.json',dict(error=repr(error)))
            raise
        finally:
            durable(attempt/'END.json',dict(exit_code=code,wall_s=time.perf_counter()-start,
                    observed=observe_process(os.getpid())))


def status_for_attempt(codes,alarm):
    if alarm:
        return 'RESOURCE_STOP',alarm
    if 130 in codes or any(c<0 for c in codes):
        return 'INTERRUPTED','PROCESS_INTERRUPTED'
    return 'FAILED','WORKER_NONZERO' if any(codes) else 'MISSING_COMPLETION_RECORD'


@contextmanager
def monitor(out,m,method,folder):
    previous=experiment.sample
    limits=m['configuration']['limits']
    injection=out/'AUDIT_RESOURCE_INJECT.json'
    fault=read(injection) if m['stage']=='diagnostic' and injection.is_file() else {}
    def sample(pid):
        result=previous(pid)
        if result is None:
            return result
        result.update(observe_process(pid))
        if (pid!=os.getpid() and fault.get('method')==method and
                (not fault.get('after_commit') or any(folder.glob('branch_*/work/iteration_*/COMMIT.json')))):
            # Exercise the same production supervisor and SIGTERM path.
            result['actual_RSS_bytes']=result['RSS_bytes']
            result['RSS_bytes']=(limits['tree_rss_mib']+100)*2**20
            result['audit_fault_injected']=True
        return result
    with worker_entry(), runtime.study_workers():
        experiment.sample=sample
        try:
            yield
        finally:
            experiment.sample=previous


def method_history(folder):
    return [read(path) for path in sorted(folder.glob('control_attempts/*/END.json'))]


def checkpoint_summary(folder):
    branches=[]
    for path in sorted(folder.glob('branch_*')):
        if path.is_dir():
            commits=sorted((path/'work').glob('iteration_*/COMMIT.json'))
            phases=sorted((path/'work').glob('PHASES_ATTEMPT_*.json'))
            branches.append(dict(branch=path.name,logical_iterations=len(commits),
                committed_counters=read(commits[-1])['counters'] if commits else None,
                actual_completed_sample_shots=sum(read(p)['known_completed_virtual_shots_lower_bound'] for p in phases),
                unknown_inflight=any(read(p)['failed_sampler_shots_unknown'] for p in phases),
                sampling_attempts=[str(p) for p in phases]))
    return branches


def run_method(out,m,c,p,base,folder,method):
    group=folder/method
    pending=[]
    for path,job in jobs(m,c,folder,method):
        path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists():
            try:
                same=read(path)==job
            except (ValueError,OSError):
                same=False
            if not same:
                root=path.parent/'superseded_jobs'
                root.mkdir(exist_ok=True)
                path.rename(root/f'{len(list(root.iterdir()))+1:04d}.json')
        if not path.exists():
            dump(path,job)
        valid,_=inspect_output(job,p,base)
        if valid is None:
            pending.append(dict(action='_classical' if method=='C_Idual' else '_branch',path=path))
    if not pending:
        return True
    attempts=group/'control_attempts'
    attempts.mkdir(exist_ok=True)
    attempt=attempts/f'{len(list(attempts.iterdir()))+1:04d}'
    attempt.mkdir()
    durable(attempt/'BEGIN.json',dict(status='RUNNING',method=method,trial_id=c['trial_id'],jobs=[str(x['path']) for x in pending]))
    try:
        with monitor(out,m,method,group):
            codes,alarm=experiment.supervise(pending,group,m['configuration'])
    except (Exception,KeyboardInterrupt) as error:
        durable(attempt/'END.json',dict(status='INTERRUPTED' if isinstance(error,KeyboardInterrupt) else 'FAILED',
                reason_code='CONTROLLER_EXCEPTION',explanation=repr(error),branches=checkpoint_summary(group)))
        raise
    checked=[inspect_output(job,p,base) for _,job in jobs(m,c,folder,method)]
    complete = all(result is not None for result,_ in checked) and alarm is None
    status,reason=('VERIFIED_COMPLETE',None) if complete else status_for_attempt(codes,alarm)
    current=sorted(group.glob('executions/*/RESOURCES.json'))
    durable(attempt/'END.json',dict(status=status,reason_code=reason,explanation=[issue for _,issue in checked if issue],
            resource_record=str(current[-1]) if current else None,exit_codes=codes,
            submitted_jobs=[str(x['path']) for x in pending],branches=checkpoint_summary(group)))
    return complete


def execute(out,*,resume):
    out=out.resolve()
    state=preflight(out)
    m=read(out/'MANIFEST.json')
    if m['stage']=='formal' and state['state']!='EXPERIMENT_READY':
        raise ValueError('HOLD_FORMAL_EXECUTION')
    execution=out/'EXECUTION_STATE.json'
    with locked(out/'EXECUTION.lock'):
        if execution.exists() and not resume:
            raise ValueError('USE_PUBLIC_RESUME_FOR_EXISTING_RUN')
        if resume and not execution.exists():
            raise ValueError('NO_PUBLIC_RUN_TO_RESUME')
        durable(execution,dict(state='RUNNING',cases=len(m['cases']),version=m['version']))
        # No carried-over observations enter the current stopper. A current
        # worker group can still be terminated by the real RSS/disk checks.
        for c in m['cases']:
            folder=out/c['output_subdir']
            folder.mkdir(parents=True,exist_ok=True)
            p=load_problem(c['input'],m['configuration']['rest_options'])
            base=read_initial(c['initial_directory']).checked_plan(p)
            for method in METHODS:
                active=dict(trial_id=c['trial_id'],method=method,version=m['version'])
                durable(execution,dict(state='RUNNING',**active))
                try:
                    complete=run_method(out,m,c,p,base,folder,method)
                except (Exception,KeyboardInterrupt) as error:
                    durable(execution,dict(state='INTERRUPTED' if isinstance(error,KeyboardInterrupt) else 'FAILED',
                        error=repr(error),**active))
                    raise
                if not complete:
                    record=method_history(folder/method)[-1]
                    result=dict(state='INTERRUPTED_RESOURCE' if record['status']=='RESOURCE_STOP'
                                else record['status'],reason=record['reason_code'],**active)
                    durable(execution,result)
                    return result
            marker=folder/'CASE_COMMIT.json'
            record=dict(version=m['version'],trial_id=c['trial_id'],
                method_completions={str(completion_path(job)):sha(completion_path(job)) for method in METHODS
                                    for _,job in jobs(m,c,folder,method)})
            if not marker.exists() or read(marker)!=record:
                if marker.exists():
                    backups=folder/'previous_commits'
                    backups.mkdir(exist_ok=True)
                    marker.rename(backups/f'{len(list(backups.iterdir()))+1:04d}.json')
                durable(marker,record)
        result=dict(state='COMPLETE',cases=len(m['cases']),version=m['version'])
        durable(execution,result)
        return result


def method_record(m,c,p,base,folder,method,execution):
    group=folder/method
    history=method_history(group)
    checks=[(job,inspect_output(job,p,base)) for _,job in jobs(m,c,folder,method)]
    valid=[(job,result) for job,(result,_) in checks if result is not None]
    active=(execution.get('trial_id'),execution.get('method'))==(c['trial_id'],method)
    attempt_history = []
    recoveries = []
    for _,job in jobs(m,c,folder,method):
        root=completion_path(job).parent
        for start in sorted(root.glob('worker_attempts/*/BEGIN.json')):
            end=start.with_name('END.json')
            attempt_history.append(dict(start=read(start), end=read(end) if end.exists() else None,
                                        branch=job['branch']))
        recoveries += [read(path) for path in sorted(root.glob('recoveries/*/REASON.json'))]
    if len(valid)==len(checks):
        if method=='C_Idual':
            chosen=valid[0][1]
            selected_branch=None
        else:
            initial=dict(plan=str(Path(c['initial_directory'])/'plan.json'),metrics=metrics(p,base,measure(p,base)))
            candidates=[(None,initial),*((job['branch'],v) for job,v in valid)]
            ref=measure(p,base)
            selected_branch,chosen=min(candidates,key=lambda x:selection_key(
                measure(p,load_plan(x[1]['plan'])),ref,initial=x[0] is None,
                branch_id=x[0] or 0,stable_id=x[1]['metrics']['physical_hash']))
        actual=chosen['metrics']
        status='NORMAL_INITIAL_RETAINED' if actual['physical_hash']==identity(base) else 'NORMAL_CHANGED'
        if chosen['plan']==str(Path(c['initial_directory'])/'plan.json'):
            # The initial candidate participates in the same rank rule. Its
            # selected result may legitimately be the fixed B plan.
            selected_branch=None
        return dict(status=status,eligible=True,reason=None,reason_code=None,metrics=actual,
                    D_km=actual['D_km'],W_total_min=actual['W_total_min'],
                    I_dual_pi0_percent=actual['I_dual_percent'],I_dual_C_posthoc_percent=None,
                    branch=selected_branch,saved_plan=chosen['plan'],attempts=history,
                    worker_attempts=attempt_history,recoveries=recoveries)
    issues=[dict(branch=job['branch'],reason=issue) for job,(_,issue) in checks if issue]
    if active and execution.get('state')=='RUNNING':
        # An orphaned RUNNING snapshot is distinguished from a live controller.
        status=execution.get('effective_status','RUNNING')
        code=None if status=='RUNNING' else 'CONTROLLER_EXITED'
    elif active and execution.get('state')=='INTERRUPTED_RESOURCE':
        status,code='RESOURCE_STOP',execution.get('reason')
    elif history and history[-1]['status']!='VERIFIED_COMPLETE':
        status,code=history[-1]['status'],history[-1].get('reason_code')
    elif valid or any(x['reason']!='NO_COMPLETION_RECORD' for x in issues):
        status,code='INCOMPLETE_SAVE','MISSING_OR_INVALID_PUBLISHED_JOB'
    elif group.exists():
        status,code='INTERRUPTED','JOB_NOT_PUBLISHED'
    else:
        status,code='NOT_STARTED','NO_ATTEMPT'
    return dict(status=status,eligible=False,reason=issues,reason_code=code,metrics=None,
                D_km=None,W_total_min=None,I_dual_pi0_percent=None,I_dual_C_posthoc_percent=None,
                branch=None,saved_plan=None,attempts=history,worker_attempts=attempt_history,recoveries=recoveries)


def live_state(out):
    file=out/'EXECUTION_STATE.json'
    if not file.exists():
        return {'state':'NOT_STARTED'}
    snapshot=read(file)
    lock=out/'EXECUTION.lock'
    if snapshot['state']=='RUNNING':
        try:
            with locked(lock):
                snapshot['effective_status']='INTERRUPTED'
        except BlockingIOError:
            pass
    return snapshot


def aggregate(out):
    out=out.resolve()
    preflight(out,probe=False)
    m=read(out/'MANIFEST.json')
    execution=live_state(out)
    summaries=[]
    records=[]
    bases={}
    for c in m['cases']:
        s=c['scale']
        if s not in bases:
            p=load_problem(c['input'],m['configuration']['rest_options'])
            base=read_initial(c['initial_directory']).checked_plan(p)
            b=metrics(p,base,measure(p,base))
            bases[s]=(p,base,b)
        p,base,b=bases[s]
        row=dict(scale=s,trial_id=c['trial_id'],seed=c['seed'],baseline_metrics=b,methods={})
        records.append(row)
        for method in METHODS:
            row['methods'][method]=method_record(m,c,p,base,out/c['output_subdir'],method,execution)
        cm=row['methods']['C_Idual']['metrics']
        for method,data in row['methods'].items():
            if cm and data['metrics']:
                data['I_dual_C_posthoc_percent']=analysis.delta(data['metrics'],cm)['I_dual_percent']
            summaries.append(dict(trial_id=c['trial_id'],scale=s,method=method,
                **{k:v for k,v in data.items() if k not in ('metrics','attempts','worker_attempts','recoveries','reason')},
                reason=json.dumps(data['reason'],ensure_ascii=False),attempt_count=len(data['attempts']),
                recovery_count=len(data['recoveries'])))
    target=out/'analysis'
    target.mkdir(exist_ok=True)
    result=target/f'{len(list(target.iterdir()))+1:04d}'
    result.mkdir()
    dump(result/'OBSERVATIONS.json',records)
    stats=analysis.summarize(records)
    dump(result/'DESCRIPTIVE.json',stats)
    analysis.csvwrite(result/'TRIAL_STATUS.csv',summaries)
    summary=dict(state=execution.get('effective_status',execution['state']),planned_cases=len(m['cases']),method_rows=len(summaries),
                eligible=sum(x['eligible'] for x in summaries),status_counts=dict(Counter(x['status'] for x in summaries)),
                J_eff={x['scale']:{'primary':x['primary_J_eff'],'control':x['control_J_eff']} for x in stats['cohorts']},
                directory=str(result),workers_submitted=0,
                formal_J_contribution=0 if m['stage']!='formal' else 1)
    dump(result/'SUMMARY.json',summary)
    return summary
