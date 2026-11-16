"""Independent small Pricing benchmark. Never reads delivery data or runs DWT.
Same tensor training, exact ring-XY, penalties, depth and seeds for all adapters.
"""
from pathlib import Path
import sys,os,time,json,resource,platform,subprocess,hashlib,importlib.metadata as md
ROOT=Path(__file__).resolve().parents[1]; REPO=ROOT.parents[2]
sys.path.insert(0,str(REPO/'src'))
# Set by controller before native imports; one physical core per process.
import numpy as np
from scipy.optimize import minimize
from qiskit.quantum_info import Statevector
from kmd_toc.column_generation.aoa import PricingAOA,AOAConfig
from kmd_toc.column_generation.models import Route,reduced_cost as trip_rc
from kmd_toc.column_generation.reduction import contract
from kmd_toc.vehicle_day.fixtures import small_problem
from kmd_toc.vehicle_day.model import ObjectiveProfile
from kmd_toc.vehicle_day.generation import seed_plan,enumerate_days
from kmd_toc.vehicle_day.master import solve_lp,reduced_cost,solve_integer
from kmd_toc.vehicle_day.validation import validate_day,validate_plan
# Import the same union before timing; dependency setup is measured by controller.
from qulacs import QuantumCircuit as QulacsCircuit
from quri_parts.circuit import QuantumCircuit as QuriCircuit
from quri_parts.qulacs.simulator import evaluate_state_to_vector
from qamomile.optimization.binary_model import BinaryModel,VarType
# The reference wrappers do not pass HiGHS' native thread option. Limit only
# this independent process, preserving all model/solver options and source files.
import kmd_toc.vehicle_day.master as day_master
def one_thread(function):
    def call(*args,**kwargs):
        kwargs['options']={**kwargs.get('options',{}),'threads':1}
        return function(*args,**kwargs)
    return call
day_master.linprog=one_thread(day_master.linprog)
day_master.milp=one_thread(day_master.milp)

def backend_build(engine,angles,backend):
    if backend=='qiskit': return engine.circuit(angles)
    if backend=='qulacs':
        from qulacs import QuantumCircuit
        from qulacs.gate import DenseMatrix,RZ,PauliRotation
        c=QuantumCircuit(engine.q)
        for t in engine.positions:c.add_X_gate(engine.bit[0,t])
    else:
        from quri_parts.circuit import QuantumCircuit
        c=QuantumCircuit(engine.q)
        for t in engine.positions:c.add_X_gate(engine.bit[0,t])
    _,z,zz=engine.ising
    for gamma,beta in np.asarray(angles).reshape(-1,2):
        for i,v in z.items():
            if abs(v)>1e-14:
                if backend=='qulacs':c.add_gate(RZ(i,-2*gamma*v))
                else:c.add_RZ_gate(i,2*gamma*v)
        for (i,j),v in zz.items():
            if abs(v)>1e-14:
                if backend=='qulacs':c.add_gate(PauliRotation([i,j],[3,3],-2*gamma*v))
                else:c.add_PauliRotation_gate([i,j],[3,3],2*gamma*v)
        matrix=engine.full_xy_block(beta)
        for t in engine.positions:
            targets=[engine.bit[i,t] for i in range(engine.n)]
            if backend=='qulacs':c.add_gate(DenseMatrix(targets,matrix))
            else:c.add_UnitaryMatrix_gate(targets,matrix.tolist())
    return c

def evolve(c,backend,q):
    if backend=='qiskit':return Statevector.from_instruction(c).data
    if backend=='qulacs':
        from qulacs import QuantumState
        s=QuantumState(q);c.update_quantum_state(s);return s.get_vector()
    from quri_parts.core.state import GeneralCircuitQuantumState
    from quri_parts.qulacs.simulator import evaluate_state_to_vector
    return evaluate_state_to_vector(GeneralCircuitQuantumState(q,circuit=c)).vector

def experiment(backend,seed,case='selection'):
    t0=time.perf_counter()
    p=small_problem(4,2);profile=ObjectiveProfile('D');pool=seed_plan(p)
    lp=solve_lp(p,pool,profile,'II');assert lp['success']
    # Same three singleton domain as the small-reference day Pricing API.
    subset=(sorted(p.base.customers,key=lambda i:(-lp['dual']['customer'][i-1],i))[:3]
            if case=='selection' else list(pool[0].trips[0].customers))
    slots=len(subset)+1
    dom=contract(p.base,lp['dual']['customer'],[(i,) for i in subset],'survey',slots=slots)
    cfg=AOAConfig(slots=slots,p=2,max_evaluations=80,restarts=1,train_shots=1000,final_shots=4096,solver_seed=seed)
    e=PricingAOA(dom.pricing,dom.dual,cfg)
    formulation_s=0.
    if backend=='qamomile_ising':
        ts=time.perf_counter()
        qubo={(ids[0],ids[-1]):v for ids,v in e.polynomial.terms.items() if ids}
        model=BinaryModel.from_qubo(qubo,e.polynomial.terms.get((),0.))
        spin=model.change_vartype(VarType.SPIN)
        assert spin.num_bits==e.q
        e.ising=(spin.constant,spin.linear,spin.quad)
        new_energy=np.array([spin.calc_energy([1-2*((int(mask)>>i)&1) for i in range(e.q)]) for mask in e.indices])
        assert np.allclose(new_energy,e.energy,rtol=0,atol=1e-10)
        formulation_s=time.perf_counter()-ts
    setup=time.perf_counter()-t0
    rng=np.random.default_rng(np.random.SeedSequence(seed).spawn(1)[0])
    initial=np.array([a for layer in range(1,cfg.p+1) for a in (.1*layer/cfg.p,np.pi/4*(1-layer/(cfg.p+1)))])
    trace=[]
    def objective(a):
        prob=np.abs(e.tensor_state(a))**2;prob/=prob.sum()
        count=rng.multinomial(cfg.train_shots,prob);value=float(count@e.energy/cfg.train_shots)
        trace.append({'angles':a.tolist(),'value':value});return value
    ts=time.perf_counter();opt=minimize(objective,initial,method='COBYLA',options={'maxiter':cfg.max_evaluations,'tol':cfg.tolerance});training=time.perf_counter()-ts
    execution_backend='qiskit' if backend=='qamomile_ising' else backend
    ts=time.perf_counter();c=backend_build(e,opt.x,execution_backend);build=time.perf_counter()-ts
    ts=time.perf_counter();vec=evolve(c,execution_backend,e.q);simulation=time.perf_counter()-ts
    expected=e.tensor_state(opt.x);embedded=vec[e.indices]
    fidelity=float(abs(np.vdot(expected,embedded))**2);leak=max(0.,float(1-np.vdot(embedded,embedded).real))
    assert abs(1-fidelity)<1e-8 and leak<1e-8
    # Match final seed generation in PricingAOA.run; common sampler isolates backend.
    sampling_seed=int(rng.integers(0,2**31));prob=np.abs(embedded)**2;prob/=prob.sum()
    ts=time.perf_counter();counts=np.random.default_rng(sampling_seed).multinomial(cfg.final_shots,prob);sampling=time.perf_counter()-ts
    sampled=set();feasible=0;valid_energy=[];reasons={}
    ts=time.perf_counter()
    for k,count in enumerate(counts):
        if not count:continue
        routes,reason=e.decode(e.sequences[k]);reasons[reason]=reasons.get(reason,0)+int(count)
        if reason=='VALID':
            feasible+=int(count);valid_energy.append(float(e.energy[k]));sampled.update(dom.expand(r) for r in routes)
    raw_sampled=sampled.copy()
    if case=='macro':
        sampled={r for r in sampled if len(r.customers)==len(subset) and set(r.customers)==set(subset)}
    partners={Route((i,)) for i in p.base.customers}|{Route(t.customers) for x in pool for t in x.trips}|sampled
    cols=enumerate_days(p,route_pool=partners,required_routes=sampled) if sampled else []
    for x in cols:assert not validate_day(p,x)
    existing={x.identity for x in pool};negative=[(reduced_cost(p,x,lp['dual'],profile),x) for x in cols if x.identity not in existing and reduced_cost(p,x,lp['dual'],profile)<-1e-7]
    new=sorted(negative,key=lambda t:(t[0],t[1].column_id))[:20]
    updated=pool+[x for _,x in new];lp_after=solve_lp(p,updated,profile,'II');ip=solve_integer(p,updated,profile)
    plancheck=validate_plan(p,ip['selected']) if ip['success'] else None
    assert lp_after['success'] and ip['success'] and plancheck['valid']
    post=time.perf_counter()-ts
    # Existing DWT's full-route acceptance applied diagnostically to same samples.
    macro_accept={r.customers for r in sampled if len(r.customers)==len(subset) and set(r.customers)==set(subset)}
    out=dict(backend=backend,case=case,seed=seed,pid=os.getpid(),affinity=sorted(os.sched_getaffinity(0)),config=vars(cfg),subset=subset,formulation_adapter_s=formulation_s,
       setup_and_RMP_s=setup,training_s=training,circuit_build_s=build,state_evolution_s=simulation,sampling_s=sampling,postprocess_completion_RMP_IP_validation_s=post,
       pricing_kernel_s=training+build+simulation+sampling+formulation_s,small_pipeline_s=time.perf_counter()-t0,
       feasible_rate=feasible/cfg.final_shots,best_penalized_sample_energy=min((float(e.energy[k]) for k,count in enumerate(counts) if count),default=None),
       best_valid_energy=min(valid_energy,default=None),best_trip_rc=min((trip_rc(p.base,r,lp['dual']['customer']) for r in sampled),default=None),
       routes=[list(r.customers) for r in sorted(sampled)],raw_distinct_routes=len(raw_sampled),distinct_routes=len(sampled),
       changed_set_routes=sum(frozenset(r.customers) not in {frozenset(t.customers) for c in pool for t in c.trips} for r in sampled),
       DWT_full_macro_accepted=len(macro_accept),negative_valid_day_columns=len(negative),added_columns=len(new),
       best_true_day_rc=min((rc for rc,x in negative),default=None),initial_lp=lp['objective'],updated_lp=lp_after['objective'],integer_objective=ip['objective'],final_plan=plancheck,
       qubits=e.q,one_hot_states=len(e.assignments),statevector_bytes=16*(1<<e.q),
       logical_depth=int(c.depth() if execution_backend=='qiskit' else c.calculate_depth() if execution_backend=='qulacs' else c.depth),
       fidelity=fidelity,leakage=leak,optimized_angles=opt.x.tolist(),nfev=int(opt.nfev),optimizer_success=bool(opt.success),optimizer_message=str(opt.message),
       trace=trace,sampling_seed=sampling_seed,sample_counts=counts.tolist(),reason_counts=reasons,
       max_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,cpu_s=resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime)
    return out

if __name__=='__main__':
    backend=sys.argv[1];seed=int(sys.argv[2]);dest=Path(sys.argv[3]);case=sys.argv[4] if len(sys.argv)>4 else 'selection'
    begin=time.perf_counter();result=experiment(backend,seed,case)
    result['worker_measured_s']=time.perf_counter()-begin
    dest.write_text(json.dumps(result,indent=2,default=lambda x:x.item() if hasattr(x,'item') else str(x)))
    print(backend,seed,result['pricing_kernel_s'],result['fidelity'])
