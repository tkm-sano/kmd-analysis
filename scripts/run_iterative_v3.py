#!/usr/bin/env python3
"""Registered adaptive common-initial planner: register/run/resume/aggregate/readiness."""
import argparse,os,sys,signal,time,resource,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('register','run','resume','aggregate','readiness','_branch','_classical'))
    p.add_argument('--output',type=Path);p.add_argument('--config',type=Path);p.add_argument('--job',type=Path)
    p.add_argument('--diagnostic-input',type=Path)
    args=p.parse_args()
    from kmd_toc.iterative_v3.io import read,dump,atomic,load_problem,read_initial,verify_pins
    if args.action=='_classical':
        from kmd_toc.iterative_v3.experiment import classical_helper
        return 0 if classical_helper(read(args.job)) else 2
    if args.action=='_branch':
        job=read(args.job);out=Path(job['output']);out.mkdir(parents=True,exist_ok=True)
        attempt=out/f'ATTEMPT_{len(list(out.glob("ATTEMPT_*.json")))+1:03d}.json';begin=time.perf_counter();cpu=time.process_time();status='FAILED'
        def stop(sig,frame):raise KeyboardInterrupt('explicit process termination')
        signal.signal(signal.SIGTERM,stop)
        try:
            os.sched_setaffinity(0,{job['cpu']});verify_pins(job['code_hashes'])
            problem=load_problem(job['input'],job['rest_options']);initial=read_initial(job['initial_directory'])
            from kmd_toc.iterative_v3.search import run
            r=run(problem,initial,out,job['condition'],job['settings'],job['seed'],job['branch']);status=r['status']
            return 0 if r['status']=='COMPLETE' else 2
        except BaseException as e:
            status='INTERRUPTED' if isinstance(e,KeyboardInterrupt) else 'FAILED'
            dump(out/f'{status}_{len(list(out.glob(status+"_*.json")))+1:03d}.json',dict(error=repr(e),traceback=traceback.format_exc()))
            return 130 if status=='INTERRUPTED' else 2
        finally:
            dump(attempt,dict(status=status,PID=os.getpid(),CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-begin,
                affinity=sorted(os.sched_getaffinity(0)),native_threads=1,python=sys.version,executable=sys.executable,
                RSS_highwater_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024))
    if not args.output:p.error('--output is required')
    from kmd_toc.iterative_v3.experiment import register,execute
    if args.action=='register':
        if not args.config:p.error('--config is required')
        config=read(args.config)
        diagnostic={s:args.diagnostic_input for s in config['scales']} if args.diagnostic_input else None
        register(args.config,args.output,diagnostic_inputs=diagnostic);print('REGISTERED',args.output);return 0
    if args.action in ('run','resume'):
        result=execute(args.output);return 0 if all(r['status']=='COMPLETE' for r in result) else 2
    from kmd_toc.iterative_v3.analysis import aggregate,readiness
    r=aggregate(args.output) if args.action=='aggregate' else readiness(args.output)
    print(r);return 0
if __name__=='__main__':raise SystemExit(main())
