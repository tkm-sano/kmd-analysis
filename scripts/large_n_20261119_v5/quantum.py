"""Independent compact-memory and polynomial-local-oracle QAOA variants.

Permutation registers contain customers 1..n and separator 0 exactly once.
Adjacent register partial-SWAPs preserve the labelled permutation subspace.
No classical optimum is supplied to either sampler.
"""
from collections import Counter
import ctypes
from dataclasses import asdict
import math
from pathlib import Path
import time
import numpy as np
from kmd_toc.d_local_design.model import Encoding,Decision,candidate_count,direct_cost

HERE=Path(__file__).resolve().parent


def compact_table(local):
    q=Encoding('compact_rank_split',local.customer_ids).q
    d=np.ascontiguousarray(local.distance_m,dtype=np.float64)
    bound=max(1.,(local.n+2)*float(d.max()))
    e=np.empty(1<<q,dtype=np.float64)
    lib=ctypes.CDLL(str(HERE/'cost_table.so'))
    fn=lib.fill_cost
    ptr=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
    fn.argtypes=[ctypes.c_int,ptr,ptr,ctypes.c_uint64,ctypes.c_double]
    fn.restype=ctypes.c_uint64
    count=fn(local.n,d,e,len(e),bound)
    if count!=candidate_count(local.n):raise ValueError('COMPACT_TABLE_SIZE')
    return e,bound


def compact_state(energy,angles,timing=None):
    from qulacs import QuantumState
    from qulacs.gate import H,RX,DiagonalMatrix
    begin=time.perf_counter();q=(len(energy)-1).bit_length();state=QuantumState(q)
    for b in range(q):H(b).update_quantum_state(state)
    if timing is not None:timing['simulation_s']+=time.perf_counter()-begin
    for gamma,beta in np.asarray(angles).reshape(-1,2):
        begin=time.perf_counter()
        phase=np.empty(len(energy),dtype=np.complex128)
        # Small chunks avoid full-size multiply/exp intermediate arrays.
        for start in range(0,len(energy),1<<18):
            stop=min(len(energy),start+(1<<18))
            np.multiply(energy[start:stop],-1j*gamma,out=phase[start:stop])
            np.exp(phase[start:stop],out=phase[start:stop])
        gate=DiagonalMatrix(list(range(q)),phase)
        del phase
        if timing is not None:timing['circuit_s']+=time.perf_counter()-begin
        begin=time.perf_counter()
        gate.update_quantum_state(state);del gate
        # Qulacs RX(theta)=exp(+i theta X/2), opposite Qiskit RX convention.
        for b in range(q):RX(b,float(-2*beta)).update_quantum_state(state)
        if timing is not None:timing['simulation_s']+=time.perf_counter()-begin
    return state


def initial_order(local):
    selected=set(local.customer_ids)
    original={tuple(r['trip_id']):r['original_customers'] for r in local.outside_routes}
    orders=[tuple(s for s in original[k] if s in selected) for k in local.trip_ids]
    labels={s:i+1 for i,s in enumerate(local.customer_ids)}
    return tuple(labels[s] for s in orders[0])+(0,)+tuple(labels[s] for s in orders[1])


def register_layout(n):
    width=n.bit_length()
    return width,(n+1)*width,(n+1)*width+1


def decode_register(bits,ids):
    n=len(ids);w,anc,q=register_layout(n)
    if not 0<=bits<(1<<q) or bits>>anc:raise ValueError('ANCILLA_OR_RANGE')
    labels=tuple((bits>>(i*w))&((1<<w)-1) for i in range(n+1))
    if set(labels)!=set(range(n+1)) or len(set(labels))!=n+1:raise ValueError('NOT_A_PERMUTATION')
    split=labels.index(0)
    return Decision(tuple(ids[x-1] for x in labels[:split]),tuple(ids[x-1] for x in labels[split+1:])).validate(ids)


def encode_labels(labels):
    n=len(labels)-1;w,_,_=register_layout(n)
    if set(labels)!=set(range(n+1)):raise ValueError('LABELS')
    return sum(int(a)<<(i*w) for i,a in enumerate(labels))


def proxy_lookups(local):
    d=np.asarray(local.distance_m)
    return {'edge':d.tolist(),'first':d[0].tolist(),'last':d[:,0].tolist(),
            'version':'depot_proxy_v1','bound_m':max(1.,(local.n+2)*float(d.max()))}


def boundary_lookups(p,plan,local):
    """Exact D of completed blocks up to an assignment-independent constant.

    Separator adjacency marks end of trip1 / start of trip2; no prefix flag or
    global permutation cost table is needed. W remains full-schedule evaluated.
    """
    selected=set(local.customer_ids);routes={(t.vehicle_id,t.trip_no):tuple(v.stop_id for v in t.visits) for t in plan.trips}
    ends=[]
    for key in local.trip_ids:
        route=routes[key];anchor=next((i for i,s in enumerate(route) if s in selected),len(route))
        prefix=[s for s in route[:anchor] if s not in selected]
        suffix=[s for s in route[anchor:] if s not in selected]
        ends.append((prefix[-1] if prefix else p.depot.depot_id,suffix[0] if suffix else p.depot.depot_id))
    index={s:i for i,s in enumerate(p.od.ids)}
    def dist(a,b):return float(p.od.distance_m[index[a],index[b]])
    P1,S1=ends[0];P2,S2=ends[1]
    edge=np.asarray(local.distance_m,dtype=float).copy()
    for j,s in enumerate(local.customer_ids,1):edge[j,0]=dist(s,S1);edge[0,j]=dist(P2,s)
    first=[dist(P1,S1),*(dist(P1,s) for s in local.customer_ids)]
    last=[dist(P2,S2),*(dist(s,S2) for s in local.customer_ids)]
    bound=max(1.,(local.n+2)*max(float(edge.max()),max(first),max(last)))
    return {'edge':edge.tolist(),'first':first,'last':last,'version':'boundary_D_v2',
            'bound_m':bound,'boundary_nodes':ends,'W_in_oracle':False}


def lookup_cost(labels,lookups):
    return math.fsum([lookups['first'][labels[0]],lookups['last'][labels[-1]],
                     *(lookups['edge'][a][b] for a,b in zip(labels,labels[1:]))])


def partial_swap(qc,left,right,anc,beta):
    """e^(-i beta SWAP_register), compute eigenvalue, RZ, uncompute."""
    qc.h(anc)
    for a,b in zip(left,right):qc.cswap(anc,a,b)
    qc.h(anc);qc.rz(2*beta,anc);qc.h(anc)
    for a,b in zip(left,right):qc.cswap(anc,a,b)
    qc.h(anc)


def local_phase(qc,qubits,energy,gamma):
    """Exact parameterized diagonal, Walsh coefficients + Gray parity walks.

    q local wires: 2^q-1 RZ and 2^q-2 CX; local q<=2*ceil(log2(n+1)).
    Unlike a global rank oracle this cost grows polynomially in n.
    """
    from kmd_toc.d_local_design.quantum import walsh
    coeff=walsh(energy);qc.global_phase-=gamma*float(coeff[0])
    for target in range(len(qubits)):
        previous=0
        for k in range(1<<target):
            gray=k^(k>>1)
            if k:
                bit=(gray^previous).bit_length()-1
                qc.cx(qubits[bit],qubits[target])
            qc.rz(2*gamma*float(coeff[(1<<target)|gray]),qubits[target])
            previous=gray
        if previous:qc.cx(qubits[previous.bit_length()-1],qubits[target])


def register_circuit(local,angles,lookups=None,prepare_beta=math.pi/4):
    from qiskit import QuantumCircuit
    lookups=lookups or proxy_lookups(local)
    n=local.n;w,anc,q=register_layout(n);size=1<<w
    regs=[list(range(i*w,(i+1)*w)) for i in range(n+1)]
    qc=QuantumCircuit(q)
    for i,label in enumerate(initial_order(local)):
        for b in range(w):
            if (label>>b)&1:qc.x(regs[i][b])
    def mixer(beta):
        # Fixed brickwork: even bonds, then odd bonds. Connected adjacent-swap
        # graph represents all permutations as depth increases.
        for parity in (0,1):
            for i in range(parity,n,2):partial_swap(qc,regs[i],regs[i+1],anc,beta)
    for i in range(n):partial_swap(qc,regs[i],regs[i+1],anc,math.pi/4)
    edge=np.zeros(size*size);first=np.zeros(size);last=np.zeros(size)
    for a in range(n+1):
        first[a]=lookups['first'][a]/lookups['bound_m'];last[a]=lookups['last'][a]/lookups['bound_m']
        for b in range(n+1):edge[a+(b<<w)]=lookups['edge'][a][b]/lookups['bound_m']
    for gamma,beta in np.asarray(angles).reshape(-1,2):
        local_phase(qc,regs[0],first,gamma)
        for i in range(n):local_phase(qc,regs[i]+regs[i+1],edge,gamma)
        local_phase(qc,regs[-1],last,gamma)
        mixer(beta)
    return qc


def born_sample(mps,shots,seed):
    """Exact computational-basis Born sampling of the saved approximate MPS.

    Batched conditional contractions avoid Aer rebuilding/collapsing one MPS
    for every shot. This changes the RNG implementation, not the distribution.
    """
    gamma,lambdas=mps;n=len(gamma)
    if n>63:raise ValueError('SAMPLER_UINT64_LIMIT_63_QUBITS')
    A=[tuple(np.asarray(g)*(np.asarray(lambdas[i])[None,:] if i<len(lambdas) else 1.) for g in pair)
       for i,pair in enumerate(gamma)]
    right=[None]*(n+1);right[n]=np.ones((1,1),dtype=complex)
    for i in range(n-1,-1,-1):right[i]=sum(g@right[i+1]@g.conj().T for g in A[i])
    prefix=np.ones((shots,1),dtype=complex);bits=np.zeros(shots,dtype=np.uint64)
    rng=np.random.default_rng(seed)
    for i in range(n):
        v0=prefix@A[i][0];v1=prefix@A[i][1]
        p0=np.einsum('bi,ij,bj->b',v0,right[i+1],v0.conj(),optimize=True).real
        p1=np.einsum('bi,ij,bj->b',v1,right[i+1],v1.conj(),optimize=True).real
        p0=np.maximum(p0,0);p1=np.maximum(p1,0);total=p0+p1
        if np.any(total<1e-200):raise ValueError('ZERO_MPS_CONDITIONAL_NORM')
        one=rng.random(shots)>=p0/total
        prefix=np.where(one[:,None],v1,v0)
        norm=np.where(one,p1,p0)
        prefix/=np.sqrt(np.maximum(norm,1e-300))[:,None]
        bits|=one.astype(np.uint64)<<np.uint64(i)
    return dict(Counter(format(int(x),f'0{n}b') for x in bits))


def run_kernel(local,settings,implementation,lookups=None,progress=None,bond=None,forward_only=False):
    from scipy.optimize import minimize
    timing={'table_s':0.,'circuit_s':0.,'simulation_s':0.,'decode_s':0.,'sampling_s':0.}
    history=[];n=local.n
    start=time.perf_counter()
    if implementation=='compact_qulacs':
        energy,bound=compact_table(local)
        q=Encoding('compact_rank_split',local.customer_ids).q
    elif implementation=='register_tebd':
        from fused_mps import RegisterMPS,sample as fused_sample
        lookups=lookups or proxy_lookups(local);q=register_layout(n)[2];bound=lookups['bound_m']
        from qiskit import transpile
        from qiskit.circuit import ParameterVector
        parameters=ParameterVector('theta',2*settings['p'])
        compile_start=time.perf_counter()
        template=transpile(register_circuit(local,list(parameters),lookups),
            basis_gates=['rz','sx','x','cx'],optimization_level=0,seed_transpiler=17)
        timing['compile_once_s']=time.perf_counter()-compile_start
    else:raise ValueError('IMPLEMENTATION')
    timing['table_s']=time.perf_counter()-start-timing.get('compile_once_s',0.)
    metadata=[]
    def execute(angles,shots,seed,save=False):
        begin=time.perf_counter()
        if implementation=='compact_qulacs':
            state=compact_state(energy,angles,timing)
            begin=time.perf_counter();raw=state.sampling(shots,seed)
            counts=dict(Counter(format(int(x),f'0{q}b') for x in raw))
            timing['simulation_s']+=time.perf_counter()-begin
        else:
            timing['circuit_s']+=time.perf_counter()-begin
            begin=time.perf_counter()
            width,anc,qcount=register_layout(n)
            state=RegisterMPS(initial_order(local),1<<width,max_bond=bond,threshold=1e-18)
            state.prepare_sweep()
            for gamma,beta in np.asarray(angles).reshape(-1,2):
                state.phase(lookups,float(gamma),bound);state.mixer(float(beta))
            mps=state.state()
            timing['simulation_s']+=time.perf_counter()-begin
            metadata.append({k:v for k,v in mps.items() if k!='tensors'})
            begin=time.perf_counter();counts=fused_sample(mps,shots,seed,width,qcount)
            timing['sampling_s']+=time.perf_counter()-begin
            if save:
                saved_state['mps']=mps;saved_state['max_bond']=mps['max_bond']
                saved_state['native_depth']=template.depth();saved_state['native_gates']=dict(template.count_ops())
        return counts
    def score(bits):
        value=int(bits.replace(' ',''),2)
        if implementation=='compact_qulacs':return float(energy[value])
        decision=decode_register(value,local.customer_ids)
        labels={s:i+1 for i,s in enumerate(local.customer_ids)}
        order=tuple(labels[s] for s in decision.trip_1)+(0,)+tuple(labels[s] for s in decision.trip_2)
        return lookup_cost(order,lookups)/bound
    saved_state={}
    def objective(angles):
        counts=execute(angles,settings['training_shots'],local.seed+len(history))
        invalid=0;total=0.
        for bits,c in counts.items():
            try:total+=score(bits)*c
            except ValueError:total+=2*c;invalid+=c
        value=total/settings['training_shots']
        row={'angles':list(map(float,angles)),'energy':value,'counts':counts,'invalid_samples':invalid}
        history.append(row)
        if progress:progress({'phase':'training_complete','evaluation':len(history),'shots':settings['training_shots'],**row})
        return value
    begin=time.perf_counter()
    if forward_only:
        angles=np.array(settings.get('fixed_angles',settings['initial_angles']*settings['p']));message='FORWARD_DIAGNOSTIC_NO_OPTIMIZER'
    else:
        fit=minimize(objective,settings['initial_angles']*settings['p'],method='COBYLA',
                     options={'maxiter':settings['max_evaluations'],'rhobeg':.1,'tol':.01})
        angles=fit.x;message=str(fit.message)
    optimizer_s=time.perf_counter()-begin
    counts=execute(angles,settings['final_shots'],local.seed+100000,save=True)
    if progress:progress({'phase':'final_complete','shots':settings['final_shots'],'counts':counts,'angles':list(map(float,angles))})
    begin=time.perf_counter();decoded=[];good=0;reasons=Counter()
    for bits,c in counts.items():
        index=int(bits.replace(' ',''),2)
        try:
            decision=(Encoding('compact_rank_split',local.customer_ids).decode(index) if implementation=='compact_qulacs' else decode_register(index,local.customer_ids))
            decoded.append((score(bits),index,decision,c));good+=c
        except ValueError as e:reasons[str(e)]+=c
    decoded.sort(key=lambda x:(x[0],x[1]));timing['decode_s']=time.perf_counter()-begin
    result={'implementation':implementation,'n':n,'qubits':q,'ancillas':0 if implementation=='compact_qulacs' else 1,
            'settings':settings,'seed':local.seed,'forward_only':forward_only,'angles':list(map(float,angles)),
            'history':history,'final_counts':counts,'nfev':len(history),'optimizer_s_inclusive':optimizer_s,
            'training_shots':len(history)*settings['training_shots'],'final_shots':settings['final_shots'],
            'decode_rate':good/settings['final_shots'],'invalid_reasons':dict(reasons),'timing':timing,
            'optimizer_message':message,'normalization_bound_m':bound,'metadata':metadata,
            'cost_version':lookups['version'] if lookups else 'depot_proxy_v1',
            'measurement_backend':'grouped_register_TEBD_Born_sampler_v5' if implementation=='register_tebd' else 'Qulacs_sampling',
            'MPS_circuit_evolutions_per_angle':1 if implementation=='register_tebd' else None,
            **{k:v for k,v in saved_state.items() if k!='mps'}}
    return decoded,result,saved_state.get('mps')


def mps_overlap(a,b):
    if isinstance(a,dict):
        from fused_mps import overlap
        return overlap(a,b)
    env=np.ones((1,1),dtype=complex)
    for i,(ga,gb) in enumerate(zip(a[0],b[0])):
        env=sum(x.conj().T@env@y for x,y in zip(ga,gb))
        if i<len(a[1]):env=env*np.asarray(a[1][i])[:,None]*np.asarray(b[1][i])[None,:]
    return complex(env[0,0])
