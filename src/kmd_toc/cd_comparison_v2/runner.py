"""Four fresh single-core processes; no resume, no legacy experiment writes."""
from dataclasses import asdict,replace
from pathlib import Path
import json,os,subprocess,sys,time,signal
from .resources import sample
from kmd_toc.common_initial_v1.plans import dump,sha,read_initial,exact_metrics
from kmd_toc.measurement_audit_v1.measurement import physical_payload,digest_payload,cross_evaluate
from kmd_toc.objective_alignment_v1.archive import Archive
from kmd_toc.objective_alignment_v1.objective import measure,record
from kmd_toc.duty_break_v1.models import load_plan

ROOT=Path(__file__).resolve().parents[3]
def read(p):return json.loads(Path(p).read_text())
def select_four(p,initial,condition,branches,output):
    if set(branches)!=set(range(4)):raise ValueError('FOUR_EXPLICIT_BRANCH_RECORDS_INCLUDING_MISSING')
    out=Path(output);out.mkdir(parents=True,exist_ok=False);base=initial.checked_plan(p)
    method='D' if condition=='D_quantum' else 'C'
    base=replace(base,method_id=method,execution_kind='quantum_circuit_simulator' if method=='D' else 'classical')
    archive=Archive(p,base,out/'candidates');excluded=[];accepted=[]
    for b,value in sorted(branches.items()):
        if value is None:excluded.append(dict(branch=b,status='MISSING'));continue
        result,plan=value
        try:
            if result['status']!='COMPLETE':raise ValueError('BRANCH_NOT_COMPLETE:'+result['status'])
            if result['condition_id']!=condition or result['branch_id']!=b:raise ValueError('BRANCH_IDENTITY_MISMATCH')
            if result['initial_plan_sha256']!=initial.manifest['plan_sha256']:raise ValueError('BRANCH_INITIAL_MISMATCH')
            if result['trial_id']!=initial.manifest['trial_id']:raise ValueError('BRANCH_TRIAL_MISMATCH')
            if plan.method_id!=method or plan.execution_kind!=('quantum_circuit_simulator' if method=='D' else 'classical'):
                raise ValueError('BRANCH_EXECUTION_KIND_OR_METHOD_MISMATCH')
            if result.get('selected',{}).get('stable_id')!=digest_payload(physical_payload(plan)):
                raise ValueError('BRANCH_FINAL_PHYSICAL_HASH_MISMATCH')
            if exact_metrics(p,plan)!=result['metrics']:raise ValueError('BRANCH_SAVED_DW_MISMATCH')
            archive.add(plan,origin=f'branch_{b}',branch_id=b)
            if archive.rows[-1]['status']=='INFEASIBLE_OR_MEASUREMENT_FAIL':raise ValueError('BRANCH_PHYSICAL_FAIL')
            accepted.append(b)
        except ValueError as e:excluded.append(dict(branch=b,status='FAILED_OR_INVALID',reason=str(e)))
    final,why=archive.best();archive.save(out/'ARCHIVE.json');dump(out/'plan.json',asdict(final))
    r=dict(status='COMPLETE_FOUR_BRANCHES' if len(accepted)==4 else 'PARTIAL_MISSING_OR_FAILED_BRANCHES',
        condition_id=condition,trial_id=initial.manifest['trial_id'],initial_plan_sha256=initial.manifest['plan_sha256'],
        initial_physical_hash=initial.manifest['physical_plan_hash'],
        selected_branch_id=None if why['initial'] else why['branch_id'],selection=why,accepted_branches=accepted,
        excluded=excluded,metrics=exact_metrics(p,final),branch_count_successful=len(accepted),
        main_experiment='HOLD',statistical_outer_trial=False)
    dump(out/'SELECTION.json',r);return r

def physical_cores(count=4):
    result=[];seen=set()
    for c in sorted(os.sched_getaffinity(0)):
        f=Path(f'/sys/devices/system/cpu/cpu{c}/topology')
        key=((f/'physical_package_id').read_text(),(f/'core_id').read_text()) if f.exists() else c
        if key in seen:continue
        seen.add(key);result.append(c)
        if len(result)==count:return result
    raise ValueError('FOUR_PHYSICAL_CORES_UNAVAILABLE_NO_SILENT_SERIAL_FALLBACK')

def run_four(p,initial,input_directory,output,*,condition,settings,outer_seed,cpus=None):
    from .engine import validate_settings
    validate_settings(settings);initial.checked_plan(p)
    cpus=physical_cores() if cpus is None else list(cpus)
    if len(cpus)!=4 or len(set(cpus))!=4 or not set(cpus)<=os.sched_getaffinity(0):raise ValueError('FOUR_VALID_DISTINCT_CPUS_REQUIRED')
    out=Path(output).resolve();out.mkdir(parents=True,exist_ok=False);children=[];handles=[];t0=time.perf_counter();c0=time.process_time()
    source={str(f.relative_to(ROOT)):sha(f) for f in [*(ROOT/'src/kmd_toc/cd_comparison_v2').glob('*.py'),ROOT/'scripts/run_cd_comparison_v2.py']}
    common=dict(condition=condition,settings=settings,outer_seed=outer_seed,input_directory=str(Path(input_directory).resolve()),
        initial_directory=str(initial.directory),initial_manifest_sha256=sha(initial.directory/'INITIAL.json'),
        source_sha256=source,problem_hash=p.fingerprint,rest_options=p.rest_options.payload(),trial_id=initial.manifest['trial_id'])
    env={**os.environ,'PYTHONPATH':str(ROOT/'src'),'PYTHONDONTWRITEBYTECODE':'1',
        **{k:'1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}}
    peak=0.;last_cpu={}
    try:
        for b,cpu in enumerate(cpus):
            folder=out/f'branch_{b}';folder.mkdir();job=folder/'JOB.json'
            dump(job,{**common,'branch_id':b,'cpu':cpu,'output':str(folder/'work')})
            h=(folder/'worker.log').open('x');handles.append(h)
            executable=settings.get('branch_python',sys.executable)
            c=subprocess.Popen([executable,'-B',str(ROOT/'scripts/run_cd_comparison_v2.py'),'_branch','--job',str(job)],
                cwd=ROOT,env=env,stdout=h,stderr=subprocess.STDOUT,start_new_session=True)
            children.append((c,b));dump(folder/'PID.json',dict(PID=c.pid,identity=sample(c.pid),cpu=cpu))
        with (out/'RESOURCES.jsonl').open('x') as f:
            while any(c.poll() is None for c,_ in children):
                sampled=[];rss=sample(os.getpid())['RSS_bytes']
                for c,b in children:
                    if c.poll() is not None:continue
                    pr=sample(c.pid)
                    if pr:
                        rss+=pr['RSS_bytes'];last_cpu[str(b)]=pr['CPU_s']
                        sampled.append(dict(branch=b,**pr))
                peak=max(peak,rss);f.write(json.dumps(dict(elapsed_s=time.perf_counter()-t0,tree_RSS_bytes=rss,processes=sampled))+'\n');f.flush()
                time.sleep(.1)
    except BaseException:
        for c,b in children:
            if c.poll() is None:c.terminate()
        for c,b in children:c.wait()
        raise
    finally:
        for h in handles:h.close()
    branches={};records=[]
    for c,b in children:
        rc=c.wait();folder=out/f'branch_{b}/work';path=folder/'RESULT.json'
        if not path.exists():
            branches[b]=None;records.append(dict(branch=b,status='MISSING_RESULT',process_exit_code=rc));continue
        result=read(path)
        try:plan=load_plan(folder/'plan.json')
        except (ValueError,FileNotFoundError):branches[b]=None;records.append(dict(branch=b,status='INVALID_PLAN',process_exit_code=rc));continue
        if rc!=0:result={**result,'status':'FAILED_PROCESS_EXIT'}
        branches[b]=(result,plan);records.append(dict(branch=b,process_exit_code=rc,**result))
    r=select_four(p,initial,condition,branches,out/'selection')
    r.update(branch_records=records,wall_s=time.perf_counter()-t0,parent_CPU_s=time.process_time()-c0,
        sum_branch_algorithm_CPU_s=sum(x.get('CPU_s',0) for x in records),
        sampled_tree_peak_RSS_MiB=peak/2**20,CPU_measurement='parent + algorithm branch CPU; fresh-process startup CPU sampled separately',
        last_sampled_process_CPU_s=last_cpu,cpus=cpus,native_threads_per_branch=1,
        initialization_scope='fresh process imports/input validation included in parent wall; branch algorithm wall separately recorded',
        formal_budget='HOLD; finite K/R, generator counts and completion policy explicit',source_sha256=source)
    dump(out/'RESULT.json',r);return r
