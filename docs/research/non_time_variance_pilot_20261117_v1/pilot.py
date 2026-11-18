"""Registered 75-attempt pilot; delegates timed work unchanged to termination_v1."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import fcntl
import importlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tarfile
import time

ROOT=Path(__file__).resolve().parents[3]
DOC=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from kmd_toc.comparison_v1.contract import read,digest,dump,atomic,fingerprint,check_freeze,check_profile,input_inventory,TIME_KIND
from kmd_toc.termination_v1 import runner
ID='non_time_variance_pilot_20261117_v1'
OUT=ROOT/'output/toc_delivery'/ID
OLD=ROOT/'output/toc_delivery/termination_rules_20261116_v1/scales_02'
METHODS=('A','B','C','D','D_CLASSICAL_REPLACEMENT')
SCALES=('S1','S2','S3')
SEED_ROOT=202611170917
ORDER_SEED=202611170918

def utc():return datetime.now(timezone.utc).isoformat()
def ticks(pid):return Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19]
def boot():return Path('/proc/sys/kernel/random/boot_id').read_text().strip()
def alive(info):
    try:return info['boot_id']==boot() and info['start_ticks']==ticks(info['pid'])
    except (FileNotFoundError,ProcessLookupError):return False

def make_runs():
    import numpy as np
    from kmd_toc.dwt.parallel import branch_seeds
    order=np.random.default_rng(ORDER_SEED);runs=[]
    for rep in range(1,6):
        block=[]
        for si,s in enumerate(SCALES):
            for mi,m in enumerate(METHODS):
                derived=np.random.SeedSequence([SEED_ROOT,si,mi,rep]).generate_state(2)
                seeds={'solver_seed':int(derived[0])%(2**31-1),'quantum_seed':int(derived[1])}
                if m=='A':seeds={'solver_seed':None,'quantum_seed':None}
                block.append({'run_id':f'{s}_{m}_pilot_r{rep:02d}','case_id':s,'method':m,
                    'repeat_id':rep,'block':rep,'attempt_id':1,'retry_of':None,'seeds':seeds,
                    'seed_entropy':None if m=='A' else [SEED_ROOT,si,mi,rep],
                    'branches':[seeds.copy()] if m=='A' else branch_seeds(seeds,4)})
        order.shuffle(block);runs.extend(block)
    for i,r in enumerate(runs):r['order_index']=i+1
    return runs

def environment():
    names=('numpy','scipy','ortools','qiskit','ortools.constraint_solver._pywrapcp',
        'ortools.sat.python.cp_model_helper','scipy.optimize._highspy._core',
        'qiskit.quantum_info.states.quantum_state','scipy.optimize._cobyla_py')
    deps={}
    for name in names:
        mod=importlib.import_module(name);p=Path(mod.__file__)
        deps[name]={'version':getattr(mod,'__version__',None),'module_file':str(p),'sha256':digest(p)}
    deps['python']={'path':sys.executable,'version':sys.version}
    olddeps=read(ROOT/'docs/research/termination_rules_20261116_v1/DEPENDENCY_FILES.json')
    p=Path(olddeps['VeRyPy.parallel_savings']['module_file'])
    deps['VeRyPy.parallel_savings']={'module_file':str(p),'sha256':digest(p)}
    return {'dependencies':deps,'affinity':sorted(os.sched_getaffinity(0)),'uname':list(os.uname()),
        'environment':{k:os.environ.get(k) for k in ('PYTHONPATH','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')},
        'rlimits':{k:list(resource.getrlimit(getattr(resource,k))) for k in ('RLIMIT_CPU','RLIMIT_AS','RLIMIT_DATA','RLIMIT_RSS','RLIMIT_NOFILE')},
        'proc_self_cgroup':Path('/proc/self/cgroup').read_text(),'mountinfo':Path('/proc/self/mountinfo').read_text(),
        'boot_id':boot(),'recorded_utc':utc(),'cache_policy':'no intentional warming, clearing, prefetch or method-specific operation',
        'timing_environment':'existing NFS workspace and frozen OD; shared host load uncontrolled; fresh child imports inside T'}

def validate(m,lock=None):
    if not m.get('executable') or m.get('phase')!='non_time_variance_pilot':raise ValueError('MAIN_OR_OTHER_PHASE_NOT_AUTHORIZED')
    if m['experiment_id']!=ID or m['r_pilot']!=5 or m['T_kind']!=TIME_KIND:raise ValueError('PILOT_IDENTITY_CHANGED')
    if m['runs']!=make_runs() or len(m['runs'])!=75 or m['run_list_hash']!=fingerprint(m['runs']):raise ValueError('REGISTERED_LIST_CHANGED')
    if m['config']!=read(runner.CONFIG) or m['config_hash']!=digest(runner.CONFIG):raise ValueError('REGISTERED_CONFIG_CHANGED')
    runner.validate_config(m['config'])
    if lock is not None and fingerprint(m)!=lock['manifest_fingerprint']:raise ValueError('REGISTRATION_CHANGED')
    return m

def load_registration(root):
    root=Path(root);lock=read(root/'REGISTRATION_LOCK.json')
    for name in ('REGISTERED.json','PILOT_MANIFEST.json'):
        if digest(root/name)!=lock[name]:raise ValueError('REGISTRATION_BYTES_CHANGED:'+name)
    m=validate(read(root/'REGISTERED.json'),lock)
    if digest(root/'SOURCE_SNAPSHOT.tar.gz')!=m['snapshot_sha256']:raise ValueError('SNAPSHOT_CHANGED')
    return m

def preflight(m):
    check_freeze();check_profile(m['cpu_profile']['cpu_ids'])
    for name,h in m['source_hashes'].items():
        if digest(ROOT/name)!=h:raise ValueError('REGISTERED_SOURCE_CHANGED:'+name)
    for case in m['cases']:
        for name,h in case['input']['files'].items():
            if digest(Path(case['input']['directory'])/name)!=h:raise ValueError('REGISTERED_INPUT_CHANGED:'+name)
    for name,d in m['environment']['dependencies'].items():
        if 'module_file' in d and digest(d['module_file'])!=d['sha256']:raise ValueError('DEPENDENCY_CHANGED:'+name)
    if sys.executable!=m['environment']['dependencies']['python']['path']:raise ValueError('INTERPRETER_CHANGED')

def register(root):
    start=time.perf_counter();root=Path(root).resolve();root.mkdir(parents=True,exist_ok=False)
    old=read(OLD/'REGISTERED.json');c=runner.validate_config(read(runner.CONFIG));check_freeze()
    inherited_changes=[]
    for name,h in old['source_hashes'].items():
        if name.startswith(('src/kmd_toc/termination_v1/','src/kmd_toc/baseline_a/','src/kmd_toc/pipeline/','src/kmd_toc/vehicle_day/','src/kmd_toc/column_generation/','src/kmd_toc/common/')) or name==str(runner.CONFIG.relative_to(ROOT)):
            if digest(ROOT/name)!=h:inherited_changes.append(name)
    if inherited_changes:raise ValueError('INHERITED_ALGORITHM_CHANGED:'+str(inherited_changes))
    check_profile(old['cpu_profile']['cpu_ids'])
    cases=[]
    for case in old['cases']:
        now=input_inventory(case['input']['directory'])
        if now!=case['input']:raise ValueError('INHERITED_INPUT_CHANGED')
        cases.append(case)
    runs=make_runs()
    # Inspect old registered seed values, never mix old rows into estimation.
    oldseed=set();oldpaths=[]
    for base in (ROOT/'output/toc_delivery/comparison_design_20261116_v1',ROOT/'output/toc_delivery/termination_rules_20261116_v1'):
        for p in sorted(base.glob('*/REGISTERED.json')):
            oldpaths.append(str(p.relative_to(ROOT)))
            def collect(v):
                if isinstance(v,dict):
                    for k,x in v.items():
                        if k in ('solver_seed','quantum_seed') and isinstance(x,int):oldseed.add(x)
                        else:collect(x)
                elif isinstance(v,list):
                    for x in v:collect(x)
            collect(read(p).get('runs',[]))
    newseed=[r['seeds'][k] for r in runs for k in ('solver_seed','quantum_seed') if r['seeds'][k] is not None]
    newseed.extend(b[k] for r in runs if r['method']!='A' for b in r['branches'] for k in ('solver_seed','quantum_seed') if b[k] is not None)
    if oldseed.intersection(newseed):raise ValueError('OLD_SEED_NUMERIC_COLLISION')
    sources={str(p.relative_to(ROOT)):digest(p) for p in runner.code_files()}
    for p in DOC.iterdir():
        if p.suffix in ('.py','.md'):sources[str(p.relative_to(ROOT))]=digest(p)
    with tarfile.open(root/'SOURCE_SNAPSHOT.tar.gz','w:gz') as archive:
        for name in sources:archive.add(ROOT/name,arcname=name)
    env=environment();dump(root/'ENVIRONMENT.json',env)
    m={'experiment_id':ID,'phase':'non_time_variance_pilot','executable':True,'r_pilot':5,
        'contract_id':'whole-method-finite-work-v1','config':c,'config_hash':digest(runner.CONFIG),
        'inherited_config_metadata':'root_seed/validation count in inherited config NOT used to generate this pilot; see seed_rule/r_pilot',
        'T_kind':TIME_KIND,'cpu_profile':old['cpu_profile'],'cases':cases,'runs':runs,
        'run_list_hash':fingerprint(runs),'source_hashes':sources,'snapshot_sha256':digest(root/'SOURCE_SNAPSHOT.tar.gz'),
        'physical_hash':old['physical_hash'],'environment':env,'registered_utc':utc(),
        'seed_rule':{'root':SEED_ROOT,'order_seed':ORDER_SEED,'formula':'SeedSequence([root,scale_index,method_index,repeat]), solver modulo (2**31-1), quantum uint32; existing branch_seeds then SeedSequence([branch quantum,round,route])',
            'old_manifests_checked':oldpaths,'old_seed_collision':False,'A_seed':None},
        'reference_groups':{s:[r['run_id'] for r in runs if r['case_id']==s and r['method']=='A'] for s in SCALES},
        'analysis':{'protocol':str((DOC/'PROTOCOL.md').relative_to(ROOT)),'protocol_hash':digest(DOC/'PROTOCOL.md'),
            'targets':read(ROOT/'configs/toc_delivery/comparison_design_20261116_v1.json')['auxiliary']['target_values'],
            'quality_target_use':'descriptive only; never termination/adoption','old_observations_in_estimation':False},
        'stopping':'exact fixed list once; preserve failure/interruption; no elapsed solver cutoffs or adaptive count',
        'selection':old['selection'],'termination_rules':old['termination_rules']}
    validate(m)
    dump(root/'REGISTERED.json',m);dump(root/'PILOT_MANIFEST.json',m)
    dump(root/'REGISTRATION_LOCK.json',{'REGISTERED.json':digest(root/'REGISTERED.json'),'PILOT_MANIFEST.json':digest(root/'PILOT_MANIFEST.json'),
        'manifest_fingerprint':fingerprint(m),'run_list_hash':m['run_list_hash'],'registered_before_any_trial':True})
    dump(root/'MAIN_MANIFEST.json',{'experiment_id':ID+'_main_pending','phase':'formal','executable':False,'decision':'HOLD',
        'scales':list(SCALES),'M_per_scale':1,'R_a':None,'h_D_adopted':None,'rate_halfwidth_adopted':None,
        'primary_scope_adopted':None,'formal_seed_list':None,'execution_order':None,'A_time_reference_members':None,
        'fixed_conditions_from_pilot':m['config_hash'],'pilot_run_list_hash':m['run_list_hash'],'runs':[],
        'main_stop_rule':'fixed preregistered list including failures, after explicit user decisions; no pilot reuse'})
    dump(root/'REGISTRATION_TIMING.json',{'wall_s':time.perf_counter()-start,'outside_T':True})
    print(json.dumps({'registered':str(root),'trials':75,'list_hash':m['run_list_hash']}),flush=True)

def attempt_state(directory):
    directory=Path(directory)
    if (directory/'RESULT.json').exists():return 'FINISHED'
    if directory.exists():return 'UNFINISHED'
    return 'NOT_STARTED'

def run(root):
    root=Path(root).resolve();m=load_registration(root)
    with (root/'BATCH.lock').open('a') as guard:
        try:fcntl.flock(guard,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('BATCH_ALREADY_RUNNING')
        preflight(m)
        # A previous crashed coordinator can leave live children, including just before STARTED.
        residual=[]
        for p in Path('/proc').glob('[0-9]*/cmdline'):
            try:
                command=p.read_bytes().replace(b'\0',b' ').decode(errors='replace')
                if str(root/'runs') in command and 'kmd_toc.termination_v1.runner child' in command:residual.append(int(p.parent.name))
            except (FileNotFoundError,PermissionError,ProcessLookupError):pass
        if residual:raise ValueError('EXISTING_CHILDREN_REQUIRE_RECOVERY:'+str(residual))
        # Do not start any new run while an earlier started result remains unrecovered.
        if any(attempt_state(root/'runs'/r['run_id'])=='UNFINISHED' for r in m['runs']):raise ValueError('UNFINISHED_ATTEMPT_PRESERVED_NO_AUTOMATIC_RESTART')
        info={'pid':os.getpid(),'start_ticks':ticks(os.getpid()),'boot_id':boot(),'started_utc':utc()}
        atomic(root/'COORDINATOR.json',info)
        begin=time.perf_counter()
        from kmd_toc.comparison_v1.execution import physical_checks,auxiliary
        from kmd_toc.common.models import load_problem,load_plan
        setup=time.perf_counter()-begin
        (root/'runs').mkdir(exist_ok=True)
        records=[];stop=None
        try:
            for r in m['runs']:
                directory=root/'runs'/r['run_id']
                if attempt_state(directory)=='FINISHED':continue
                preflight(m) # uniform management check outside existing timed operation
                # Preserve the inherited runner's parent mask; children alone pin to
                # registered cores. Always restore after a trial if a callee alters it.
                original=set(os.sched_getaffinity(0))
                before=time.perf_counter();when=utc()
                atomic(root/'ACTIVE.json',{'run_id':r['run_id'],'order_index':r['order_index'],'start_utc':when,
                    'before_execute_perf_counter':before,'boot_id':boot(),'coordinator':info})
                before_execute=time.perf_counter()
                try:row=runner.execute(m,r,directory)
                finally:os.sched_setaffinity(0,original)
                after=time.perf_counter()
                meta={'run_id':r['run_id'],'order_index':r['order_index'],'start_utc':when,'end_utc':utc(),
                    'before_management_write_perf_counter':before,'before_execute_perf_counter':before_execute,
                    'after_execute_perf_counter':after,'boot_id':boot(),'wrapper_wall_s':after-before,
                    'T_attempt':row['T_attempt'],'wrapper_outside_T_s':after-before-row['T_attempt'],
                    'parent_affinity_restored':sorted(os.sched_getaffinity(0)),
                    'exact_T_origin_perf_counter':None,'origin_reason':'existing timed runner does not export exact parent start; wrapper timestamps bracket execute',
                    'observed_elapsed_only':False}
                dump(directory/'MANAGEMENT.json',meta);records.append(meta)
                print(json.dumps({'finished_order':r['order_index'],'of':75,'run_id':r['run_id'],'state':row['execution_state']}),flush=True)
                fatal=('USER_CANCELLED','EXTERNAL_INTERRUPTION','RESOURCE_STOP')
                if row['execution_state'] in fatal or row['input_state']!='VALID':stop={'run_id':r['run_id'],'reason':row['execution_state'],'error':row['error']};break
                if isinstance(row.get('error'),dict) and 'CHANGED' in row['error'].get('message',''):stop={'run_id':r['run_id'],'reason':'IDENTITY_MISMATCH'};break
                if any(b.get('error',{}).get('message')=='CHILD_EXIT_WITHOUT_RESULT' for b in row['branches'] if isinstance(b.get('error'),dict)):
                    stop={'run_id':r['run_id'],'reason':'UNRECOVERED_CHILD'};break
        finally:
            atomic(root/'LAST_INVOCATION.json',{'started':info,'ended_utc':utc(),'setup_s':setup,'stop':stop,
                'wall_after_imports_s':time.perf_counter()-begin,'new_completed_ids':[r['run_id'] for r in records],
                'all_registered_results_present':all(attempt_state(root/'runs'/r['run_id'])=='FINISHED' for r in m['runs'])})
        return stop

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('register','run','aggregate','validate'));p.add_argument('path',nargs='?',default=str(OUT));a=p.parse_args()
    root=Path(a.path)
    if a.action=='register':register(root)
    elif a.action=='run':
        try:run(root)
        except BaseException as error:
            if root.is_dir():atomic(root/'RUN_MANAGEMENT_FAILURE.json',{'type':type(error).__name__,'message':str(error),'utc':utc(),'automatic_retry':False})
            raise
    elif a.action=='validate':preflight(load_registration(root));print('registration valid')
    else:
        from analysis import aggregate
        aggregate(root)
if __name__=='__main__':main()
