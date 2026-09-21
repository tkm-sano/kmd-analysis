"""Offline analysis AFTER pure construction. No Aer, sampler or optimizer imports."""
import argparse, itertools, os, threading, time
import numpy as np
from .common import *
from .construction import construct, validate_state, preparation
from traffic_simulation.r24_vrptw_qaoa_worker.adapter import Adapter
from traffic_simulation.r24_vrptw_qaoa_worker.contract import load, environment
from traffic_simulation.r24_vrptw_quantum_encoding_preflight.model import factorized, decode_candidate
from traffic_simulation.r24_direct_qubo.model import factorized as cvrp_factorized
from traffic_simulation.r24_qaoa_initial_state_cross_condition_reproducibility_spec.design import structured, route_words
from traffic_simulation.r24_qaoa_resource_gate_redesign.gates import GateEngine, snapshot, process_memory

class Monitor:
    def __enter__(self):
        self.done=threading.Event();self.peak=0;self.trace=[];self.start=time.monotonic()
        base=snapshot(os.getpid(),process_memory(os.getpid()),{})
        self.engine=GateEngine(base,load()['resource_gate']);self.check()
        self.thread=threading.Thread(target=self.loop,daemon=True);self.thread.start();return self
    def check(self):
        mem=process_memory(os.getpid(),self.peak);self.peak=mem['peak_rss_bytes']
        s=snapshot(os.getpid(),mem,dict(elapsed_seconds=time.monotonic()-self.start));d=self.engine.evaluate(s)
        if time.monotonic()-self.start>900:d['stop']=True;d['stop_reasons'].append('OFFLINE_WORKER_WALL_STOP')
        self.trace.append(dict(snapshot=s,decision=d))
        if d['stop']:
            dump('STOP_SNAPSHOT.json',self.trace[-1]);dump('RESOURCE_TRACE_STOP.json',self.trace)
            os._exit(75)
    def loop(self):
        while not self.done.wait(.25):self.check()
    def __exit__(self,*args):
        self.done.set();self.thread.join();self.check()
        dump('resource/'+str(time.time_ns())+'.json',self.trace)

def circuit_signature(qc):
    return digest(dict(N=qc.num_qubits,phase=str(qc.global_phase),gates=[dict(name=g.operation.name,q=[qc.find_bit(q).index for q in g.qubits],parameters=[str(x) for x in g.operation.params]) for g in qc.data]))

def counts(qc):
    return dict(qubits=qc.num_qubits,one_qubit=sum(len(g.qubits)==1 for g in qc.data),two_qubit=sum(len(g.qubits)==2 for g in qc.data),CX=int(qc.count_ops().get('cx',0)),depth=qc.depth(),identity=circuit_signature(qc))

def evolve(qc,monitor):
    from qiskit.quantum_info import Statevector
    state=Statevector.from_int(0,2**qc.num_qubits)
    # Gate-wise checkpoints permit resource STOP without waiting for a full circuit.
    for gate in qc.data:
        if monitor.done.is_set():raise RuntimeError('monitor ended')
        state=state.evolve(gate.operation,[qc.find_bit(q).index for q in gate.qubits])
    state=state*np.exp(1j*float(qc.global_phase));v=state.data
    assert np.isfinite(v).all() and abs(float(np.vdot(v,v).real)-1)<1e-10
    return v

def circuit_validation(ad,state,monitor):
    from qiskit import QuantumCircuit,transpile,qpy
    from qiskit.circuit import Parameter
    s=load();tr=s['transpilation'];params=s['parameters'];start=time.monotonic()
    prep=preparation(state);prep2=preparation(construct(dict(n=ad.model['n'],m=ad.model['m'],variable_order=ad.order)))
    assert prep==prep2
    settings={k:tr[k] for k in ('basis_gates','optimization_level','seed_transpiler','coupling_map','num_processes')}
    pt=transpile(prep,**settings)
    m=ad.model;gamma,beta=Parameter('gamma'),Parameter('beta')
    layer=QuantumCircuit(ad.N)
    a=-m['h']/2-(m['J'].sum(axis=0)+m['J'].sum(axis=1))/4
    const=m['offset']+m['h'].sum()/2+m['J'].sum()/4
    layer.global_phase=-gamma*float(const)
    for i,c in enumerate(a):
        if c:layer.rz(2*gamma*float(c),i)
    for i,j in zip(*np.nonzero(m['J'])):
        layer.cx(int(i),int(j));layer.rz(gamma*float(m['J'][i,j])/2,int(j));layer.cx(int(i),int(j))
    layer.rx(2*beta,range(ad.N))
    logical=prep.compose(layer);compiled=transpile(logical,**settings)
    bound=compiled.assign_parameters({gamma:params['initial_alpha']/params['scale'],beta:params['initial_beta']})
    assert not bound.parameters and not bound.num_clbits and compiled.layout is None
    # Check unchanged cost/X layer against the accepted offline Standard worker.
    from traffic_simulation.r24_vrptw_qaoa_worker.worker import prepare
    rid=next(r['run_id'] for r in rows(FREEZE/'RUN_PLAN.csv') if r['condition']==ad.cid)
    standard=prepare(rid,check_environment=False)
    standard_layer=standard['logical'].copy()
    for _ in range(ad.N):
        assert standard_layer.data[0].operation.name=='h';del standard_layer.data[0]
    standard_layer=standard_layer.assign_parameters({p:(gamma if p.name=='gamma' else beta) for p in standard_layer.parameters})
    assert standard_layer==layer,'cost/mixer layer changed'
    build_seconds=time.monotonic()-start
    folder=OUT/'circuits'/ad.cid;folder.mkdir(parents=True,exist_ok=True)
    for name,qc in [('preparation',pt),('combined_symbolic',compiled),('combined_bound',bound)]:
        with (folder/(name+'.qpy')).open('wb') as f:qpy.dump(qc,f)
    sanity=[]
    for phase,qc in [('preparation',pt),('fixed_parameter_norm_only',bound)]:
        t=time.monotonic();v=evolve(qc,monitor)
        item=dict(condition=ad.cid,phase=phase,engine='Qiskit quantum_info.Statevector deterministic gate evolution',qubits=ad.N,dimension=len(v),norm=float(np.vdot(v,v).real),finite=True,seconds=time.monotonic()-t,shots=0,Aer_calls=0,status='PASS')
        if phase=='preparation':
            ref=np.zeros(2**ad.N,complex);ref[state['support']]=state['amplitude']
            # Native transpilation X -> Rx(pi) is checked including global phase.
            assert np.max(abs(v-ref))<1e-12
            item.update(max_amplitude_error=float(np.max(abs(v-ref))),structured_support_mass=float(np.sum(abs(v[state['support']])**2)),amplitudes_sha256=__import__('hashlib').sha256(v.tobytes()).hexdigest())
        sanity.append(item)
    return dict(preparation_logical=counts(prep),preparation_transpiled=counts(pt),QAOA_layer=counts(transpile(layer,**settings)),combined_logical=counts(logical),combined_transpiled=counts(compiled),build_seconds=build_seconds,parameters={k:params[k] for k in ['initial_alpha','initial_beta','scale','initial_gamma']},theoretical_statevector_bytes=16*2**ad.N,planned_process_bytes=512*1024**2+8*(16*2**ad.N),sanity=sanity,cost_mixer_identity='PASS',regenerated_preparation_identity='PASS')

def masks_and_metrics(ad,state):
    """Exhaustive initial support properties, no evolved QAOA performance metrics.

Independent replay cached only by route word; slack affects capacity encoding,
not physical replay. Full masks are checked against the saved feasible authority.
"""
    m=ad.model;N=ad.N;B=state['route_qubits'];size=1<<N
    keys=['visit','slot','route','physical_capacity','capacity_encoding','temporal','depot','no_good','ancilla','evaluable','overall_feasible','optimal']
    masks={k:np.zeros(size,bool) for k in keys}
    replay_masks={k:np.zeros(1<<B,bool) for k in ['route','physical_capacity','temporal','depot','evaluable','overall']}
    waiting=[]
    for symbols in itertools.product(range(m['n']+1),repeat=m['m']*m['n']):
        bits=np.zeros(N,dtype=np.int64)
        word=sum(1<<(slot*(m['n']+1)+node) for slot,node in enumerate(symbols))
        bits[:B]=[(word>>i)&1 for i in range(B)]
        d=decode_candidate(m,bits);r=d.get('replay')
        if not r:continue
        p=d['encoding_residuals'];replay_masks['evaluable'][word]=True
        replay_masks['route'][word]=all(p[k]==0 for k in ['slot','prefix','reach']) and r['route_feasible']
        for k,rk in [('physical_capacity','capacity_feasible'),('temporal','temporal_feasible'),('depot','depot_feasible'),('overall','overall_feasible')]:replay_masks[k][word]=r[rk]
        if word==state['route_word']:
            waiting=r['customers'];dump('replay/'+ad.cid+'.json',dict(purpose='INITIAL_SUPPORT_REPLAY_DIAGNOSTIC',route_word=word,independent_validator=r))
    min_dist=np.full(size,N+1,np.uint8)
    pop=np.array([i.bit_count() for i in range(1<<16)],dtype=np.uint8)
    feasible_ids=[int(k,2) for k in ad.feasible]
    for start in range(0,size,32768):
        ids=np.arange(start,min(start+32768,size),dtype=np.int64);bits=(ids[:,None]>>np.arange(N))&1
        _,p,_=factorized(m,bits);basep=cvrp_factorized(m['base'],bits)[1]
        assert all(np.array_equal(p[k],basep[k]) for k in basep)
        ix=ids&((1<<B)-1)
        for k in ['route','physical_capacity','temporal','depot','evaluable']:masks[k][ids]=replay_masks[k][ix]
        for k,rk in [('visit','visit'),('slot','slot'),('capacity_encoding','capacity'),('ancilla','ancilla')]:masks[k][ids]=p[rk]==0
        masks['no_good'][ids]=(p['temporal']==0)&(p['depot']==0)
        masks['overall_feasible'][ids]=np.logical_and.reduce([v==0 for v in p.values()])&replay_masks['overall'][ix]
        distance=np.full(len(ids),N+1,np.uint8)
        for f in feasible_ids:
            xor=ids^f;distance=np.minimum(distance,pop[xor&65535]+pop[xor>>16])
        min_dist[ids]=distance
    assert set(np.flatnonzero(masks['overall_feasible']))==set(feasible_ids)
    masks['optimal'][[int(k,2) for k in ad.optimal]]=True
    result=[]
    for kind,ids in [('Uniform',np.arange(size)),('Structured',np.array(state['support']))]:
        hist=np.bincount(min_dist[ids],minlength=N+1)
        result.append(dict(condition=ad.cid,state=kind,qubits=N,support_size=len(ids),norm=1.,**{k+'_mass':float(v[ids].mean()) for k,v in masks.items()},
            NOT_EVALUABLE_mass=float((~masks['evaluable'][ids]).mean()),no_good_violated_mass=float((~masks['no_good'][ids]).mean()),
            nearest_mean=float(min_dist[ids].mean()),nearest_median=float(np.median(min_dist[ids])),nearest_min=int(min_dist[ids].min()),nearest_max=int(min_dist[ids].max()),
            distance_histogram=hist.tolist(),**{f'distance_le_{i}_mass':float((min_dist[ids]<=i).mean()) for i in range(5)},
            authority='EXACT_INITIAL_STATE_SUPPORT_PROPERTY; not QAOA sampling',distance_reference='condition-specific complete feasible set'))
    # Check the full structured support through the accepted independent adapter.
    for word in state['support']:
        d=ad.inspect(format(word,f'0{N}b'))
        for k,dk in [('visit','visit'),('route','route'),('physical_capacity','capacity'),('temporal','temporal'),('depot','depot'),('overall_feasible','overall_feasible'),('optimal','optimal_or_null')]:assert bool(masks[k][word])==(d[dk] is True)
    return result,waiting

def wide_regression(ad,state,metrics):
    if ad.condition['TW_regime']!='WIDE':return None
    old=next(r for r in rows(CV/'INITIAL_STATE_STATIC_DIAGNOSTICS.csv') if r['condition']==ad.cid.split('-TW-')[0])
    assert structured(ad.model['n'],ad.model['m'])==(state['route_qubits'],state['route_word'])
    assert min(route_words(ad.model['n'],ad.model['m']))==state['route_word']
    for k in ['qubits','route_qubits','route_word','support_size']:assert int(old[k])==(len(state['support']) if k=='support_size' else state[k])
    bits=(np.array(state['support'])[:,None]>>np.arange(ad.N))&1
    energy=cvrp_factorized(ad.model['base'],bits)[2]
    assert np.isclose(energy.mean(),float(old['energy_mean']),rtol=1e-12)
    assert np.isclose(energy.var(),float(old['energy_variance']),rtol=1e-12)
    a=next(x for x in metrics if x['state']=='Structured');b=next(x for x in metrics if x['state']=='Uniform')
    if ad.model['n']==2:
        oldmetrics=rows(BASE/'r24_qaoa_initial_state_mixer_ablation/20260917_v1/INITIAL_METRICS.csv')
        for new,arm in [(a,'B'),(b,'A')]:
            oldm=next(x for x in oldmetrics if x['configuration']==arm)
            for oldkey,newkey in [('feasible_mass','overall_feasible_mass'),('optimal_mass','optimal_mass'),('mean_nearest_feasible_distance','nearest_mean'),('visit_valid_mass','visit_mass'),('slot_valid_mass','slot_mass')]:assert abs(float(oldm[oldkey])-new[newkey])<1e-12
    return dict(status='PASS',support_identity=True,probability_identity=True,base_penalty_residual_identity=True,saved_energy_moments=True,prior_scientifically_executed_CVRP_size=ad.model['n']==2,N003_scope='Existing general formula/static diagnostics; N003 was not in prior 3-base scientific cross-condition execution')

def one(cid,simulate=True):
    start=time.monotonic();ad=Adapter(cid);m=ad.model
    assert not m['chains'] and m['N']==m['base']['N'],'UNHANDLED_TEMPORAL_ANCILLA_STOP'
    inputs=dict(n=m['n'],m=m['m'],variable_order=ad.order)
    state=construct(inputs);validate_state(state);assert construct(inputs)==state
    assert structured(m['n'],m['m'])==(state['route_qubits'],state['route_word'])
    with Monitor() as monitor:
        metrics,waiting=masks_and_metrics(ad,state)
        regression=wide_regression(ad,state,metrics)
        circ=circuit_validation(ad,state,monitor) if simulate else None
    result=dict(condition=cid,inputs=inputs,variable_order_hash=digest(ad.order),state=state,state_hash=digest(state),support_hash=digest(state['support']),metrics=metrics,
      temporal_patterns=len(m['patterns']),temporal_terms=len(m['terms']),temporal_ancillas=len(m['chains']),interactions=int(np.count_nonzero(m['J'])),
      wide_regression=regression,circuits=circ,waiting_records=waiting,seconds=time.monotonic()-start,peak_RSS=monitor.peak,status='PASS')
    dump('conditions/'+cid+'.json',result)
    print(json.dumps(dict(condition=cid,status='PASS',seconds=result['seconds'],structured=metrics[1],peak_RSS=monitor.peak)),flush=True)
    return result

def main():
    args=argparse.ArgumentParser();args.add_argument('--first',action='store_true');a=args.parse_args()
    environment();cs=rows(FREEZE/'SCIENTIFIC_CONDITION_SET.csv')
    if a.first:
        assert not (OUT/'FIRST_CANDIDATE_CHECKPOINT.json').exists()
        r=one(cs[0]['condition']);assert r['wide_regression']['status']=='PASS'
        dump('FIRST_CANDIDATE_CHECKPOINT.json',dict(status='PASS',condition=r['condition'],candidate='A',seconds=r['seconds'],peak_RSS=r['peak_RSS'],remaining_minutes=[15,25],basis='First WIDE exact enumeration, existing CVRP regression, preparation and fixed-parameter non-sampling statevector sanity PASS'))
    else:
        assert read(OUT/'FIRST_CANDIDATE_CHECKPOINT.json')['status']=='PASS'
        for i,c in enumerate(cs[1:],start=1):one(c['condition'],simulate=i in (1,2))
if __name__=='__main__':main()
