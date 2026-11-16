"""Parent wall measurement, immutable transport, independent checks, hard watchdog."""
import ctypes
from dataclasses import asdict
import json
import math
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

from .contract import (ROOT, TIME_KIND, atomic, check_freeze, check_profile, digest, dump,
                       read, run_identity, validate_manifest)


class OuterDeadline(TimeoutError):
    pass


def cleanup(process):
    """Stop only our new session, reap leader and adopted grandchildren."""
    if process is None:return {'session_empty':True,'reaped':[]}
    pgid=process.pid
    observed=[];pending=[pgid];seen=set()
    while pending:
        pid=pending.pop()
        if pid in seen:continue
        seen.add(pid)
        try:
            base=Path(f'/proc/{pid}')
            children=(base/f'task/{pid}/children').read_text().split()
            pending.extend(map(int,children))
            stat=(base/'stat').read_text().rsplit(')',1)[1].split()
            status=dict(s.split(':',1) for s in (base/'status').read_text().splitlines() if ':' in s)
            observed.append({'pid':pid,'affinity':sorted(os.sched_getaffinity(pid)),
                'observed_cpu_s':(int(stat[11])+int(stat[12]))/os.sysconf('SC_CLK_TCK'),
                'max_rss_KiB':int(status.get('VmHWM','0 kB').split()[0]),
                'threads':int(status.get('Threads','0')),'scope':'partial live process observation before cleanup'})
        except (FileNotFoundError,ProcessLookupError):pass
    try:os.killpg(pgid,signal.SIGTERM)
    except ProcessLookupError:pass
    try:process.wait(timeout=.2)
    except subprocess.TimeoutExpired:pass
    try:os.killpg(pgid,signal.SIGKILL)
    except ProcessLookupError:pass
    process.wait(timeout=2)
    reaped=[]
    until=time.perf_counter()+2
    while time.perf_counter()<until:
        try:
            pid,_=os.waitpid(-pgid,os.WNOHANG)
            if pid:reaped.append(pid);continue
        except ChildProcessError:
            break
        time.sleep(.005)
    try:os.killpg(pgid,0);empty=False
    except ProcessLookupError:empty=True
    return {'session_empty':empty,'reaped':reaped,'leader_pid':pgid,
            'leader_returncode':process.returncode,'live_process_observations':observed,
            'complete_CPU_accounting':False}


def supervise(command,out,deadline,on_message,*,memory_limit_MiB=None,dependency_prefix=None):
    # Linux subreaper prevents orphaned fork grandchildren/zombies after timeout.
    if ctypes.CDLL(None,use_errno=True).prctl(36,1,0,0,0)!=0:
        raise OSError(ctypes.get_errno(),'PR_SET_CHILD_SUBREAPER')
    process=None;seen=False;ended='NORMAL';caught=None
    try:
        with (Path(out)/'execution.log').open('x') as log:
            process=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,
                start_new_session=True,env={**os.environ,'PYTHONPATH':(dependency_prefix+':' if dependency_prefix else '')+str(ROOT/'src'),'PYTHONDONTWRITEBYTECODE':'1',
                    'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1'})
            next_sample=0.
            while True:
                if time.perf_counter()>=deadline:raise OuterDeadline('COMMON_OUTER_WALL_LIMIT')
                if memory_limit_MiB is not None and time.perf_counter()>=next_sample:
                    from .telemetry import tree_sample
                    sample=tree_sample(process.pid)
                    with (Path(out)/'RESOURCE_SAMPLES.jsonl').open('a') as stream:
                        stream.write(json.dumps(sample)+'\n')
                    next_sample=time.perf_counter()+.5
                    if sample['tree_rss_sum_KiB']>memory_limit_MiB*1024:
                        raise MemoryError('REGISTERED_PROCESS_TREE_RSS_LIMIT')
                message=Path(out)/'message.json'
                if not seen and message.exists():
                    on_message(read(message));seen=True
                if process.poll() is not None:
                    if not seen and message.exists():on_message(read(message));seen=True
                    if process.returncode!=0:ended='CHILD_PROCESS_ERROR'
                    break
                time.sleep(.005)
    except OuterDeadline as error:
        ended='OUTER_WALL_LIMIT';caught=str(error)
    except BaseException as error:
        caught={'type':type(error).__name__,'message':str(error)};ended='RUNTIME_ERROR'
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        info=cleanup(process)
    return {'termination_reason':ended,'error':caught,'cleanup':info,'received_message':seen}


def physical_checks(p,plan,method):
    from kmd_toc.common.validation import validate_plan
    from kmd_toc.baseline_a.program_validation import audit_plan
    common=validate_plan(p,plan).as_dict()
    independent=audit_plan(p,plan)
    agrees=(common['feasible'] and independent['feasible'] and
        abs(common['D_km']-float(independent['D_km']))<=1e-7 and
        common['W_min']==float(independent['W_min']))
    specific=None
    if method=='A':
        from kmd_toc.baseline_a.rule_validation import audit_rule
        specific=audit_rule(p,plan)
        meta=plan.method_settings
        trace=meta.get('candidate_trace',[])
        rules=(meta.get('method_version')=='A_rule_v1-20261115' and
            meta.get('accepted_moves',math.inf)<=len(p.vehicles) and
            meta.get('accepted_moves')==sum(x['status']=='ACCEPTED' for x in trace) and
            all(tuple(x['after'])<tuple(x['before']) for x in trace if x['status']=='ACCEPTED') and
            meta.get('loading_rule')=='ready_FCFS')
        agrees=agrees and specific['feasible'] and rules
    return bool(agrees),{'common_physical':common,'independent_physical':independent,'method_specific':specific}


def auxiliary(p,plan):
    trips=[{k:getattr(t,k) for k in ('vehicle_id','trip_no','berth_id','ready_s','load_start_s','load_end_s',
                                   'departure_s','return_s','waiting_s','distance_m')} for t in plan.trips]
    vehicles=[]
    for i,v in enumerate(p.vehicles):
        own=[t for t in plan.trips if t.vehicle_id==v.vehicle_id]
        returned=max((t.return_s for t in own),default=None)
        vehicles.append({'vehicle_index':i,'vehicle_id':v.vehicle_id,'active':bool(own),
            'final_return_s':returned,'L_s':returned-v.first_ready_s if own else 0,
            'O_s':max(0,returned-v.return_deadline_s) if own else 0})
    return {'active_vehicles':sum(v['active'] for v in vehicles),'nonempty_trips':len(trips),
        'vehicles':vehicles,'events':trips,'berths':{b.berth_id:[{'start_s':t.load_start_s,'end_s':t.load_end_s,
            'vehicle_id':t.vehicle_id,'trip_no':t.trip_no} for t in sorted(plan.trips,key=lambda t:t.load_start_s)
            if t.berth_id==b.berth_id] for b in p.berths}}


def execute(manifest,run,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    case=next(c for c in manifest['cases'] if c['case_id']==run['case_id'])
    row={**run_identity(manifest,run),'input_state':'VALID' if case['input'].get('preflight_physical_validation')=='VALID' else 'NOT_CHECKED',
        'termination_reason':'NOT_STARTED',
        'validation_state':'NOT_RUN','adoptable':False,'D':None,'W':None,'W_first':None,'W_reload':None,
        'T_program':None,'T_attempt':None,'T_input':None,'T_planning':None,'T_validation':None,
        'T_adapter':None,'T_setup':None,'T_export':None,'J':None,'J_reason':'A_TIME_REFERENCE_INCOMPLETE',
        'error':None,'plan_sha256':None,'plan_semantic_hash':None,'native_time':None}
    # Identity/manifest persistence is registration. No delivery input is loaded yet.
    dump(out/'manifest.json',{'run':run,'case':case,'contract_id':manifest['contract_id'],
        'resource_contract':manifest['resource_contract'],'T_kind':TIME_KIND,'source_hashes':manifest['source_hashes']})
    start=time.perf_counter();deadline=start+case['budget_wall_s'];cpu=time.process_time()
    p=None;proc=None;accepted=None;checks=None;aux=None;input_end=None;validation_s=0.;adapter_s=0.
    phase='INPUT';process_info=None
    previous_handler=signal.getsignal(signal.SIGALRM)
    def alarm(*_):raise OuterDeadline('COMMON_OUTER_WALL_LIMIT')
    signal.signal(signal.SIGALRM,alarm)
    signal.setitimer(signal.ITIMER_REAL,case['budget_wall_s'])
    try:
        check_freeze();check_profile(manifest['cpu_profile']['cpu_ids'])
        if run['method']=='A':os.sched_setaffinity(0,{manifest['cpu_profile']['cpu_ids'][0]})
        for name,expected in manifest['source_hashes'].items():
            if digest(ROOT/name)!=expected:raise ValueError('REGISTERED_SOURCE_CHANGED:'+name)
        for name,expected in case['input']['files'].items():
            if digest(Path(case['input']['directory'])/name)!=expected:raise ValueError('INPUT_HASH_MISMATCH:'+name)
        from kmd_toc.common.models import load_problem,load_plan
        from .contract import fingerprint
        p=load_problem(case['input']['directory'])
        if p.fingerprint!=row['input_hash'] or p.od.fingerprint!=row['OD_hash']:
            raise ValueError('COMMON_INPUT_IDENTITY_MISMATCH')
        row['input_state']='VALID'
        input_end=time.perf_counter();phase='EXECUTION'
        (out/'native').mkdir()
        atomic(out/'job.json',{'manifest':manifest,'case':case,'run':run,'deadline_perf_counter':deadline})
        def receive(message):
            nonlocal accepted,checks,validation_s,adapter_s,phase,aux
            if message['kind']!='candidate':
                row['native_status']=message.get('native_status');return
            phase='ADAPTER'
            before=time.perf_counter()
            raw=out/'candidate_plan.json'
            if digest(raw)!=message['sha256']:raise ValueError('PLAN_TRANSPORT_HASH_MISMATCH')
            plan=load_plan(raw)
            expected_method='B' if run['method']=='D_CLASSICAL_REPLACEMENT' else run['method']
            if plan.method_id!=expected_method:raise ValueError('METHOD_IMPLEMENTATION_MISMATCH')
            content=raw.read_bytes()
            adapter_s+=time.perf_counter()-before
            phase='VALIDATION';before=time.perf_counter()
            valid,checks=physical_checks(p,plan,run['method'])
            validation_s+=time.perf_counter()-before
            codes={v['code'] for v in checks['common_physical']['violations']}
            row['validation_state']='VALIDATED' if valid else ('NO_FEASIBLE_PLAN' if codes and
                codes<={'RETURN_DEADLINE_2000','BERTH_AVAILABILITY'} else 'INVALID_PLAN')
            row['native_status']=message.get('native_status')
            row['native_stop_reason']=message.get('native_stop_reason')
            row['worker_resources']={k:message.get(k) for k in ('worker_pid','cpu_time_s','max_rss_KiB','native_threads','observed_threads')}
            # A's intrinsic safety cap cannot be bypassed by a larger common cap.
            if message.get('native_status') in ('NATIVE_TIME_LIMIT','TIME_BUDGET_EXCEEDED'):
                valid=False;row['validation_state']='NATIVE_DEADLINE_REJECTED'
            aux=auxiliary(p,plan)
            if valid and time.perf_counter()<deadline:
                common=checks['common_physical']
                prepared={'D':common['D_km'],'W':common['W_min'],'W_first':common['W1_min'],
                    'W_reload':common['W2_min'],'plan_sha256':message['sha256'],
                    'plan_semantic_hash':fingerprint(asdict(plan)),
                    'validated_at_s':time.perf_counter()-start}
                # Adopted bytes are the exact received bytes, not a reserialization.
                with (out/'plan.json').open('xb') as stream:stream.write(content)
                atomic(out/'validated_checkpoint.json',prepared)
                if time.perf_counter()<deadline:
                    accepted={**prepared,'validated_at_s':time.perf_counter()-start}
            phase='EXECUTION'
        control_options={}
        if manifest.get('design_extension'):
            control_options={'memory_limit_MiB':manifest['design_extension'].get('tree_memory_limit_MiB'),
                             'dependency_prefix':manifest['design_extension'].get('dependency_prefix')}
        process_info=supervise([sys.executable,'-B','-m','kmd_toc.comparison_v1.worker',str(out)],out,deadline,receive,**control_options)
        row.update(termination_reason=process_info['termination_reason'],error=process_info['error'])
        if not process_info['cleanup']['session_empty']:
            row.update(termination_reason='CLEANUP_ERROR',error='OWNED_PROCESS_GROUP_NOT_EMPTY')
            accepted=None
        if row.get('native_stop_reason')=='MOVE_LIMIT' and row['termination_reason']=='NORMAL':
            row['termination_reason']='A_MOVE_LIMIT'
        if row['validation_state']=='NOT_RUN' and row['termination_reason']=='NORMAL':
            row['validation_state']='NO_PLAN'
    except OuterDeadline as error:
        row.update(termination_reason='OUTER_WALL_LIMIT',error={'phase':phase,'message':str(error)})
    except Exception as error:
        row.update(termination_reason='INPUT_INVALID' if phase=='INPUT' else 'RUNTIME_ERROR',
            input_state='INVALID' if phase=='INPUT' else row['input_state'],
            error={'phase':phase,'type':type(error).__name__,'message':str(error)})
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,previous_handler)
    elapsed=time.perf_counter()-start
    if elapsed>case['budget_wall_s'] and row['termination_reason'] in ('NORMAL','A_MOVE_LIMIT'):
        row['termination_reason']='OUTER_WALL_LIMIT'
    row.update(T_attempt=elapsed,T_input=input_end-start if input_end else elapsed,
        T_planning=max(0,elapsed-(input_end-start)-validation_s-adapter_s) if input_end else None,
        T_validation=validation_s if input_end else None,T_adapter=adapter_s if input_end else None,
        parent_cpu_s=time.process_time()-cpu,parent_max_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        parent_pid=os.getpid(),parent_affinity=sorted(os.sched_getaffinity(0)),
        native_threads_environment={k:os.environ.get(k) for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')},
        process_control=process_info)
    if accepted is not None:
        row.update(**{k:v for k,v in accepted.items() if k!='validated_at_s'},adoptable=True,
            T_program=elapsed if elapsed<=case['budget_wall_s'] else accepted['validated_at_s'],
            validation_completed_at_s=accepted['validated_at_s'],
            success_kind='LIMIT_WITH_VALIDATED_PLAN' if row['termination_reason']=='OUTER_WALL_LIMIT' else 'VALIDATED_PLAN')
    else:
        row['success_kind']='NO_ADOPTABLE_PLAN'
        if row['validation_state']=='NOT_RUN' and row['input_state']=='VALID':row['validation_state']='NO_PLAN'
    export=time.perf_counter()
    if (out/'native_result.json').exists():
        native=read(out/'native_result.json')
        row['native_time']={k:native.get(k) for k in ('T_program_s','T_attempt_wall_s','T_native_program','dependency_setup_s')}
        row['T_setup']=native.get('dependency_setup_s')
        row['native_resources']={k:native.get(k) for k in ('process_cpu_s','total_process_cpu_s','max_rss_KiB',
            'aggregate_RSS_upper_bound_KiB','parallel_branches','quantum_backend_environment','quantum_accounting_complete',
            'total_training_shots','total_final_shots','completed_quantum_call_observations','selected_branch')}
        row['native_limit_stop']=bool((native.get('error') or {}).get('scheduled_budget_stop')) or any(
            b.get('timed_out') or (b.get('error') or {}).get('scheduled_budget_stop') or
            b.get('status') in ('TIME_BUDGET_EXCEEDED','BRANCH_WALL_TIMEOUT') for b in native.get('parallel_branches',[]))
    if checks is not None:dump(out/'validation.json',checks)
    if aux is not None:dump(out/'auxiliary.json',{**aux,'diagnostic_only':not row['adoptable']})
    if (out/'candidate_plan.json').exists() and not row['adoptable']:
        (out/'rejected_plan.json').write_bytes((out/'candidate_plan.json').read_bytes())
    row['T_export']=time.perf_counter()-export
    row['timing_notes']='T_setup overlaps T_planning; native times overlap parent wall; do not sum them. Transfer and IPC included. Archival export excluded.'
    dump(out/'result.json',row)
    dump(out/'OUTPUT_HASHES.json',{str(f.relative_to(out)):digest(f) for f in out.rglob('*') if f.is_file()})
    return row


def run_registered(path,*,allow_formal=False):
    path=Path(path).resolve();manifest=validate_manifest(read(path));check_freeze()
    if manifest['phase']=='formal' and not allow_formal:raise ValueError('FORMAL_EXECUTION_REQUIRES_SEPARATE_EXPLICIT_AUTHORIZATION')
    check_profile(manifest['cpu_profile']['cpu_ids'])
    os.sched_setaffinity(0,set(manifest['cpu_profile']['cpu_ids']))
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
    setup=time.perf_counter()
    # Same coordinator validation-library state before every method; no input,
    # route pool, solver or circuit is prepared here. Every fresh child startup
    # and its method-specific initialization remains INSIDE the parent wall.
    from kmd_toc.common.models import load_problem,load_plan
    from kmd_toc.common.validation import validate_plan
    from kmd_toc.baseline_a.program_validation import audit_plan
    from kmd_toc.baseline_a.rule_validation import audit_rule
    import platform
    dump(path.parent/'COORDINATOR_SETUP.json',{'wall_s':time.perf_counter()-setup,
        'scope':'uniform coordinator validation library imports only; no problem-specific work',
        'python':sys.version,'executable':sys.executable,'platform':platform.platform(),
        'python_search_path':sys.path,'dependency_prefix':manifest.get('design_extension',{}).get('dependency_prefix'),
        'cpu_model':next((s for s in Path('/proc/cpuinfo').read_text().splitlines() if s.startswith('model name')),None),
        'meminfo':[s for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith(('MemTotal:','MemAvailable:'))]})
    with (path.parent/'environment.txt').open('x') as stream:
        subprocess.run([sys.executable,'-m','pip','freeze'],stdout=stream,stderr=subprocess.STDOUT,check=True)
    out=path.parent/'runs';out.mkdir(exist_ok=False)
    rows=[]
    for run in manifest['runs']:
        pipeline_deadline=manifest.get('design_extension',{}).get('pipeline_deadline_perf_counter')
        case=next(c for c in manifest['cases'] if c['case_id']==run['case_id'])
        if pipeline_deadline and time.perf_counter()+case['budget_wall_s']+10>pipeline_deadline:
            dump(path.parent/'SAFETY_STOP.json',{'reason':'PIPELINE_BUDGET_RESERVATION',
                'remaining':'NOT_STARTED; no shortened trials or replacement'})
            break
        os.sched_setaffinity(0,set(manifest['cpu_profile']['cpu_ids']))
        row=execute(manifest,run,out/run['run_id']);rows.append(row)
        print(json.dumps({k:row.get(k) for k in ('run_id','method','termination_reason','validation_state','adoptable','D','W','T_program','T_attempt')},ensure_ascii=False),flush=True)
        if manifest.get('design_extension') and (row['input_state']=='INVALID' or
                row['termination_reason']=='CLEANUP_ERROR' or
                'REGISTERED_PROCESS_TREE_RSS_LIMIT' in str(row.get('error'))):
            dump(path.parent/'SAFETY_STOP.json',{'run_id':run['run_id'],'reason':row.get('error') or row['termination_reason'],
                'remaining':'preserve as NOT_STARTED; no replacement'})
            break
    dump(path.parent/'ALL_RESULTS.json',rows)
    return rows
