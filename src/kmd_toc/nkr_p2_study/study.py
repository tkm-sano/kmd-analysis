"""Registered staged pilot, sequential groups, four single-thread CPU branches."""
from dataclasses import asdict
from datetime import datetime, timezone
import gzip
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time
import traceback

import psutil

from kmd_toc.d_local_design.pipeline import ROOT, INPUTS, SAVED, read, dump, digest, environment
from kmd_toc.common.models import load_problem, load_plan
from kmd_toc.d_local_design.completion import physical
from kmd_toc.main_experiment_d import shots, depth
from kmd_toc.main_experiment_d.quantum import backend_modules
from . import model, kernel

CONFIG = ROOT/'configs/nkr_p2_20261120/protocol.json'
OUT = ROOT/'output/nkr_p2_20261120_v1'
DOC = ROOT/'docs/research/nkr_p2_20261120'


def gzsave(path, data):
    with gzip.open(path, 'wt') as stream: json.dump(data, stream, allow_nan=False)


def load_case(scale):
    p = load_problem(INPUTS/scale); plan = load_plan(SAVED/f'{scale}_B_pilot_r01/plan.json')
    if not physical(p, plan)[0]: raise ValueError('INITIAL_PLAN_INVALID')
    return p, plan


def source_pins():
    files = [CONFIG, *Path(__file__).parent.glob('*.py')]
    files = [p for p in files if p.name not in ('analyze.py',)]
    files += list((ROOT/'src/kmd_toc/main_experiment_d').glob('*.py'))
    files += [shots.CONFIG, depth.CONFIG, ROOT/'scripts/p2_precision_20261120/sector_mps.py',
              ROOT/'scripts/large_n_20261119_v5/quantum.py',ROOT/'src/kmd_toc/d_local_design/completion.py',
              ROOT/'src/kmd_toc/d_local_design/coverage.py',ROOT/'src/kmd_toc/cargo_wait_v2/evaluation.py',
              ROOT/'configs/toc_delivery/dw_policy_20261117_v1.json',ROOT/'docs/research/DW_RESEARCH_POLICY.md']
    return {str(p.relative_to(ROOT)):digest(p) for p in files}


def check_pins():
    m = read(OUT/'MANIFEST.json')
    for name, expected in {**m['source_hashes'], **m['input_hashes']}.items():
        if digest(ROOT/name) != expected: raise ValueError('SOURCE_OR_INPUT_CHANGED:'+name)
    return m


def cpus_available():
    load = psutil.cpu_percent(interval=.5, percpu=True); seen=set(); chosen=[]
    for cpu in sorted(os.sched_getaffinity(0), key=lambda i:(load[i],i)):
        base=Path(f'/sys/devices/system/cpu/cpu{cpu}/topology')
        physical_id=((base/'physical_package_id').read_text().strip(),(base/'core_id').read_text().strip())
        if physical_id in seen or load[cpu] > 25: continue
        chosen.append(cpu);seen.add(physical_id)
        if len(chosen)==4: break
    if len(chosen)!=4: raise ValueError('FOUR_AVAILABLE_PHYSICAL_CORES_REQUIRED')
    return chosen, {str(i):load[i] for i in chosen}


def initialize():
    if OUT.exists(): raise ValueError('NEW_EXPERIMENT_ID_REQUIRED')
    protocol=read(CONFIG);env=environment();cpus,load=cpus_available();pins={}
    for scale in ('S1','S2','S3'):
        for path in [INPUTS/scale/'input.json',*(INPUTS/scale/'od').glob('*'),SAVED/f'{scale}_B_pilot_r01/plan.json']:
            if path.is_file():pins[str(path.relative_to(ROOT))]=digest(path)
    shots.frozen_config();depth.frozen_config()
    OUT.mkdir(parents=True,exist_ok=False)
    dump(OUT/'PROTOCOL.json',protocol)
    dump(OUT/'MANIFEST.json',{'experiment_id':protocol['experiment_id'],'main_experiment':False,
        'registered_utc':datetime.now(timezone.utc).isoformat(),'HEAD':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'source_hashes':source_pins(),'input_hashes':pins,'environment':env,'cpus':cpus,'cpu_load_percent':load,
        'freeze':{'depth':depth.frozen_config(),'shots':shots.frozen_config()},
        'process_load':[{'pid':p.pid,'name':p.info['name'],'rss':p.info['memory_info'].rss} for p in psutil.process_iter(['name','memory_info']) if p.info['memory_info'] and p.info['memory_info'].rss>1024**3]})
    dump(OUT/'RUN_CONTROL.json',{'measured_supervisor_wall_s':0.,'groups':[],'main_experiment':False})
    dump(OUT/'DECISION.json',{'status':'HOLD','adopted_n':None,'adopted_K_coefficient':None,'adopted_R':None})
    print('Registered',OUT,flush=True)


def structural():
    check_pins();q,_=backend_modules();records=[]
    for scale in ('S1','S2','S3'):
        p,plan=load_case(scale)
        for n in (10,12):
            local=model.pick(p,plan,set(),n,model.seed_for(9201,0,1,1));lookup=q.boundary_lookups(p,plan,local)
            record=model.validate_oracle(p,plan,local,q,lookup,20)
            lower=model.unconstrained_bound(local,lookup)+record['constant_outside_m']
            base=model.dw(p,plan)['D_km']*1000
            if lower>base+1e-7:raise ValueError('INCUMBENT_EXCLUDED_FROM_SPACE')
            records.append({'scale':scale,'n':n,'initial_D_m':base,'unconstrained_lower_D_m':lower,
                'potential_D_gain_m':base-lower,'local_customer_ids':local.customer_ids,**record,
                'note':'unconstrained lower bound, no feasible improvement or QAOA superiority inferred'})
    dump(OUT/'STRUCTURAL.json',{'status':'PASS','model_version':read(CONFIG)['model_version'],'checks':records})
    print('Structural checks PASS',len(records),flush=True)


def worker(job_path):
    job=read(job_path);out=Path(job['output']);protocol=read(OUT/'PROTOCOL.json')
    os.sched_setaffinity(0,{job['cpu']});start=time.perf_counter();cpu=time.process_time()
    status='COMPLETE';reason=None;sets=[];started_sets=[];rows=[];iterations=[]
    timings={'initial_plan_generation_s':None,'input_saved_plan_load_s':0.,'candidate_generation_s':0.,
             'oracle_validation_s':0.,'assessment_s':0.,'final_validation_s':0.}
    current_call=None
    try:
        begin=time.perf_counter();p,plan=load_case(job['scale']);timings['input_saved_plan_load_s']=time.perf_counter()-begin
        initial=model.dw(p,plan);current=initial
        for r in range(1,job['R']+1):
            iteration_start=time.perf_counter();before_r=current;adopted_r=0;calls_r=0
            for k in range(1,job['K']+1):
                call_id=f'r{r:03d}_k{k:03d}';seed=model.seed_for(job['outer_seed'],job['branch'],r,k)
                begin=time.perf_counter();local=model.pick(p,plan,set().union(*sets) if sets else set(),job['n'],seed)
                generation_s=time.perf_counter()-begin;timings['candidate_generation_s']+=generation_s
                row={'r':r,'k':k,'call_id':call_id,'seed':seed,'generated':local is not None,'generation_s':generation_s,'status':'NO_SELECTION'}
                if local is None:
                    rows.append(row);continue
                current_call=call_id;call_dir=out/'calls'/call_id;call_dir.parent.mkdir(parents=True,exist_ok=True)
                row.update(customer_ids=local.customer_ids,trips=local.trip_ids,status='STARTED')
                begin=time.perf_counter();q,_=backend_modules();lookup=q.boundary_lookups(p,plan,local)
                oracle_check=model.validate_oracle(p,plan,local,q,lookup,2)
                timings['oracle_validation_s']+=time.perf_counter()-begin;row['oracle_check']=oracle_check
                started_sets.append(set(local.customer_ids));rows.append(row)
                dump(out/'HEARTBEAT.json',{'event':'call_started','call_id':call_id,'monotonic':time.monotonic(),'r':r,'k':k})
                decoded,quantum=kernel.run(p,plan,local,protocol,call_dir)
                sets.append(set(local.customer_ids));calls_r+=1
                begin=time.perf_counter()
                def save_candidate(index, proposal):
                    path=call_dir/f'candidate_{index}.json.gz';gzsave(path,asdict(proposal));return str(path.relative_to(OUT))
                selected,assessment=model.assess(p,plan,local,decoded,save_candidate,protocol['postmeasurement_checks'])
                timings['assessment_s']+=time.perf_counter()-begin
                metrics=model.dw(p,selected);adopted=selected is not plan
                row.update(status='COMPLETE',quantum=quantum,assessment=assessment,before=current,after=metrics,adopted=adopted,
                    coverage=model.coverage(sets,len(p.stops)),elapsed_wall_s=time.perf_counter()-start)
                dump(call_dir/'ASSESSMENT.json',row)
                if adopted:plan=selected;adopted_r+=1
                current=metrics
                dump(out/'PARTIAL.json',{'status':'IN_PROGRESS','last_completed':call_id,'rows':rows,'sets':[sorted(s) for s in sets],
                    'iterations':iterations,'initial':initial,'after':current,'plan':asdict(plan),'timings':timings,'wall_s':time.perf_counter()-start})
                dump(out/'HEARTBEAT.json',{'event':'call_complete','call_id':call_id,'monotonic':time.monotonic()})
            iteration={'r':r,'quantum_calls':calls_r,'adopted':adopted_r,'D':current['D_km'],'W':current['W_mean_min_per_operation'],
                'W_total':current['W_total_min'],'delta_D_r':current['D_km']-before_r['D_km'],
                'delta_W_r':current['W_mean_min_per_operation']-before_r['W_mean_min_per_operation'],
                'wall_s':time.perf_counter()-iteration_start,'cumulative_wall_s':time.perf_counter()-start,
                **model.coverage(sets,len(p.stops))}
            iterations.append(iteration);dump(out/f'ITERATION_{r:03d}.json',iteration);gzsave(out/f'ITERATION_{r:03d}.plan.json.gz',asdict(plan))
        begin=time.perf_counter()
        if not physical(p,plan)[0]:raise ValueError('FINAL_PLAN_INVALID')
        timings['final_validation_s']=time.perf_counter()-begin
    except Exception as error:
        status='FAILED';reason=f'{type(error).__name__}:{error}'
        dump(out/'FAILURE.json',{'reason':reason,'traceback':traceback.format_exc(),'call_id':current_call})
    finally:
        if 'plan' in locals():dump(out/'plan.json',asdict(plan))
        result={'status':status,'reason':reason,'job':job,'PID':os.getpid(),'affinity':sorted(os.sched_getaffinity(0)),
            'native_threads':1,'initial':initial if 'initial' in locals() else None,'after':current if 'current' in locals() else None,
            'sets':[sorted(s) for s in sets],'started_sets':[sorted(s) for s in started_sets],
            'rows':rows,'iterations':iterations,'timings':timings,'wall_s':time.perf_counter()-start,
            'CPU_s':time.process_time()-cpu,'RSS_highwater_MiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024}
        dump(out/'RESULT.json',result)


def disk_bytes():return sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())


def supervise(tag,scale,n,K,R,seed,branches=4):
    manifest=check_pins();protocol=read(OUT/'PROTOCOL.json');safety=protocol['safety_only'];control=read(OUT/'RUN_CONTROL.json')
    group=OUT/'groups'/tag
    if group.exists():raise ValueError('GROUP_EXISTS_NEW_ID_REQUIRED:'+tag)
    group.mkdir(parents=True,exist_ok=False)
    if environment()['effective_available_bytes'] < (safety['min_free_GiB_before_four_branches'] if branches==4 else 9)*1024**3:
        dump(group/'GROUP.json',{'status':'NOT_RUN_RESOURCE','tag':tag});return
    if control['measured_supervisor_wall_s']>=safety['batch_wall_s']:
        dump(group/'GROUP.json',{'status':'NOT_RUN_BATCH_BUDGET','tag':tag});return
    cpus,load=cpus_available();dump(group/'PREFLIGHT.json',{'cpus':cpus,'load':load,'memory_available':psutil.virtual_memory().available,
        'local_calls_planned':branches*K*R,'slots_planned':branches*n*K*R,'full_main_T':None})
    env={**os.environ,'PYTHONPATH':str(ROOT/'src'),'PYTHONDONTWRITEBYTECODE':'1',
         **{k:'1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}}
    children=[];handles=[];start=time.perf_counter();reason=None;peaks={};last_disk=0
    for b in range(branches):
        folder=group/f'branch_{b}';folder.mkdir()
        job={'tag':tag,'scale':scale,'n':n,'K':K,'R':R,'outer_seed':seed,'branch':b,'cpu':cpus[b],
             'output':str(folder),'model_version':protocol['model_version'],'main_experiment':False}
        dump(folder/'JOB.json',job);log=(folder/'worker.log').open('x');handles.append(log)
        child=subprocess.Popen([sys.executable,'-B','-m','kmd_toc.nkr_p2_study','_worker',str(folder/'JOB.json')],env=env,cwd=ROOT,
            stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append((child,folder));peaks[b]=0
    while any(child.poll() is None for child,_ in children):
        elapsed=time.perf_counter()-start
        for b,(child,folder) in enumerate(children):
            if child.poll() is None:
                try:peaks[b]=max(peaks[b],psutil.Process(child.pid).memory_info().rss)
                except psutil.NoSuchProcess:pass
                if peaks[b]>safety['per_worker_RSS_GiB']*1024**3:reason='RSS_SAFETY_STOP'
                heartbeat=folder/'HEARTBEAT.json'
                if heartbeat.exists():
                    h=read(heartbeat)
                    if h['event']=='call_started' and time.monotonic()-h['monotonic']>safety['local_wall_s']:reason='LOCAL_WALL_SAFETY_STOP'
            elif (folder/'RESULT.json').exists() and read(folder/'RESULT.json')['status']!='COMPLETE':reason='BRANCH_FAILURE'
            elif not (folder/'RESULT.json').exists():reason='BRANCH_PROCESS_FAILED'
        if elapsed>safety['group_wall_s']:reason='GROUP_WALL_SAFETY_STOP'
        if control['measured_supervisor_wall_s']+elapsed>safety['batch_wall_s']:reason='BATCH_WALL_SAFETY_STOP'
        if elapsed-last_disk>15:
            if disk_bytes()>safety['disk_GiB']*1024**3:reason='DISK_SAFETY_STOP'
            last_disk=elapsed
        if reason:
            for child,_ in children:
                if child.poll() is None:os.killpg(child.pid,signal.SIGTERM)
            break
        time.sleep(.25)
    for child,_ in children:
        try:child.wait(timeout=5)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
    for handle in handles:handle.close()
    parent_check_start=time.perf_counter();branch_results=[]
    p,initial=load_case(scale)
    for b,(child,folder) in enumerate(children):
        result_path=folder/'RESULT.json';partial=folder/'PARTIAL.json'
        result=read(result_path) if result_path.exists() else read(partial) if partial.exists() else {'status':'INCOMPLETE','rows':[]}
        result['sampled_peak_RSS_MiB']=peaks[b]/1024**2;result['returncode']=child.returncode
        if (folder/'plan.json').exists():
            final=load_plan(folder/'plan.json')
            if not physical(p,final)[0] or model.dw(p,final)!=result['after']:raise ValueError('PARENT_FINAL_VALIDATION_FAILED')
        elif result.get('plan'):
            dump(folder/'RECOVERED.plan.json',result['plan']);final=load_plan(folder/'RECOVERED.plan.json')
            if not physical(p,final)[0] or model.dw(p,final)!=result['after']:raise ValueError('PARENT_RECOVERY_VALIDATION_FAILED')
        branch_results.append({'branch':b,'status':result['status'],'returncode':child.returncode,
            'after':result.get('after'),'sampled_peak_RSS_MiB':peaks[b]/1024**2})
    group_status='COMPLETE' if not reason and all(r['status']=='COMPLETE' and r['returncode']==0 for r in branch_results) else 'INCOMPLETE'
    result={'tag':tag,'scale':scale,'n':n,'K':K,'R':R,'outer_seed':seed,'P':branches,
        'status':group_status,'reason':reason,'branch_results':branch_results,'parent_wall_s':time.perf_counter()-start,
        'parent_final_validation_s':time.perf_counter()-parent_check_start,
        'initial_plan_generation_s':None,'timing_scope':protocol['timing'],'initial':model.dw(p,initial)}
    dump(group/'GROUP.json',result)
    control['measured_supervisor_wall_s']+=result['parent_wall_s'];control['groups'].append({'tag':tag,'status':group_status,'wall_s':result['parent_wall_s']})
    dump(OUT/'RUN_CONTROL.json',control)
    print(tag,group_status,'wall_s',round(result['parent_wall_s'],2),'reason',reason,flush=True)
    return result


def probes():
    if not (OUT/'STRUCTURAL.json').exists():raise ValueError('STRUCTURAL_GATE_REQUIRED')
    for scale in ('S1','S2','S3'):
        for n in (10,12):
            tag=f'probe_{scale}_n{n}'
            if (OUT/'groups'/tag/'GROUP.json').exists():continue
            supervise(tag,scale,n,1,1,read(CONFIG)['screen_outer_seed'],1)


def gate(scale,n,K,R):
    protocol=read(CONFIG);safety=protocol['safety_only'];probe=OUT/f'groups/probe_{scale}_n{n}/GROUP.json'
    if not probe.exists() or read(probe)['status']!='COMPLETE':return False,{'reason':'PROBE_NOT_COMPLETE'}
    prior=read(OUT/f'groups/probe_{scale}_n{n}/branch_0/RESULT.json')
    local_max=max(row['quantum']['wall_s'] for row in prior['rows'] if row['status']=='COMPLETE')
    prediction=2*local_max*K*R+60
    remaining=safety['batch_wall_s']-read(OUT/'RUN_CONTROL.json')['measured_supervisor_wall_s']
    return prediction<=min(safety['group_wall_s'],remaining),{'conservative_predicted_s':prediction,'prediction_is_not_measurement':True,
        'remaining_batch_s':remaining,'probe_local_s':local_max,'reason':'PREDICTED_SAFETY_COMPLETION_GATE'}


def stage_a():
    for scale,V in [('S1',10),('S2',20),('S3',40)]:
        for n in (10,12):
            tag=f'screen_{scale}_n{n}_K{V//2}_R5_seed9201'
            if (OUT/'groups'/tag/'GROUP.json').exists():continue
            allowed,detail=gate(scale,n,V//2,5)
            dump(OUT/'gates'/(tag+'.json'),{'allowed':allowed,**detail})
            if allowed:supervise(tag,scale,n,V//2,5,9201)


def expand():
    """B/C registered order, only after complete A in the same scale/n."""
    for scale,V in [('S1',10),('S2',20),('S3',40)]:
        for n in (10,12):
            a=OUT/f'groups/screen_{scale}_n{n}_K{V//2}_R5_seed9201/GROUP.json'
            if not a.exists() or read(a)['status']!='COMPLETE':continue
            for K,R in [(V//2,13),(V,5),(V//2,25),(2*V,5)]:
                tag=f'screen_{scale}_n{n}_K{K}_R{R}_seed9201'
                if (OUT/'groups'/tag/'GROUP.json').exists():continue
                allowed,detail=gate(scale,n,K,R);dump(OUT/'gates'/(tag+'.json'),{'allowed':allowed,**detail})
                if allowed:supervise(tag,scale,n,K,R,9201)
