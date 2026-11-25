#!/usr/bin/env python3
"""Bounded full S1-S3 checks of a calibration-locked A-area candidate."""
import argparse
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))


def main():
    if '--historical-reproduction' not in sys.argv:
        raise SystemExit('HISTORICAL_ENTRYPOINT: legacy A plans require --historical-reproduction; current A is an external administrative reference')
    sys.argv.remove('--historical-reproduction')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',required=True)
    parser.add_argument('--model-sha256',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--scenarios',nargs='+',choices=['S1','S2','S3'],default=['S1','S2','S3'])
    parser.add_argument('--diagnostic-best-area',action='store_true',help='Functional diagnostic of the best calibrated area candidate; never changes selected model')
    parser.add_argument('--repetitions',type=int,choices=[1,2],default=2)
    parser.add_argument('--worker',choices=['S1','S2','S3'],help=argparse.SUPPRESS)
    parser.add_argument('--cpus',type=int,nargs=4,help=argparse.SUPPRESS)
    args = parser.parse_args()
    for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
        os.environ[key] = '1'
    start = time.perf_counter()
    if args.worker:
        if Path(args.output).exists():
            return 2
        try:
            if not args.cpus or len(set(args.cpus))!=4 or not set(args.cpus)<=os.sched_getaffinity(0):
                raise ValueError('AREA_CPU_ALLOCATION')
            os.sched_setaffinity(0,{args.cpus[0]})
            from kmd_toc.dwt.setup import preload_dependencies
            preload_dependencies()
            from kmd_toc.baseline_a.area_program import execute
            setup = {'dependency_setup_wall_s':time.perf_counter()-start,'allocated_cpu_ids':args.cpus,
                'active_cpu_ids':sorted(os.sched_getaffinity(0)),'python':sys.version,'executable':sys.executable,
                'platform':platform.platform(),'native_threads_environment':{k:os.environ[k] for k in
                ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']}}
            row = execute(args.worker,args.model,args.model_sha256,args.output,setup,args.diagnostic_best_area)
            return 0 if row['status']=='VALIDATED' else 1
        except Exception as error:
            out = Path(args.output)
            out.mkdir(parents=True,exist_ok=True)
            (out/'PROCESS_FAILURE.json').write_text(json.dumps({'status':'PROCESS_FAILURE','type':type(error).__name__,
                'message':str(error)},indent=2)+'\n')
            return 1
    from kmd_toc.baseline_a.area_program import load_model,dump
    from kmd_toc.baseline_a.area_study import settings
    from kmd_toc.baseline_a.sequence_validation import digest
    from kmd_toc.dwt.parallel import cpu_profile
    config = settings()
    model_path = Path(args.model).resolve()
    model = load_model(model_path,args.model_sha256)
    if args.repetitions!=config['limits']['S1_S3_repetitions'] and not args.diagnostic_best_area:
        raise ValueError('SELECTED_MODEL_REQUIRES_REGISTERED_TWO_REPETITIONS')
    cpus = cpu_profile({'threads':4,'cpu_parallel':{'workers':4,'native_threads_per_branch':1,
                       'cpu_ids':None,'coordinator_reserve_fraction':.2}})['cpu_ids']
    out = Path(args.output).resolve()
    out.mkdir(parents=True,exist_ok=False)
    sources = sorted((ROOT/'src/kmd_toc').rglob('*.py'))+[Path(__file__).resolve(),ROOT/'configs/toc_delivery/a_area_v3.json']
    code_hashes = {str(p.relative_to(ROOT)):digest(p) for p in sources}
    import tarfile
    with tarfile.open(out/'SOURCE_SNAPSHOT.tar.gz','x:gz') as archive:
        for p in sources:
            archive.add(p,arcname=str(p.relative_to(ROOT)))
        archive.add(model_path,arcname='SELECTED_MODEL.json')
    dump(out/'REGISTRATION.json',{'config':config,'model_sha256':args.model_sha256,'model':model,
        'cpu_allocation':cpus,'source_hashes':code_hashes,'scenarios':args.scenarios,'main_experiment':False,
        'diagnostic_best_area':args.diagnostic_best_area,'repetitions':args.repetitions})
    with (out/'environment.txt').open('x') as stream:
        subprocess.run([sys.executable,'-m','pip','freeze'],stdout=stream,stderr=subprocess.STDOUT,check=True)
    rows = []
    for case in dict.fromkeys(args.scenarios):
        for repeat in range(args.repetitions):
            target = out/f'{case}-repeat{repeat+1:02}'
            before = time.perf_counter()
            command = [sys.executable,str(Path(__file__).resolve()),'--historical-reproduction','--worker',case,'--model',str(model_path),
                '--model-sha256',args.model_sha256,'--output',str(target),'--cpus',*map(str,cpus)]
            if args.diagnostic_best_area:
                command += ['--diagnostic-best-area']
            try:
                with (out/f'{target.name}.log').open('x') as log:
                    process = subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,
                        timeout=config['limits']['process_limit_s'])
                path = target/'metrics.json'
                row = json.loads(path.read_text()) if path.exists() else {'status':'PROCESS_FAILURE'}
                if row['status']=='VALIDATED':
                    complete = process.returncode==0 and all((target/name).is_file() for name in
                        ['plan.json','trips.csv','metrics.json','validation.json','manifest.json','EXPORT_TIMING.json','OUTPUT_HASHES.json'])
                    if complete:
                        hashes = json.loads((target/'OUTPUT_HASHES.json').read_text())
                        complete = all(digest(target/name)==h for name,h in hashes.items())
                    if not complete:
                        row.update(status='OUTPUT_FAILURE',D_km=None,W_min=None,T_program_s=None)
                row['returncode'] = process.returncode
            except subprocess.TimeoutExpired:
                row = {'status':'PROCESS_TIMEOUT','D_km':None,'W_min':None,'T_program_s':None}
            row.update(scenario_id=case,repetition=repeat+1,process_wall_including_setup_export_s=time.perf_counter()-before)
            dump(out/f'{target.name}.PROCESS.json',{k:v for k,v in row.items() if k not in ['validation','second_validation']})
            rows.append(row)
            print(json.dumps({k:row.get(k) for k in ['scenario_id','repetition','status','D_km','W_min','T_program_s']}),flush=True)
    summary = []
    for case in dict.fromkeys(args.scenarios):
        own = [r for r in rows if r['scenario_id']==case]
        valid = [r for r in own if r['status']=='VALIDATED']
        hashes = [digest(out/f'{case}-repeat{r["repetition"]:02}'/'plan.json') for r in valid]
        summary.append({'scenario_id':case,'attempts':len(own),'validated':len(valid),
            'D_km':valid[0]['D_km'] if valid else None,'W_min':valid[0]['W_min'] if valid else None,
            'T_program_s_all':[r.get('T_program_s') for r in own],
            'T_program_median_descriptive_s':statistics.median(r['T_program_s'] for r in valid) if valid else None,
            'same_plan_bytes':len(set(hashes))==1 if len(valid)==len(own) and len(valid)>=2 else None,
            'main_experiment_eligible':False,'formal_T_reference':None,'J':None})
    dump(out/'SUMMARY.json',summary)
    stable = all(digest(ROOT/p)==h for p,h in code_hashes.items())
    dump(out/'SOURCE_STABILITY.json',{'unchanged':stable})
    dump(out/'OUTPUT_HASHES.json',{str(p.relative_to(out)):digest(p) for p in out.rglob('*') if p.is_file()})
    return 0 if stable and all(r['validated']==r['attempts'] and (r['attempts']==1 or r['same_plan_bytes']) for r in summary) else 1


if __name__=='__main__':
    sys.exit(main())
