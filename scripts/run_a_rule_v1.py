#!/usr/bin/env python3
"""Registered, bounded A_rule_v1 functional checks. Never runs B/C/D."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1048576),b''):
            h.update(chunk)
    return h.hexdigest()


def dump(path,value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write('\n')


def worker(args):
    setup_start = time.perf_counter()
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        os.environ[name] = '1'
    from kmd_toc.baseline_a.rule_v1 import generate
    from kmd_toc.baseline_a.rule_validation import audit_rule
    from kmd_toc.baseline_a.rule_inputs import load_input
    from kmd_toc.common.validation import validate_plan
    out = Path(args.worker)
    manifest = json.loads((out/'manifest.json').read_text())
    cpus = manifest['allocated_cpu_ids']
    if len(cpus)!=4 or not set(cpus)<=os.sched_getaffinity(0):
        raise ValueError('CPU_ALLOCATION_CHANGED')
    available = sorted(os.sched_getaffinity(0))
    os.sched_setaffinity(0,{cpus[0]})
    limits = manifest['limits']
    resource.setrlimit(resource.RLIMIT_AS,(limits['address_space_MiB']*1048576,)*2)
    setup_s = time.perf_counter()-setup_start
    row = {k:manifest.get(k) for k in ('method','method_version','scale','scenario_id','demand_seed',
        'solver_seed','repeat_id','run_id','config_hash','code_version','resource_contract','berths')}
    row.update(status='ERROR',D=None,W=None,W_first=None,W_reload=None,T_program=None,T_input=None,
        T_planning=None,T_validation=None,T_attempt=None,T_A_human_reference=None,J=None,
        formal_T_A_ref=None,input_hash=None,error=None,main_experiment=False)
    plan = p = diagnostic = common = independent = None
    start = time.perf_counter()
    cpu_start = time.process_time()
    input_end = planning_end = None
    stage = 'INPUT'
    def timeout(*_):
        raise TimeoutError('PROGRAM_WALL_LIMIT')
    signal.signal(signal.SIGALRM,timeout)
    signal.setitimer(signal.ITIMER_REAL,limits['program_wall_s'])
    try:
        if digest(args.config)!=manifest['config_hash']:
            raise ValueError('CONFIG_HASH_MISMATCH')
        config = json.loads(Path(args.config).read_text())
        for source,expected in manifest['source_hashes'].items():
            if digest(ROOT/source)!=expected:
                raise ValueError('SOURCE_HASH_MISMATCH:'+source)
        p = load_input(config,manifest['scale'],manifest['berths'])
        row['input_hash'] = p.fingerprint
        row['OD_hash'] = p.od.fingerprint
        input_end = time.perf_counter()
        stage = 'PLANNING'
        plan,diagnostic = generate(p,deadline=start+limits['planning_absolute_wall_s'],
                                  max_evaluations=limits['candidate_evaluations'])
        planning_end = time.perf_counter()
        stage = 'VALIDATION'
        common = validate_plan(p,plan).as_dict()
        independent = audit_rule(p,plan)
        agrees = (common['feasible'] and independent['feasible'] and
            abs(common['D_km']-float(independent['D_km']))<=config['algorithm']['distance_tolerance_km'] and
            common['W_min']==float(independent['W_min']) and
            common['W1_min']==independent['W_first'] and common['W2_min']==independent['W_reload'] and
            tuple(independent['L_s'])==diagnostic['state']['L_s'] and
            tuple(independent['final_return_s'])==diagnostic['state']['final_return_s'] and
            (independent['O_s'],independent['H_s2'])==diagnostic['state']['objective'])
        limited = diagnostic['stop_reason'] in ('PLANNING_TIME_LIMIT','EVALUATION_LIMIT')
        row['status'] = ('VALIDATED_LIMIT' if limited else 'VALIDATED') if agrees else (
            ('NO_FEASIBLE_PLAN_LIMIT' if limited else 'NO_FEASIBLE_PLAN')
            if diagnostic['state']['objective'][0]>0 else 'REJECTED_PLAN')
        if agrees:
            row.update(D=common['D_km'],W=common['W_min'],W_first=common['W1_min'],W_reload=common['W2_min'])
        else:
            row['error'] = {'stage':stage,'reason':'FINAL_VALIDATION_REJECTED',
                            'not_a_proof_of_problem_infeasibility':True}
    except Exception as error:
        row.update(status='TIME_LIMIT_NO_VALIDATED_PLAN' if isinstance(error,TimeoutError) else
                   ('INPUT_INVALID' if stage=='INPUT' else 'ERROR'),
                   error={'stage':stage,'type':type(error).__name__,'message':str(error)})
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
    elapsed = time.perf_counter()-start
    row.update(T_attempt=elapsed,T_input=input_end-start if input_end else elapsed,
        T_planning=planning_end-input_end if planning_end else (elapsed-(input_end-start) if input_end and stage=='PLANNING' else None),
        T_validation=elapsed-(planning_end-start) if planning_end else None,
        pid=os.getpid(),available_cpu_ids=available,allocated_cpu_ids=cpus,
        cpu_affinity=sorted(os.sched_getaffinity(0)),native_threads=1,
        native_threads_environment={k:os.environ[k] for k in
            ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')},
        max_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        cpu_time_s=time.process_time()-cpu_start,dependency_setup_s=setup_s,
        T_scope=manifest['T_scope'])
    if row['status'].startswith('VALIDATED'):
        row['T_program'] = elapsed
        row.update(active_vehicles=len({t.vehicle_id for t in plan.trips}),nonempty_trips=len(plan.trips),
                   final_return_s=independent['final_return_s'],L_s=independent['L_s'],O_s=independent['O_s'])
    export = time.perf_counter()
    if plan:
        dump(out/('plan.json' if row['T_program'] is not None else 'rejected_plan.json'),asdict(plan))
        dump(out/'events.json',[{k:getattr(t,k) for k in ('vehicle_id','trip_no','berth_id','ready_s',
            'load_start_s','load_end_s','departure_s','return_s','waiting_s','distance_m')} for t in plan.trips])
    if diagnostic:
        dump(out/'search.json',diagnostic)
    dump(out/'validation.json',{'common':common,'independent':independent,'error':row['error']})
    dump(out/'metrics.json',row)
    dump(out/'EXPORT_TIMING.json',{'output_wall_s_through_metrics':time.perf_counter()-export})
    dump(out/'OUTPUT_HASHES.json',{p.name:digest(p) for p in out.iterdir() if p.is_file()})
    return 0 if row['T_program'] is not None else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',default=str(ROOT/'configs/toc_delivery/a_rule_v1_20261115.json'))
    parser.add_argument('--output',required=True)
    parser.add_argument('--worker',help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        return worker(args)
    config_path = Path(args.config).resolve()
    config = json.loads(config_path.read_text())
    # Pure CPU topology discovery; no solvers, demand or planning are executed.
    from kmd_toc.dwt.parallel import cpu_profile
    cpus = cpu_profile({'threads':4,'cpu_parallel':{'workers':4,'native_threads_per_branch':1,
        'cpu_ids':None,'coordinator_reserve_fraction':.2}})['cpu_ids']
    out = Path(args.output).resolve()
    out.mkdir(parents=True,exist_ok=False)
    sources = sorted((ROOT/'src/kmd_toc').rglob('*.py'))+[Path(__file__).resolve(),config_path,
        ROOT/'configs/toc_delivery/common_conditions_v1_1.json',ROOT/'configs/toc_delivery/frozen_demand_v1.json']
    hashes = {str(p.relative_to(ROOT)):digest(p) for p in sources}
    code_version = {'HEAD':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                    'source_hashes':hashes,'dirty_workspace':True}
    import tarfile
    with tarfile.open(out/'SOURCE_SNAPSHOT.tar.gz','x:gz') as archive:
        for source in sources:
            archive.add(source,arcname=str(source.relative_to(ROOT)))
    env = {'python':sys.version,'executable':sys.executable,'platform':platform.platform(),
           'allocated_cpu_ids':cpus,'cpu_count':os.cpu_count(),'cache_policy':config['resource_contract']['cache_policy']}
    env['cpu_model'] = next((line.split(':',1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines()
                            if line.startswith('model name')),None)
    env['host_meminfo'] = [line for line in Path('/proc/meminfo').read_text().splitlines()
                           if line.startswith(('MemTotal:','MemAvailable:','SwapTotal:'))]
    dump(out/'REGISTRATION.json',{'timestamp_utc':datetime.now(timezone.utc).isoformat(),'config':config,
        'config_hash':digest(config_path),'code_version':code_version,'environment':env,
        'formal_experiment':False,'limits':config['limits']})
    with (out/'environment.txt').open('x') as stream:
        subprocess.run([sys.executable,'-m','pip','freeze'],stdout=stream,stderr=subprocess.STDOUT,check=True)
    rows = []
    for condition in config['run_contract']['main']+config['run_contract']['sensitivity']:
        scale = condition['scale']
        berths = condition.get('berths',config['inputs']['scenarios'][scale]['counts'][2])
        run_id = f'{out.name}_{scale}_b{berths}_r{condition["repeat_id"]}'
        target = out/run_id
        target.mkdir(exist_ok=False)
        manifest = {'method':'A','method_version':config['method_version'],'scale':scale,
            'scenario_id':'ota-toc-frozen-demand-v1:'+scale,'demand_seed':None,'solver_seed':None,
            'repeat_id':condition['repeat_id'],'run_id':run_id,'berths':berths,
            'config_hash':digest(config_path),'code_version':code_version,'source_hashes':hashes,
            'resource_contract':config['resource_contract'],'allocated_cpu_ids':cpus,
            'limits':config['limits'],'T_scope':config['T_scope'],
            'input_files_sha256':config['inputs']['scenarios'][scale]['files'],
            'demand_seed_note':'frozen artifact is the scenario identity; no new sampling; see original frozen manifest'}
        dump(target/'manifest.json',manifest)
        command = [sys.executable,'-B',str(Path(__file__).resolve()),'--config',str(config_path),
                   '--output',str(out),'--worker',str(target)]
        process_start = time.perf_counter()
        try:
            with (target/'worker.log').open('x') as stream:
                proc = subprocess.run(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,
                                      timeout=config['limits']['process_wall_s'])
            path = target/'metrics.json'
            row = json.loads(path.read_text()) if path.exists() else {
                **{k:manifest.get(k) for k in ('method','method_version','scale','scenario_id','demand_seed',
                    'solver_seed','repeat_id','run_id','config_hash','code_version','resource_contract')},
                'status':'PROCESS_FAILURE','D':None,'W':None,'W_first':None,'W_reload':None,
                'T_program':None,'T_input':None,'T_planning':None,'T_validation':None,'input_hash':None,
                'error':{'stage':'PROCESS_SETUP_OR_TERMINATION','reason':'metrics not produced; see worker.log'},
                'T_attempt':time.perf_counter()-process_start}
            row['returncode'] = proc.returncode
            if row.get('T_program') is not None:
                footer = target/'OUTPUT_HASHES.json'
                intact = footer.exists() and all(digest(target/name)==h for name,h in
                    json.loads(footer.read_text()).items())
                if proc.returncode!=0 or not intact:
                    row.update(status='OUTPUT_FAILURE',D=None,W=None,W_first=None,W_reload=None,T_program=None,
                        error={'stage':'OUTPUT','reason':'nonzero return code or failed output hashes'})
        except subprocess.TimeoutExpired:
            row = {**{k:manifest.get(k) for k in ('method','method_version','scale','scenario_id','demand_seed',
                    'solver_seed','repeat_id','run_id','config_hash','code_version','resource_contract')},
                   'status':'PROCESS_TIMEOUT','D':None,'W':None,'W_first':None,'W_reload':None,
                   'T_program':None,'T_input':None,'T_planning':None,'T_validation':None,'input_hash':None,
                   'error':{'stage':'PROCESS','reason':'registered hard process wall limit'},
                   'T_attempt':time.perf_counter()-process_start}
        row.update(run_id=run_id,scale=scale,berths=berths,repeat_id=condition['repeat_id'],
                   process_wall_including_setup_export_s=time.perf_counter()-process_start)
        if (target/'plan.json').exists():
            row['plan_sha256'] = digest(target/'plan.json')
        dump(target/'PROCESS.json',row)
        rows.append(row)
        print(json.dumps({k:row.get(k) for k in ('run_id','status','D','W','W_first','W_reload','T_program')},ensure_ascii=False),flush=True)
    dump(out/'SUMMARY.json',rows)
    dump(out/'SOURCE_STABILITY.json',{'unchanged':all(digest(ROOT/p)==h for p,h in hashes.items())})
    dump(out/'OUTPUT_HASHES.json',{str(p.relative_to(out)):digest(p) for p in out.rglob('*') if p.is_file()})
    return 0 if all(r.get('T_program') is not None for r in rows) else 1


if __name__=='__main__':
    sys.exit(main())
