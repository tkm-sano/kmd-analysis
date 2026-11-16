"""Fresh child: frozen A directly; existing four-branch B/C/D unchanged."""
import json
import os
from pathlib import Path
import resource
import sys
import time

from .contract import ROOT, atomic, check_freeze, digest, read


def trace(out,label,**extra):
    with (Path(out)/f'path_{os.getpid()}.jsonl').open('a') as stream:
        stream.write(json.dumps({'event':label,'pid':os.getpid(),'perf_counter':time.perf_counter(),
            'affinity':sorted(os.sched_getaffinity(0)),**extra})+'\n')


def instrument_bcd(out):
    """Transparent call evidence at interfaces; inputs/returns are not changed."""
    from kmd_toc.dwt import methods
    from kmd_toc.column_generation.aoa import PricingAOA
    def wrap(function,label):
        def observed(*args,**kwargs):
            trace(out,label)
            return function(*args,**kwargs)
        return observed
    for name,label in [('directed_cw','directed_CW'),('routing_pool','OR_Routing'),
                       ('complete_routes','shared_CP_completion'),('hybrid','Huang_hybrid')]:
        setattr(methods,name,wrap(getattr(methods,name),label))
    PricingAOA.run=wrap(PricingAOA.run,'AOA_statevector_run')


def main():
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        os.environ[key]='1'
    out=Path(sys.argv[1]);job=read(out/'job.json');manifest=job['manifest'];run=job['run'];case=job['case']
    cpus=manifest['cpu_profile']['cpu_ids']
    method=run['method']
    os.sched_setaffinity(0,{cpus[0]} if method=='A' else set(cpus))
    setup=time.perf_counter()
    check_freeze()
    from dataclasses import asdict
    from kmd_toc.common.models import load_problem
    from kmd_toc.common.validation import validate_plan
    from kmd_toc.baseline_a.program_validation import audit_plan
    from kmd_toc.dwt.parallel import _plan
    if method=='A':
        import signal
        from kmd_toc.baseline_a.rule_v1 import generate
        from kmd_toc.baseline_a.rule_validation import audit_rule
        cfg=manifest['A_config']
        resource.setrlimit(resource.RLIMIT_AS,(cfg['limits']['address_space_MiB']*1048576,)*2)
        setup_s=time.perf_counter()-setup
        native_start=time.perf_counter()
        def native_timeout(*_):raise TimeoutError('FROZEN_A_NATIVE_180S_LIMIT')
        signal.signal(signal.SIGALRM,native_timeout)
        signal.setitimer(signal.ITIMER_REAL,cfg['limits']['program_wall_s'])
        p=load_problem(case['input']['directory'])
        native_input=time.perf_counter()
        trace(out,'frozen_A_rule_v1.generate')
        plan,diagnostic=generate(p,deadline=native_start+cfg['limits']['planning_absolute_wall_s'],
                                 max_evaluations=cfg['limits']['candidate_evaluations'])
        native_planning=time.perf_counter()
        common,independent=validate_plan(p,plan),audit_plan(p,plan)
        specific=audit_rule(p,plan)
        native={'status':'VALIDATED' if common.feasible and independent['feasible'] and specific['feasible'] else 'REJECTED_PLAN',
            'T_native_program':time.perf_counter()-native_start,'T_native_input':native_input-native_start,
            'T_native_planning':native_planning-native_input,'dependency_setup_s':setup_s,
            'stop_reason':diagnostic['stop_reason'],'rule_validation':specific,'search':diagnostic,
            'A_completion_called':False}
        signal.setitimer(signal.ITIMER_REAL,0)
        # Frozen A's existing 180s native cap is retained inside the new outer cap.
        if native['T_native_program']>cfg['limits']['program_wall_s']:
            native.update(status='NATIVE_TIME_LIMIT',native_cap_exceeded=True)
        atomic(out/'native_result.json',native)
    else:
        from kmd_toc.dwt.setup import preload_dependencies
        preload_dependencies(manifest['BCD_config'])
        instrument_bcd(out)
        from kmd_toc.dwt.parallel import execute_parallel
        # Reserve 10% of remaining outer wall for transfer and final parent checks.
        remaining=job['deadline_perf_counter']-time.perf_counter()
        if remaining<=0:raise TimeoutError('NO_REMAINING_COMMON_BUDGET')
        native_seconds=min(remaining*.9,case['case_parameters'].get('BCD_native_cap_s') or remaining*.9)
        trace(out,'existing_dwt.execute_parallel',method=method)
        spec={'trial_id':run['run_id'],'scenario_id':case['scenario_id'],'instance_id':case['case_id'],
            'method':method,'repetition_id':run['repeat_id'],'phase':manifest['phase'],
            'epsilon_W_min':case['case_parameters']['BCD_epsilon_W_min'],'tau_s':native_seconds,
            'input_dir':case['input']['directory'],'registered_input_hash':case['input']['input_hash'],
            'registered_OD_hash':case['input']['OD_hash'],'config':manifest['BCD_config'],
            'config_sha256':manifest['BCD_config_hash'],'execution_cpu_profile':manifest['cpu_profile'],
            'design_telemetry':bool(manifest.get('design_extension')),
            'seeds':{'solver_seed':run['solver_seed'],'quantum_seed':run['quantum_seed'],'validation_seed':None}}
        native=execute_parallel(spec,out/'native',allow_import_only_fork=True)
        atomic(out/'native_result.json',native)
        if not native.get('plan'):
            atomic(out/'message.json',{'kind':'no_plan','native_status':native['status'],
                'worker_finished_at':time.perf_counter()})
            return
        plan=_plan(native['plan'])
    # Same Plan schema: this preserves original A bytes, IDs, ordering, all clocks.
    atomic(out/'candidate_plan.json',asdict(plan))
    atomic(out/'message.json',{'kind':'candidate','sha256':digest(out/'candidate_plan.json'),
        'worker_pid':os.getpid(),'observed_threads':len(list(Path('/proc/self/task').iterdir())),
        'worker_finished_at':time.perf_counter(),'native_status':native['status'],
        'native_stop_reason':native.get('stop_reason'),
        'cpu_time_s':time.process_time(),'max_rss_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'native_threads':{k:os.environ[k] for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}})


if __name__=='__main__':
    try:
        main()
    except BaseException as error:
        import traceback
        traceback.print_exc()
        out=Path(sys.argv[1])
        atomic(out/'worker_error.json',{'type':type(error).__name__,'message':str(error),
                                      'pid':os.getpid(),'perf_counter':time.perf_counter()})
        raise
