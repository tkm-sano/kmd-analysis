"""Order-only p2 QAOA, executed on the existing permutation-sector MPS backend.

No separator register and no cross-trip swap exists. Completed objective calls
are cached by angle+seed for deterministic COBYLA replay after interruption.
"""
from pathlib import Path
from dataclasses import asdict
import math,time,resource,json
from collections import Counter
import numpy as np
from scipy.optimize import minimize
from kmd_toc.main_experiment_d.quantum import backend_modules
from kmd_toc.main_experiment_d.depth import frozen_config as depth
from kmd_toc.main_experiment_d.shots import frozen_config as shots
from .io import read,dump,atomic,digest_payload
from .order import cost,ENCODING

class DiagnosticPause(RuntimeError):pass

def sdk_circuit(problem,angles):
    from qiskit import QuantumCircuit
    q,_=backend_modules();n=problem.n;width=max(1,(n-1).bit_length());d=1<<width
    registers=[list(range(i*width,(i+1)*width)) for i in range(n)];anc=n*width
    circuit=QuantumCircuit(anc+1)
    for i,label in enumerate(range(n)):
        for bit in range(width):
            if label>>bit&1:circuit.x(registers[i][bit])
    for i in range(n-1):q.partial_swap(circuit,registers[i],registers[i+1],anc,math.pi/4)
    first=np.zeros(d);last=np.zeros(d);edge=np.zeros(d*d);lookup=problem.lookup
    first[:n]=np.array(lookup['first'])/lookup['bound_m'];last[:n]=np.array(lookup['last'])/lookup['bound_m']
    for a in range(n):
        for b in range(n):edge[a+(b<<width)]=lookup['edge'][a][b]/lookup['bound_m']
    for layer in range(2):
        gamma,beta=angles[2*layer:2*layer+2]
        q.local_phase(circuit,registers[0],first,gamma)
        for i in range(n-1):q.local_phase(circuit,registers[i]+registers[i+1],edge,gamma)
        q.local_phase(circuit,registers[-1],last,gamma)
        for parity in (0,1):
            for i in range(parity,n-1,2):q.partial_swap(circuit,registers[i],registers[i+1],anc,beta)
    return circuit

def evolve(problem,angles,settings,emit=None):
    _,sector=backend_modules();n=problem.n;width=max(1,(n-1).bit_length())
    m=sector.SectorMPS(tuple(range(n)),1<<width,settings['mps_bond'],settings['mps_cutoff'],emit)
    m.prepare_sweep()
    for layer in range(2):
        m.layer=layer+1;m.phase(problem.lookup,angles[2*layer],problem.lookup['bound_m']);m.mixer(angles[2*layer+1])
    expected=Counter({(0,'preparation','PARTIAL_SWAP'):n-1})
    for layer in (1,2):expected.update({(layer,'oracle','SINGLE_PHASE'):2,(layer,'oracle','DISTANCE_PHASE'):n-1,(layer,'mixer','PARTIAL_SWAP'):n-1})
    actual=Counter((x['layer'],x['stage'],x['kind']) for x in m.logs if x['kind']!='QR_MOVE')
    if actual!=expected:raise ValueError('ORDER_ONLY_EXECUTED_LAYER_STRUCTURE_MISMATCH')
    state=m.state()
    if not math.isfinite(state['trace_distance_error_bound']) or not 0<=state['trace_distance_error_bound']<=settings['TV_bound_max']:
        raise ValueError('ORDER_ONLY_NUMERICAL_TV_CRITERION_FAILED')
    return state,m.logs

def decode(bits,problem):
    n=problem.n;w=max(1,(n-1).bit_length());value=int(bits,2)
    if value>>(n*w):raise ValueError('NONZERO_ANCILLA_OR_OUT_OF_RANGE')
    order=tuple((value>>(i*w))&((1<<w)-1) for i in range(n));cost(problem,order)
    return order

def run(problem,settings,output,return_limit,*,pause_after_evaluations=None):
    out=Path(output);out.mkdir(parents=True,exist_ok=True);begin=time.perf_counter();cpu=time.process_time()
    if depth()['qaoa']['depth_p']!=2 or shots()['qaoa_shots']['optimization']!=1000 or shots()['qaoa_shots']['final_extraction']!=10000:
        raise ValueError('FROZEN_P_OR_SHOTS_MISMATCH')
    if settings['optimizer_max_evaluations']<5 or settings['optimizer_restarts']!=1:
        raise ValueError('EXPLICIT_FINITE_ORDER_OPTIMIZER_CONTRACT')
    manifest=dict(problem=asdict(problem),problem_hash=problem.fingerprint,settings=settings,return_limit=return_limit,
        backend='existing permutation-sector MPS',encoding=ENCODING,p=2,optimization_shots=1000,final_shots=10000,
        assignment_fixed_in_state_space=True,separator_register=False)
    if (out/'CALL.json').exists():
        if digest_payload(read(out/'CALL.json'))!=digest_payload(manifest):raise ValueError('RESUMED_QUANTUM_CALL_IDENTITY_MISMATCH')
    else:dump(out/'CALL.json',manifest)
    if (out/'RESULT.json').exists():
        result=read(out/'RESULT.json');return result['candidates'],result
    _,sector=backend_modules();evaluations=0;cached=0;history=[]
    def execute(angles,phase,index,count,seed):
        nonlocal cached
        path=out/(f'EVAL_{index:03d}.json' if phase=='optimization' else 'FINAL_SAMPLE.json')
        params=list(map(float,angles));identity=dict(angles=params,seed=seed,shots=count,phase=phase,problem_hash=problem.fingerprint)
        if path.exists():
            value=read(path)
            if value['identity']!=identity:raise ValueError('COBYLA_REPLAY_ANGLE_OR_SEED_MISMATCH')
            cached+=1;return value
        logs=[];state,updates=evolve(problem,params,settings,logs.append)
        if 'measurement_seeds' in settings:
            bound=settings['TV_bound_max']
            estimate=state['combined_error_estimate']
            if (not math.isfinite(estimate) or estimate>bound or
                any(abs(r['state_norm_squared_center']-1)>bound or r['canonical_residual']>bound for r in updates)):
                raise ValueError('ORDER_ONLY_NUMERICAL_DIAGNOSTIC_FAILED')
        w=max(1,(problem.n-1).bit_length());counts=sector.sample(state,count,seed,w,problem.n*w+1)
        if sum(counts.values())!=count:raise ValueError('ACTUAL_SHOT_COUNT_MISMATCH')
        objective=math.fsum(cost(problem,decode(bits,problem))*v for bits,v in counts.items())/count/problem.lookup['bound_m']
        value=dict(identity=identity,counts=counts,objective=objective,TV_bound=state['trace_distance_error_bound'],
            combined_error_estimate=state['combined_error_estimate'],peak_bond=state['max_bond'],updates=updates)
        atomic(path,value)
        return value
    def objective(angles):
        nonlocal evaluations
        i=evaluations;evaluations+=1
        if evaluations>settings['optimizer_max_evaluations']:raise ValueError('ORDER_OPTIMIZATION_BUDGET_EXCEEDED')
        registered=settings.get('measurement_seeds')
        seed=registered['optimization'][i] if registered is not None else problem.seed+i
        value=execute(angles,'optimization',i,1000,seed);history.append(value)
        if pause_after_evaluations and evaluations==pause_after_evaluations:raise DiagnosticPause('saved objective checkpoint diagnostic')
        return value['objective']
    fit=minimize(objective,settings['initial_angles'],method='COBYLA',options=dict(maxiter=settings['optimizer_max_evaluations'],
        rhobeg=settings['optimizer_rhobeg'],tol=settings['optimizer_tol']))
    registered=settings.get('measurement_seeds')
    final_seed=registered['final'] if registered is not None else problem.seed+100000
    final=execute(fit.x,'final_extraction',0,10000,final_seed)
    # Frequency, then encoded bits; predeclared return cap. No global-D/W or
    # distance screening after return. No refilling if diversity is smaller.
    chosen=sorted(final['counts'],key=lambda b:(-final['counts'][b],int(b,2)))[:return_limit]
    candidates=[dict(order=list(decode(b,problem)),source='measured_order_only_QAOA',bits=b,count=final['counts'][b],
        local_distance_m=cost(problem,decode(b,problem))) for b in chosen]
    circuit=sdk_circuit(problem,list(map(float,fit.x)))
    structure=[(x.operation.name,[str(v) for v in x.operation.params],[circuit.find_bit(b).index for b in x.qubits]) for x in circuit.data]
    result=dict(status='COMPLETE',candidates=candidates,problem_hash=problem.fingerprint,encoding=ENCODING,
        p=2,optimization_shots=1000,final_shots=10000,training_evaluations=evaluations,optimizer_restarts=1,
        training_shots_actual=1000*evaluations,final_shots_actual=10000,total_shots_actual=1000*evaluations+10000,
        optimizer_success=bool(fit.success),optimizer_message=str(fit.message),optimizer_fun=float(fit.fun),
        angles=list(map(float,fit.x)),convergence_certified=False,optimality_certified=False,
        sample_counts=final['counts'],unique_samples=len(final['counts']),returned=len(candidates),return_limit=return_limit,
        return_rule='frequency descending then fixed encoded bits; dedup by permutation; no refill',
        cached_evaluations_reused=cached,raw_sample_count=1000*evaluations+10000,
        max_TV_bound=max(v['TV_bound'] for v in [*history,final]),peak_bond=max(v['peak_bond'] for v in [*history,final]),
        sdk_qubits=circuit.num_qubits,sdk_gate_counts=dict(circuit.count_ops()),sdk_structure_hash=digest_payload(structure),
        wall_s=time.perf_counter()-begin,CPU_s=time.process_time()-cpu,
        RSS_highwater_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
        backend='sector MPS simulator; no QPU',repair='NONE',previous_separator_kernel_precision_inherited=False)
    dump(out/'RESULT.json',result);return candidates,result
