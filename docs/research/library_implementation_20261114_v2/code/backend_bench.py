"""Fixed-angle scaling benchmark. One warm-up + seven timed repetitions."""
import sys,json,time,os,gc
from pathlib import Path
from adapters import *

def instance(nodes):
    d=np.array([[0. if i==j else (7*i+3*j+5)%13/10+.1 for j in range(nodes)] for i in range(nodes)])
    return Instance(f'backend_n{nodes}',d,(0,)+(1,)*(nodes-1),2)

def run(backend,nodes,slots,p):
    q=nodes*(slots-1);assert q<=16 and 16*(1<<q)<=2**20
    cfg=AOAConfig(slots=slots,p=p,max_evaluations=80,restarts=1,solver_seed=1101)
    e=OriginalAOA(instance(nodes),np.arange(1,nodes)/3,cfg)
    angles=np.random.default_rng(20261114+p).uniform(.1,.8,2*p)
    expected=np.zeros(1<<q,dtype=complex);expected[e.indices]=e.tensor_state(angles)
    rows=[]
    for rep in range(-1,7):
        gc.collect();begin=time.perf_counter()
        ts=time.perf_counter();c=build(e,angles,backend);construction=time.perf_counter()-ts
        v,conv,evolution,_=simulate(c,q,backend)
        ts=time.perf_counter();prob=np.abs(v)**2;prob/=prob.sum();probability=time.perf_counter()-ts
        ts=time.perf_counter();samples=np.random.default_rng(1101+rep).choice(len(prob),size=4096,p=prob)
        counts=Counter(format(int(k),f'0{q}b') for k in samples);sampling=time.perf_counter()-ts
        total=time.perf_counter()-begin
        check=compare_states(expected,v)
        check['expectation_abs']=float(abs((abs(v[e.indices])**2)@e.energy-(abs(expected[e.indices])**2)@e.energy))
        check['leakage']=max(0.,1-float((abs(v[e.indices])**2).sum()))
        assert abs(1-check['fidelity'])<1e-8 and check['phase_aligned_max_abs']<1e-9
        assert check['probability_L1']<1e-9 and check['expectation_abs']<1e-8
        rows.append(dict(repetition=rep,warmup=rep==-1,circuit_build_s=construction,conversion_s=conv,statevector_s=evolution,
                         probability_s=probability,sampling_s=sampling,total_s=total,
                         execution_excluding_conversion_s=evolution+probability+sampling,
                         execution_including_conversion_s=conv+evolution+probability+sampling,
                         equality=check,sampling_seed=1101+rep,counts=counts))
    return dict(backend=backend,nodes=nodes,slots=slots,p=p,qubits=q,logical_depth=depths(c,backend),angles=angles.tolist(),
                statevector_estimated_bytes=16*(1<<q),rows=rows,memory=memory(),pid=os.getpid(),affinity=sorted(os.sched_getaffinity(0)))

if __name__=='__main__':
    b,n,s,p,dest=sys.argv[1:];Path(dest).write_text(json.dumps(run(b,int(n),int(s),int(p)),indent=2))
