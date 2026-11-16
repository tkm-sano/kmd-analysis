"""Observational pilot logs. No candidate is promoted or returned early."""
import json
import math
import os
from pathlib import Path
import time


def emit(directory, value):
    with (Path(directory) / 'design_trace.jsonl').open('a') as stream:
        stream.write(json.dumps({'pid': os.getpid(), 'perf_counter': time.perf_counter(), **value}) + '\n')


def install(directory, start):
    from kmd_toc.dwt import methods
    from kmd_toc.column_generation.aoa import PricingAOA
    # Installation is local to a fresh internal branch (also works with spawn).
    def observe(function, label):
        def wrapped(*args, **kwargs):
            before = time.perf_counter()
            emit(directory, {'event': label, 'kind': 'start', 'elapsed_s': before-start})
            try:
                result = function(*args, **kwargs)
                extra = {}
                if label == 'verify_candidate' and result:
                    plan = args[1]
                    extra = {'D': math.fsum(t.distance_m for t in plan.trips)/1000,
                             'W': sum(t.waiting_s for t in plan.trips)/60}
                emit(directory, {'event': label, 'kind': 'end', 'elapsed_s': time.perf_counter()-start,
                                 'wall_s': time.perf_counter()-before, **extra})
                return result
            except BaseException as error:
                emit(directory, {'event': label, 'kind': 'error', 'type': type(error).__name__,
                                 'elapsed_s': time.perf_counter()-start, 'wall_s': time.perf_counter()-before})
                raise
        return wrapped
    for name in ('verify_candidate', 'directed_cw', 'routing_pool', 'complete_routes', 'hybrid'):
        setattr(methods, name, observe(getattr(methods, name), name))
    original = PricingAOA.run
    def quantum(engine, *args, **kwargs):
        c = engine.config
        emit(directory, {'event': 'quantum_call', 'kind': 'start', 'qubits': engine.q,
                         'settings': {k: getattr(c,k) for k in ('slots','p','max_evaluations','restarts','train_shots','final_shots')}})
        result = original(engine, *args, **kwargs)
        emit(directory, {'event': 'quantum_call', 'kind': 'end',
                         'training_shots': sum(h['nfev'] for h in result['history'])*c.train_shots,
                         'final_shots': result['measured_shots']})
        return result
    PricingAOA.run = quantum


def tree_sample(leader):
    """RSS sum is conservative with shared pages; CPU samples are lower bounds."""
    pending=[leader];seen=set();observations=[]
    while pending:
        pid=pending.pop()
        if pid in seen: continue
        seen.add(pid)
        try:
            base=Path(f'/proc/{pid}')
            pending.extend(map(int,(base/f'task/{pid}/children').read_text().split()))
            stat=(base/'stat').read_text().rsplit(')',1)[1].split()
            status=dict(s.split(':',1) for s in (base/'status').read_text().splitlines() if ':' in s)
            observations.append({'pid':pid,'rss_KiB':int(status.get('VmRSS','0 kB').split()[0]),
                'cpu_s':(int(stat[11])+int(stat[12]))/os.sysconf('SC_CLK_TCK'),
                'affinity':sorted(os.sched_getaffinity(pid)), 'threads':int(status.get('Threads','0'))})
        except (FileNotFoundError,ProcessLookupError): pass
    return {'perf_counter':time.perf_counter(),'processes':observations,
            'tree_rss_sum_KiB':sum(p['rss_KiB'] for p in observations)}
