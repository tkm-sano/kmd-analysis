"""Process-local pass-through instrumentation; never changes candidates or RNG."""
from contextlib import contextmanager
from collections import defaultdict
from pathlib import Path
import time,resource
from kmd_toc.iterative_v3.io import dump

@contextmanager
def instrument(directory):
    import kmd_toc.iterative_v3.search as search
    import kmd_toc.iterative_v3.quantum as quantum
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    attempt=len(list(directory.glob('PHASES_ATTEMPT_*.json')))+1
    stats=defaultdict(lambda:dict(calls=0,wall_s=0.,CPU_s=0.));patches=[];shots=[];requested=[];unknown=[]
    def add(name,wall,cpu):
        stats[name]['calls']+=1;stats[name]['wall_s']+=wall;stats[name]['CPU_s']+=cpu
    def timed(name,fn):
        def call(*args,**kwargs):
            t=time.perf_counter();c=time.process_time()
            try:return fn(*args,**kwargs)
            finally:add(name,time.perf_counter()-t,time.process_time()-c)
        return call
    def patch(obj,name,fn):patches.append((obj,name,getattr(obj,name)));setattr(obj,name,fn)
    for name,phase in [('generate','classical_reallocation'),('build','classical_order_problem_build'),('evaluate','full_physical_completion_validation'),('classical','classical_order_solver'),('quantum','hybrid_local_call_total')]:
        patch(search,name,timed(phase,getattr(search,name)))
    patch(quantum,'evolve',timed('MPS_evolution_and_numeric_checks',quantum.evolve))
    patch(quantum,'sdk_circuit',timed('classical_SDK_circuit_construction',quantum.sdk_circuit))
    patch(quantum,'decode',timed('classical_unique_bitstring_decode',quantum.decode))
    backend=quantum.backend_modules
    def modules():
        q,s=backend();sample=s.sample
        def sampling(*args,**kwargs):
            n=int(args[1]);requested.append(n)
            try:result=timed('MPS_classical_sampling',sample)(*args,**kwargs)
            except BaseException:unknown.append(n);raise
            shots.append(n);return result
        s.sample=sampling;return q,s
    patch(quantum,'backend_modules',modules)
    minimize=quantum.minimize
    def optimization(fn,*args,**kwargs):
        calls=[0.,0.]
        def callback(*a,**k):
            t=time.perf_counter();c=time.process_time()
            try:return fn(*a,**k)
            finally:
                wall,cp=time.perf_counter()-t,time.process_time()-c;calls[0]+=wall;calls[1]+=cp
                add('classical_objective_callback_inclusive',wall,cp)
        t=time.perf_counter();c=time.process_time()
        try:return minimize(callback,*args,**kwargs)
        finally:add('COBYLA_controller_excluding_callbacks',time.perf_counter()-t-calls[0],time.process_time()-c-calls[1])
    patch(quantum,'minimize',optimization)
    try:yield stats
    finally:
        for obj,name,old in reversed(patches):setattr(obj,name,old)
        dump(directory/f'PHASES_ATTEMPT_{attempt:03d}.json',dict(phases=dict(stats),
            virtual_shots_this_attempt=None if unknown else sum(shots),known_completed_virtual_shots_lower_bound=sum(shots),
            failed_sampler_shots_unknown=bool(unknown),requested_sample_shots=requested,
            MPS_sample_calls_this_attempt=len(shots),sample_shots=shots,
            timing_scopes='nested inclusive scopes overlap; do not sum all phases; COBYLA controller excludes objective callbacks',
            quantum_hardware=False,simulator='MPS',classical_optimizer='COBYLA',
            cached_work='replayed objective calls can reuse cached samples; only fresh sample() calls are counted here',
            RSS_process_lifetime_HWM_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024))
