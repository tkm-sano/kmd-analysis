"""Independent adapters. No production file edits; exact original AOA semantics.
Qamomile constructs expressions directly from the instance (not native terms).
"""
from pathlib import Path
import sys,time,resource
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parents[2]
sys.path.insert(0,str(REPO/'src'))
import numpy as np
from scipy.optimize import minimize
from qiskit.quantum_info import Statevector
from collections import Counter
from dataclasses import asdict
from kmd_toc.column_generation.aoa import PricingAOA as OriginalAOA,AOAConfig,Polynomial
from kmd_toc.column_generation.models import Instance,Route,reduced_cost
from qulacs import QuantumCircuit as QLCircuit,QuantumState
from qulacs.gate import DenseMatrix,RZ,PauliRotation
from quri_parts.circuit import QuantumCircuit as QPCircuit
from quri_parts.qulacs.circuit import convert_circuit
from qamomile.optimization.binary_model import BinaryExpr,BinaryModel,VarType,binary


def memory():
    status={s.split(':',1)[0]:s.split(':',1)[1].strip() for s in Path('/proc/self/status').read_text().splitlines() if ':' in s}
    return {'ru_maxrss_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'VmHWM_KiB':int(status['VmHWM'].split()[0]),'threads':int(status['Threads'])}


class QamomilePolynomial:
    def __init__(self,engine):
        start=time.perf_counter();c=engine.config;n=engine.n
        variables={(i,t):binary(engine.bit[i,t]) for t in engine.positions for i in range(n)}
        def x(i,t):
            if c.fixed_depot and t==0:return BinaryExpr(constant=float(i==0))
            return variables[i,t]
        expression=BinaryExpr()
        for t in range(c.slots):
            for i in range(n):
                expression+=-float(engine.dual[i])*x(i,t)
                for j in range(n):
                    expression+=float(engine.instance.distance[i,j])*x(i,t)*x(j,(t+1)%c.slots)
        h=BinaryExpr(constant=-float(engine.instance.capacity))
        for t in range(c.slots):
            for i,d in enumerate(engine.instance.demand):h+=float(d)*x(i,t)
        expression+=c.lambda_capacity*(h+h*h)
        groups=([[(i,t) for t in range(c.slots)] for i in range(1,n)] if c.penalty=='customer_unique'
                else [[(i,t) for i in range(n)] for t in range(c.slots)])
        for group in groups:
            u=BinaryExpr()
            for i,t in group:u+=x(i,t)
            expression+=c.lambda_visit*(u*u+(-1.)*u)
        self.model=BinaryModel(expression)
        assert self.model.num_bits==engine.q,'Qamomile variable compaction changes mapping'
        self.terms={():self.model.constant,**self.model.coefficients}
        self.build_s=time.perf_counter()-start
        start=time.perf_counter();self.spin=self.model.change_vartype(VarType.SPIN)
        self.conversion_s=time.perf_counter()-start
    def ising(self):return self.spin.constant,dict(self.spin.linear),dict(self.spin.quad)
    def value(self,mask):return self.model.calc_energy([(int(mask)>>i)&1 for i in range(self.model.num_bits)])


def build(engine,angles,backend):
    if backend=='qiskit':return OriginalAOA.circuit(engine,angles)
    quri=backend in ('quri','qamomile_quri')
    c=QPCircuit(engine.q) if quri else QLCircuit(engine.q)
    for t in engine.positions:c.add_X_gate(engine.bit[0,t])
    _,z,zz=engine.ising
    for gamma,beta in np.asarray(angles).reshape(-1,2):
        for i,v in z.items():
            if abs(v)>1e-14:
                if quri:c.add_RZ_gate(i,2*gamma*v)
                else:c.add_gate(RZ(i,-2*gamma*v))
        for (i,j),v in zz.items():
            if abs(v)>1e-14:
                if quri:c.add_PauliRotation_gate([i,j],[3,3],2*gamma*v)
                else:c.add_gate(PauliRotation([i,j],[3,3],-2*gamma*v))
        u=engine.full_xy_block(beta)
        for t in engine.positions:
            targets=[engine.bit[i,t] for i in range(engine.n)]
            if quri:c.add_UnitaryMatrix_gate(targets,u.tolist())
            else:c.add_gate(DenseMatrix(targets,u))
    return c


def simulate(circuit,q,backend):
    """Separate QURI lowering from native simulation. Return times and vector."""
    ts=time.perf_counter()
    if backend in ('quri','qamomile_quri'):native=convert_circuit(circuit)
    else:native=circuit
    conversion=time.perf_counter()-ts if backend in ('quri','qamomile_quri') else 0.
    ts=time.perf_counter()
    if backend=='qiskit':vector=Statevector.from_instruction(native).data
    else:
        state=QuantumState(q);native.update_quantum_state(state);vector=state.get_vector()
    return vector,conversion,time.perf_counter()-ts,native


def depths(c,backend):
    return int(c.depth() if backend=='qiskit' else c.depth if backend in ('quri','qamomile_quri') else c.calculate_depth())


def compare_states(reference,other,energy=None):
    overlap=np.vdot(reference,other);phase=overlap/abs(overlap) if abs(overlap)>0 else 1.
    p=np.abs(reference)**2;po=np.abs(other)**2
    return {'fidelity':float(abs(overlap)**2),'phase_aligned_max_abs':float(np.max(np.abs(other-phase*reference))),
            'probability_max_abs':float(np.max(np.abs(p-po))),'probability_L1':float(np.abs(p-po).sum()),
            'expectation_abs':None if energy is None else float(abs(p@energy-po@energy))}


class BackendAOA(OriginalAOA):
    backend='qiskit'
    def _polynomial(self):
        if self.backend=='qamomile_quri':return QamomilePolynomial(self)
        return super()._polynomial()
    def circuit(self,angles):return build(self,angles,self.backend)
    def run(self,native_depth=False):
        assert not native_depth,'Native hardware transpilation is not part of this adapter'
        begin=time.perf_counter();c=self.config
        histories=[];routes=set();reasons=Counter();feasible=improving=measured=0
        timing=Counter();max_infidelity=max_leakage=0.
        for restart,seed in enumerate(np.random.SeedSequence(c.solver_seed).spawn(c.restarts)):
            rng=np.random.default_rng(seed)
            initial=np.array([a for layer in range(1,c.p+1) for a in (.1*layer/c.p,np.pi/4*(1-layer/(c.p+1)))])
            if restart:initial=rng.uniform(0,1,2*c.p)*np.tile([2*np.pi,np.pi],c.p)
            evaluations=[]
            def objective(angles):
                probabilities=np.abs(self.tensor_state(angles))**2;probabilities/=probabilities.sum()
                counts=rng.multinomial(c.train_shots,probabilities);value=float(counts@self.energy/c.train_shots)
                evaluations.append({'angles':np.asarray(angles).tolist(),'sample_mean':value});return value
            ts=time.perf_counter();opt=minimize(objective,initial,method='COBYLA',options={'maxiter':c.max_evaluations,'tol':c.tolerance});timing['training_s']+=time.perf_counter()-ts
            final_begin=time.perf_counter();ts=time.perf_counter();qc=self.circuit(opt.x);timing['circuit_build_s']+=time.perf_counter()-ts
            vector,conversion,evolution,_=simulate(qc,self.q,self.backend);timing['conversion_s']+=conversion;timing['statevector_s']+=evolution
            ts=time.perf_counter();tensor=self.tensor_state(opt.x);embedded=vector[self.indices]
            fidelity=float(abs(np.vdot(tensor,embedded))**2);leakage=max(0.,float(1-np.vdot(embedded,embedded).real))
            assert abs(1-fidelity)<1e-8 and leakage<1e-8,'Backend / one-hot tensor mismatch'
            max_infidelity=max(max_infidelity,abs(1-fidelity));max_leakage=max(max_leakage,leakage)
            timing['validation_s']+=time.perf_counter()-ts
            # Exactly the current final Qiskit sampling API for all statevectors.
            ts=time.perf_counter();state=Statevector(vector);state.seed(int(rng.integers(0,2**31)))
            counts=state.sample_counts(c.final_shots);timing['sampling_s']+=time.perf_counter()-ts
            ts=time.perf_counter()
            for bits,count in counts.items():
                mask=int(bits,2);measured+=int(count)
                if mask not in self.index_to_sequence:reasons['ONE_HOT_VIOLATION']+=int(count);continue
                candidates,reason=self.decode(self.index_to_sequence[mask]);reasons[reason]+=int(count)
                if reason=='VALID':
                    feasible+=int(count)
                    if any(reduced_cost(self.instance,r,self.dual[1:])<-1e-7 for r in candidates):improving+=int(count)
                    routes.update(candidates)
            timing['decode_s']+=time.perf_counter()-ts;timing['final_s']+=time.perf_counter()-final_begin
            histories.append({'restart':restart,'initial_angles':initial.tolist(),'optimized_angles':opt.x.tolist(),'nfev':int(opt.nfev),
                              'optimizer_success':bool(opt.success),'optimizer_message':str(opt.message),'evaluations':evaluations,'qiskit_counts':dict(counts)})
        return {'routes':[list(r.customers) for r in sorted(routes)],'config':asdict(c),'qubits':self.q,'logical_depth':depths(qc,self.backend),
                'logical_gates':dict(qc.count_ops()) if self.backend=='qiskit' else {},'native_circuit':None,
                'raw_statevector_bytes':16*(1<<self.q),'one_hot_basis_states':len(self.assignments),
                'measured_shots':measured,'feasible_shots':feasible,'improving_shots':improving,'feasible_rate':feasible/measured,'improving_rate':improving/measured,
                'reason_counts':dict(reasons),'qiskit_tensor_max_infidelity':max_infidelity,'qiskit_one_hot_max_leakage':max_leakage,
                'training_seconds':timing['training_s'],'qiskit_seconds':timing['final_s'],'total_seconds':time.perf_counter()-begin,
                'history':histories,'backend':self.backend,'timing':dict(timing),'internal_depot_handling':'split at depot; free-fleet reference only'}


def backend_class(name):
    return type('ConfiguredAOA',(BackendAOA,),{'backend':name})


def set_native_threads():
    # Independent process only. SciPy forwards this option to HiGHS.
    import kmd_toc.vehicle_day.master as master
    for name in ['linprog','milp']:
        original=getattr(master,name)
        if getattr(original,'_one_thread',False):continue
        def wrapper(*args,_original=original,**kwargs):
            kwargs['options']={**kwargs.get('options',{}),'threads':1};return _original(*args,**kwargs)
        wrapper._one_thread=True;setattr(master,name,wrapper)
