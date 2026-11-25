"""Four branches, sequential conditions, no clock-driven exclusion/stopping."""
from dataclasses import asdict
from datetime import datetime,timezone
import csv
import fcntl
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import sys
import time

import psutil

from kmd_toc.d_local_design.pipeline import environment
from kmd_toc.duty_break_v1.scheduler import replay
from kmd_toc.common.models import load_plan as load_legacy
from kmd_toc.d_final_selection_v1.ranking import Candidate,select,metric_record
from kmd_toc.d_final_selection_v1.policy import require_frozen as selection_frozen
from kmd_toc.main_experiment_d import shots,depth
from .common import *

REFERENCE_PY='/tmp/kmd-library-validation-20261114-v2/bin/python'


def grid():
    with (ROOT/'output/nkr_p2_20261120_v1/ALL54.csv').open() as f:
        return [{'scale':r['scale'],'n':int(r['n']),'K':int(r['K']),'R':int(r['R'])} for r in csv.DictReader(f)]


def tag(c,seed=9201):return f'{c["scale"]}_n{c["n"]}_K{c["K"]}_R{c["R"]}_seed{seed}'


def ordered_grid():
    original=grid();minimum=[]
    for n in (10,12):
        for scale,V in [('S1',10),('S2',20),('S3',40)]:minimum.append(dict(scale=scale,n=n,K=V//2,R=5))
    return minimum+[r for r in original if r not in minimum]


def cpus():
    load=psutil.cpu_percent(interval=.2,percpu=True);chosen=[];seen=set()
    for cpu in sorted(os.sched_getaffinity(0),key=lambda c:(load[c],c)):
        p=Path(f'/sys/devices/system/cpu/cpu{cpu}/topology')
        key=((p/'physical_package_id').read_text(),(p/'core_id').read_text())
        if key in seen:continue
        chosen.append(cpu);seen.add(key)
        if len(chosen)==4:return chosen
    raise ValueError('FOUR_PHYSICAL_CORES_UNAVAILABLE')


def initialize(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);protocol=read(CONFIG)
    assert len(grid())==54 and len({tag(x) for x in grid()})==54
    shots.frozen_config();depth.frozen_config();selection_frozen()
    files=[CONFIG,ROOT/'output/nkr_p2_20261120_v1/ALL54.csv',ROOT/'scripts/run_nkr_unlimited.py',
        ROOT/'scripts/large_n_20261119_v5/quantum.py',ROOT/'scripts/p2_precision_20261120/sector_mps.py']
    for package in ['nkr_unlimited','nkr_p2_study','main_experiment_d','common','fcfs_v1','duty_break_v1',
                    'd_final_selection_v1','d_local_design','cargo_wait_v2','pipeline','termination_v1','baseline_a']:
        files.extend((ROOT/'src/kmd_toc'/package).glob('*.py'))
    files.extend([shots.CONFIG,depth.CONFIG,ROOT/'configs/toc_delivery/common_conditions_v1_1.json',
        ROOT/'configs/toc_delivery/duty_break_20261121_v1.json',ROOT/'configs/toc_delivery/termination_rules_20261116_v1.json',
        ROOT/'docs/research/FCFS_OPERATING_POLICY_V1.md',ROOT/'docs/frozen/配送計画最適化_評価指標と実験条件_1-7.md',
        ROOT/'configs/d_final_selection_20261121_v1/policy.json',ROOT/'docs/research/d_final_selection_20261121_v1/FREEZE_SPEC.md'])
    for scale in ('S1','S2','S3'):
        files.extend(p for p in (INPUTS/scale).rglob('*') if p.is_file())
        files.append(SAVED/f'{scale}_B_pilot_r01/plan.json')
    pins={str(p.relative_to(ROOT)):digest(p) for p in sorted(set(files))}
    limits={'RLIMIT_CPU':list(resource.getrlimit(resource.RLIMIT_CPU)),'RLIMIT_AS':list(resource.getrlimit(resource.RLIMIT_AS)),
        'scheduler_environment':{k:os.environ[k] for k in ('SLURM_JOB_ID','SLURM_JOB_TIME_LIMIT','PBS_JOBID','LSB_JOBID','JOB_ID') if k in os.environ},
        'external_wall_limit_detected':False,'scope':'No CPU RLIMIT and no job-scheduler variables detected here; external platform/session termination cannot be ruled out.'}
    dump(out/'MANIFEST.json',{'experiment_id':protocol['experiment_id'],'protocol':protocol,'pins':pins,
        'registered_utc':datetime.now(timezone.utc).isoformat(),'HEAD':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'environment':environment(),'limits':limits,'grid':grid(),'execution_order':ordered_grid(),
        'main_experiment':False,'statistical_J_not_selected':True,'parameter_freeze':False})
    for scale in ('S1','S2','S3'):
        p=problem(scale);old=load_legacy(SAVED/f'{scale}_B_pilot_r01/plan.json');initial=replay(p,old)
        m,v=checked(p,initial);folder=out/'baselines'/scale;folder.mkdir(parents=True)
        routes=lambda plan:{(t.vehicle_id,t.trip_no):tuple(v.stop_id for v in t.visits) for t in plan.trips}
        if routes(old)!=routes(initial):raise ValueError('INITIAL_ROUTES_CHANGED')
        dump(folder/'plan.json',asdict(initial));dump(folder/'BASELINE.json',{'metrics':recorded(m),
            'old_plan_sha256':digest(SAVED/f'{scale}_B_pilot_r01/plan.json'),'new_plan_sha256':digest(folder/'plan.json'),
            'transformation':'explicit fixed-route current duty/FCFS scheduling, not initial route regeneration',
            'same_routes_and_assignment':routes(old)==routes(initial),'old_W_not_used_for_delta':True,'initial_route_generation_s':None,
            'site_feasibility':v['stopping_site_feasibility']})
    from .report import update
    update(out)


def supervise(out,folder,jobs,kind):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    if (folder/'GROUP.json').exists():return read(folder/'GROUP.json')
    check_pins(out);protocol=read(CONFIG);safety=protocol['safety_only'];cores=cpus()
    if environment()['effective_available_bytes']<safety['min_free_GiB_before_four_branches']*1024**3:
        result={'status':'RESOURCE_UNAVAILABLE','reason':'MEASURED_AVAILABLE_MEMORY_BELOW_36_GIB','jobs':jobs}
        dump(folder/'GROUP.json',result);return result
    if shutil.disk_usage(out).free<safety['min_disk_free_GiB']*1024**3:
        result={'status':'RESOURCE_UNAVAILABLE','reason':'ACTUAL_DISK_FREE_BELOW_1_GIB','jobs':jobs}
        dump(folder/'GROUP.json',result);return result
    attempts=folder/'executions';attempts.mkdir(exist_ok=True);execution=attempts/f'{len(list(attempts.iterdir()))+1:03d}';execution.mkdir()
    start=time.perf_counter();cpu_start=time.process_time();children=[];handles=[];peak=0;child_cpu={};reason=None
    env={**os.environ,'PYTHONPATH':str(ROOT/'src'),'PYTHONDONTWRITEBYTECODE':'1',
         **{k:'1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}}
    try:
        for b,job in enumerate(jobs):
            worker_folder=folder/f'branch_{b}';worker_folder.mkdir(exist_ok=True)
            if (worker_folder/'RESULT.json').exists():
                # Completed and failed attempts are retained; never automatically
                # restart a genuine algorithm/precision failure.
                continue
            job={**job,'cpu':cores[b],'cohort':str(Path(out).resolve()),'output':str(worker_folder.resolve())}
            dump(worker_folder/'JOB.json',job);h=(execution/f'branch_{b}.log').open('x');handles.append(h)
            executable=REFERENCE_PY if kind=='reference' else sys.executable
            child=subprocess.Popen([executable,'-B',str(ROOT/'scripts/run_nkr_unlimited.py'),'_'+kind,'--job',str(worker_folder/'JOB.json')],
                cwd=ROOT,env=env,stdout=h,stderr=subprocess.STDOUT,start_new_session=True)
            children.append((child,worker_folder,b));dump(execution/f'PID_{b}.json',{'PID':child.pid,'branch':b,'cpu':cores[b]})
        with (execution/'RESOURCES.jsonl').open('x') as trace:
            while any(c.poll() is None for c,_,_ in children):
                rss=0;sample={'elapsed_s':time.perf_counter()-start,'processes':[]}
                for c,_,b in children:
                    if c.poll() is not None:continue
                    try:
                        pr=psutil.Process(c.pid);mem=pr.memory_info().rss;times=pr.cpu_times();used=times.user+times.system
                        child_cpu[str(c.pid)]=used;rss+=mem;sample['processes'].append({'PID':c.pid,'branch':b,'RSS_bytes':mem,'CPU_s':used})
                        if mem>safety['per_worker_RSS_GiB']*1024**3:reason='MEASURED_WORKER_RSS_LIMIT_8_GIB'
                    except psutil.NoSuchProcess:pass
                rss+=psutil.Process().memory_info().rss;peak=max(peak,rss);sample['tree_RSS_bytes']=rss
                trace.write(json.dumps(sample)+'\n');trace.flush()
                if shutil.disk_usage(out).free<safety['min_disk_free_GiB']*1024**3:reason='ACTUAL_DISK_EXHAUSTION_MARGIN'
                if reason:
                    for c,_,_ in children:
                        if c.poll() is None:os.killpg(c.pid,signal.SIGTERM)
                    break
                # This interval observes resources; it is never an execution deadline.
                time.sleep(1)
        for c,_,_ in children:
            c.wait()
    except BaseException:
        for c,_,_ in children:
            if c.poll() is None:os.killpg(c.pid,signal.SIGTERM)
        raise
    finally:
        for h in handles:h.close()
        dump(execution/'SEGMENT.json',{'wall_s':time.perf_counter()-start,'parent_CPU_s':time.process_time()-cpu_start,
             'sampled_tree_peak_RSS_MiB':peak/1024**2,'last_sampled_child_CPU_s':child_cpu,'reason':reason})
    branches=[]
    for b in range(4):
        path=folder/f'branch_{b}/RESULT.json'
        branches.append(read(path) if path.exists() else {'status':'PROCESS_FAILED_OR_INTERRUPTED','reason':reason or 'NO_RESULT_PROCESS_EXIT'})
    complete=all(r['status']=='COMPLETE' for r in branches)
    if not complete and reason is None:
        reason='BRANCH_FAILURE: '+'; '.join(str(r.get('reason') or r['status']) for r in branches if r['status']!='COMPLETE')
    result={'status':'COMPLETE' if complete and not reason else 'FAILED_NON_TIME','reason':reason,
        'kind':kind,'condition':{k:jobs[0].get(k) for k in ('scale','n','K','R','outer_seed')},
        'branches':[{'branch':b,**{k:r.get(k) for k in ('status','reason','after','CPU_s','wall_s','RSS_highwater_MiB','coverage')}} for b,r in enumerate(branches)],
        'parent_wall_s':sum(read(p)['wall_s'] for p in attempts.glob('*/SEGMENT.json')),
        'parent_CPU_s':sum(read(p)['parent_CPU_s'] for p in attempts.glob('*/SEGMENT.json')),
        'sampled_tree_peak_RSS_MiB':max(read(p)['sampled_tree_peak_RSS_MiB'] for p in attempts.glob('*/SEGMENT.json')),
        'CPU_s':sum(r.get('CPU_s',0.) for r in branches)+sum(read(p)['parent_CPU_s'] for p in attempts.glob('*/SEGMENT.json')),
        'external_interruption_segments':len(list(attempts.iterdir()))-1,'initial_plan_generation_s':None,'full_planning_time_s':None}
    result['CPU_measurement_scope']='parent process CPU + complete worker process CPU; no double counting of native threads'
    if any(r.get('CPU_s') is None for r in branches) or result['external_interruption_segments']:
        result['known_CPU_lower_bound_s']=result['CPU_s'];result['CPU_s']=None
        result['CPU_measurement_scope']='incomplete/interrupted worker CPU not fully available; resource samples retained, never imputed as zero'
    if complete:
        p=problem(jobs[0]['scale']);initial=load_plan(Path(out)/'baselines'/jobs[0]['scale']/'plan.json')
        candidates=[Candidate(None,checked(p,initial)[0])];plans={None:initial}
        for b in range(4):
            plan=load_plan(folder/f'branch_{b}/plan.json');m,_=checked(p,plan)
            candidates.append(Candidate(b,m));plans[b]=plan
        if kind=='reference':
            from kmd_toc.termination_v1.work import key
            bid=min(range(4),key=lambda b:(key(plans[b]),b));selected=plans[bid];result['selected_branch_id']=bid
        else:
            reference=Path(out)/'references'/f'{jobs[0]["scale"]}_seed{jobs[0]["outer_seed"]}'
            if not (reference/'plan.json').exists():
                result.update(status='HOLD_C_REFERENCE_NON_TIME',reason='NO_VALID_CURRENT_C_REFERENCE')
                selected=None
            else:
                cp=load_plan(reference/'plan.json');cm,_=checked(p,cp);winner,why=select(candidates,cm);selected=plans[winner.branch_id]
                result.update(selected_branch_id=winner.branch_id,selection=why,selected=metric_record(winner.metrics,cm),
                    initial=recorded(candidates[0].metrics),C_reference=recorded(cm),C_reference_sha256=digest(reference/'plan.json'),
                    delta_D=float(winner.metrics.D-candidates[0].metrics.D),delta_W=float(winner.metrics.W-candidates[0].metrics.W),
                    strict_dual_vs_initial=winner.metrics.D<candidates[0].metrics.D and winner.metrics.W<candidates[0].metrics.W)
                result['branch_metrics']=[{'branch':c.branch_id,**metric_record(c.metrics,cm)} for c in candidates]
        if selected is not None:dump(folder/'plan.json',asdict(selected))
    dump(folder/'GROUP.json',result);return result


def ensure_reference(out,scale,seed):
    folder=Path(out)/'references'/f'{scale}_seed{seed}'
    jobs=[{'scale':scale,'outer_seed':seed,'seed':legacy.seed_for(seed,b,0,0)%(2**31-1),'branch':b} for b in range(4)]
    return supervise(out,folder,jobs,'reference')


def run_condition(out,c,seed):
    reference=ensure_reference(out,c['scale'],seed)
    group=Path(out)/'groups'/tag(c,seed);group.mkdir(parents=True,exist_ok=True)
    if not (group/'REFERENCE_ASSIGNMENT.json').exists():
        path=Path(out)/'references'/f'{c["scale"]}_seed{seed}'/'plan.json'
        same=None
        if path.exists():
            initial=load_plan(Path(out)/'baselines'/c['scale']/'plan.json');cp=load_plan(path)
            same=initial.trips==cp.trips and initial.breaks==cp.breaks
        dump(group/'REFERENCE_ASSIGNMENT.json',{'scale':c['scale'],'outer_seed':seed,
            'C_reference_path':str(path),'C_reference_sha256':digest(path) if path.exists() else None,
            'C_status':reference['status'],'registered_before_D_branches':True,
            'one_C_for_all_four_branches':True,'initial_is_same_physical_plan_as_C':same,'statistical_pairing_not_claimed':True})
    result=supervise(out,group,[{**c,'outer_seed':seed,'branch':b} for b in range(4)],'worker')
    from .report import update
    update(out);print(tag(c,seed),result['status'],result.get('delta_D'),result.get('delta_W'),flush=True)
    return result


def confirmation_conditions(out):
    result=[]
    for scale,V in [('S1',10),('S2',20),('S3',40)]:
        fixed=[dict(scale=scale,n=n,K=V//2,R=5) for n in (10,12)]
        candidates=[]
        for c in grid():
            p=Path(out)/'groups'/tag(c)/'GROUP.json'
            if c['scale']!=scale or not p.exists():continue
            r=read(p)
            if r['status']=='COMPLETE' and r.get('selected',{}).get('I_dual') is not None:
                candidates.append(((-r['selected']['I_dual'],r['parent_wall_s'],c['n'],c['K'],c['R']),c))
        if candidates:
            best=min(candidates,key=lambda x:x[0])[1]
            if best not in fixed:fixed.append(best)
        result.extend(fixed)
    from .report import proposal
    rows=[]
    for c in grid():
        path=Path(out)/'groups'/tag(c)/'GROUP.json'
        if path.exists():rows.append({**c,**read(path)})
    common=proposal(rows)
    if common.get('common_candidate'):
        n,coefficient,R=common['common_candidate']
        for scale,V in [('S1',10),('S2',20),('S3',40)]:
            c=dict(scale=scale,n=n,K=int(coefficient*V),R=R)
            if c not in result:result.append(c)
    return result


def run(out):
    out=Path(out).resolve();check_pins(out)
    with (out/'CONTROLLER.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        dump(out/'CONTROLLER.json',{'PID':os.getpid(),'started_utc':datetime.now(timezone.utc).isoformat(),
            'command':'run --resume','time_caps':None,'status':'RUNNING'})
        for c in ordered_grid():run_condition(out,c,9201)
        confirmations=confirmation_conditions(out)
        dump(out/'CONFIRMATION_SELECTION.json',{'rule':read(CONFIG)['confirmation_rule'],'conditions':confirmations,
             'seeds':read(CONFIG)['confirmation_outer_seeds'],'screen_all54_terminal_before_selection':True})
        for seed in read(CONFIG)['confirmation_outer_seeds']:
            for c in confirmations:run_condition(out,c,seed)
        from .report import update
        update(out)
        dump(out/'CONTROLLER.json',{'PID':os.getpid(),'ended_utc':datetime.now(timezone.utc).isoformat(),'status':'FINISHED',
             'time_caps':None,'parameter_freeze':False,'main_experiment':False})
